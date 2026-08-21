# Architecture — Redcare Agentic AI Platform

> How a customer question becomes a safe, grounded, observable, affordable answer —
> and every piece of technology that makes that true, in the order it acts.

---

## 0. The one-paragraph version

An internal team ships an agent by adopting a template. The agent runs as a container
on Azure Container Apps and can reach exactly one AI endpoint: the **LiteLLM gateway**.
The gateway decides which model serves the call, enforces the team's entitlement, rate
limit and budget, fails over across regions and providers, caches near-duplicate
questions, and writes a cost line attributed to a cost centre. Around the model call
sit the platform's **guardrails**; around the whole turn sits an **OpenTelemetry trace**
and an **append-only audit record**. Everything the agent may *do* is a declared tool,
and anything that changes a system of record is blocked behind a **human approval**.
All of it is defined in **Terraform**, shipped by **GitHub Actions**, and gated on an
**eval suite** that must pass before a change can merge.

---

## 1. The problem this platform exists to solve

Six months into "every team should use AI", a company without a platform reliably has:

| Symptom | Root cause |
|---|---|
| Provider keys in four repos and two Vercel projects | No central place to get model access |
| An invoice nobody can explain | No per-team cost attribution |
| One team's traffic spike rate-limiting everyone | No per-tenant rate limits |
| A hallucinated answer in a customer complaint | No groundedness measurement |
| "Which version of the prompt produced that?" — unanswerable | Prompts as string literals |
| A regional outage taking every AI feature down | Single deployment, no failover |
| A DPO who cannot sign anything off | No audit trail, no data-residency proof |

None of these is a model problem. They are all **platform** problems, and they are
what this architecture is built to make structurally impossible rather than
individually policed.

The product goal, stated as one sentence a stakeholder can hold: **any team at Redcare
can put a safe, observed, affordable AI agent in front of customers within a week, and
the company can prove afterwards what it did and what it cost.**

---

## 2. The request path, end to end

A customer types *"Can I take ibuprofen with warfarin?"* Here is every hop.

```
Customer
   │  HTTPS
   ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ Azure Front Door + WAF          DDoS, TLS, OWASP rules, geo-filtering            │
└──────────────────────────────────────────────────────────────────────────────────┘
   │  private
   ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ Container App: carecopilot-agent            (Azure Container Apps, VNet-injected) │
│                                                                                   │
│  1. router.classify      cheap classifier → trivial | standard | complex          │
│  2. router.resolve       entitlement → tier → health. Emits the *reason*.         │
│  3. finops.preflight     tenant daily budget + session ceiling checked first      │
│  4. guardrails.input     injection → scope → PII redaction                        │
│  5. agent.step.N         plan (LLM) → act (tools) → observe → repeat              │
│  6. guardrails.output    secrets → grounding → medical-advice → PII → disclosure  │
│  7. persist + account    session, spend ledger, metrics, audit record             │
└──────────────────────────────────────────────────────────────────────────────────┘
   │                            │                                │
   │ every model call           │ every tool call                │ every span
   ▼                            ▼                                ▼
┌──────────────────┐   ┌────────────────────────┐   ┌───────────────────────────────┐
│ LiteLLM gateway  │   │ Systems of record      │   │ OTel Collector                │
│ (Container App)  │   │  SAP-OMS   orders      │   │  redact → tail-sample → fan out│
│                  │   │  WMS       stock       │   │                               │
│ virtual keys     │   │  ABDA      interactions│   │  → Azure Monitor / App Insights│
│ entitlement      │   │  AI Search policies    │   │  → Prometheus → Grafana        │
│ rpm/tpm limits   │   │  ServiceNow escalation │   │  → Log Analytics (audit, 7y)   │
│ budgets          │   └────────────────────────┘   └───────────────────────────────┘
│ retries+failover │
│ semantic cache   │──── Redis (semantic cache) ─────┐
│ spend attribution│──── PostgreSQL (spend, keys) ───┤  both private-endpoint only
│ callbacks        │                                  │
└──────────────────┘                                  │
   │         │                                        │
   ▼         ▼                                        │
Azure OpenAI  Azure OpenAI      Anthropic             │
Sweden Central West Europe      (deep tier)           │
(primary)      (failover)                             │
   └───────── all reached over private endpoints ─────┘
```

### Why each step is where it is

**Classification before routing.** A greeting and a drug-interaction question do not
need the same model. Classifying first means the expensive tier is spent on the turns
that need it. The classifier itself runs on the cheap tier and costs about $0.0001 —
it pays for itself the first time it keeps a "hello" off the deep model.

**Budget check before guardrails.** Guardrails cost CPU; a tenant already over budget
should be refused before the platform spends anything on them, including its own.

**Guardrails before the model, not only after.** Prompt injection has to be caught
before the model reads it. PII has to be removed before the prompt leaves the VNet.
An output-only guardrail is a guardrail that already lost.

**Grounding checked against tool observations, not against a vibe.** Every factual
claim in the answer — an order number, a stock state, a policy id, a risk band — must
appear in something a tool returned. This is a cheap, explainable check that catches
the failure mode people actually fear.

**Human approval before the side effect, not after the answer.** The agent never opens
a pharmacist ticket on its own. It *prepares* one and stops. That is EU AI Act Art. 14
expressed as a code path rather than a paragraph in a policy document.

---

## 3. The technology map — what each thing is for

### 3.1 Azure Cloud — the substrate

| Service | Role | Why this one |
|---|---|---|
| **Container Apps** | Runs the agents and the gateway | Revisions, traffic splitting, KEDA autoscaling, managed identity and scale-to-zero without operating a Kubernetes control plane. A small platform team should be maintaining golden paths, not etcd. The exit to AKS stays open because the unit of deployment is a plain OCI image. |
| **Azure OpenAI** (Sweden Central + West Europe) | Model deployments | EU data residency, enterprise agreement, private endpoints, per-region quota. The second region is failover *and* a second quota pool. |
| **Azure AI Search** | Policy/knowledge index for RAG | Hybrid retrieval with a semantic ranker. In RAG, retrieval is what is usually wrong with a bad answer, not the model. |
| **Key Vault** | Every secret | RBAC (not legacy access policies), purge protection, private endpoint. Secret *values* never enter Terraform. |
| **Entra ID** | Identity for humans and workloads | Workload identity federation removes the last long-lived credential from CI. |
| **PostgreSQL Flexible Server** | Gateway spend logs, transcripts, approvals, eval history | Point-in-time restore on the financial and evidential record. Managed identity auth only. |
| **Azure Cache for Redis** | Gateway semantic cache, agent session state | The cheapest token is the one never sent. |
| **Log Analytics + App Insights** | Telemetry and the audit table | One workspace so a single KQL query can join a trace, a cost and an escalation. |
| **Managed Grafana** | Dashboards | Provisioned from Git; a dashboard nobody can recreate makes an outage worse. |
| **Content Safety** | Provider-independent content filtering | The filter must not change when the model behind the endpoint changes. |
| **Front Door + WAF** | Edge | DDoS, TLS, OWASP, geo-filtering before anything reaches the VNet. |
| **Defender for Cloud** | Posture and runtime threat detection | Container, Key Vault and AI plans. |

**The network rule that shapes everything else:** the AI plane has no public ingress
and no unmonitored egress. Every dependency is a private endpoint with a matching
private DNS zone. (Missing the DNS zone is the single most common Azure private-
networking mistake — the endpoint exists, the name still resolves publicly, and the
traffic quietly leaves the VNet.)

### 3.2 LiteLLM / AI Gateway — the choke point

The gateway is the most important design decision in the platform, because it is the
only thing that makes every other guarantee **enforceable rather than advisory**.

| It owns | Without it |
|---|---|
| Virtual keys per team | Provider keys copied into N repos |
| Entitlement (which team, which model) | Anyone can call the most expensive model |
| Rate limits (rpm/tpm per key) | One team's spike throttles everyone |
| Budgets, enforced pre-call | A runaway loop is discovered on the invoice |
| Retries, timeouts, cooldowns | N different retry policies, all subtly wrong |
| Cross-region and cross-provider failover | A regional outage is a company-wide outage |
| Semantic caching | Paying repeatedly for "where is my order?" |
| Cost attribution to a cost centre | An invoice nobody can explain |
| Guardrail hooks and PII masking | Every team reimplements redaction |
| One OTel/Langfuse callback for everyone | Observability that depends on who remembered |

The **virtual key is the unit of governance**: a revocable credential carrying a
tenant, a cost centre, an entitlement list, rate limits, a budget and an owning Entra
group. Onboarding a team is issuing one; offboarding is revoking one.

Model names are **abstractions, not products**. Tenants ask for `carecopilot-balanced`,
not `gpt-4o-2024-11-20`. Swapping the model underneath is a config change reviewed in
a PR and validated by the eval gate — no tenant code changes.

### 3.3 Terraform / Infrastructure as Code — the definition

```
modules/
  network/        VNet, subnets, NSGs, 8 private DNS zones
  identity/       managed identities, RBAC, GitHub OIDC federation
  security/       Key Vault, secret slots, Content Safety, Defender
  data/           Azure OpenAI (2 regions), AI Search, Storage, Postgres, Redis
  runtime/        Container Apps environment + ACR   ← shared fabric
  gateway/        the LiteLLM container app
  compute/        the agents, as a map — onboarding is a map entry
  observability/  Log Analytics, App Insights, Grafana, 6 alert rules, budgets
envs/
  dev/   prod/    same modules, different numbers
```

Three things worth pointing at:

1. **`runtime/` exists because of a real dependency cycle.** The gateway needs a
   registry to pull from; the agents need the gateway's URL. Putting the registry in
   `compute/` and the environment in `gateway/` makes the two modules depend on each
   other and Terraform refuses to build a graph. The fix is not a workaround, it is
   the correct decomposition: the compute *fabric* is shared infrastructure that both
   sit on. Ownership follows the same line.

2. **`compute/` takes agents as a map.** Onboarding the tenth team is a map entry, not
   a new pipeline. That is the actual test of whether something is a platform.

3. **dev and prod are the same code.** What differs is size and cost. What never
   differs is posture — private networking, managed identity, no public data access,
   guardrails on, audit on. If a control had to be turned *on* for production, dev
   would be the weak link an attacker uses.

**State** lives in Azure Storage with blob leasing for locks, versioning and soft
delete, private-endpoint only, one container per environment. Nobody holds standing
write access to the subscriptions; GitHub gets a few minutes of it via OIDC.

### 3.4 GitHub + GitHub Actions — the only path to production

```
Pull request ──► CI                     lint → test → EVALS → terraform → security → gate
             └─► terraform plan         plan + Checkov + tfsec + Conftest, posted as a comment

Merge to main ─► CD                     build → SBOM → Trivy → cosign sign → dev deploy
                                        → smoke → online eval → prod canary 10%
                                        → bake 15 min → promote 100% (or roll back)
             └─► terraform apply        dev automatic; prod behind 2 approvers

Nightly ──────► drift detection         non-empty plan opens an issue
```

Four things that are not decoration:

- **The eval job is a required check.** For a non-deterministic system, unit tests
  prove the plumbing and evals prove the behaviour. Safety is thresholded at 1.00 —
  one safety miss fails the build.
- **The plan comment is the review artefact.** A reviewer approving an infrastructure
  PR is approving a diff of *resources*, not a diff of HCL. The reviewed plan file is
  the file that gets applied.
- **OIDC everywhere.** No client secret exists to leak. Entra ID checks that the
  token's subject matches an exact federated credential — a different branch, a
  different environment or a fork does not match.
- **Rollback is a traffic-weight change.** Seconds, not a rebuild. A rollback that
  needs a rebuild is not a rollback.

### 3.5 Observability — four signal families

Classic APM answers *"was it fast and did it 500?"*. That is necessary and nowhere
near sufficient for an agent, which can be fast, return 200, and still be wrong,
ungrounded, unaffordable or looping.

| Family | Metrics | The question it answers |
|---|---|---|
| **RED** | `agent_requests_total`, `agent_request_duration_seconds`, `agent_errors_total` | Is the service up? |
| **Agent** | `agent_steps_per_turn`, `agent_tool_calls_total`, `agent_tool_duration_seconds`, `agent_loop_termination_total` | Is it behaving? |
| **Quality** | `guardrail_firings_total`, `agent_groundedness_ratio`, `agent_escalations_total`, `agent_eval_score` | Is it right? |
| **FinOps** | `llm_tokens_total`, `llm_cost_usd_total`, `llm_cost_usd_per_turn`, `llm_cache_events_total`, `llm_budget_remaining_usd` | Is it affordable? |

Traces carry the causal story of one turn. The **OTel Collector** is the seam that
keeps the application vendor-neutral: the app speaks OTLP and knows nothing about
Azure Monitor. It also does the work you do not want in a request path — batching,
retry, memory limiting, and a **redaction pass** so prompts and completions never
reach a trace backend that is not an approved store for health data.

**Tail sampling, not head sampling.** Keep every error, every turn over 4s, every
guardrail firing and every escalation; sample 20% of the boring successes. A head
sampler has to guess before the request runs.

**SLOs with error budgets**, because an SLO without an error budget is a wish:

| SLO | Objective | Window | Budget |
|---|---|---|---|
| Gateway availability | 99.9% | 30d | 43.2 min |
| Turn latency | p95 < 4.0s | 30d | 43.2 min |
| Groundedness | ≥ 97% of turns fully grounded | 7d | 302.4 min |
| Guardrail coverage | 100% of turns pass both pipelines | 30d | 0 |

Multi-window burn-rate alerts: 14.4× over 1h pages someone; 6× over 6h opens a ticket.
A single threshold catches an outage and misses a leak.

### 3.6 LLMOps / MLOps — how quality is managed

**Prompts are versioned platform assets.** Each has an id, a semantic version, an
owner and an eval suite. Every turn records which version produced it, so a quality
move can be attributed to a prompt change the same way a latency regression is
attributed to a deploy.

**Evals are the release gate.** Four scorer families matching the four ways a turn
goes wrong:

| Scorer | Threshold | Catches |
|---|---:|---|
| `task_success` | 0.85 | Did it do the right thing at all? |
| `safety` | **1.00** | Did it refuse or escalate when it had to? |
| `groundedness` | 0.95 | Is every claim traceable to a tool result? |
| `efficiency` | 0.90 | Steps, latency and cost per solved turn |

The golden set is 16 cases covering happy paths, negatives, clinical high-risk,
policy grounding, prompt injection, scope, PII and cost. Three rules that make a suite
survive a year: write the failure cases first; every production incident becomes a
case; keep it fast enough to run on every PR, because a nightly gate is not a gate.

**Online evaluation** closes the loop: the same suite runs against the deployed
revision after every deploy, and `agent_eval_score` alerts when the live distribution
drifts away from what CI approved.

### 3.7 Security — the controls, and what each one is actually for

| Control | Threat it addresses |
|---|---|
| Workload identity + OIDC federation | Credential theft — there is no long-lived credential |
| Key Vault RBAC + purge protection + private endpoint | Secret exfiltration; unrecoverable deletion |
| Private endpoints + NSG egress deny | A compromised agent posting customer data to an arbitrary host |
| Prompt-injection guardrail | An attacker rewriting the agent's instructions through a message |
| PII redaction before the model call | Health data leaving the VNet, or landing in a log |
| Output secret scan | The model repeating a credential it saw in a tool result |
| Tool scopes on the virtual key | Least privilege at the prompt boundary — the agent is only *told about* tools it may use |
| HITL on side-effecting tools | An agent acting on a system of record without a human |
| SBOM + Trivy + cosign + ACR content trust | Supply-chain compromise; an unsigned image cannot run |
| gitleaks over full history | A key committed and force-pushed away |
| Conftest / Checkov / tfsec on the *plan* | Compliant-looking HCL that produces a public storage account |

**The trust boundary that matters most in an agentic system:** tool output is data,
never instruction. A policy document, an order note or a product description can
contain text engineered to look like a system prompt. The agent's system prompt says
so explicitly, and the injection guardrail runs over content before it is used.

### 3.8 FinOps — unit economics as a first-class concern

Cost per turn is the number everything else is a proxy for.

| Lever | Effect | Cost |
|---|---|---|
| Router-model tiering | Trivial turns on the cheap tier: ~16× cheaper per token | one classifier call |
| Semantic cache | 25-35% of support traffic answered for free | Redis |
| Rolling context window | Bounded prompt growth across a long session | slight context loss |
| Per-request / per-session / per-tenant ceilings | A runaway loop stops itself | a degraded answer |
| Budget enforced at the gateway | Spend stops before the invoice moves | refused calls |

All five are visible in the playground's FinOps panel and in the Grafana dashboard,
so a product manager can reason about the economics without asking an engineer.

---

## 4. How the pieces are governed

### EU AI Act

CareCopilot is classified **limited-risk**: a customer-facing informational assistant
that is not a medical device and not diagnostic, because all clinical judgement is
routed to a registered pharmacist. That classification is a decision, made on the
record, and it is enforced by the design — the moment the agent could give a dose, it
would be a different tier and would need a different control set.

| Article | Obligation | Implemented by |
|---|---|---|
| Art. 50 | Transparency — the user knows it is AI | `guardrails.ensure_disclaimer` on every reply |
| Art. 12 | Record-keeping over the system's lifetime | Append-only `AgentAudit_CL`, 7-year retention |
| Art. 14 | Effective human oversight | HITL approval gate on every side-effecting tool |
| Art. 15 | Accuracy and robustness | Groundedness scorer + CI gate at 0.95 |

### GDPR

Health data is special-category under Art. 9. Lawful basis: Art. 6(1)(b) contract and
Art. 9(2)(h) pharmacy care. Data residency EU-only, enforced by a Terraform variable
validation *and* an OPA policy — belt and braces, because a region typo is a
reportable breach rather than a lint warning. Minimisation by redaction before the
model call. Retention split: transcripts 90 days, audit 7 years.

---

## 5. What I would build in the first 90 days

Ordered by what unblocks the most other work, not by what demos best.

**Days 1-30 — make model access safe and countable.**
Stand up the gateway, issue virtual keys to the three teams already calling providers
directly, and turn off their provider keys. Nothing else can be enforced until every
call goes through one place. Success: 100% of spend attributable to a key, and one
dashboard showing cost per team.

**Days 31-60 — make quality measurable.**
Ship the eval harness and the guardrail library as platform capabilities, and make the
eval gate a required check on the first tenant repo. Success: one team's agent cannot
merge a change that regresses safety, and they can see why.

**Days 61-90 — make onboarding cheap.**
Golden-path template, the agents map, the scorecard. Success: a new team goes from
zero to a traced, guarded, evaluated agent in dev in under a day, with one platform
review rather than a platform project.

The sequencing argument: **enforcement before measurement before self-service.**
Self-service on top of unmeasured, unenforced access just multiplies the problem
faster.

---

## 6. What is deliberately not here, and why

| Not built | Why |
|---|---|
| Multi-agent orchestration framework | Two agents that need to coordinate usually mean one workflow was decomposed wrong. Earn it with a real case. |
| Fine-tuning pipeline | Retrieval and prompting exhaust their headroom long before fine-tuning is the cheapest next move. |
| Self-hosted models on GPUs | The cost only works at a volume Redcare does not have yet, and it moves the operational burden onto a small team. |
| A bespoke vector database | AI Search covers hybrid retrieval and is already in the security perimeter. |
| Kubernetes | Container Apps covers the requirements; AKS is a second product to operate. |
| Agent-to-agent protocols | Standards are still moving. Committing early is expensive to undo. |

Each of these is a *not yet* with a stated trigger, not a *never*. Knowing what you
are not building — and being able to say why in one sentence — is most of platform
product management.
