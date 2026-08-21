"""
Model catalogue + routing policy.

This mirrors, in code, what the LiteLLM proxy is configured to do in
`gateway/litellm/config.yaml`. Keeping a typed copy in the service lets the
playground *show* the routing decision (which is otherwise invisible inside the
proxy) and lets CI assert that the app and the gateway agree on the catalogue.

Prices are USD per 1M tokens and match Azure OpenAI / Anthropic list pricing
used for internal chargeback. They are data, not logic — a PM can change them
without touching a code path.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

Tier = Literal["fast", "balanced", "deep", "embedding"]


@dataclass(frozen=True)
class ModelEntry:
    """One deployment behind the gateway."""

    public_name: str  # what tenants ask for  ("carecopilot-balanced")
    provider: str  # azure | anthropic | self-hosted
    upstream_model: str  # what the provider actually serves
    region: str  # data residency matters for health data
    tier: Tier
    input_usd_per_mtok: float
    output_usd_per_mtok: float
    context_window: int
    p50_latency_ms: int
    supports_tools: bool = True
    fallbacks: tuple[str, ...] = ()
    data_zone: str = "eu"

    def cost_usd(self, input_tokens: int, output_tokens: int) -> float:
        return (
            input_tokens * self.input_usd_per_mtok + output_tokens * self.output_usd_per_mtok
        ) / 1_000_000

    def as_dict(self) -> dict:
        d = asdict(self)
        d["fallbacks"] = list(self.fallbacks)
        return d


# --- the catalogue the platform team publishes -------------------------------------
CATALOG: dict[str, ModelEntry] = {
    "carecopilot-fast": ModelEntry(
        public_name="carecopilot-fast",
        provider="azure",
        upstream_model="azure/gpt-4o-mini-2024-07-18",
        region="swedencentral",
        tier="fast",
        input_usd_per_mtok=0.15,
        output_usd_per_mtok=0.60,
        context_window=128_000,
        p50_latency_ms=420,
        fallbacks=("carecopilot-balanced",),
    ),
    "carecopilot-balanced": ModelEntry(
        public_name="carecopilot-balanced",
        provider="azure",
        upstream_model="azure/gpt-4o-2024-11-20",
        region="swedencentral",
        tier="balanced",
        input_usd_per_mtok=2.50,
        output_usd_per_mtok=10.00,
        context_window=128_000,
        p50_latency_ms=980,
        fallbacks=("carecopilot-balanced-westeu", "carecopilot-deep"),
    ),
    "carecopilot-balanced-westeu": ModelEntry(
        public_name="carecopilot-balanced-westeu",
        provider="azure",
        upstream_model="azure/gpt-4o-2024-11-20",
        region="westeurope",
        tier="balanced",
        input_usd_per_mtok=2.50,
        output_usd_per_mtok=10.00,
        context_window=128_000,
        p50_latency_ms=1_040,
        fallbacks=("carecopilot-deep",),
    ),
    "carecopilot-deep": ModelEntry(
        public_name="carecopilot-deep",
        provider="anthropic",
        upstream_model="anthropic/claude-sonnet-4-5",
        region="eu-central",
        tier="deep",
        input_usd_per_mtok=3.00,
        output_usd_per_mtok=15.00,
        context_window=200_000,
        p50_latency_ms=1_800,
        fallbacks=("carecopilot-balanced",),
    ),
    "carecopilot-embed": ModelEntry(
        public_name="carecopilot-embed",
        provider="azure",
        upstream_model="azure/text-embedding-3-large",
        region="swedencentral",
        tier="embedding",
        input_usd_per_mtok=0.13,
        output_usd_per_mtok=0.0,
        context_window=8_191,
        p50_latency_ms=90,
        supports_tools=False,
    ),
}


# --- virtual keys: one per tenant/team, the unit of governance ----------------------
@dataclass(frozen=True)
class VirtualKey:
    key_alias: str
    tenant: str
    cost_centre: str
    allowed_models: tuple[str, ...]
    rpm_limit: int
    tpm_limit: int
    daily_budget_usd: float
    owner_group: str  # Entra ID group that owns the key
    data_classification: str


VIRTUAL_KEYS: dict[str, VirtualKey] = {
    "sk-carecopilot-dev": VirtualKey(
        key_alias="carecopilot-dev",
        tenant="pharmacy-care",
        cost_centre="cc-4711-customer-care",
        # The regional twin of an entitled model is entitled too — otherwise the
        # key has a fallback chain it is not allowed to use, and a Sweden Central
        # outage takes the tenant down instead of failing over.
        allowed_models=(
            "carecopilot-fast",
            "carecopilot-balanced",
            "carecopilot-balanced-westeu",
            "carecopilot-embed",
        ),
        rpm_limit=60,
        tpm_limit=120_000,
        daily_budget_usd=25.0,
        owner_group="grp-ai-pharmacy-care",
        data_classification="confidential-health",
    ),
    "sk-carecopilot-prod": VirtualKey(
        key_alias="carecopilot-prod",
        tenant="pharmacy-care",
        cost_centre="cc-4711-customer-care",
        allowed_models=tuple(CATALOG.keys()),
        rpm_limit=600,
        tpm_limit=1_500_000,
        daily_budget_usd=900.0,
        owner_group="grp-ai-pharmacy-care",
        data_classification="confidential-health",
    ),
    "sk-marketing-dev": VirtualKey(
        key_alias="marketing-dev",
        tenant="growth-marketing",
        cost_centre="cc-8802-growth",
        allowed_models=("carecopilot-fast",),
        rpm_limit=30,
        tpm_limit=40_000,
        daily_budget_usd=5.0,
        owner_group="grp-ai-growth",
        data_classification="internal",
    ),
}


class RoutingDecision(dict):
    """Plain dict so it serialises straight into the trace shown in the playground."""


def resolve_model(
    requested: str,
    *,
    virtual_key: str,
    complexity: str = "standard",
    unhealthy: frozenset[str] = frozenset(),
) -> RoutingDecision:
    """
    Decide which deployment actually serves a call, and say *why*.

    Order of precedence, deliberately boring and auditable:
      1. the key must be entitled to the model            (governance)
      2. complexity may upgrade/downgrade the tier        (cost/quality)
      3. health checks may divert to a fallback           (reliability)
    """
    reasons: list[str] = []
    key = VIRTUAL_KEYS.get(virtual_key)
    if key is None:
        return RoutingDecision(selected=None, reasons=["virtual key not recognised"], denied=True)

    candidate = requested if requested in CATALOG else "carecopilot-balanced"
    if candidate != requested:
        reasons.append(f"'{requested}' not in catalogue → default 'carecopilot-balanced'")

    # 2. complexity-based tiering — the cheapest model that can do the job
    if complexity == "trivial" and "carecopilot-fast" in key.allowed_models:
        if candidate != "carecopilot-fast":
            reasons.append("classifier scored the turn 'trivial' → downshift to fast tier")
        candidate = "carecopilot-fast"
    elif complexity == "complex" and "carecopilot-deep" in key.allowed_models:
        if candidate != "carecopilot-deep":
            reasons.append("classifier scored the turn 'complex' → upshift to deep tier")
        candidate = "carecopilot-deep"

    # 1. entitlement
    if candidate not in key.allowed_models:
        allowed_same_tier = [m for m in key.allowed_models if m in CATALOG]
        if not allowed_same_tier:
            return RoutingDecision(
                selected=None,
                reasons=[*reasons, f"key '{key.key_alias}' entitled to no catalogue model"],
                denied=True,
            )
        reasons.append(
            f"key '{key.key_alias}' not entitled to '{candidate}' → '{allowed_same_tier[0]}'"
        )
        candidate = allowed_same_tier[0]

    # 3. health / failover
    hops = 0
    while candidate in unhealthy and hops < 4:
        entry = CATALOG[candidate]
        nxt = next((f for f in entry.fallbacks if f in key.allowed_models), None)
        if nxt is None:
            break
        reasons.append(f"'{candidate}' unhealthy → failover to '{nxt}'")
        candidate = nxt
        hops += 1

    if not reasons:
        reasons.append("requested model served directly")

    return RoutingDecision(
        selected=candidate,
        entry=CATALOG[candidate].as_dict(),
        reasons=reasons,
        denied=False,
        tenant=key.tenant,
        cost_centre=key.cost_centre,
    )
