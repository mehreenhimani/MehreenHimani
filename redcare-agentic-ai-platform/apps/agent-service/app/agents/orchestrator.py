"""
The agent loop.

Shape: classify -> route -> guard input -> {plan, act}* -> guard output -> respond.

Everything the loop does is recorded on a Trace and returned to the caller, so
the playground can show *why* an answer looks the way it does. That transparency
is the product: a platform that hides the agent's reasoning cannot be debugged
by the teams adopting it, and cannot be audited by the people who have to sign
it off.

Four independent stop conditions keep an agent from being a runaway process:
  max_steps        — planner iterations
  max_tool_calls   — blast radius
  per-request cost — FinOps
  per-session cost — FinOps
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.agents.prompts import SYSTEM_PROMPT
from app.config import settings
from app.gateway.catalog import CATALOG, VIRTUAL_KEYS, resolve_model
from app.gateway.client import GatewayError, LLMResponse, build_client
from app.guardrails import engine as guards
from app.memory.store import approvals, budgets, sessions
from app.observability import telemetry as tel
from app.tools.registry import registry


@dataclass
class TurnResult:
    reply: str
    session_id: str
    trace_id: str
    model_used: str
    routing: dict[str, Any]
    steps: list[dict[str, Any]] = field(default_factory=list)
    guardrails: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    stop_reason: str = "completed"
    escalated: bool = False
    pending_approval: dict[str, Any] | None = None
    session_spend_usd: float = 0.0
    tenant_spend_usd: float = 0.0
    trace: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


_TRIVIAL_RE = re.compile(
    r"^\s*(hi|hello|hey|hallo|guten tag|thanks|danke|thank you|"
    r"bye|tschüss)\b[\s!.?]*$",
    re.I,
)
_COMPLEX_HINTS = (
    "interaction",
    "wechselwirkung",
    "pregnan",
    "schwanger",
    "dose",
    "dosier",
    "side effect",
    "nebenwirkung",
    "allergic",
    "allergisch",
    "complaint",
    "beschwerde",
    "unacceptable",
    "lawyer",
    "anwalt",
    "chest pain",
    "bleeding",
)


class Orchestrator:
    def __init__(self) -> None:
        self.client = build_client()
        self.unhealthy: set[str] = set()  # toggled by the playground's chaos switch

    # -- helpers -----------------------------------------------------------------------
    def classify_complexity(self, utterance: str) -> tuple[str, str]:
        """
        Router-model pattern: a cheap classifier decides which tier pays for the turn.

        Heuristic here so the playground is deterministic and free. In production this
        is one `carecopilot-fast` call using COMPLEXITY_CLASSIFIER — roughly $0.0001,
        which pays for itself the first time it keeps a greeting off the deep tier.
        """
        low = utterance.lower()
        if _TRIVIAL_RE.match(utterance):
            return "trivial", "greeting or closing with no information need"
        hits = [h for h in _COMPLEX_HINTS if h in low]
        if hits or len(utterance) > 320:
            return "complex", f"safety/consequence signal: {', '.join(hits[:3]) or 'long turn'}"
        return "standard", "routine support request"

    @staticmethod
    def _granted_scopes(virtual_key: str) -> frozenset[str]:
        """Scopes ride on the virtual key. Least privilege at the prompt boundary."""
        base = {"orders:read", "catalogue:read", "knowledge:read"}
        key = VIRTUAL_KEYS.get(virtual_key)
        if key and key.data_classification == "confidential-health":
            base |= {"clinical:screen", "escalation:write"}
        return frozenset(base)

    # -- the loop ----------------------------------------------------------------------
    async def run_turn(
        self,
        *,
        utterance: str,
        session_id: str | None = None,
        virtual_key: str = "sk-carecopilot-dev",
        requested_model: str | None = None,
        locale: str = "en-GB",
        auto_approve: bool = False,
    ) -> TurnResult:
        t0 = time.perf_counter()
        key = VIRTUAL_KEYS.get(virtual_key)
        tenant = key.tenant if key else "unknown"
        session = sessions.get_or_create(session_id, tenant=tenant, virtual_key=virtual_key)
        trace = tel.Trace(session_id=session.session_id, tenant=tenant)

        result = TurnResult(
            reply="",
            session_id=session.session_id,
            trace_id=trace.trace_id,
            model_used="",
            routing={},
        )

        with trace.span(
            "agent.turn",
            kind="server",
            tenant=tenant,
            session_id=session.session_id,
            utterance_chars=len(utterance),
        ):
            # ---- 0. entitlement -------------------------------------------------------
            if key is None:
                return self._fail(
                    result,
                    trace,
                    tenant,
                    t0,
                    401,
                    "unauthorised",
                    "That API key is not recognised by the gateway.",
                )

            # ---- 1. classify + route --------------------------------------------------
            with trace.span("router.classify") as s:
                complexity, why = self.classify_complexity(utterance)
                s.attributes.update(complexity=complexity, reason=why)
            with trace.span("router.resolve") as s:
                routing = resolve_model(
                    requested_model or settings.default_model,
                    virtual_key=virtual_key,
                    complexity=complexity,
                    unhealthy=frozenset(self.unhealthy),
                )
                routing["complexity"] = complexity
                routing["complexity_reason"] = why
                s.attributes.update(
                    selected=routing.get("selected"), reasons="; ".join(routing["reasons"])
                )
            if routing.get("denied"):
                return self._fail(
                    result,
                    trace,
                    tenant,
                    t0,
                    403,
                    "entitlement_denied",
                    "This key is not entitled to any model in the catalogue.",
                )
            model = routing["selected"]
            result.model_used, result.routing = model, routing

            # ---- 2. budget pre-flight -------------------------------------------------
            with trace.span("finops.preflight") as s:
                spent_today = budgets.spent(tenant)
                s.attributes.update(
                    tenant_spend_usd=round(spent_today, 4), daily_limit_usd=key.daily_budget_usd
                )
                if spent_today >= key.daily_budget_usd:
                    return self._fail(
                        result,
                        trace,
                        tenant,
                        t0,
                        429,
                        "budget_exhausted",
                        "The daily AI budget for this team is used up. "
                        "Requests resume at 00:00 UTC or when the owner "
                        "raises the limit.",
                    )
                if session.spend_usd >= settings.per_session_budget_usd:
                    return self._fail(
                        result,
                        trace,
                        tenant,
                        t0,
                        429,
                        "session_budget",
                        "This conversation hit its cost ceiling. Start a "
                        "new session or hand over to an agent.",
                    )

            # ---- 3. input guardrails --------------------------------------------------
            with trace.span("guardrails.input") as s:
                gin = guards.run_input_guardrails(
                    utterance,
                    enabled=settings.guardrails_enabled,
                    redact=settings.pii_redaction_enabled,
                )
                result.guardrails += [v.as_dict() for v in gin.verdicts]
                for v in gin.verdicts:
                    if v.triggered:
                        tel.GUARDRAIL_FIRINGS.labels(v.check, v.action.value, v.severity).inc()
                s.attributes.update(blocked=gin.blocked, reason=gin.block_reason)
            if gin.blocked:
                tel.record_audit(
                    trace_id=trace.trace_id,
                    session_id=session.session_id,
                    tenant=tenant,
                    event="input_blocked",
                    reason=gin.block_reason,
                    actor="guardrails",
                )
                return self._fail(
                    result,
                    trace,
                    tenant,
                    t0,
                    200,
                    gin.block_reason,
                    guards.BLOCK_MESSAGE,
                    blocked=True,
                )

            safe_utterance = gin.text

            # ---- 4. build the working context -----------------------------------------
            system = SYSTEM_PROMPT.render(
                tenant=tenant,
                locale=locale,
                session_id=session.session_id,
                today=date.today().isoformat(),
                prompt_id=SYSTEM_PROMPT.prompt_id,
                version=SYSTEM_PROMPT.version,
            )
            messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
            messages += session.messages[-8:]  # rolling window keeps cost bounded
            messages.append({"role": "user", "content": safe_utterance})

            scopes = self._granted_scopes(virtual_key)
            tools = registry.schemas(granted_scopes=scopes)
            observations: list[dict[str, Any]] = []
            turn_cost = 0.0
            tool_budget = settings.max_tool_calls
            stop = "completed"
            final_text = ""

            # ---- 5. plan / act --------------------------------------------------------
            for step_no in range(1, settings.max_steps + 1):
                with trace.span(f"agent.step.{step_no}", step=step_no) as step_span:
                    try:
                        with trace.span("llm.call", kind="client", model=model) as llm_span:
                            resp: LLMResponse = await self.client.complete(
                                model=model,
                                messages=messages,
                                tools=tools,
                                metadata={
                                    "tenant": tenant,
                                    "cost_centre": key.cost_centre,
                                    "session_id": session.session_id,
                                    "trace_id": trace.trace_id,
                                    "prompt_version": SYSTEM_PROMPT.version,
                                    "environment": settings.environment,
                                },
                            )
                            llm_span.attributes.update(
                                input_tokens=resp.input_tokens,
                                output_tokens=resp.output_tokens,
                                cost_usd=round(resp.cost_usd, 6),
                                cached=resp.cached,
                                finish_reason=resp.finish_reason,
                                latency_ms=resp.latency_ms,
                            )
                    except GatewayError as exc:
                        tel.ERRORS.labels(tenant, exc.kind).inc()
                        trace.event("gateway_error", kind=exc.kind, detail=str(exc))
                        # reliability: one failover hop, then degrade honestly
                        fallbacks = CATALOG[model].fallbacks if model in CATALOG else ()
                        nxt = next((f for f in fallbacks if f in key.allowed_models), None)
                        if nxt and nxt != model:
                            self.unhealthy.add(model)
                            routing["reasons"].append(f"runtime failure on '{model}' → '{nxt}'")
                            model = nxt
                            result.model_used = nxt
                            continue
                        return self._fail(
                            result,
                            trace,
                            tenant,
                            t0,
                            exc.status,
                            exc.kind,
                            "The AI gateway is unavailable. I've logged this "
                            "and a human agent can help right away.",
                        )

                    turn_cost += resp.cost_usd
                    result.input_tokens += resp.input_tokens
                    result.output_tokens += resp.output_tokens
                    tel.record_spend(
                        tenant=tenant,
                        model=model,
                        cost_centre=key.cost_centre,
                        cost_usd=resp.cost_usd,
                        input_tokens=resp.input_tokens,
                        output_tokens=resp.output_tokens,
                        cached=resp.cached,
                    )

                    step_record = {
                        "step": step_no,
                        "model": model,
                        "latency_ms": resp.latency_ms,
                        "cost_usd": round(resp.cost_usd, 6),
                        "input_tokens": resp.input_tokens,
                        "output_tokens": resp.output_tokens,
                        "finish_reason": resp.finish_reason,
                        "tool_calls": [],
                        "content": resp.content,
                    }

                    # per-request budget guard
                    if turn_cost > settings.per_request_budget_usd:
                        stop = "request_budget_exceeded"
                        step_record["halted"] = stop
                        result.steps.append(step_record)
                        final_text = (
                            resp.content
                            or "This is taking more effort than the cost ceiling for a "
                            "single question allows. Let me hand you to a colleague."
                        )
                        break

                    if not resp.tool_calls:
                        final_text = resp.content
                        result.steps.append(step_record)
                        stop = "completed"
                        break

                    # ---- act ----------------------------------------------------------
                    messages.append(
                        {
                            "role": "assistant",
                            "content": resp.content or None,
                            "tool_calls": resp.tool_calls,
                        }
                    )

                    for call in resp.tool_calls:
                        if tool_budget <= 0:
                            stop = "tool_budget_exceeded"
                            break
                        tool_budget -= 1
                        name = call["function"]["name"]
                        try:
                            args = json.loads(call["function"]["arguments"] or "{}")
                        except json.JSONDecodeError:
                            args = {}
                        spec = registry.get(name)

                        # human-in-the-loop gate on side-effecting tools
                        if (
                            spec
                            and spec.requires_approval
                            and settings.hitl_enabled
                            and not auto_approve
                        ):
                            req = approvals.request(
                                session_id=session.session_id,
                                tool=name,
                                arguments=args,
                                rationale="Side-effecting tool requires human approval "
                                "before execution.",
                            )
                            trace.event(
                                "approval_requested", tool=name, approval_id=req.approval_id
                            )
                            tel.record_audit(
                                trace_id=trace.trace_id,
                                session_id=session.session_id,
                                tenant=tenant,
                                event="approval_requested",
                                tool=name,
                                approval_id=req.approval_id,
                                actor="agent",
                            )
                            result.pending_approval = req.as_dict()
                            step_record["tool_calls"].append(
                                {
                                    "tool": name,
                                    "arguments": args,
                                    "status": "awaiting_approval",
                                    "approval_id": req.approval_id,
                                }
                            )
                            tel.TOOL_CALLS.labels(tenant, name, "awaiting_approval").inc()
                            stop = "awaiting_human_approval"
                            final_text = (
                                "I've prepared a handover to a registered pharmacist. "
                                "A colleague will confirm it before anything is sent — "
                                f"reference `{req.approval_id}`."
                            )
                            continue

                        with trace.span("tool.call", kind="client", tool=name) as ts:
                            tstart = time.perf_counter()
                            output = await registry.invoke(name, args)
                            elapsed = time.perf_counter() - tstart
                            failed = isinstance(output, dict) and "error" in output
                            ts.attributes.update(
                                arguments=json.dumps(args)[:200],
                                status="error" if failed else "ok",
                                duration_ms=round(elapsed * 1000, 1),
                                systems=",".join(spec.systems_touched) if spec else "",
                            )
                            ts.status = "ERROR" if failed else "OK"
                        tel.TOOL_CALLS.labels(tenant, name, "error" if failed else "ok").inc()
                        tel.TOOL_LATENCY.labels(name).observe(elapsed)

                        observations.append({"tool": name, **(output or {})})
                        rec = {
                            "tool": name,
                            "arguments": args,
                            "status": "error" if failed else "ok",
                            "duration_ms": round(elapsed * 1000, 1),
                            "output": output,
                            "systems_touched": list(spec.systems_touched) if spec else [],
                            "data_classification": spec.data_classification if spec else "unknown",
                        }
                        step_record["tool_calls"].append(rec)
                        result.tool_calls.append(rec)
                        messages.append(
                            {
                                "role": "tool",
                                "name": name,
                                "tool_call_id": call.get("id", ""),
                                "content": json.dumps(output),
                            }
                        )

                    result.steps.append(step_record)
                    step_span.attributes.update(tools_called=len(step_record["tool_calls"]))
                    if stop in ("tool_budget_exceeded", "awaiting_human_approval"):
                        break
            else:
                stop = "max_steps_reached"
                final_text = (
                    "I wasn't able to close this out on my own. Let me put you "
                    "through to a colleague who can."
                )

            if not final_text:
                final_text = (
                    "I couldn't complete that. A colleague from customer care "
                    "can pick it up right away."
                )

            # ---- 6. output guardrails -------------------------------------------------
            with trace.span("guardrails.output") as s:
                gout = guards.run_output_guardrails(
                    final_text, observations, enabled=settings.guardrails_enabled
                )
                result.guardrails += [v.as_dict() for v in gout.verdicts]
                for v in gout.verdicts:
                    if v.triggered:
                        tel.GUARDRAIL_FIRINGS.labels(v.check, v.action.value, v.severity).inc()
                s.attributes.update(blocked=gout.blocked, escalate=gout.escalate)

            grounded = not any(v.check == "grounding" and v.triggered for v in gout.verdicts)
            tel.GROUNDEDNESS.labels(tenant).set(1.0 if grounded else 0.0)

            reply = gout.text
            if gout.escalate:
                result.escalated = True
                tel.ESCALATIONS.labels(tenant, "medical_advice_policy").inc()

            # ---- 7. persist + account -------------------------------------------------
            session.messages.append({"role": "user", "content": safe_utterance})
            session.messages.append({"role": "assistant", "content": reply})
            session.spend_usd += turn_cost
            session.turns += 1
            tenant_total = budgets.add(tenant, turn_cost)
            tel.BUDGET_REMAINING.labels(tenant).set(max(0.0, key.daily_budget_usd - tenant_total))

            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            result.reply = reply
            result.cost_usd = round(turn_cost, 6)
            result.latency_ms = elapsed_ms
            result.stop_reason = stop
            result.session_spend_usd = round(session.spend_usd, 6)
            result.tenant_spend_usd = round(tenant_total, 6)

            tel.REQUESTS.labels(tenant, stop, settings.environment).inc()
            tel.REQUEST_LATENCY.labels(tenant).observe(elapsed_ms / 1000)
            tel.AGENT_STEPS.labels(tenant).observe(len(result.steps))
            tel.COST_PER_TURN.labels(tenant).observe(turn_cost)
            tel.LOOP_TERMINATION.labels(tenant, stop).inc()
            tel.record_audit(
                trace_id=trace.trace_id,
                session_id=session.session_id,
                tenant=tenant,
                event="turn_completed",
                model=model,
                stop_reason=stop,
                cost_usd=round(turn_cost, 6),
                tools=[c["tool"] for c in result.tool_calls],
                grounded=grounded,
                escalated=result.escalated,
                actor="agent",
            )
            tel.log.info(
                "agent turn complete",
                extra={
                    "trace_id": trace.trace_id,
                    "session_id": session.session_id,
                    "tenant": tenant,
                    "model": model,
                    "cost_usd": turn_cost,
                    "latency_ms": elapsed_ms,
                    "outcome": stop,
                },
            )

        result.trace = trace.as_dict()
        tel.RECENT_TRACES.appendleft(
            {**result.trace, "reply": reply[:200], "cost_usd": result.cost_usd, "stop_reason": stop}
        )
        return result

    # -- failure path ---------------------------------------------------------------------
    def _fail(
        self,
        result: TurnResult,
        trace: tel.Trace,
        tenant: str,
        t0: float,
        status: int,
        kind: str,
        message: str,
        *,
        blocked: bool = False,
    ) -> TurnResult:
        result.reply = message
        result.stop_reason = kind
        result.latency_ms = int((time.perf_counter() - t0) * 1000)
        result.trace = trace.as_dict()
        tel.REQUESTS.labels(tenant, kind, settings.environment).inc()
        if not blocked:
            tel.ERRORS.labels(tenant, kind).inc()
        tel.LOOP_TERMINATION.labels(tenant, kind).inc()
        tel.RECENT_TRACES.appendleft(
            {**result.trace, "reply": message[:200], "cost_usd": 0.0, "stop_reason": kind}
        )
        return result


orchestrator = Orchestrator()
