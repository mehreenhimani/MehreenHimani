"""
Guardrails: the platform's shared safety layer.

The point of putting these in the *platform* rather than in each agent is that a
tenant team should not have to reimplement PII redaction or injection detection
to ship. They get it by adopting the golden path. Each check returns a Verdict
so the decision is observable, testable and reviewable — a guardrail that fires
silently is a guardrail nobody can audit.

Ordering matters and is deliberate:
  input : injection -> jailbreak -> topic policy -> PII redaction
  output: grounding -> medical-advice policy -> PII leak -> disclaimer
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Action(StrEnum):
    ALLOW = "allow"
    REDACT = "redact"
    ANNOTATE = "annotate"
    BLOCK = "block"
    ESCALATE = "escalate"


@dataclass
class Verdict:
    check: str
    action: Action
    triggered: bool
    detail: str = ""
    severity: str = "info"  # info | low | medium | high
    evidence: list[str] = field(default_factory=list)
    latency_ms: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "action": self.action.value,
            "triggered": self.triggered,
            "detail": self.detail,
            "severity": self.severity,
            "evidence": self.evidence[:5],
            "latency_ms": round(self.latency_ms, 2),
        }


@dataclass
class GuardrailResult:
    text: str
    verdicts: list[Verdict]
    blocked: bool = False
    block_reason: str = ""
    escalate: bool = False

    @property
    def triggered(self) -> list[Verdict]:
        return [v for v in self.verdicts if v.triggered]


# --- patterns -----------------------------------------------------------------------
_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b")),
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}[ ]?(?:[A-Z0-9]{4}[ ]?){2,7}[A-Z0-9]{1,4}\b")),
    # No leading \b: a word boundary cannot match before "+", so "+49 170 1234567"
    # would slip through. A negative lookbehind on a digit does the real job here —
    # it stops the pattern from biting a chunk out of a longer number.
    ("PHONE_DE", re.compile(r"(?<![\d+])(?:\+49|0049|0)[ -]?\d{2,5}[ -]?\d{3,9}\b")),
    ("INSURANCE_NO", re.compile(r"\b[A-Z]\d{9}\b")),
    ("CARD", re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")),
    ("DOB", re.compile(r"\b(?:0?[1-9]|[12]\d|3[01])[./](?:0?[1-9]|1[0-2])[./](?:19|20)\d{2}\b")),
]

_INJECTION_PATTERNS = [
    r"ignore (?:all |any )?(?:previous|prior|above) (?:instructions|prompts|rules)",
    r"disregard (?:the )?(?:system|previous) (?:prompt|message|instructions)",
    r"you are now (?:a|an|in) \w+",
    r"reveal (?:your|the) (?:system )?prompt",
    r"print (?:your|the) (?:instructions|system prompt|rules)",
    r"developer mode|do anything now|\bDAN\b",
    r"(?:new|updated) instructions?\s*:",
    r"</?(?:system|assistant)>",
    r"repeat (?:everything|the text) above",
    r"act as (?:if you (?:are|were)|a) (?:unrestricted|uncensored|jailbroken)",
]
_INJECTION_RE = re.compile("|".join(f"(?:{p})" for p in _INJECTION_PATTERNS), re.I)

_EXFIL_RE = re.compile(
    r"\b(?:send|post|upload|forward|exfiltrate)\b.{0,40}\b(?:http|https|webhook|curl)\b", re.I
)

_MEDICAL_ADVICE_RE = re.compile(
    r"\b(?:you should take|take \d+\s*(?:mg|ml|tablets?|pills?)|"
    r"increase your dose|stop taking|double the dose|safe to take .* while pregnant|"
    r"i diagnose|you (?:probably )?have\b.{0,30}(?:infection|condition|disease))",
    re.I,
)

_OFF_TOPIC_RE = re.compile(
    r"\b(?:write me a (?:poem|song|essay)|python script|stock tip|"
    r"who will win the|political opinion|translate this contract)\b",
    re.I,
)

_SECRET_RE = re.compile(
    r"\b(?:sk-[A-Za-z0-9]{8,}|Bearer\s+[A-Za-z0-9._-]{16,}|"
    r"AKIA[0-9A-Z]{16}|(?:api[_-]?key|password)\s*[:=]\s*\S{6,})",
    re.I,
)


# --- individual checks ---------------------------------------------------------------
def detect_prompt_injection(text: str) -> Verdict:
    hits = [m.group(0)[:80] for m in _INJECTION_RE.finditer(text)]
    exfil = [m.group(0)[:80] for m in _EXFIL_RE.finditer(text)]
    if hits or exfil:
        return Verdict(
            "prompt_injection",
            Action.BLOCK,
            True,
            "Instruction-override or exfiltration pattern detected.",
            "high",
            hits + exfil,
        )
    return Verdict("prompt_injection", Action.ALLOW, False, "No override pattern found.")


def detect_topic_policy(text: str) -> Verdict:
    hits = [m.group(0) for m in _OFF_TOPIC_RE.finditer(text)]
    if hits:
        return Verdict(
            "topic_policy",
            Action.BLOCK,
            True,
            "Request falls outside the pharmacy support scope.",
            "medium",
            hits,
        )
    return Verdict("topic_policy", Action.ALLOW, False, "Within supported scope.")


def redact_pii(text: str) -> tuple[str, Verdict]:
    found: list[str] = []
    out = text
    for label, pattern in _PII_PATTERNS:

        def _sub(m: re.Match[str], _l: str = label) -> str:
            found.append(f"{_l}:{m.group(0)[:4]}…")
            return f"[{_l}_REDACTED]"

        out = pattern.sub(_sub, out)
    if found:
        return out, Verdict(
            "pii_redaction",
            Action.REDACT,
            True,
            f"Redacted {len(found)} identifier(s) before the model call.",
            "medium",
            found,
        )
    return out, Verdict("pii_redaction", Action.ALLOW, False, "No direct identifiers found.")


def detect_secret_leak(text: str) -> Verdict:
    hits = [m.group(0)[:20] + "…" for m in _SECRET_RE.finditer(text)]
    if hits:
        return Verdict(
            "secret_leak",
            Action.BLOCK,
            True,
            "Credential-shaped string in model output.",
            "high",
            hits,
        )
    return Verdict("secret_leak", Action.ALLOW, False, "No credential pattern in output.")


def detect_medical_advice(text: str) -> Verdict:
    hits = [m.group(0)[:80] for m in _MEDICAL_ADVICE_RE.finditer(text)]
    if hits:
        return Verdict(
            "medical_advice_policy",
            Action.ESCALATE,
            True,
            "Output reads as individualised medical advice — routing to a pharmacist.",
            "high",
            hits,
        )
    return Verdict(
        "medical_advice_policy",
        Action.ALLOW,
        False,
        "No individualised clinical instruction detected.",
    )


def check_grounding(text: str, observations: list[dict]) -> Verdict:
    """
    Cheap, explainable groundedness proxy: every factual claim the agent makes
    about orders, stock or policy must trace to a tool observation. Production
    swaps the body for an LLM-as-judge call on the `carecopilot-fast` tier; the
    *contract* — a Verdict with evidence — stays identical.
    """
    factual = re.findall(
        r"\b(?:RC\d{8}|in_stock|out_of_stock|low_stock|in_transit|"
        r"delivered|POL-[A-Z]{2,4}-\d{3}|HIGH_RISK|MODERATE_RISK)\b",
        text,
    )
    if not factual:
        return Verdict("grounding", Action.ALLOW, False, "No verifiable claim asserted.")
    corpus = " ".join(str(o) for o in observations)
    unsupported = [c for c in set(factual) if c not in corpus]
    if unsupported:
        return Verdict(
            "grounding",
            Action.ANNOTATE,
            True,
            "Claims not present in any tool observation.",
            "high",
            unsupported,
        )
    return Verdict(
        "grounding",
        Action.ALLOW,
        False,
        f"All {len(set(factual))} claim(s) trace to a tool observation.",
    )


_DISCLAIMER = (
    "\n\n_Redcare CareCopilot provides general pharmacy information, not medical "
    "advice. A registered pharmacist reviews anything clinical._"
)


def ensure_disclaimer(text: str) -> tuple[str, Verdict]:
    if "not medical advice" in text.lower() or "keine medizinische" in text.lower():
        return text, Verdict("disclaimer", Action.ALLOW, False, "Disclaimer already present.")
    return text + _DISCLAIMER, Verdict(
        "disclaimer",
        Action.ANNOTATE,
        True,
        "Appended the regulatory disclaimer (EU AI Act Art. 50).",
        "low",
    )


# --- pipelines ------------------------------------------------------------------------
BLOCK_MESSAGE = (
    "I can't help with that request. If you were asking about an order, a "
    "product, or one of our policies, please rephrase it and I'll take another look."
)


def run_input_guardrails(
    text: str, *, enabled: bool = True, redact: bool = True
) -> GuardrailResult:
    if not enabled:
        return GuardrailResult(text, [Verdict("guardrails", Action.ALLOW, False, "disabled")])
    verdicts: list[Verdict] = []
    v = detect_prompt_injection(text)
    verdicts.append(v)
    if v.triggered:
        return GuardrailResult(
            BLOCK_MESSAGE, verdicts, blocked=True, block_reason="prompt_injection"
        )
    v = detect_topic_policy(text)
    verdicts.append(v)
    if v.triggered:
        return GuardrailResult(BLOCK_MESSAGE, verdicts, blocked=True, block_reason="topic_policy")
    out = text
    if redact:
        out, v = redact_pii(text)
        verdicts.append(v)
    return GuardrailResult(out, verdicts)


def run_output_guardrails(
    text: str, observations: list[dict], *, enabled: bool = True
) -> GuardrailResult:
    if not enabled:
        return GuardrailResult(text, [Verdict("guardrails", Action.ALLOW, False, "disabled")])
    verdicts: list[Verdict] = []
    out = text

    v = detect_secret_leak(out)
    verdicts.append(v)
    if v.triggered:
        return GuardrailResult(BLOCK_MESSAGE, verdicts, blocked=True, block_reason="secret_leak")

    verdicts.append(check_grounding(out, observations))

    v = detect_medical_advice(out)
    verdicts.append(v)
    escalate = v.triggered

    out, v2 = redact_pii(out)
    v2.check = "pii_egress"
    verdicts.append(v2)

    out, v3 = ensure_disclaimer(out)
    verdicts.append(v3)

    return GuardrailResult(out, verdicts, escalate=escalate)
