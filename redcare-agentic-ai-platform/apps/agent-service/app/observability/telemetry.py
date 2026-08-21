"""
Observability for an agentic system.

Classic APM answers "was the request fast and did it 500?". That is necessary and
nowhere near sufficient for an agent, where a request can be fast, return 200,
and still be wrong, ungrounded, unaffordable, or looping. So we emit four
families and treat all four as first-class:

  1. RED        — rate, errors, duration (the service is up)
  2. Agent      — steps per turn, tool calls, tool errors, loop terminations
  3. Quality    — guardrail firings, groundedness, escalation rate, eval scores
  4. FinOps     — tokens and cost per request / tenant / model, cache hit rate

Prometheus carries the aggregates, OpenTelemetry spans carry the causal story of
one turn, and the structured trace object carries the human-readable "why" the
playground renders. In Azure the OTLP endpoint is the OTel Collector, which fans
out to Azure Monitor / Application Insights and Managed Grafana.
"""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from collections import deque
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from prometheus_client import Counter, Gauge, Histogram

from app.config import settings

# --- 1. RED --------------------------------------------------------------------------
REQUESTS = Counter(
    "agent_requests_total", "Agent turns handled", ["tenant", "outcome", "environment"]
)
REQUEST_LATENCY = Histogram(
    "agent_request_duration_seconds",
    "End-to-end turn latency",
    ["tenant"],
    buckets=(0.25, 0.5, 1, 2, 3, 5, 8, 13, 21, 34),
)
ERRORS = Counter("agent_errors_total", "Errors by kind", ["tenant", "kind"])

# --- 2. Agent behaviour ----------------------------------------------------------------
AGENT_STEPS = Histogram(
    "agent_steps_per_turn",
    "Planner iterations per turn",
    ["tenant"],
    buckets=(1, 2, 3, 4, 5, 6, 8, 10),
)
TOOL_CALLS = Counter("agent_tool_calls_total", "Tool invocations", ["tenant", "tool", "status"])
TOOL_LATENCY = Histogram(
    "agent_tool_duration_seconds",
    "Tool latency",
    ["tool"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)
LOOP_TERMINATION = Counter(
    "agent_loop_termination_total", "Why the loop stopped", ["tenant", "reason"]
)

# --- 3. Quality / safety ----------------------------------------------------------------
GUARDRAIL_FIRINGS = Counter(
    "guardrail_firings_total", "Guardrail verdicts that triggered", ["check", "action", "severity"]
)
ESCALATIONS = Counter("agent_escalations_total", "Handovers to a human", ["tenant", "reason"])
GROUNDEDNESS = Gauge("agent_groundedness_ratio", "Share of turns fully grounded", ["tenant"])
EVAL_SCORE = Gauge("agent_eval_score", "Latest offline eval score", ["suite", "metric"])

# --- 4. FinOps ---------------------------------------------------------------------------
TOKENS = Counter("llm_tokens_total", "Tokens through the gateway", ["tenant", "model", "direction"])
COST = Counter(
    "llm_cost_usd_total", "Spend through the gateway", ["tenant", "model", "cost_centre"]
)
COST_PER_TURN = Histogram(
    "llm_cost_usd_per_turn",
    "Cost of one agent turn",
    ["tenant"],
    buckets=(0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.25, 0.5, 1.0),
)
CACHE_HITS = Counter(
    "llm_cache_events_total", "Gateway semantic-cache events", ["tenant", "result"]
)
BUDGET_REMAINING = Gauge("llm_budget_remaining_usd", "Daily budget headroom", ["tenant"])


# --- structured logging ------------------------------------------------------------------
class JsonFormatter(logging.Formatter):
    """One JSON object per line — what Azure Monitor and Loki both want."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "service": settings.service_name,
            "env": settings.environment,
            "version": settings.version,
        }
        for key in (
            "trace_id",
            "session_id",
            "tenant",
            "step",
            "tool",
            "model",
            "cost_usd",
            "latency_ms",
            "outcome",
        ):
            if (val := getattr(record, key, None)) is not None:
                payload[key] = val
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> logging.Logger:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    return logging.getLogger(settings.service_name)


log = configure_logging()


# --- spans -------------------------------------------------------------------------------
@dataclass
class Span:
    name: str
    span_id: str
    parent_id: str | None
    started_at: float
    kind: str = "internal"
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0
    status: str = "OK"

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "kind": self.kind,
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events,
        }


class Trace:
    """
    A minimal, dependency-free OTel-shaped trace.

    Why not just use the OTel SDK? We do, in production — `otel_export()` below
    converts this to OTLP. But an agent trace is also a *product surface*: it is
    what the playground renders, what an auditor reads, and what an eval replays.
    Owning the shape keeps that surface stable no matter which vendor we export to.
    """

    def __init__(
        self, trace_id: str | None = None, *, session_id: str = "", tenant: str = ""
    ) -> None:
        self.trace_id = trace_id or uuid.uuid4().hex
        self.session_id = session_id
        self.tenant = tenant
        self.started_at = time.time()
        self.spans: list[Span] = []
        self._stack: list[str] = []

    @contextmanager
    def span(self, name: str, kind: str = "internal", **attributes: Any) -> Iterator[Span]:
        s = Span(
            name=name,
            span_id=uuid.uuid4().hex[:16],
            parent_id=self._stack[-1] if self._stack else None,
            started_at=time.perf_counter(),
            kind=kind,
            attributes=dict(attributes),
        )
        self.spans.append(s)
        self._stack.append(s.span_id)
        try:
            yield s
        except Exception as exc:
            s.status = "ERROR"
            s.events.append({"name": "exception", "type": type(exc).__name__, "message": str(exc)})
            raise
        finally:
            s.duration_ms = (time.perf_counter() - s.started_at) * 1000
            self._stack.pop()

    def event(self, name: str, **attributes: Any) -> None:
        if self.spans and self._stack:
            current = next(s for s in reversed(self.spans) if s.span_id == self._stack[-1])
            current.events.append({"name": name, **attributes})

    def as_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "tenant": self.tenant,
            "spans": [s.as_dict() for s in self.spans],
            "total_ms": round((time.time() - self.started_at) * 1000, 2),
        }

    def otel_export(self) -> dict[str, Any]:
        """OTLP/JSON resource-spans payload — what the collector receives."""
        return {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            {
                                "key": "service.name",
                                "value": {"stringValue": settings.service_name},
                            },
                            {"key": "service.version", "value": {"stringValue": settings.version}},
                            {
                                "key": "deployment.environment",
                                "value": {"stringValue": settings.environment},
                            },
                            {"key": "redcare.tenant", "value": {"stringValue": self.tenant}},
                        ]
                    },
                    "scopeSpans": [
                        {
                            "scope": {"name": "carecopilot.agent"},
                            "spans": [
                                {
                                    "traceId": self.trace_id,
                                    "spanId": s.span_id,
                                    "parentSpanId": s.parent_id or "",
                                    "name": s.name,
                                    "attributes": [
                                        {"key": k, "value": {"stringValue": str(v)}}
                                        for k, v in s.attributes.items()
                                    ],
                                    "status": {"code": 2 if s.status == "ERROR" else 1},
                                }
                                for s in self.spans
                            ],
                        }
                    ],
                }
            ]
        }


# --- in-memory ring buffers (the playground's "recent activity" panes) -------------------
RECENT_TRACES: deque[dict[str, Any]] = deque(maxlen=100)
AUDIT_LOG: deque[dict[str, Any]] = deque(maxlen=500)
SPEND_LEDGER: deque[dict[str, Any]] = deque(maxlen=1000)


def record_audit(**fields: Any) -> None:
    """
    Append-only audit record.

    In Azure this is a Log Analytics custom table with an immutability policy and
    a 10-year retention tier, because EU AI Act Art. 12 requires automatic
    logging over the lifetime of the system — retention is a platform decision,
    not a per-team one.
    """
    entry = {"ts": datetime.now(UTC).isoformat(), "env": settings.environment, **fields}
    AUDIT_LOG.appendleft(entry)


def record_spend(
    *,
    tenant: str,
    model: str,
    cost_centre: str,
    cost_usd: float,
    input_tokens: int,
    output_tokens: int,
    cached: bool = False,
) -> None:
    COST.labels(tenant, model, cost_centre).inc(cost_usd)
    TOKENS.labels(tenant, model, "input").inc(input_tokens)
    TOKENS.labels(tenant, model, "output").inc(output_tokens)
    CACHE_HITS.labels(tenant, "hit" if cached else "miss").inc()
    SPEND_LEDGER.appendleft(
        {
            "ts": datetime.now(UTC).isoformat(),
            "tenant": tenant,
            "model": model,
            "cost_centre": cost_centre,
            "cost_usd": round(cost_usd, 6),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cached": cached,
        }
    )


def slo_snapshot() -> dict[str, Any]:
    """
    The SLOs the platform commits to tenants. Error budget = 1 - SLO, and burn
    rate is what pages someone — an SLO without an error budget is a wish.
    """
    return {
        "slos": [
            {
                "name": "gateway availability",
                "objective": "99.9%",
                "window": "30d",
                "indicator": "successful /chat/completions ÷ total",
                "error_budget_min": 43.2,
            },
            {
                "name": "agent turn latency",
                "objective": "p95 < 4.0s",
                "window": "30d",
                "indicator": "agent_request_duration_seconds",
                "error_budget_min": 43.2,
            },
            {
                "name": "groundedness",
                "objective": "≥ 97% of turns fully grounded",
                "window": "7d",
                "indicator": "agent_groundedness_ratio",
                "error_budget_min": 302.4,
            },
            {
                "name": "guardrail coverage",
                "objective": "100% of turns pass both pipelines",
                "window": "30d",
                "indicator": "guardrail_firings_total ÷ agent_requests_total",
                "error_budget_min": 0,
            },
        ],
        "burn_rate_alerts": [
            {
                "severity": "page",
                "condition": "14.4x burn over 1h",
                "meaning": "2% of the 30-day budget in an hour — someone wakes up",
            },
            {
                "severity": "ticket",
                "condition": "6x burn over 6h",
                "meaning": "degradation that will exhaust the budget this week",
            },
        ],
    }
