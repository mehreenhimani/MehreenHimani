# Platform scorecard

Every agent on the platform is scored, monthly and automatically, against the same
eight criteria. The score is published in the internal catalogue next to the agent.

## Why score at all

A platform team's hardest problem is not building capabilities, it is knowing whether
anyone adopted them. "Are teams using the gateway?" answered by intuition is how a
platform ends up with three shadow integrations and a surprise invoice. Answered by a
scorecard, it becomes a number that moves, a conversation with a specific team, and a
backlog item with evidence behind it.

The scorecard is also how the platform team finds its own gaps. When six teams all
score low on the same criterion, that is not six teams being careless — it is one
platform capability that is too hard to adopt, and it goes to the top of the roadmap.

## The criteria

| # | Criterion | Weight | Passing | Signal |
|---|---|---:|---|---|
| 1 | **Gateway routing** — all model calls go through LiteLLM | 20% | 100% of calls | gateway spend logs vs. provider invoices |
| 2 | **Eval coverage** — a golden set gating CI | 15% | ≥ 15 cases, gate enforced | `eval-report.json` in the last 10 builds |
| 3 | **Guardrails** — platform input/output pipelines enabled | 15% | both enabled, no overrides | `/platform/config` on the running revision |
| 4 | **Observability** — traces, metrics and audit reaching the platform | 15% | all three present | Log Analytics + Prometheus targets |
| 5 | **IaC coverage** — no resource created outside Terraform | 10% | zero drift for 30 days | nightly drift job |
| 6 | **Cost hygiene** — budget set, cost centre tagged, cache used | 10% | budget < 2× actual, cache ≥ 15% | spend ledger |
| 7 | **Security** — no critical CVEs, image signed, no secrets in code | 10% | clean on the deployed digest | Trivy, cosign, gitleaks |
| 8 | **Human oversight** — approval flow on every side-effecting tool | 5% | 100% gated | tool registry metadata |

## Bands

| Score | Band | What it means |
|---|---|---|
| 90-100 | **Paved road** | Fully on the golden path. Ships without platform involvement. |
| 70-89 | **Adopted** | On the platform with known gaps. One or two backlog items. |
| 50-69 | **Partial** | Real risk somewhere. Platform team pairs with the tenant this quarter. |
| < 50 | **Off-road** | Not eligible for production traffic until it improves. |

## What it is not

It is not a performance review, and the moment it is used as one, teams start gaming
it and the numbers stop being useful. It is a map of where the paved road has
potholes. If an agent scores badly on evals, the first question is "is our eval
tooling hard to adopt?", not "why did this team not care?".
