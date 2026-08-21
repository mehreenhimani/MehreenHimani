"""
Session and approval state.

In-memory here so the playground has no dependencies; in Azure the same two
interfaces are backed by Azure Cache for Redis (hot session state, TTL) and
Azure Database for PostgreSQL (durable transcripts, approvals, evals). The
interface is deliberately narrow so swapping the backend is a config change,
not a rewrite — that is what makes it a platform capability rather than an
app detail.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class Session:
    session_id: str
    tenant: str
    virtual_key: str
    created_at: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    spend_usd: float = 0.0
    turns: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def get_or_create(self, session_id: str | None, *, tenant: str, virtual_key: str) -> Session:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        sid = session_id or f"sess_{uuid.uuid4().hex[:12]}"
        s = Session(
            session_id=sid,
            tenant=tenant,
            virtual_key=virtual_key,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._sessions[sid] = s
        return s

    def all(self) -> list[Session]:
        return list(self._sessions.values())

    def reset(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None


@dataclass
class ApprovalRequest:
    """A human-in-the-loop gate on a side-effecting tool call."""

    approval_id: str
    session_id: str
    tool: str
    arguments: dict[str, Any]
    rationale: str
    requested_at: str
    status: str = "pending"  # pending | approved | rejected | expired
    decided_by: str = ""
    decided_at: str = ""
    decision_note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class ApprovalStore:
    def __init__(self) -> None:
        self._items: dict[str, ApprovalRequest] = {}

    def request(
        self, *, session_id: str, tool: str, arguments: dict, rationale: str
    ) -> ApprovalRequest:
        req = ApprovalRequest(
            approval_id=f"apr_{uuid.uuid4().hex[:10]}",
            session_id=session_id,
            tool=tool,
            arguments=arguments,
            rationale=rationale,
            requested_at=datetime.now(UTC).isoformat(),
        )
        self._items[req.approval_id] = req
        return req

    def decide(
        self, approval_id: str, *, approve: bool, actor: str, note: str = ""
    ) -> ApprovalRequest | None:
        req = self._items.get(approval_id)
        if req is None or req.status != "pending":
            return None
        req.status = "approved" if approve else "rejected"
        req.decided_by = actor
        req.decided_at = datetime.now(UTC).isoformat()
        req.decision_note = note
        return req

    def pending(self) -> list[ApprovalRequest]:
        return [r for r in self._items.values() if r.status == "pending"]

    def all(self) -> list[ApprovalRequest]:
        return sorted(self._items.values(), key=lambda r: r.requested_at, reverse=True)


class BudgetLedger:
    """Daily spend per tenant — the app-side mirror of LiteLLM's budget enforcement."""

    def __init__(self) -> None:
        self._spend: dict[str, float] = defaultdict(float)

    def add(self, tenant: str, usd: float) -> float:
        self._spend[tenant] += usd
        return self._spend[tenant]

    def spent(self, tenant: str) -> float:
        return self._spend[tenant]

    def remaining(self, tenant: str, limit: float) -> float:
        return max(0.0, limit - self._spend[tenant])

    def snapshot(self) -> dict[str, float]:
        return {k: round(v, 6) for k, v in self._spend.items()}


sessions = SessionStore()
approvals = ApprovalStore()
budgets = BudgetLedger()
