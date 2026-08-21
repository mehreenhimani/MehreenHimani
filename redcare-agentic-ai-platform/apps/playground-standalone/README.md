# Standalone console

The whole platform in one HTML file. Open `console.html` in a browser — no
install, no server, no API key, no network call.

```bash
open apps/playground-standalone/console.html      # macOS
xdg-open apps/playground-standalone/console.html  # Linux
```

## Why this exists

`apps/agent-service` is the reference implementation and the thing that would
actually run in Azure. But a Python service on a branch is not something you can
hand someone and have them *use* in thirty seconds, and a platform nobody can
open is a platform nobody forms an opinion about.

So the agent is ported to the browser: the same model catalogue, the same routing
rules, the same guardrail patterns, the same tool contracts, the same agent loop,
the same scorers and the same thresholds. The "model" is the deterministic
decision table the Python service uses in `LLM_MODE=mock`, which is what makes
the loop legible and the eval suite repeatable.

## What you can actually do with it

| Try this | What it demonstrates |
|---|---|
| Ask *"Where is my order RC10045821?"* | A grounded turn: routing decision with its reason, the tool call, the systems touched, the cost |
| Ask *"Can I take ibuprofen with warfarin?"* | HIGH_RISK screen → the human-approval gate. The pharmacist ticket does not exist until you approve it under **Governance** |
| Click the prompt-injection example | The input guardrail refuses before the model is called — note the turn costs $0.00 |
| Paste an IBAN with an order number | PII redaction before the prompt leaves the service |
| **Gateway** → mark `carecopilot-balanced` unhealthy, ask another question | Cross-region failover, with the reason in the trace |
| **Gateway** → switch to the `marketing-dev` key | Entitlement enforcement — a key that may only use the cheap tier |
| **Gateway** → turn guardrails off, re-send the injection | What the platform is actually preventing |
| **Evals** → run the golden set | The CI release gate, safety thresholded at 1.00 |

## Keeping it honest

The two implementations have to agree, or the console becomes a nice-looking lie.
`verify.py` compares the parts that are cheap to compare — the catalogue, the
virtual keys, the eval thresholds and the golden-set case ids — and fails if they
have drifted.

```bash
python3 apps/playground-standalone/verify.py
```

Rebuild after editing anything in `src/`:

```bash
python3 apps/playground-standalone/build.py
```
