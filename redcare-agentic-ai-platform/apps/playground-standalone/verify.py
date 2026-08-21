#!/usr/bin/env python3
"""
Check the browser port has not drifted from the Python service.

Two implementations of the same platform is a maintenance hazard: the console
looks authoritative, so if its catalogue or its thresholds quietly diverge from
the service, it becomes a convincing lie. This compares the parts that are cheap
to compare and fails loudly when they disagree.

It deliberately does *not* try to diff the agent loop or the guardrail regexes —
those are compared by behaviour instead: both implementations run the same
16-case golden set and both must reach the same gate verdict.

    python3 apps/playground-standalone/verify.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "apps" / "playground-standalone" / "src"
sys.path.insert(0, str(ROOT / "apps" / "agent-service"))

from app.evals.suite import GOLDEN_SET, THRESHOLDS          # noqa: E402
from app.gateway.catalog import CATALOG, VIRTUAL_KEYS       # noqa: E402

problems: list[str] = []


def check(label: str, py, js) -> None:
    if py == js:
        print(f"  ✓ {label}")
    else:
        problems.append(f"{label}\n      python: {py}\n      browser: {js}")


engine = (SRC / "engine.js").read_text()
orch = (SRC / "orchestrator.js").read_text()


def object_literal(source: str, name: str) -> str:
    """The body of `const <name> = { … };`, matched by brace depth.

    A regex over the whole file picks up entries from neighbouring objects — the
    virtual keys and the catalogue share an indentation pattern — so the search
    has to be scoped to one literal at a time.
    """
    start = source.index(f"const {name} = {{")
    i = source.index("{", start)
    depth = 0
    for j in range(i, len(source)):
        if source[j] == "{":
            depth += 1
        elif source[j] == "}":
            depth -= 1
            if depth == 0:
                return source[i + 1:j]
    raise ValueError(f"unbalanced braces in {name}")


CATALOG_JS = object_literal(engine, "CATALOG")
KEYS_JS = object_literal(engine, "KEYS")

# --- model catalogue ------------------------------------------------------------
js_models = set(re.findall(r'^\s{2}"([a-z0-9-]+)": \{$', CATALOG_JS, re.M))
check("catalogue: model names", set(CATALOG), js_models)

for name, entry in CATALOG.items():
    block = re.search(rf'"{re.escape(name)}": \{{(.*?)\n  \}},', CATALOG_JS, re.S)
    if not block:
        problems.append(f"catalogue: '{name}' missing from the browser port")
        continue
    b = block.group(1)

    def field(key):
        m = re.search(rf'{key}: "?([^",\n]+)"?', b)
        return m.group(1).strip() if m else None

    check(f"catalogue: {name} upstream", entry.upstream_model, field("upstream"))
    check(f"catalogue: {name} region", entry.region, field("region"))
    check(f"catalogue: {name} input price", entry.input_usd_per_mtok, float(field("inUsd")))
    check(f"catalogue: {name} output price", entry.output_usd_per_mtok, float(field("outUsd")))
    js_fb = re.search(r"fallbacks: \[(.*?)\]", b, re.S)
    check(f"catalogue: {name} fallbacks", list(entry.fallbacks),
          [x.strip().strip('"') for x in js_fb.group(1).split(",") if x.strip()] if js_fb else [])

# --- virtual keys ---------------------------------------------------------------
js_keys = set(re.findall(r'^\s{2}"(sk-[a-z-]+)": \{$', KEYS_JS, re.M))
check("keys: identifiers", set(VIRTUAL_KEYS), js_keys)

for kid, key in VIRTUAL_KEYS.items():
    block = re.search(rf'"{re.escape(kid)}": \{{(.*?)\n  \}},', KEYS_JS, re.S)
    if not block:
        problems.append(f"keys: '{kid}' missing from the browser port")
        continue
    b = block.group(1)
    models = re.search(r"models: (\[[^\]]*\]|Object\.keys\(CATALOG\))", b)
    raw = models.group(1) if models else "[]"
    js_allowed = (sorted(CATALOG) if "Object.keys" in raw
                  else sorted(x.strip().strip('"') for x in raw.strip("[]").split(",") if x.strip()))
    check(f"keys: {key.key_alias} entitlements", sorted(key.allowed_models), js_allowed)
    budget = re.search(r"dailyUsd: ([\d.]+)", b)
    check(f"keys: {key.key_alias} daily budget", key.daily_budget_usd, float(budget.group(1)))

# --- eval gate ------------------------------------------------------------------
js_thresholds = dict(
    (k, float(v)) for k, v in
    re.findall(r"(\w+): ([\d.]+)", re.search(r"THRESHOLDS = \{(.*?)\}", orch, re.S).group(1)))
check("evals: thresholds", dict(THRESHOLDS), js_thresholds)

js_case_ids = re.findall(r'\{ id: "([a-z0-9-]+)"', orch)
check("evals: golden-set case ids", [c.case_id for c in GOLDEN_SET], js_case_ids)

# --- report ---------------------------------------------------------------------
print()
if problems:
    print(f"DRIFT DETECTED — {len(problems)} mismatch(es) between the service and the console:\n")
    for p in problems:
        print(f"  ✗ {p}")
    print("\nUpdate apps/playground-standalone/src/ and rerun build.py.")
    sys.exit(1)

print("No drift: the browser console and the Python service agree on the "
      "catalogue, the virtual keys, the eval thresholds and the golden set.")
