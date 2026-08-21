"""
Runtime configuration for the CareCopilot agent service.

Every value is 12-factor: environment first, safe default second. In Azure the
values arrive as container env vars that Terraform wires to Key Vault secret
references, so the application code never sees a secret literal.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    # --- identity of this workload -------------------------------------------------
    service_name: str = os.getenv("SERVICE_NAME", "carecopilot-agent")
    environment: str = os.getenv("ENVIRONMENT", "local")
    version: str = os.getenv("APP_VERSION", "1.4.0")

    # --- LLM access (always through the gateway, never straight to a provider) ------
    # mock     -> deterministic in-process model, zero credentials, used by the playground and CI
    # litellm  -> real LiteLLM proxy (OpenAI-compatible /chat/completions)
    llm_mode: str = os.getenv("LLM_MODE", "mock")
    gateway_base_url: str = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
    gateway_virtual_key: str = os.getenv("LITELLM_VIRTUAL_KEY", "sk-carecopilot-dev")
    gateway_timeout_s: float = _float("LITELLM_TIMEOUT_S", 30.0)

    # --- agent loop ----------------------------------------------------------------
    max_steps: int = _int("AGENT_MAX_STEPS", 6)
    max_tool_calls: int = _int("AGENT_MAX_TOOL_CALLS", 8)
    default_model: str = os.getenv("AGENT_DEFAULT_MODEL", "carecopilot-balanced")

    # --- FinOps guardrails ---------------------------------------------------------
    per_request_budget_usd: float = _float("BUDGET_PER_REQUEST_USD", 0.08)
    per_session_budget_usd: float = _float("BUDGET_PER_SESSION_USD", 0.50)
    daily_tenant_budget_usd: float = _float("BUDGET_TENANT_DAILY_USD", 25.0)

    # --- safety --------------------------------------------------------------------
    guardrails_enabled: bool = _bool("GUARDRAILS_ENABLED", True)
    pii_redaction_enabled: bool = _bool("PII_REDACTION_ENABLED", True)
    hitl_enabled: bool = _bool("HITL_ENABLED", True)

    # --- observability -------------------------------------------------------------
    otel_endpoint: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    trace_sample_rate: float = _float("OTEL_TRACES_SAMPLER_ARG", 1.0)

    # --- platform metadata (used by the scorecard / catalogue) ---------------------
    tenant_id: str = os.getenv("TENANT_ID", "pharmacy-care")
    cost_centre: str = os.getenv("COST_CENTRE", "cc-4711-customer-care")
    data_classification: str = os.getenv("DATA_CLASSIFICATION", "confidential-health")
    eu_ai_act_risk_tier: str = os.getenv("EU_AI_ACT_RISK_TIER", "limited-risk")

    allowed_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()
        )
    )

    @property
    def is_mock(self) -> bool:
        return self.llm_mode == "mock"


settings = Settings()
