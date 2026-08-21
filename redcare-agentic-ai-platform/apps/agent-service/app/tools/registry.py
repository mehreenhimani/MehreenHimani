"""
Tool registry — the agent's blast radius, declared as data.

Every tool carries more than a JSON schema. It carries the platform metadata a
governance review actually asks for: what data it touches, whether it mutates
state, whether a human must approve it, and what it costs in latency. The
registry is the single place where "what can this agent do?" is answerable, and
it is what the /platform/tools endpoint publishes to the internal catalogue.
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

Handler = Callable[..., Awaitable[dict] | dict]


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Handler
    # --- platform metadata ---------------------------------------------------------
    side_effect: bool = False  # does it change state in a system of record?
    requires_approval: bool = False  # human-in-the-loop gate before execution
    data_classification: str = "internal"
    systems_touched: tuple[str, ...] = ()
    timeout_s: float = 5.0
    owner: str = "platform-team"
    slo_p95_ms: int = 800
    scopes: tuple[str, ...] = ()  # entitlements the caller must hold

    def openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def card(self) -> dict[str, Any]:
        """Human-facing tool card for the internal developer portal."""
        return {
            "name": self.name,
            "description": self.description,
            "side_effect": self.side_effect,
            "requires_approval": self.requires_approval,
            "data_classification": self.data_classification,
            "systems_touched": list(self.systems_touched),
            "owner": self.owner,
            "slo_p95_ms": self.slo_p95_ms,
            "scopes": list(self.scopes),
            "parameters": self.parameters,
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> ToolSpec:
        if spec.name in self._tools:
            raise ValueError(f"tool '{spec.name}' already registered")
        self._tools[spec.name] = spec
        return spec

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def all(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def schemas(self, *, granted_scopes: frozenset[str] | None = None) -> list[dict]:
        """Only advertise tools the caller is entitled to — least privilege at the prompt."""
        out = []
        for t in self._tools.values():
            if t.scopes and granted_scopes is not None and not set(t.scopes) <= granted_scopes:
                continue
            out.append(t.openai_schema())
        return out

    async def invoke(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        spec = self.get(name)
        if spec is None:
            return {"error": "unknown_tool", "detail": f"no tool named '{name}'"}
        try:
            result = spec.handler(**arguments)
            if inspect.isawaitable(result):
                result = await asyncio.wait_for(result, timeout=spec.timeout_s)
            return result  # type: ignore[return-value]
        except TimeoutError:
            return {"error": "tool_timeout", "detail": f"'{name}' exceeded {spec.timeout_s}s"}
        except TypeError as exc:
            return {"error": "bad_arguments", "detail": str(exc)}
        except Exception as exc:
            return {"error": "tool_failed", "detail": f"{type(exc).__name__}: {exc}"}


registry = ToolRegistry()
