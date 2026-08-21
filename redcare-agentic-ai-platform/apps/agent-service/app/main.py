"""
CareCopilot agent service — HTTP surface.

Three groups of endpoints, and the split is the point:

  /v1/*        the tenant's product API      (chat, approvals, sessions)
  /platform/*  the platform's control plane  (catalogue, keys, tools, SLOs, evals)
  /metrics,/healthz,/readyz   the operator's contract with Kubernetes/Container Apps

A platform product manager should be able to open /platform/* and answer "what
can this thing do, who is allowed to do it, what does it cost, and is it safe"
without reading any code. That is the internal developer experience this role
is accountable for.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

import app.tools.pharmacy  # noqa: F401  — registers the tool surface on import
from app.agents.orchestrator import orchestrator
from app.agents.prompts import REGISTRY as PROMPT_REGISTRY
from app.config import settings
from app.evals.suite import GOLDEN_SET, run_suite
from app.gateway.catalog import CATALOG, VIRTUAL_KEYS
from app.memory.store import approvals, budgets, sessions
from app.observability import telemetry as tel
from app.tools.registry import registry

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")


@asynccontextmanager
async def lifespan(_: FastAPI):
    tel.log.info("service starting", extra={"tenant": settings.tenant_id})
    yield
    await orchestrator.client.aclose()
    tel.log.info("service stopped")


api = FastAPI(
    title="Redcare CareCopilot — Agentic AI Platform reference tenant",
    version=settings.version,
    description=(
        "Reference agent running on the Redcare Agentic AI Platform. "
        "Demonstrates gateway-mediated model access, tool orchestration, "
        "guardrails, human-in-the-loop, observability and FinOps controls."
    ),
    lifespan=lifespan,
)
api.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins) or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- request/response models -------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None
    virtual_key: str = "sk-carecopilot-dev"
    model: str | None = None
    locale: str = "en-GB"
    auto_approve: bool = False


class ApprovalDecision(BaseModel):
    approve: bool
    actor: str = "supervisor@redcare.example"
    note: str = ""


class ChaosRequest(BaseModel):
    model: str
    unhealthy: bool


# --- tenant API ----------------------------------------------------------------------------
@api.post("/v1/chat", tags=["tenant"])
async def chat(req: ChatRequest) -> dict[str, Any]:
    """One agent turn, with the full decision trace attached."""
    result = await orchestrator.run_turn(
        utterance=req.message,
        session_id=req.session_id,
        virtual_key=req.virtual_key,
        requested_model=req.model,
        locale=req.locale,
        auto_approve=req.auto_approve,
    )
    return result.as_dict()


@api.get("/v1/sessions", tags=["tenant"])
async def list_sessions() -> dict[str, Any]:
    return {
        "sessions": [
            {
                "session_id": s.session_id,
                "tenant": s.tenant,
                "turns": s.turns,
                "spend_usd": round(s.spend_usd, 6),
                "created_at": s.created_at,
                "messages": len(s.messages),
            }
            for s in sessions.all()
        ]
    }


@api.delete("/v1/sessions/{session_id}", tags=["tenant"])
async def reset_session(session_id: str) -> dict[str, Any]:
    return {"deleted": sessions.reset(session_id), "session_id": session_id}


# --- human-in-the-loop -----------------------------------------------------------------------
@api.get("/v1/approvals", tags=["human-in-the-loop"])
async def list_approvals() -> dict[str, Any]:
    return {
        "pending": [a.as_dict() for a in approvals.pending()],
        "all": [a.as_dict() for a in approvals.all()[:50]],
    }


@api.post("/v1/approvals/{approval_id}", tags=["human-in-the-loop"])
async def decide_approval(approval_id: str, body: ApprovalDecision) -> dict[str, Any]:
    req = approvals.decide(approval_id, approve=body.approve, actor=body.actor, note=body.note)
    if req is None:
        raise HTTPException(404, "No pending approval with that id.")
    executed: dict[str, Any] | None = None
    if body.approve:
        executed = await registry.invoke(req.tool, req.arguments)
        tel.TOOL_CALLS.labels("pharmacy-care", req.tool, "ok").inc()
    tel.record_audit(
        event="approval_decided",
        approval_id=approval_id,
        tool=req.tool,
        decision=req.status,
        actor=body.actor,
        note=body.note,
        session_id=req.session_id,
    )
    return {"approval": req.as_dict(), "executed": executed}


# --- platform control plane -------------------------------------------------------------------
@api.get("/platform/catalog", tags=["platform"])
async def model_catalog() -> dict[str, Any]:
    """What models exist, where they run, what they cost, what they fail over to."""
    return {
        "models": [m.as_dict() for m in CATALOG.values()],
        "unhealthy": sorted(orchestrator.unhealthy),
    }


@api.get("/platform/keys", tags=["platform"])
async def virtual_keys() -> dict[str, Any]:
    """Virtual keys are the unit of governance: entitlement + rate limit + budget + owner."""
    return {
        "keys": [
            {
                **k.__dict__,
                "allowed_models": list(k.allowed_models),
                "spend_today_usd": round(budgets.spent(k.tenant), 6),
                "budget_remaining_usd": round(budgets.remaining(k.tenant, k.daily_budget_usd), 6),
            }
            for k in VIRTUAL_KEYS.values()
        ]
    }


@api.get("/platform/tools", tags=["platform"])
async def tool_catalog() -> dict[str, Any]:
    """Every tool with its governance metadata — the agent's declared blast radius."""
    return {"tools": [t.card() for t in registry.all()]}


@api.get("/platform/prompts", tags=["platform"])
async def prompt_catalog() -> dict[str, Any]:
    return {
        "prompts": [
            {
                "prompt_id": p.prompt_id,
                "version": p.version,
                "owner": p.owner,
                "eval_suite": p.eval_suite,
                "template": p.template,
            }
            for p in PROMPT_REGISTRY.values()
        ]
    }


@api.get("/platform/slo", tags=["platform"])
async def slos() -> dict[str, Any]:
    return tel.slo_snapshot()


@api.get("/platform/spend", tags=["platform"])
async def spend() -> dict[str, Any]:
    return {
        "by_tenant": budgets.snapshot(),
        "ledger": list(tel.SPEND_LEDGER)[:100],
        "limits": {k.tenant: k.daily_budget_usd for k in VIRTUAL_KEYS.values()},
    }


@api.get("/platform/traces", tags=["platform"])
async def traces(limit: int = 25) -> dict[str, Any]:
    return {"traces": list(tel.RECENT_TRACES)[:limit]}


@api.get("/platform/audit", tags=["platform"])
async def audit(limit: int = 100) -> dict[str, Any]:
    """Append-only decision log — EU AI Act Art. 12 record-keeping."""
    return {"entries": list(tel.AUDIT_LOG)[:limit]}


@api.get("/platform/governance", tags=["platform"])
async def governance() -> dict[str, Any]:
    """The compliance posture of this tenant, as data rather than a slide."""
    return {
        "tenant": settings.tenant_id,
        "eu_ai_act": {
            "risk_tier": settings.eu_ai_act_risk_tier,
            "rationale": (
                "Customer-facing informational assistant. Not a medical device "
                "and not a diagnostic system: all clinical judgement is routed "
                "to a registered pharmacist, which keeps it out of Annex III."
            ),
            "obligations": [
                {
                    "article": "Art. 50 — transparency",
                    "control": "Every reply carries an AI disclosure and a non-advice notice.",
                    "implemented_by": "guardrails.ensure_disclaimer",
                    "status": "met",
                },
                {
                    "article": "Art. 12 — record-keeping",
                    "control": "Append-only audit log with 10-year retention in Log Analytics.",
                    "implemented_by": "telemetry.record_audit",
                    "status": "met",
                },
                {
                    "article": "Art. 14 — human oversight",
                    "control": "Side-effecting tools blocked behind explicit human approval.",
                    "implemented_by": "orchestrator HITL gate",
                    "status": "met",
                },
                {
                    "article": "Art. 15 — accuracy & robustness",
                    "control": "Groundedness scorer plus a CI eval gate at 0.95.",
                    "implemented_by": "evals.suite.THRESHOLDS",
                    "status": "met",
                },
            ],
        },
        "gdpr": {
            "lawful_basis": "Art. 6(1)(b) contract; Art. 9(2)(h) health data for pharmacy care",
            "data_residency": "EU only — Sweden Central primary, West Europe failover",
            "minimisation": "Direct identifiers redacted before the model call",
            "retention": {"transcripts_days": 90, "audit_years": 10},
            "sub_processors": ["Microsoft Azure (EU)", "Anthropic (EU inference zone)"],
        },
        "data_classification": settings.data_classification,
        "controls": {
            "secrets": "Azure Key Vault + workload identity, zero secrets in code or CI",
            "network": "Private endpoints only; no public egress from the agent subnet",
            "identity": "Entra ID workload identity federation, no long-lived credentials",
            "supply_chain": "SBOM + Trivy + cosign signature verified at admission",
        },
    }


@api.post("/platform/evals/run", tags=["platform"])
async def run_evals() -> dict[str, Any]:
    """The same suite CI runs on every PR. Exposed so a PM can run it from the UI."""

    async def runner(utterance: str) -> dict[str, Any]:
        r = await orchestrator.run_turn(
            utterance=utterance, session_id=None, virtual_key="sk-carecopilot-prod"
        )
        return r.as_dict()

    report = await run_suite(runner)
    for metric, value in report["aggregate"].items():
        tel.EVAL_SCORE.labels("carecopilot-core-v3", metric).set(value)
    return report


@api.get("/platform/evals/cases", tags=["platform"])
async def eval_cases() -> dict[str, Any]:
    return {"suite": "carecopilot-core-v3", "cases": [c.__dict__ for c in GOLDEN_SET]}


@api.post("/platform/chaos", tags=["platform"])
async def chaos(body: ChaosRequest) -> dict[str, Any]:
    """
    Reliability drill: mark a deployment unhealthy and watch the router fail over.
    Real platforms need a way to *rehearse* degradation, not just document it.
    """
    if body.model not in CATALOG:
        raise HTTPException(404, f"unknown model '{body.model}'")
    if body.unhealthy:
        orchestrator.unhealthy.add(body.model)
    else:
        orchestrator.unhealthy.discard(body.model)
    tel.record_audit(
        event="chaos_toggle", model=body.model, unhealthy=body.unhealthy, actor="platform-operator"
    )
    return {"unhealthy": sorted(orchestrator.unhealthy)}


@api.get("/platform/config", tags=["platform"])
async def effective_config() -> dict[str, Any]:
    """Effective runtime config, secrets excluded — first question in every incident."""
    return {
        "service": settings.service_name,
        "environment": settings.environment,
        "version": settings.version,
        "llm_mode": settings.llm_mode,
        "gateway_base_url": settings.gateway_base_url,
        "virtual_key": settings.gateway_virtual_key[:12] + "…",
        "max_steps": settings.max_steps,
        "max_tool_calls": settings.max_tool_calls,
        "budgets": {
            "per_request_usd": settings.per_request_budget_usd,
            "per_session_usd": settings.per_session_budget_usd,
            "tenant_daily_usd": settings.daily_tenant_budget_usd,
        },
        "guardrails_enabled": settings.guardrails_enabled,
        "pii_redaction_enabled": settings.pii_redaction_enabled,
        "hitl_enabled": settings.hitl_enabled,
        "otel_endpoint": settings.otel_endpoint or "(not configured — local mode)",
    }


# --- operator contract -----------------------------------------------------------------------
@api.get("/healthz", tags=["ops"])
async def healthz() -> dict[str, str]:
    """Liveness: is the process itself sane? Never touches a dependency."""
    return {"status": "ok", "service": settings.service_name, "version": settings.version}


@api.get("/readyz", tags=["ops"])
async def readyz() -> JSONResponse:
    """Readiness: can this replica actually serve? Checks the gateway dependency."""
    checks = {
        "tools_registered": len(registry.all()) > 0,
        "catalog_loaded": len(CATALOG) > 0,
        "gateway": settings.is_mock or bool(settings.gateway_base_url),
    }
    ready = all(checks.values())
    return JSONResponse({"ready": ready, "checks": checks}, status_code=200 if ready else 503)


@api.get("/metrics", tags=["ops"])
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@api.middleware("http")
async def add_trace_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["x-service"] = settings.service_name
    response.headers["x-environment"] = settings.environment
    response.headers["x-version"] = settings.version
    return response


# --- the playground --------------------------------------------------------------------------
if os.path.isdir(STATIC_DIR):
    api.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @api.get("/", include_in_schema=False)
    async def playground() -> FileResponse:
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
