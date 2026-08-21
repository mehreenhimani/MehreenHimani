"""
Eval runner for CI.

Exits non-zero when the gate fails, which is what turns a report into a control.
Writes JSON for machines and Markdown for the pull-request comment, because the
person deciding whether to merge reads the second one.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import app.tools.pharmacy  # noqa: F401 — registers the tool surface
from app.agents.orchestrator import orchestrator
from app.evals.suite import GOLDEN_SET, run_suite


def to_markdown(report: dict) -> str:
    gate = report["gate"]
    status = "✅ **PASSED**" if report["gate_passed"] else "❌ **FAILED**"
    lines = [
        f"## Agent eval gate — {status}",
        "",
        f"`carecopilot-core-v3` · {report['cases']} cases · "
        f"${report['total_cost_usd']:.4f} · p95 {report['p95_latency_ms']} ms",
        "",
        "| metric | score | threshold | |",
        "|---|---:|---:|:--:|",
    ]
    for metric, g in gate.items():
        mark = "✅" if g["pass"] else "❌"
        lines.append(
            f"| {metric.replace('_', ' ')} | {g['value']:.2%} | {g['threshold']:.0%} | {mark} |"
        )

    if report["failures"]:
        lines += ["", "### Failing cases", "", "| case | why |", "|---|---|"]
        for f in report["failures"]:
            lines.append(f"| `{f['case_id']}` | {'; '.join(f['reasons'])} |")
    else:
        lines += ["", "_Every case passed._"]

    lines += [
        "",
        "<details><summary>All cases</summary>",
        "",
        "| case | tags | result | cost | steps |",
        "|---|---|:--:|---:|---:|",
    ]
    for r in report["results"]:
        mark = "✅" if r["passed"] else "❌"
        tags = ", ".join(r["tags"])
        lines.append(
            f"| `{r['case_id']}` | {tags} | {mark} | ${r['cost_usd']:.5f} | {r['steps']} |"
        )
    lines += ["", "</details>"]
    return "\n".join(lines)


async def main_async(args: argparse.Namespace) -> int:
    cases = GOLDEN_SET
    if args.tag:
        cases = [c for c in GOLDEN_SET if args.tag in c.tags]
        if not cases:
            print(f"no cases carry the tag '{args.tag}'", file=sys.stderr)
            return 2

    async def runner(utterance: str) -> dict:
        result = await orchestrator.run_turn(
            utterance=utterance, session_id=None, virtual_key="sk-carecopilot-prod"
        )
        return result.as_dict()

    report = await run_suite(runner, cases)

    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2, default=str))
    if args.markdown:
        Path(args.markdown).write_text(to_markdown(report))

    print(to_markdown(report))

    if not report["gate_passed"]:
        print("\n::error::Eval gate failed — this change cannot be promoted.", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Run the CareCopilot eval suite.")
    p.add_argument("--output", help="write the JSON report here")
    p.add_argument("--markdown", help="write the Markdown report here")
    p.add_argument("--tag", help="run only cases carrying this tag")
    args = p.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
