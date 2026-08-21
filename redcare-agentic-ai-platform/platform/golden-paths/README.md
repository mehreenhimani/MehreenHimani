# Golden paths

A golden path is the **paved road**: the way to build an agent at Redcare that is
already wired for the gateway, guardrails, evals, observability, IaC and CI. It is
not a mandate. Teams may leave the road; they simply carry the work themselves when
they do, and the scorecard makes that visible rather than argued about.

## The bet

Platform adoption is won on **time to first token** and lost on friction. If starting
a compliant agent takes a week of reading, teams will copy an existing service, and
whatever that service got wrong propagates. If it takes an hour, the compliant path
is also the fastest path, and governance stops being a negotiation.

Target: **< 1 hour from `gh repo create` to a traced, guarded, evaluated agent
answering in dev.**

## What a team gets

```
my-agent/
  app/
    main.py                FastAPI service with /healthz, /readyz, /metrics
    agent.py               the loop — plan, act, verify
    tools/                 your tools, with governance metadata required
    prompts.py             versioned prompts, not string literals
  evals/
    golden_set.yaml        your cases; the platform ships the scorers
  infra/
    agent.tf               ~20 lines: an entry in the platform's agents map
  .github/workflows/
    ci.yml                 lint, test, evals, scan — inherited, not copied
  Dockerfile               multi-stage, non-root, health-checked
  README.md                filled in from the template's cookiecutter answers
```

Inherited without writing a line: the AI gateway client, a virtual key with a budget,
input and output guardrails, OTel tracing, Prometheus metrics, the audit log, the
approval flow for side-effecting tools, and the eval gate.

## What a team must still decide

Deliberately not automated, because these are product decisions and a template that
guesses them is a template that produces a compliant-looking agent nobody signed off:

1. **The tools** — what the agent may do, and which of them change state.
2. **The golden set** — 15-30 cases including the ones you expect to fail.
3. **The EU AI Act risk tier** — and the reasoning behind it.
4. **The escalation path** — who picks up when the agent hands over.
5. **The daily budget** — and who is told when it is hit.

## Onboarding, end to end

| Step | Who | Time |
|---|---|---|
| `redcare agent new my-agent` from the template | tenant team | 5 min |
| Define tools and golden set | tenant team | 2-4 h |
| Open a PR adding the agent to `infra/terraform/envs/dev` | tenant team | 15 min |
| Platform review: risk tier, budget, tool blast radius | platform team | 1 day SLA |
| Merge → dev deploy + eval gate | pipeline | 10 min |
| Production canary → promote | pipeline + 2 approvers | 1 day |

The platform team's job in that table is one review, not a project. That is the test
of whether something is a platform: onboarding the tenth team should cost the same as
onboarding the second.
