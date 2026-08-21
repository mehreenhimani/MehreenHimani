#!/usr/bin/env python3
"""
Assemble the standalone console into one self-contained HTML file.

The Python service in apps/agent-service is the reference implementation. This
build is a faithful port of it to the browser — same catalogue, routing rules,
guardrail patterns, tool contracts, agent loop, scorers and thresholds — so the
platform can be opened and operated without installing anything.

    python3 apps/playground-standalone/build.py

Keep the two in step: if a routing rule or a threshold changes in the Python,
change it here too. `verify.py` checks the parts that are cheap to compare.
"""
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "src"

head = (SRC / "head.html").read_text()
body = (SRC / "body.html").read_text()
css = (SRC / "style.css").read_text()
js = "\n".join((SRC / f).read_text() for f in ("engine.js", "orchestrator.js", "ui.js"))

out = head.replace("__CSS__", css) + "\n" + body.replace("__JS__", js)
target = HERE / "console.html"
target.write_text(out)
print(f"wrote {target.relative_to(HERE.parent.parent)} — {len(out):,} bytes")
