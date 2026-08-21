"""
The only place in the service that talks to a model.

Two backends, one interface:

  * LiteLLMClient  -> real HTTP call to the LiteLLM proxy's OpenAI-compatible
                      /v1/chat/completions. The proxy owns keys, budgets,
                      routing, caching, retries and logging.
  * MockClient     -> deterministic in-process model. No credentials, no
                      network, no cost. This is what makes the playground
                      runnable on a laptop and what CI uses so that agent-loop
                      tests are hermetic and repeatable.

The service never holds a provider API key in either mode. In `litellm` mode it
holds a *virtual key* — a revocable, budgeted, per-tenant credential that the
platform team issues and can rotate without redeploying the tenant.
"""

from __future__ import annotations

import json
import random
import re
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.config import settings
from app.gateway.catalog import CATALOG


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0
    cached: bool = False
    finish_reason: str = "stop"
    upstream_request_id: str = ""


class GatewayError(RuntimeError):
    """Raised when the gateway refuses or fails a call (budget, entitlement, 5xx)."""

    def __init__(self, message: str, *, status: int = 502, kind: str = "upstream_error"):
        super().__init__(message)
        self.status = status
        self.kind = kind


# ---------------------------------------------------------------------------------
# Real gateway
# ---------------------------------------------------------------------------------
class LiteLLMClient:
    """Thin OpenAI-compatible client pointed at the LiteLLM proxy."""

    def __init__(self, base_url: str, virtual_key: str, timeout_s: float = 30.0):
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout_s,
            headers={"Authorization": f"Bearer {virtual_key}"},
        )

    async def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            # LiteLLM forwards `metadata` to every configured callback (Langfuse,
            # OTel, Azure Monitor) — this is how a spend line gets a cost centre.
            "metadata": metadata or {},
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        started = time.perf_counter()
        try:
            r = await self._client.post("/v1/chat/completions", json=payload)
        except httpx.HTTPError as exc:  # network / timeout
            raise GatewayError(
                f"gateway unreachable: {exc}", status=503, kind="gateway_unreachable"
            ) from exc
        latency_ms = int((time.perf_counter() - started) * 1000)

        if r.status_code == 429:
            raise GatewayError(
                "rate limit or budget exceeded at the gateway", status=429, kind="rate_limited"
            )
        if r.status_code == 401:
            raise GatewayError("virtual key rejected", status=401, kind="unauthorised")
        if r.status_code >= 400:
            raise GatewayError(
                f"gateway returned {r.status_code}: {r.text[:300]}",
                status=r.status_code,
                kind="upstream_error",
            )

        body = r.json()
        choice = body["choices"][0]
        usage = body.get("usage", {})
        entry = CATALOG.get(model)
        in_tok = usage.get("prompt_tokens", 0)
        out_tok = usage.get("completion_tokens", 0)
        return LLMResponse(
            content=choice["message"].get("content") or "",
            tool_calls=choice["message"].get("tool_calls") or [],
            model=body.get("model", model),
            input_tokens=in_tok,
            output_tokens=out_tok,
            latency_ms=latency_ms,
            # prefer the gateway's own accounting when present; fall back to catalogue
            cost_usd=float(
                body.get("response_cost") or (entry.cost_usd(in_tok, out_tok) if entry else 0.0)
            ),
            cached=bool(body.get("cache_hit", False)),
            finish_reason=choice.get("finish_reason", "stop"),
            upstream_request_id=r.headers.get("x-litellm-call-id", ""),
        )

    async def aclose(self) -> None:
        await self._client.aclose()


# ---------------------------------------------------------------------------------
# Mock gateway — a deterministic "model" good enough to exercise the whole loop
# ---------------------------------------------------------------------------------
_ORDER_RE = re.compile(r"\b(?:RC|ORD)[- ]?(\d{6,10})\b", re.I)
_PRODUCT_HINTS = (
    "ibuprofen",
    "paracetamol",
    "aspirin",
    "warfarin",
    "metformin",
    "omeprazole",
    "sertraline",
    "amoxicillin",
    "vitamin d",
    "insulin",
    "simvastatin",
)


class MockClient:
    """
    Rule-based stand-in for a tool-calling LLM.

    It is intentionally *legible*: you can read exactly why it chose a tool. That
    makes the playground a teaching instrument rather than a black box, and it
    makes agent-loop tests deterministic. Token counts and latency are simulated
    from the catalogue entry so cost and latency panels stay realistic.
    """

    def __init__(self, seed: int = 7):
        # A fixed seed is the whole point: the playground and CI must produce the
        # same simulated latencies every run. Nothing here is a security primitive.
        self._rng = random.Random(seed)  # noqa: S311

    async def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResponse:
        entry = CATALOG.get(model) or CATALOG["carecopilot-balanced"]
        user_text = self._last_user(messages)
        called = {self._tool_name(m) for m in messages if m.get("role") == "tool"}
        observations = {
            self._tool_name(m): m.get("content", "") for m in messages if m.get("role") == "tool"
        }

        tool_calls, content = self._decide(user_text, called, observations, tools or [])

        in_tok = max(40, sum(len(str(m.get("content", ""))) for m in messages) // 4)
        out_tok = max(12, (len(content) + sum(len(json.dumps(t)) for t in tool_calls)) // 4)
        # Simulated latency jitter — a deterministic seed is the point here,
        # so a non-cryptographic generator is the correct choice.
        jitter = self._rng.uniform(0.75, 1.35)
        latency = int(entry.p50_latency_ms * jitter * (1.6 if tool_calls else 1.0))

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            model=model,
            input_tokens=in_tok,
            output_tokens=out_tok,
            latency_ms=latency,
            cost_usd=entry.cost_usd(in_tok, out_tok),
            finish_reason="tool_calls" if tool_calls else "stop",
            upstream_request_id=f"mock-{self._rng.randrange(16**8):08x}",
        )

    # -- decision table -------------------------------------------------------------
    def _decide(
        self, text: str, called: set[str], obs: dict[str, str], tools: list[dict]
    ) -> tuple[list[dict], str]:
        available = {t["function"]["name"] for t in tools}
        low = text.lower()

        def call(name: str, args: dict) -> list[dict]:
            return [
                {
                    "id": f"call_{self._rng.randrange(16**6):06x}",
                    "type": "function",
                    "function": {"name": name, "arguments": json.dumps(args)},
                }
            ]

        order_match = _ORDER_RE.search(text)
        products = [p for p in _PRODUCT_HINTS if p in low]

        # 1. order status
        if order_match and "lookup_order" in available and "lookup_order" not in called:
            return call("lookup_order", {"order_id": "RC" + order_match.group(1)}), ""

        # 2. interaction safety — always before any product advice
        if (
            len(products) >= 2
            and "check_interactions" in available
            and "check_interactions" not in called
        ):
            return call("check_interactions", {"medications": products[:4]}), ""

        # 3. availability
        if (
            products
            and any(
                w in low
                for w in ("stock", "available", "in stock", "delivery", "when can", "order")
            )
            and "check_stock" in available
            and "check_stock" not in called
        ):
            return call("check_stock", {"product": products[0]}), ""

        # 4. policy / regulatory retrieval
        if (
            any(
                w in low
                for w in (
                    "return",
                    "refund",
                    "prescription",
                    "rezept",
                    "policy",
                    "gdpr",
                    "data",
                    "cancel",
                    "insurance",
                    "reimburse",
                )
            )
            and "search_policy" in available
            and "search_policy" not in called
        ):
            return call("search_policy", {"query": text[:160]}), ""

        # 5. escalation on clinical risk
        risky = any(
            w in low
            for w in (
                "dose",
                "dosage",
                "dosier",
                "overdose",
                "how many mg",
                "how much should",
                "should i take",
                "how many tablets",
                "pregnan",
                "schwanger",
                "breastfeed",
                "chest pain",
                "bleeding",
                "side effect",
                "nebenwirkung",
                "allergic",
                "allergisch",
                "is it safe to",
            )
        )
        if (
            (risky or "HIGH_RISK" in obs.get("check_interactions", ""))
            and "escalate_to_pharmacist" in available
            and "escalate_to_pharmacist" not in called
        ):
            return call(
                "escalate_to_pharmacist",
                {
                    "reason": "clinical judgement required",
                    "summary": text[:200],
                },
            ), ""

        return [], self._answer(text, obs)

    def _answer(self, text: str, obs: dict[str, str]) -> str:
        if not obs:
            return (
                "I can help with order status, product availability, medication "
                "interaction checks, and our returns or prescription policies. "
                "Could you tell me the order number or the products involved?"
            )
        parts = ["Here is what I found:"]
        for name, payload in obs.items():
            try:
                data = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                data = {"result": payload}
            parts.append(f"- **{name}**: {self._summarise(name, data)}")
        parts.append(
            "\nThis is general pharmacy information, not medical advice. "
            "For anything about dosage or your personal treatment, a registered "
            "pharmacist will confirm before we act."
        )
        return "\n".join(parts)

    @staticmethod
    def _summarise(name: str, data: dict) -> str:
        if name == "lookup_order":
            return (
                f"order {data.get('order_id')} is **{data.get('status')}**, "
                f"carrier {data.get('carrier')}, ETA {data.get('eta')}"
            )
        if name == "check_stock":
            return (
                f"{data.get('product')} — {data.get('availability')}, "
                f"{data.get('units_available')} units, ships {data.get('ships_in')}"
            )
        if name == "check_interactions":
            return f"severity **{data.get('severity')}** — {data.get('summary', 'see detail')}"
        if name == "search_policy":
            hits = data.get("results", [])
            return "; ".join(f"{h['title']} ({h['source']})" for h in hits[:2]) or "no match"
        if name == "escalate_to_pharmacist":
            return f"ticket {data.get('ticket_id')} raised, SLA {data.get('sla')}"
        return json.dumps(data)[:180]

    @staticmethod
    def _last_user(messages: list[dict]) -> str:
        for m in reversed(messages):
            if m.get("role") == "user":
                return str(m.get("content", ""))
        return ""

    @staticmethod
    def _tool_name(message: dict) -> str:
        return message.get("name") or message.get("tool_name") or "unknown"

    async def aclose(self) -> None:  # symmetry with LiteLLMClient
        return None


def build_client():
    if settings.is_mock:
        return MockClient()
    return LiteLLMClient(
        settings.gateway_base_url, settings.gateway_virtual_key, settings.gateway_timeout_s
    )
