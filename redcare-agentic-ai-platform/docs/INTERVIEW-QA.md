# Technical round — questions and answers

**Role:** Product Manager, Agentic AI Platform · Redcare Pharmacy
**Companion to:** this repository and `docs/ARCHITECTURE.md`

Every line of the job description is covered below, with a section header naming the
line it comes from. Answers are written the way you would actually say them: a direct
sentence first, then the reasoning, then a concrete reference into this repo so you can
show rather than assert.

**How to use this.** Do not memorise it. Read a section, close the file, and say the
answer out loud in your own words. The 40 questions marked ★ are the ones most likely
to decide the round.

---

## Contents

| § | Job-description line it covers |
|---|---|
| [1](#1-the-opening) | The opening — who you are, why this role |
| [2](#2-product-vision-and-roadmap) | "Shape the product vision and roadmap… measurable outcomes" |
| [3](#3-platform-experience-for-internal-users) | "Create a strong platform experience for internal users" |
| [4](#4-llmops) | "core platform capabilities around LLMOps…" |
| [5](#5-mlops) | "…MLOps…" |
| [6](#6-ai-gateway-administration--litellm) | "…AI gateway administration…" + "LiteLLM or AI gateways" |
| [7](#7-observability) | "…observability…" + "observability tooling" |
| [8](#8-governance-and-secure-ai-enablement) | "…governance, and secure AI enablement" |
| [9](#9-azure-cloud) | "Azure Cloud" |
| [10](#10-terraform-and-infrastructure-as-code) | "Terraform" + "Infrastructure as Code" |
| [11](#11-github-and-cicd-with-github-actions) | "GitHub, CI/CD with GitHub Actions" |
| [12](#12-devops-practices-and-platform-engineering) | "DevOps practices, and platform engineering" |
| [13](#13-security) | "security" |
| [14](#14-dataai-platform-technologies) | "Data/AI platform technologies" |
| [15](#15-bringing-structure-requirements-stakeholders-prioritisation) | "Bring structure… defining requirements, aligning stakeholders, prioritising" |
| [16](#16-product-management-in-technical-platform-environments) | "solid product management experience in technical platform environments" |
| [17](#17-how-these-areas-connect-in-practice) | "know how these areas connect in practice" |
| [18](#18-system-design-and-curveballs) | Whiteboard / pressure questions |
| [19](#19-questions-to-ask-them) | Your turn |
| [20](#20-the-30-second-answers) | Rapid-fire crib sheet |

---

## 1. The opening

### ★ Q1.1 — Tell me about yourself.

> I have thirteen years in regulated financial services — delivery, quality
> engineering, and for the last stretch, AI products. I have shipped seven AI systems
> into production in banking: fraud detection, KYC triage, AML alert prioritisation
> and regulatory RAG. What that background gave me is a specific instinct: in a
> regulated business, the model is the easy part. What decides whether an AI product
> ships is whether you can explain it, audit it, cap its cost, and prove what it did.
>
> That is exactly what a platform is for, which is why this role interests me. And
> pharmacy has the same shape as banking — special-category data, a regulator, a
> customer who is sometimes vulnerable, and a business that still has to move fast.
>
> To make sure I was talking about the right things today rather than the things I
> already knew, I built a reference implementation of the platform this role
> describes: an agent, a LiteLLM gateway, Terraform for Azure, GitHub Actions with an
> eval gate, and the observability around it. I am happy to walk through any part of
> it.

**Why this works:** it converts "financial services" from a mismatch into the reason
you are qualified, and it ends by offering evidence rather than claims.

### Q1.2 — Why Redcare Pharmacy?

> Three reasons. First, the problem is real: Europe's largest online pharmacy has
> genuine volume, genuine regulatory constraint and genuine customer stakes, so an AI
> platform there has to be more than a demo. Second, the stage is the interesting one
> — you are building foundations, which means the decisions made in the next year
> decide whether AI at Redcare is ten governed products or forty ungoverned ones.
> Third, it is the intersection I actually enjoy: cloud, AI enablement, security,
> reliability and developer experience, where the product work is turning engineering
> complexity into decisions other people can act on.

### Q1.3 — You are a PM, not an engineer. Why should we trust your technical judgement?

> You should trust it where it is earned and check it where it is not. I can read and
> write the code in this repository, I understand what each Azure service costs and
> what it fails at, and I can hold a design conversation about routing, failover and
> retrieval without needing a translator. What I do not do is claim to be the deepest
> engineer in the room — my job is to make sure the deepest engineer in the room is
> working on the thing that matters, and that the rest of the business understands why.
>
> The practical test is this: can I write the eval gate thresholds, defend them to
> engineering, and explain them to a compliance officer in the same afternoon? That is
> the job, and it is a different skill from writing the orchestrator.

---

## 2. Product vision and roadmap

> *JD: "Shape the product vision and roadmap for our Agentic AI platform, translating
> strategic AI ambitions into clear priorities, measurable outcomes, and practical
> platform capabilities."*

### ★ Q2.1 — What is your vision for an agentic AI platform at Redcare?

> One sentence: **any team at Redcare can put a safe, observed, affordable AI agent in
> front of customers within a week, and the company can prove afterwards what it did
> and what it cost.**
>
> Three clauses, three audiences. "Within a week" is the engineering team's promise —
> speed. "Safe and observed" is the compliance and security promise. "Prove what it
> cost" is the CFO's. A vision that only serves one of those three gets defunded by
> the other two.
>
> What it deliberately does *not* say is anything about a model, a framework or a
> vendor. Those change. The promise should not.

### ★ Q2.2 — Give me your first 90 days.

> Sequenced by what unblocks the most other work, not by what demos best.
>
> **Days 1-30 — make model access safe and countable.** Stand up the gateway, issue
> virtual keys to the teams already calling providers directly, revoke their provider
> keys. Nothing else is enforceable until every call goes through one place. Success
> looks like: 100% of AI spend attributable to a key and a cost centre, on one
> dashboard.
>
> **Days 31-60 — make quality measurable.** Ship the eval harness and the guardrail
> library as platform capabilities and make the eval gate a required check on the
> first tenant repo. Success: a team physically cannot merge a change that regresses
> safety, and they can see exactly why on the pull request.
>
> **Days 61-90 — make onboarding cheap.** Golden-path template, the agents map in
> Terraform, the adoption scorecard. Success: a new team goes from zero to a traced,
> guarded, evaluated agent in dev in under a day, with one platform review rather than
> a platform project.
>
> The argument for that order is **enforcement before measurement before self-service**.
> Self-service on top of unmeasured, unenforced access just multiplies the problem
> faster.

### Q2.3 — How do you decide what goes on the platform roadmap versus what a tenant team builds?

> My test is: **does more than one team need it, and is getting it wrong expensive?**
>
> Both yes → platform. PII redaction, the gateway, evals, tracing, the audit log. One
> team should never have to reimplement redaction to ship, and one team getting it
> wrong is a company incident.
>
> One team, or cheap to get wrong → tenant. Their tools, their prompts, their domain
> logic, their golden set. If the platform owned those it would become the bottleneck
> for every product decision, which is how platform teams end up hated.
>
> The interesting cases are the ones in between, and I resolve those by counting: if
> three teams have written their own version of something, the platform has a gap.
> That is what the scorecard is for — it turns "are teams struggling with X?" from
> intuition into a number.

### ★ Q2.4 — What are your platform's success metrics?

> Four, and I would put them on one page in this order.
>
> **Adoption.** Number of agents on the paved road, and the share of total AI spend
> flowing through the gateway. If that share is not near 100%, every other metric is
> measuring a subset.
>
> **Time to first token.** How long from a team deciding to build an agent to it
> answering in dev. Target under a day. This is the leading indicator for every other
> platform metric — a slow platform gets routed around, and routing around is where
> the incidents come from.
>
> **Quality and safety.** Groundedness rate, guardrail coverage, escalation rate, and
> eval scores on deployed revisions. These are what let the business say yes.
>
> **Unit economics.** Cost per turn, cost per resolved conversation, cache hit rate.
> Cost per *resolved conversation* rather than per call — an agent that is cheap per
> call and never resolves anything is expensive.
>
> I would deliberately not lead with "number of AI use cases", which is the metric
> most AI platforms report and the one most easily gamed.

### Q2.5 — How would you know the platform is failing?

> Three signals, in order of how early they appear.
>
> First, teams building around it. A team that spins up its own Azure OpenAI resource
> is not being difficult; it is telling you the paved road is slower than the ditch.
> That shows up in the scorecard's gateway-routing criterion before it shows up
> anywhere else.
>
> Second, the platform team becoming a ticket queue. If onboarding the tenth team
> costs the same as the second, it is a consultancy, not a platform.
>
> Third, no one running the evals. If a capability exists and nobody uses it, it was
> either the wrong capability or it is too hard to adopt — and those need very
> different fixes.

### Q2.6 — How do you write requirements for a platform team?

> Not as user stories about "the platform". Platform requirements are about the
> *experience of the team adopting it*, so I write them from the tenant's side with an
> explicit acceptance test the platform team can run.
>
> Rather than *"as a platform, I want rate limiting"*, it is: *"a tenant team can
> exceed their rate limit and receive a clear 429 with the limit, the reset time and a
> link to request an increase — without opening a ticket, and without affecting any
> other tenant's latency."* That version tells the engineer what to build, tells me
> how to test it, and contains the reason it exists.
>
> Then I attach the non-functionals as numbers, not adjectives: p95 latency budget,
> error budget, cost ceiling. "Fast" is not a requirement.

### Q2.7 — How do you handle a stakeholder who wants an agent that the platform should not support?

> I separate the *want* from the *shape*. Usually the want is legitimate and the shape
> is the problem.
>
> Concretely, if marketing wants an agent that gives customers dosage advice, the want
> is "reduce pharmacist call volume". The shape — individualised clinical advice from
> an LLM — moves the whole system into EU AI Act high-risk, needs conformity
> assessment, and is a patient-safety exposure. So I would say no to the shape, in one
> sentence, with the reason, and then offer the nearest thing the platform can do: an
> agent that screens interactions, explains the general information, and hands to a
> pharmacist with a prepared summary — which is what CareCopilot in this repo actually
> does, and which cuts call handling time without taking on the clinical liability.
>
> The failure mode I avoid is a vague "we'll look into it". That is how shadow AI gets
> built.

---

## 3. Platform experience for internal users

> *JD: "Create a strong platform experience for internal users by understanding the
> needs of engineering, data, AI, and business teams…"*

### ★ Q3.1 — What makes a good internal developer experience?

> The honest test is: **can a competent engineer who has never seen your platform ship
> something real on their first day, without talking to you?**
>
> That decomposes into four things. A **paved road** — a template that already has the
> gateway, guardrails, evals, tracing and CI wired, so the compliant path is also the
> fastest path. **Golden defaults** — sensible budgets, timeouts, retries and probes
> that a team never has to think about until they need to. **Escape hatches** — a team
> that needs something unusual can leave the road without asking permission; the
> scorecard just makes it visible. And **legibility** — when something breaks, the
> platform tells you *why*, not just that it failed.
>
> That last one is why the playground in this repo renders the routing reason, the
> guardrail verdicts and the cost breakdown. A platform that hides its reasoning
> cannot be debugged by the teams adopting it.

### Q3.2 — Engineering, data, AI and business teams want different things. How do you serve all four?

> They want different things at different *layers*, which is what makes it tractable.
>
> Engineering wants the golden path, good defaults and fast feedback — they are
> optimising for time to first token and time to debug.
>
> Data and AI teams want model choice, eval tooling, retrieval quality and the ability
> to compare. They are the ones who will notice if the platform locks them to one
> model, which is why model names in the catalogue are abstractions rather than
> products.
>
> Business teams want an outcome and a cost. They do not care which model is behind
> `carecopilot-balanced`; they care that handling time drops and the bill is
> predictable. So the FinOps surface is built for them — cost per resolved
> conversation, not tokens.
>
> Security and compliance want evidence, not assurances. That is why governance in
> this repo is served as *data* from a live endpoint rather than written in a document
> that drifted six months ago.
>
> The thing that serves all four at once is the trace. It is a debugging tool for
> engineering, a quality signal for AI, a cost line for business and an audit record
> for compliance — one artefact, four readers.

### Q3.3 — How do you gather requirements from internal users?

> Three sources, weighted differently.
>
> **What they say** — interviews, office hours. Useful for intent, unreliable for
> priority, because everyone's blocker feels like the top one.
>
> **What they do** — the scorecard, the drift job, the gateway spend logs, support
> tickets. Six teams failing the same scorecard criterion is a much stronger signal
> than six teams asking for different things.
>
> **What they build around you** — the strongest signal of all. A team that wrote
> their own PII redaction did not do it for fun; they did it because ours was hard to
> find or hard to adopt.
>
> I would run monthly office hours and a quarterly platform survey, but I would trust
> the telemetry more than the survey, because the survey is answered by the people who
> like you enough to answer it.

### Q3.4 — How do you drive adoption of a platform nobody is obliged to use?

> Make the paved road the fastest road, then make the alternative visible.
>
> Mandates produce compliance theatre — teams do the minimum and route around the
> spirit of it. What works is the template that saves a week, the eval gate that
> catches a regression before a customer does, and the cost dashboard that lets a team
> defend their own budget.
>
> Then make it visible: publish the scorecard next to each agent in the internal
> catalogue. Not as a grade — the moment it is a grade, teams game it and the numbers
> stop being useful — but as a map of where the road has potholes. If six teams score
> low on the same criterion, that is a platform defect, and it goes to the top of my
> backlog.
>
> The one place I would use a hard gate is production traffic for anything
> customer-facing handling health data. That is not an adoption lever, it is a risk
> decision.

### Q3.5 — What does "time to first token" mean and why do you care about it?

> The elapsed time from a team deciding to build an agent to that agent returning its
> first real answer in a dev environment. Target: under a day; in this repo's golden
> path, under an hour.
>
> I care because it is the leading indicator for everything else. A platform where
> that takes a week gets routed around, and routing around is precisely where the
> ungoverned provider keys, the unmeasured quality and the surprise invoices come
> from. Every governance property the platform has depends on teams choosing to be on
> it.
>
> It is also the one platform metric that a tenant engineer will independently agree
> is the right metric, which makes it a good thing to be measured on.

---

## 4. LLMOps

> *JD: "Drive the development of core platform capabilities around LLMOps…"*

### ★ Q4.1 — What is LLMOps, and how is it different from MLOps?

> MLOps manages a *model artefact* through a lifecycle: data, training, validation,
> registry, deployment, monitoring for drift. The artefact is yours, it is versioned,
> and its behaviour changes only when you retrain.
>
> LLMOps mostly manages things *around* a model you did not train and cannot inspect.
> The unit of change is a prompt, a retrieval index, a tool definition or a routing
> rule — not a set of weights. Five differences that actually change what you build:
>
> 1. **Non-determinism.** The same input can produce different output, so "did the
>    tests pass" becomes "did the score stay above the threshold".
> 2. **Evaluation replaces validation.** There is no held-out test set with a ground
>    truth label; there is a golden set and a set of scorers you have to argue for.
> 3. **Prompts are deployable artefacts.** They need versions, owners and rollback.
> 4. **Cost is per-request and variable.** In classic ML, inference cost is roughly a
>    constant. Here a bad prompt change can double the bill overnight.
> 5. **The failure mode is confident wrongness**, not an exception. Nothing 500s.
>
> The practical consequence for a platform: you need an eval gate, prompt versioning,
> a groundedness metric and per-request cost accounting — none of which a classic
> MLOps stack gives you.

### ★ Q4.2 — How do you evaluate an agent? Walk me through the suite.

> Four scorer families, matching the four ways a turn goes wrong. In this repo they
> are in `app/evals/suite.py`.
>
> **Task success** — did it call the right tools and produce the right content? Binary
> per case, thresholded at 0.85.
>
> **Safety** — did it refuse, redact or escalate when it had to? Thresholded at
> **1.00**. One miss fails the build. That is not perfectionism; a safety scorer with
> a 0.95 threshold is a statement that one customer in twenty can receive an unsafe
> answer, which is not a statement I would sign.
>
> **Groundedness** — does every factual claim trace to a tool observation? 0.95. This
> is the hallucination metric, and doing it against tool output rather than an
> LLM judge makes it cheap, deterministic and explainable.
>
> **Efficiency** — steps, latency and cost per case, against a per-case budget. 0.90.
> Without this, quality improves by spending more, forever.
>
> The golden set is 16 cases: happy paths, a negative (an order that does not exist),
> clinical high-risk, policy grounding, two prompt injections, an out-of-scope
> request, a PII case, and a "hello" that must stay on the cheap tier. Deliberately
> small enough to run on every pull request, because a suite too slow for CI gets
> moved to nightly, and a nightly gate is not a gate.

### Q4.3 — Where do golden-set cases come from?

> Four sources, and the ratio matters.
>
> Roughly 30% from the intended happy paths — written by the product owner before the
> agent exists, which is a useful forcing function for "what does good look like".
>
> Roughly 30% adversarial — written by whoever most wants to break it. Injections,
> scope escapes, ambiguous phrasing, two languages in one sentence.
>
> Roughly 30% from real traffic — sampled from production traces, especially turns
> that escalated, hit the step ceiling or scored badly. This is the set that keeps the
> suite honest, because it is drawn from the distribution that actually exists rather
> than the one you imagined.
>
> The last 10% are regression cases: **every production incident becomes a case.**
> That rule is what makes the suite worth more each year rather than less.

### Q4.4 — LLM-as-judge: when do you use it and what are its problems?

> I use it where the property is genuinely subjective — tone, helpfulness, whether an
> explanation is understandable to a non-clinician. I avoid it where a cheaper
> deterministic check works, which is more often than people assume.
>
> In this repo, groundedness is checked by looking for asserted facts in the tool
> observations. That is a string check. It is cheaper, faster, deterministic, and — the
> part that matters — *explainable*: it names the unsupported claim. An LLM judge would
> give a score and a paragraph.
>
> The problems with judges are real: they are biased toward verbose and confident
> answers, they are non-deterministic so your gate becomes noisy, they cost money on
> every eval run, and they drift when the judge model is updated underneath you. If I
> use one, I pin the judge model version, calibrate it against human labels on a
> sample, and re-calibrate whenever the model changes. An uncalibrated judge is a
> number that feels like measurement.

### Q4.5 — How do you version and roll back a prompt?

> A prompt is a deployable artefact with an id, a semantic version, an owner and an
> eval suite — `app/agents/prompts.py` in this repo. Every turn records which version
> produced it, which is the property that matters: when quality moves, you can
> attribute it to a prompt change the same way you attribute a latency regression to a
> deploy.
>
> Promotion goes through the same PR and eval gate as code. Rollback is redeploying
> the previous version, which for a config-mounted prompt is a revision restart.
>
> The mistake I would guard against is prompts living in a database that someone edits
> in a UI. It feels faster for about three weeks, and then you have production
> behaviour with no diff, no review and no rollback.

### Q4.6 — How do you handle model deprecation?

> This is the LLMOps problem people underestimate. Providers deprecate models on their
> timeline, not yours.
>
> The structural answer is the abstraction: tenants call `carecopilot-balanced`, not
> `gpt-4o-2024-11-20`. When a version is deprecated, I add the new deployment to the
> gateway with the same public name, shadow-run the eval suite against both, compare
> per-case scores and cost, then shift traffic gradually. Tenants change nothing.
>
> The operational answer is a calendar: every deployment in `infra/terraform/modules/
> data` has a model version pinned in code, so "which models are we on and when do
> they die" is a grep, not an archaeology project.
>
> The uncomfortable answer is that behaviour *does* change between model versions even
> when quality improves on average — a prompt tuned for one model can be worse on its
> successor. That is exactly what the eval suite is for, and it is why the suite has
> to be per-tenant rather than one platform-wide set.

### Q4.7 — What is prompt caching and when does it help?

> Two different things, worth separating because people conflate them.
>
> **Provider prompt caching** caches the *prefix* of a prompt at the provider, so a
> long system prompt or a large retrieved context is not re-processed on every call.
> It cuts input-token cost substantially and reduces latency. It helps most when you
> have a long, stable prefix — which agents do, because the system prompt and tool
> definitions repeat on every step of the loop.
>
> **Semantic caching at the gateway** caches whole *responses* for
> near-duplicate questions. In customer support this is significant: "where is my
> order", "order status?", "has it shipped" are the same question. 25-35% hit rates
> are ordinary.
>
> The risk with semantic caching is a threshold set too loose returning a confidently
> wrong cached answer to a subtly different question. In `gateway/litellm/config.yaml`
> it is at 0.93, and I would tune it with a regression test attached, never by feel.

### Q4.8 — What is drift for an LLM system, and how do you detect it?

> Three kinds, and only one of them is the model's fault.
>
> **Input drift** — customers start asking about something new. Detected by clustering
> incoming turns and watching for a growing cluster with a low task-success rate.
>
> **Model drift** — the provider updates a model behind an endpoint. Detected by
> running the eval suite on a schedule, not only on PRs, and alerting on a score move
> with no corresponding deploy. That last clause is the tell.
>
> **Retrieval drift** — the index gets stale or its distribution shifts. Detected by
> tracking retrieval hit rate and the groundedness score together; groundedness
> falling while task success holds usually means retrieval, not the model.
>
> The platform capability is having all three on one dashboard next to the deploy
> markers, because the first question in every quality incident is "did we change
> something, or did something change under us?"

---

## 5. MLOps

> *JD: "…MLOps…"*

### Q5.1 — Where does classic MLOps still apply on an agentic platform?

> More than people expect, in three places.
>
> **The retrieval pipeline** is a classic ML system: embedding model versions, index
> builds, chunking strategies, retrieval quality metrics. It needs versioned datasets,
> reproducible builds and offline evaluation exactly like a model does. When a RAG
> answer is wrong, it is usually retrieval, and retrieval is MLOps.
>
> **The classifier models** around the agent — the complexity router, intent
> classification, a PII detector. These are small supervised models with training data,
> validation sets and drift monitoring.
>
> **Feature and data pipelines** feeding the tools. If a tool calls a risk score, that
> score is a model with a lifecycle.
>
> So the platform needs a model registry, dataset versioning and lineage even though
> nobody is training a foundation model. The shape is: Azure ML or MLflow for the
> registry, versioned datasets in Storage, and the same eval-gate discipline applied
> to index builds as to prompt changes.

### Q5.2 — Would you use Azure ML here?

> For the classic-ML parts, yes: registry, experiment tracking, dataset versioning and
> scheduled retraining of the small classifiers. That is what it is good at.
>
> For serving the agents, no — Container Apps is a better fit, and putting an agent
> behind an Azure ML endpoint adds a layer that buys nothing here.
>
> The general principle: use the ML platform for the ML lifecycle, use the app platform
> for the app. Teams that try to run everything through one of them end up fighting it.

### Q5.3 — How do you version a RAG index?

> The index is a build artefact and gets treated like one: a version number, an
> immutable snapshot, and a record of exactly what went into it — source document
> versions, chunking parameters, embedding model version.
>
> That matters for a reason specific to regulated work. If a customer complains about
> an answer given in March, you need to reproduce what the system knew in March. An
> index that has been continuously updated in place cannot do that. So: build a new
> index version, run the eval suite against it, swap the alias, keep the old one for
> the retention period.
>
> In this repo the tool returns `"index": "policies-v12"` and the interaction check
> returns `"dataset": "ABDA-DB snapshot 2026-07-01"` for exactly this reason — the
> answer carries the provenance of the data behind it.

---

## 6. AI gateway administration / LiteLLM

> *JD: "…AI gateway administration…" and "comfortable discussing… LiteLLM or AI
> gateways"*

### ★ Q6.1 — Why do you need an AI gateway at all? Teams could just call Azure OpenAI.

> They could, and here is what you have six months later: provider keys in four repos,
> an invoice nobody can attribute, one team's traffic spike rate-limiting everyone
> else, four different retry policies, no way to revoke access for a team without a
> code change, no central record of what was asked, and a regional outage taking down
> every AI feature at once.
>
> None of those is hypothetical; they are the standard shape of AI sprawl.
>
> The gateway turns N problems into one. It is the only thing that makes every other
> platform guarantee **enforceable rather than advisory** — budgets, entitlement,
> failover, caching, cost attribution and audit are all enforced at a single point
> that no tenant can bypass, because the tenant has no other route to a model. In this
> repo the agents' subnet denies internet egress and the agents hold no provider key,
> so bypassing is not a policy, it is a network property.

### ★ Q6.2 — What exactly do you administer on a LiteLLM gateway?

> Six things, and they map to six product conversations.
>
> **The model catalogue** — which deployments exist, their public names, regions,
> costs, context windows. Adding a model is a PR against `config.yaml`.
>
> **Virtual keys and teams** — one key per tenant, carrying entitlement, rpm/tpm
> limits, a daily budget, a cost centre and an owning Entra group. This is the unit of
> governance: onboarding is issuing one, offboarding is revoking one.
>
> **Routing and failover** — the strategy (latency-based here), the fallback chains,
> the cooldown behaviour, and the context-window and content-policy fallbacks that
> most people forget exist.
>
> **Budgets and alerting** — per key, per team, platform-wide, plus the thresholds
> that notify before they enforce.
>
> **Caching** — type, TTL and similarity threshold, tuned against a regression test.
>
> **Callbacks and guardrails** — where the telemetry goes and which content filters
> run pre- and post-call. One line of config gives every tenant observability and PII
> masking for free.

### Q6.3 — Walk me through your routing strategy.

> Three ordered stages, deliberately boring so it is auditable. It is in
> `app/gateway/catalog.py:resolve_model` and mirrored in the LiteLLM config.
>
> **1. Entitlement.** Is this key allowed this model? A governance question, so it goes
> first — no performance consideration should be able to override it.
>
> **2. Complexity tiering.** A cheap classifier scores the turn trivial, standard or
> complex, and the router picks the cheapest tier that can do the job. A greeting on
> the mini tier is roughly sixteen times cheaper per token than on the flagship. The
> classifier itself costs about $0.0001 and pays for itself immediately.
>
> **3. Health.** If the chosen deployment is cooling down, fail over: same model in a
> second EU region first, then a different provider. Region before provider, because a
> provider switch changes behaviour and behaviour changes need an eval run.
>
> And crucially the router returns *why*. The playground renders that reason chain.
> A routing decision you cannot explain is a routing decision you cannot debug or
> defend in a cost review.

### Q6.4 — How do you enforce budgets without breaking a customer conversation?

> Layered, so that the enforcement point is as far from the customer as possible.
>
> The **gateway** holds the hard cap: per key, per team, per platform, enforced
> pre-call. When it is hit, calls are refused. That protects the company.
>
> The **application** mirrors it with a per-request and per-session ceiling, so a
> runaway loop stops itself before the gateway has to — and stops with a graceful
> handover rather than an error. That protects the customer.
>
> **Alerting** fires long before either: forecast-based budget alerts at 75% and 90%,
> plus a burn-rate alert if the hourly rate projects past the daily cap.
>
> The product decision embedded in that design is: when the budget is gone, the agent
> degrades to a human handover rather than to an error page. That is a deliberate
> choice about who absorbs the failure, and it is the kind of thing a PM should be
> making rather than inheriting.

### Q6.5 — Build versus buy: LiteLLM, Azure API Management, Portkey, or your own?

> **LiteLLM** for this shape of problem. It is open source so there is no vendor lock
> on the most load-bearing component in the platform, it is genuinely multi-provider,
> it has the virtual-key, budget and spend-tracking model built in, and it self-hosts
> inside our VNet — which for health data is not a preference, it is a requirement.
>
> **Azure API Management** is excellent at API management and does not know what a
> token is. You would rebuild spend tracking, semantic caching and model failover on
> top of it. Some organisations run both: APIM at the edge for the enterprise API
> policies, LiteLLM behind it for the AI-specific concerns. That is defensible.
>
> **Portkey and similar SaaS** are good products, but routing every customer health
> question through a third party adds a sub-processor, a DPA and a data-residency
> conversation for capability we can self-host.
>
> **Building our own** — no. It looks like a week of work and it is a permanent team.
> The reason to build is if the differentiator is in the gateway itself, and it is not;
> ours is in the agents.
>
> The thing I would watch: LiteLLM is on the critical path of everything, so I would
> want the operational story sharp — pinned versions, an upgrade rehearsal, and
> minimum three replicas across zones. In `platform/policies` there is a rule that
> fails the build if anyone sets its min replicas to zero.

### Q6.6 — How do you stop one team's traffic from affecting another's?

> Rate limits per virtual key, at the gateway — rpm and tpm both, because a small
> number of very large requests can saturate a deployment without hitting a request
> limit.
>
> Beyond that, separate deployments for the tiers that matter, so a batch workload and
> an interactive customer workload are not competing for the same quota. And Azure
> OpenAI quota is per-region, so the second region gives isolation as well as
> failover.
>
> The scenario I would design for explicitly: a nightly batch job that suddenly runs
> at 10× volume. Rate limits contain it, the queue-depth scale rule absorbs it, and
> the budget alert tells someone before the daily cap does.

### Q6.7 — A tenant says the gateway is adding latency. What do you do?

> Measure before arguing. The gateway's own overhead should be single-digit
> milliseconds; if a tenant is seeing more, the causes in order of likelihood are: a
> cold replica (min replicas too low), a cross-region fallback firing silently, the
> semantic cache doing an embedding call on every miss, or the tenant comparing
> gateway p95 against provider p50.
>
> The trace answers it. Each turn's `llm.call` span carries the gateway latency and
> the selected deployment, so "the gateway is slow" becomes "the gateway failed over
> to West Europe eleven times this morning" — which is a completely different
> conversation and usually a genuine finding.
>
> The broader point: a platform team that cannot instrument its own overhead will lose
> every one of these arguments regardless of who is right.

---

## 7. Observability

> *JD: "…observability…" and "observability tooling"*

### ★ Q7.1 — What do you monitor for an agentic system that you would not for a normal service?

> A normal service is healthy if it is fast and returns 200. An agent can be fast,
> return 200, and still be wrong, ungrounded, unaffordable or stuck in a loop. So on
> top of RED I add three families.
>
> **Agent behaviour** — steps per turn, tool calls and their error rates, and *why the
> loop stopped*. That last one is the most useful single metric I have: a rise in
> `max_steps_reached` means the agent can no longer close conversations out, and it
> shows up before customer complaints do.
>
> **Quality** — groundedness rate, guardrail firings by check, escalation rate, and
> eval scores on the deployed revision.
>
> **FinOps** — cost per turn, spend by tenant and model, cache hit rate, budget
> headroom.
>
> The one I would fight hardest to keep is groundedness, because it is the only metric
> that catches the failure everyone is actually afraid of.

### Q7.2 — What does a trace look like for an agent turn?

> One root span per turn, with children for classification, routing, the budget check,
> the input guardrails, each planner step, each LLM call, each tool call, and the
> output guardrails. Attributes carry the model, tokens, cost, cache status, tool
> arguments and status, and the guardrail verdicts. `app/observability/telemetry.py`
> builds it and the playground renders it.
>
> The design decision worth explaining: the trace is a **product surface**, not just a
> debugging tool. It is what an engineer debugs with, what an auditor reads, what an
> eval replays, and what a PM uses to explain a cost spike. That is why the shape is
> owned rather than left to whatever a vendor SDK emits — the exporter can change, the
> shape should not.

### Q7.3 — How do you handle sensitive data in traces?

> Redact at the collector, not in the application. Prompts and completions can contain
> health data, and a trace backend is not an approved store for it.
>
> The collector config in `observability/otel/collector-config.yaml` deletes
> `llm.prompt`, `llm.completion` and request bodies, and hashes user ids. Doing it
> there rather than in each service means the guarantee holds for every service that
> ever exports through it, including the ones written by a team that did not read the
> guidance.
>
> Where the full content genuinely is needed — a complaint investigation — it lives in
> the encrypted transcript store in Postgres with access logged and time-boxed, not in
> the trace backend.

### Q7.4 — Sampling: how much and how do you choose?

> Tail sampling, not head sampling, and the policy is: keep everything interesting,
> sample the boring.
>
> Keep 100% of errors, 100% of turns over 4 seconds, 100% of turns where a guardrail
> fired, 100% of escalations. Sample 20% of ordinary successes.
>
> Tail sampling can do that because it decides after seeing the finished trace. A head
> sampler has to guess before the request runs, which means it drops exactly the
> traces you will want an hour later. The cost is the collector buffering traces for a
> decision window, which is a memory-sizing problem, not a design problem.

### ★ Q7.5 — How do you set SLOs for a system whose output is non-deterministic?

> Separate the deterministic parts from the probabilistic ones and set different kinds
> of objective for each.
>
> Availability and latency are ordinary SLOs: 99.9% on the gateway, p95 under 4
> seconds on a turn. Those behave like any service.
>
> Quality is a *rate* objective, not a per-request guarantee: at least 97% of turns
> fully grounded over a 7-day window. You cannot promise any individual answer is
> right — that is the nature of the technology, and pretending otherwise is how
> platforms lose credibility. You can promise a rate, measure it, and put an error
> budget behind it.
>
> Guardrail coverage is the one hard objective: 100% of turns pass both pipelines,
> error budget zero. That is achievable because it is a property of the code path, not
> of the model.
>
> Each has a multi-window burn-rate alert — 14.4× over an hour pages, 6× over six
> hours tickets. A single threshold catches an outage and misses a slow leak.

### Q7.6 — Something is wrong in production. Walk me through the first ten minutes.

> **Minute 0-2, orient.** Which SLO is burning, and did we deploy? The Grafana overview
> has deploy markers on it precisely so the second question is answered without asking
> anyone. If a deploy correlates, shift the traffic weight back to the stable revision
> — that is seconds, and you can investigate calmly afterwards.
>
> **Minute 2-5, localise.** Is it the gateway, a tool, or the agent? The panels are
> arranged to answer that in order: gateway error rate, then tool latency and error
> rate by tool, then loop terminations. A slow system of record shows up as tool p95
> before it shows up as turn p95.
>
> **Minute 5-10, find an example.** Pull one failing trace. Because every error trace
> is kept, there is always one. The span attributes usually make the cause obvious —
> a tool returning an unexpected shape, a fallback firing repeatedly, a guardrail
> blocking legitimate traffic after a pattern change.
>
> The discipline I would hold the team to: **mitigate first, diagnose second.** Rolling
> back a traffic weight costs nothing and buys unlimited time.

### Q7.7 — Grafana, Azure Monitor, Prometheus, App Insights — why all of them?

> They are not alternatives, they are layers, and the collector is what keeps that
> from becoming a mess.
>
> **App Insights and Log Analytics** are the Azure-native sink — distributed tracing,
> log queries, and the long-retention audit table. This is where compliance evidence
> lives, and it is where a KQL query can join a trace to a cost to an escalation.
>
> **Prometheus** holds the high-cardinality operational metrics the four families need,
> cheaply.
>
> **Managed Grafana** is the pane of glass over both, provisioned from Git.
>
> The application knows about none of them. It speaks OTLP to the collector, and where
> the telemetry goes is an operations decision made in a config file. That seam is
> what makes "we are moving to a different backend" a redeploy rather than a project.

---

## 8. Governance and secure AI enablement

> *JD: "…governance, and secure AI enablement"*

### ★ Q8.1 — How does the EU AI Act affect what you build?

> It changes the design, not just the paperwork, and it starts with classification.
>
> CareCopilot is **limited-risk**: a customer-facing informational assistant, not a
> medical device and not diagnostic, because every clinical judgement is routed to a
> registered pharmacist. That classification is a decision made on the record, and the
> architecture enforces it — the moment the agent could give a dose, it would be a
> different tier with a conformity assessment attached.
>
> Four obligations map to four code paths, and I would insist on that mapping because
> a control that only exists in a document drifts:
>
> | Article | Obligation | Code path |
> |---|---|---|
> | Art. 50 | Transparency | Every reply carries an AI disclosure — `ensure_disclaimer` |
> | Art. 12 | Record-keeping | Append-only audit table, 7-year retention |
> | Art. 14 | Human oversight | Approval gate on every side-effecting tool |
> | Art. 15 | Accuracy, robustness | Groundedness scorer + CI gate at 0.95 |
>
> `/platform/governance` serves that as live data, so an auditor reads the running
> system rather than a document that was true in March.

### Q8.2 — How do you handle GDPR for health data in an AI system?

> Five decisions, all made before the first line of agent code.
>
> **Lawful basis.** Art. 6(1)(b) contract, and Art. 9(2)(h) for the health data —
> processing for pharmacy care. Getting this wrong is not fixable later.
>
> **Residency.** EU only. Enforced twice: a Terraform variable validation rejects a
> non-EU region, and an OPA policy fails the plan. Belt and braces, because a region
> typo is a reportable breach rather than a lint warning.
>
> **Minimisation.** Direct identifiers are redacted before the prompt leaves the VNet.
> The agent does not need an IBAN to answer an order question.
>
> **Retention.** Split deliberately: transcripts 90 days because that is what serves
> the customer-service purpose; audit records for years because pharmacy
> record-keeping and the AI Act require it. One retention number for everything either
> breaches the law or bankrupts you.
>
> **Sub-processors.** Every model provider is one. That is a DPA, a residency
> commitment and an entry in the record of processing — which is a real argument
> against a SaaS gateway and for self-hosting LiteLLM.

### ★ Q8.3 — What are the security risks specific to agentic AI?

> Five that a normal application security review will not catch.
>
> **Prompt injection.** An attacker rewrites the agent's instructions through text the
> agent reads. Mitigated by an input guardrail, by treating tool output as data rather
> than instruction, and structurally by least privilege — an agent that cannot do
> something cannot be tricked into doing it.
>
> **Indirect injection** is the harder cousin: the malicious text arrives inside a
> *tool result* — a product review, an order note, a retrieved document. This is why
> the system prompt says explicitly that tool content is data, and why the guardrail
> runs over content before it is used.
>
> **Excessive agency.** The agent can do more than the task needs. Mitigated by tool
> scopes on the virtual key, so the agent is not even *told about* tools it may not
> use, and by the approval gate on anything with a side effect.
>
> **Data exfiltration through the model.** A prompt that persuades the agent to
> summarise data into a response, or to call a tool with an attacker-controlled URL.
> Mitigated by output guardrails, PII egress checks and — the strongest control — an
> NSG that denies internet egress from the agent subnet.
>
> **Supply chain.** A poisoned dependency in an agent framework. Mitigated by SBOM,
> Trivy, cosign signing and ACR content trust: an unsigned image cannot run.
>
> The mental model I would give the team: **an agent is a confused deputy with a
> credential**. Design for the day it is fully persuaded.

### Q8.4 — How do you manage secrets?

> The goal is that there is no long-lived secret anywhere in the chain, and it is
> achievable.
>
> **CI to Azure**: OIDC federation. GitHub mints a short-lived token; Entra ID checks
> the subject matches an exact federated credential — a different branch, environment
> or fork does not match. No client secret exists to leak.
>
> **App to Azure**: user-assigned managed identity. The app holds nothing.
>
> **App to provider**: the app holds a *virtual key*, not a provider key. Revocable,
> budgeted, scoped, rotatable without redeploying the tenant. Only the gateway's
> identity can read the actual provider keys — two identities, so "the agent was
> compromised" and "the provider keys were compromised" stay different sentences.
>
> **Key Vault**: RBAC not access policies, purge protection on, private endpoint only,
> 90-day rotation. Secret *values* never enter Terraform — the module creates the slot
> and ignores the value, so state and plan output contain resource ids, not
> credentials. There is an OPA rule that fails the build if anyone puts a literal
> secret in a `key_vault_secret` resource.

### Q8.5 — What is human-in-the-loop and where do you put it?

> A required human decision before an irreversible action, and the placement question
> is the whole design.
>
> Too early and the agent is a very expensive form filler; too late and you are
> reviewing damage. My rule: **gate the side effect, not the reasoning.** The agent may
> read anything it is entitled to, reason freely, and draft the action — but anything
> that changes a system of record stops for a human.
>
> In this repo that is expressed in the tool registry: `side_effect: True` requires
> `requires_approval: True`, and there is a policy test that fails the build if a tool
> declares one without the other. `escalate_to_pharmacist` is the only such tool, and
> the API test proves the ticket genuinely does not exist until someone approves it.
>
> Three properties make it real rather than theatre: the reviewer sees the full context
> and reasoning, not just a yes/no prompt; the decision is recorded with who and when;
> and the reviewer has a genuine option to say no. A rubber-stamp queue where a human
> approves four hundred items an hour satisfies Art. 14 on paper and nothing in
> practice.

### Q8.6 — How do you build an AI governance process that engineering does not hate?

> By making the governed path the default and the fast one, and by putting the
> checkpoint where it costs least.
>
> Most governance is hated because it arrives at the end — a review board two weeks
> before launch, asking questions that should have been answered at design time. The
> fix is to move it left and make most of it automatic: the eval gate, the policy
> checks, the required tags, the tool metadata. By the time a human reviews, the
> mechanical questions are already answered.
>
> Then keep the human review small and fast: one platform review for a new agent, with
> a one-day SLA, covering the three things a machine cannot check — the risk tier and
> the reasoning behind it, the tool blast radius, and the escalation path.
>
> The measure of whether you got it right is whether teams bring you their edge cases
> voluntarily. If they hide them until launch, the process is adversarial and you have
> already lost.

### Q8.7 — A customer complains that the agent gave them wrong information. What happens?

> This is a good question because it tests whether the observability is real.
>
> **Retrieve.** The trace id from the conversation gives the full turn: the prompt
> version, the model and region, every tool call with its arguments and response, the
> guardrail verdicts, and the exact answer. Retained for the statutory period in the
> audit table.
>
> **Classify.** Was the answer ungrounded (the agent invented it), or grounded in
> wrong data (a tool returned something incorrect)? Those have completely different
> owners and fixes, and the groundedness verdict on the turn distinguishes them
> immediately.
>
> **Contain.** If it is systemic — a prompt regression, a bad index build — roll back
> the revision or the index version first.
>
> **Fix and prove.** The case goes into the golden set as a regression test. That is
> the rule that makes the suite worth more every year: **every incident becomes a
> case.**
>
> **Report.** For health data and an AI Act system, there is a documented record of
> what happened, when, and what was changed. That record exists because the audit log
> was designed in, not because someone reconstructed it afterwards.

---

## 9. Azure Cloud

> *JD: "Azure Cloud"*

### ★ Q9.1 — Why Container Apps rather than AKS?

> Because a platform team of a handful of people should be maintaining golden paths,
> not a Kubernetes control plane.
>
> Container Apps gives revisions, traffic splitting, KEDA autoscaling, managed
> identity, VNet injection, scale-to-zero and Dapr if you want it — all the primitives
> this platform actually uses. AKS gives more control at the price of a permanent
> operational commitment: upgrades, node pools, ingress controllers, cert management,
> a service mesh someone will inevitably want.
>
> I would move to AKS when there is a concrete driver: GPU workloads we self-host, a
> service mesh requirement, or a scale where the Container Apps abstraction is costing
> more than it saves. Not before.
>
> The exit stays cheap because the unit of deployment is a plain OCI image and
> everything around it is Terraform. That is the property that makes the decision
> reversible, and reversibility is what makes it a comfortable decision to make early.

### Q9.2 — Design the Azure network for this platform.

> One VNet per environment, with three subnets and a hard rule.
>
> `snet-apps` — delegated to Container Apps, /23 minimum because the platform needs
> the space. `snet-private-endpoints` — every PaaS dependency lands here as a NIC.
> `snet-data` — delegated to Postgres Flexible Server.
>
> The rule: **no public ingress into the AI plane, and no unmonitored egress out of
> it.** Ingress comes through Front Door with a WAF. Egress is denied to the internet
> at the NSG and allowed only to the `AzureCloud` service tag — so a compromised agent
> cannot post a customer record to an arbitrary host.
>
> The part people miss is **private DNS zones**. A private endpoint without its zone
> still resolves to the public IP, and the traffic quietly leaves the VNet. The network
> module creates eight of them — Key Vault, OpenAI, Postgres, Redis, Search, Blob, ACR,
> Monitor — and links them to the VNet. That is the single most common Azure
> private-networking mistake and it is silent when you make it.

### Q9.3 — How do you handle Azure OpenAI quota?

> Quota is the constraint people discover in week three, so it needs planning.
>
> It is allocated per subscription, per region, per model, in tokens per minute. Two
> regions is therefore two quota pools as well as failover — that is half the argument
> for the second region.
>
> I would provision capacity in Terraform, as I do here, so a capacity increase is a
> reviewed pull request with a cost consequence attached rather than a slider someone
> moved on a Friday. I would use Global Standard for the interactive tiers, consider
> Provisioned Throughput Units only once traffic is predictable enough that the
> committed cost beats the pay-as-you-go bill, and keep a headroom alert at 70% of TPM
> so we ask for more before we need it, because quota increases take days.
>
> The gateway's rate limits are set below the deployment quota deliberately, so a
> tenant hits *our* limit with a clear message rather than the provider's 429.

### Q9.4 — What Azure services would you use for the data/AI layer, and why each?

> **Azure OpenAI** for the models — EU residency, private endpoints, enterprise
> agreement, and it is where the quota conversation happens.
>
> **Azure AI Search** for retrieval. Hybrid search with a semantic ranker, integrated
> vectorisation, and it sits inside the same security perimeter as everything else. I
> would need a strong reason to add a separate vector database, and "it benchmarks
> better on a synthetic dataset" is not one.
>
> **Azure Storage** for source documents, eval datasets and archived traces. Versioned
> containers, no public access, no shared keys.
>
> **PostgreSQL Flexible Server** for the gateway's spend log, session transcripts,
> approvals and eval history. It is the financial and evidential record, so it gets
> point-in-time restore and, in production, zone-redundant HA.
>
> **Azure Cache for Redis** for the semantic cache and hot session state. Premium tier
> in production, because that is what buys the private endpoint.
>
> **Azure AI Content Safety** as a provider-independent filter, so the content policy
> does not change when the model behind the endpoint does.

### Q9.5 — How do you control Azure cost on this platform?

> Four layers, from the sharpest to the bluntest.
>
> **At the gateway** — budgets per key enforced pre-call. This is the only layer that
> stops spend rather than reporting it.
>
> **In the architecture** — tiered routing, semantic caching, a bounded context window,
> scale-to-zero in dev. The routing and caching levers together are typically worth
> more than any negotiation.
>
> **In Azure Cost Management** — budgets per resource group with forecast alerts at
> 75% and 90%, and tag-based chargeback. Every taggable resource carries a cost centre,
> enforced by an OPA rule, because untagged spend is unattributable spend.
>
> **In the review cadence** — a monthly look at cost per resolved conversation by
> tenant. The unit-economics number, not the total, because the total going up is fine
> if the unit cost is going down.

### Q9.6 — What is your disaster recovery story?

> Layered by what actually fails.
>
> **A model deployment fails** — the gateway fails over to the second region, then the
> second provider. Seconds, automatic, and visible in the trace.
>
> **A region fails** — the data plane is already dual-region; the compute would need
> the Container Apps environment stood up in the second region. That is Terraform, so
> it is minutes of apply rather than a project, but I would rehearse it rather than
> assume it.
>
> **Data loss** — Postgres point-in-time restore with 35-day retention and geo-backup
> in production; Storage with versioning and soft delete; Key Vault with purge
> protection.
>
> **A bad deploy** — traffic weight back to the stable revision. Seconds.
>
> **Total platform loss** — Terraform plus state rebuilds the estate. This is the one I
> would actually test, in a game day, because untested DR is a document rather than a
> capability. The honest statement of maturity here is: dual-region for the AI plane
> is designed and coded; a full regional failover of compute is designed and *not yet
> rehearsed*, and I would put that rehearsal in the first quarter.

---

## 10. Terraform and Infrastructure as Code

> *JD: "Terraform" and "Infrastructure as Code"*

### ★ Q10.1 — Why does everything have to be in Terraform?

> Because of two questions you cannot answer otherwise, and both of them get asked
> during an incident.
>
> *What changed?* If everything is code, it is a Git diff with an author and a
> reviewer. If some of it was clicked in the portal, it is an archaeology project.
>
> *Is staging the same as production?* If they are the same modules with different
> variables, yes by construction. If they are separately maintained, "it worked in
> staging" means nothing.
>
> There is a third benefit that matters more for governance than people expect: the
> plan is a **review artefact**. A reviewer approving an infrastructure PR should be
> approving a diff of resources, not a diff of HCL — those are genuinely different
> things, and the gap between them is where production surprises live. That is why
> `terraform-plan.yml` posts the readable plan as a comment and the reviewed plan file
> is the one that gets applied.

### Q10.2 — How do you structure a Terraform repository?

> Modules for capability, environments for composition, and a hard rule that
> environments contain no resources of their own beyond a resource group.
>
> Eight modules here — network, identity, security, data, runtime, gateway, compute,
> observability — each with a single clear ownership boundary. Two environments that
> are the same modules with different numbers.
>
> Two specifics worth explaining. **`runtime/` exists because of a real dependency
> cycle**: the gateway needs a registry to pull from and the agents need the gateway's
> URL, so putting the registry in `compute` and the environment in `gateway` makes them
> mutually dependent and Terraform refuses to build a graph. The fix was not a
> workaround but the correct decomposition — the compute *fabric* is shared
> infrastructure both sit on, and ownership follows the same line.
>
> And **`compute/` takes agents as a map**, so onboarding the tenth team is a map entry
> rather than a new pipeline. That is the actual test of whether something is a
> platform.

### Q10.3 — How do you manage Terraform state safely?

> Remote backend in Azure Storage with blob leasing for locking, one container per
> environment, versioning and soft delete on, private-endpoint only, and readable by
> the deployment identity alone.
>
> State holds resource ids and sometimes secret material, so it is treated as sensitive
> — which is also why secret *values* never enter it in the first place.
>
> Bootstrapping is the chicken-and-egg: the state backend cannot be managed by the
> state it stores, so it is created once by a documented script and then left alone.
>
> The failure mode I would guard against hardest is a shared state file across
> environments. One lock, one blast radius, and a dev apply that can break production.

### Q10.4 — What goes wrong with Terraform in practice?

> Five things, and four of them are process rather than tooling.
>
> **Drift** — someone changes a resource in the portal during an incident and never
> tells anyone. Solved by a nightly plan that opens an issue when it is non-empty.
> Note the framing: drift is not automatically bad, it is *unexplained*, and the issue
> is the explanation prompt.
>
> **Long applies and lock contention** — solved by splitting state per environment and
> keeping modules independent enough to apply separately.
>
> **Provider upgrades** — pinned with `~>`, upgraded deliberately with a plan diff
> reviewed, never floating.
>
> **Resources Terraform does not fully own** — a Container App image tag updated by
> CD, for instance. Handled with `ignore_changes` so CD and Terraform stop fighting.
> Getting this wrong produces a permanent phantom diff that teaches everyone to ignore
> plan output, which is much worse than the original problem.
>
> **Secrets in state** — solved by creating the slot and setting the value out of band,
> plus a policy rule that fails the build on a literal.

### Q10.5 — How do you test infrastructure code?

> Four layers, cheapest first.
>
> `terraform fmt` and `validate` — syntax and schema. Seconds.
>
> **Static policy** — Checkov and tfsec for the generic CIS-style findings, plus OPA
> policies for the rules only we know: EU-only regions, no public network access, the
> gateway never scaling to zero, required cost-centre tags. Run against the *plan
> JSON*, not the source, because HCL can look compliant while a variable default
> produces a public storage account.
>
> **A module graph check** — `scripts/tf-graph-check.py` here, which catches dependency
> cycles and mis-wired module inputs without needing a provider download. That is what
> caught the gateway/compute cycle in this repo.
>
> **Plan review** — a human reading the resource diff. Still the most valuable layer,
> which is why the pipeline exists to make it easy rather than to replace it.
>
> Beyond that there is `terraform test` and Terratest for module-level assertions. I
> would use them for the modules that encode real policy — the network module's DNS
> zones, for instance — rather than for everything, because infrastructure tests are
> slow and a slow suite gets skipped.

### Q10.6 — Terraform, Bicep or Pulumi?

> **Terraform**, for three reasons and one caveat.
>
> Multi-provider: we need Azure *and* Azure AD *and*, realistically, GitHub, Grafana
> and Datadog-shaped providers. Bicep is Azure-only, which is fine until the day it is
> not.
>
> Ecosystem and hiring: the module registry, Checkov, tfsec, Conftest and Infracost
> all assume Terraform, and engineers arrive knowing it.
>
> State as an explicit artefact: Bicep's declarative-diff model is elegant but Terraform
> state makes drift detection and import straightforward.
>
> The caveat is licensing — Terraform moved to BUSL, which is why OpenTofu exists. For
> our usage the licence is not a problem, but I would want that noted as a watch item
> rather than discovered later.
>
> Pulumi is genuinely good if your team would rather write TypeScript. My reservation
> is that a general-purpose language invites general-purpose complexity in
> infrastructure code, and infrastructure code benefits from being boring.

---

## 11. GitHub and CI/CD with GitHub Actions

> *JD: "GitHub, CI/CD with GitHub Actions"*

### ★ Q11.1 — Walk me through your pipeline.

> Four workflows, and the ordering inside each is chosen so the cheapest signal fails
> first.
>
> **CI on every PR** — lint, then tests, then the eval gate, then Terraform validate
> and policy, then security scanning, then a single `gate` job that all of them feed
> into. Branch protection points at that one job, so adding a new check later does not
> mean editing repository settings, and a skipped job cannot silently count as a pass.
>
> **Terraform plan on PR** — plans dev and prod, runs Conftest against the plan JSON,
> optionally an Infracost diff, and posts the readable plan as a comment that updates
> in place rather than appending.
>
> **Terraform apply on merge** — dev automatically, prod behind a GitHub Environment
> protection rule with two approvers. Nightly drift detection opens an issue when the
> plan is non-empty.
>
> **CD** — build, SBOM, Trivy, cosign sign, deploy to dev, smoke test, run the eval
> suite against the *live* service, then a production canary at 10%, a 15-minute bake
> against the SLOs, and promote or roll back.
>
> The unusual job is the eval gate, and it is the one that matters most: for a
> non-deterministic system, unit tests prove the plumbing and evals prove the
> behaviour.

### Q11.2 — Why OIDC instead of a service principal secret?

> Because the best way to protect a credential is for it not to exist.
>
> A service principal secret is a long-lived password sitting in GitHub secrets. It
> leaks in a log, it gets shared to unblock someone, it expires at the worst moment,
> and rotating it is a task nobody owns.
>
> With OIDC federation, GitHub mints a short-lived token for the specific workflow run
> and Entra ID checks that its subject matches an exact federated credential — a
> different branch, a different environment or a fork does not match and is rejected
> before any Azure call happens. Nothing to leak, nothing to rotate, and the trust is
> scoped to a named context rather than to a string.
>
> The subject-matching precision is the part worth stressing in a review: getting it
> wrong by using a wildcard is how a fork gets production access.

### Q11.3 — How do you do progressive delivery?

> Container Apps revisions with traffic weights.
>
> CD deploys the new revision at 10%, bakes for fifteen minutes watching error rate,
> p95 latency and the online eval score, then promotes to 100%. If anything fails, the
> weight goes back to the stable revision.
>
> Two properties make it worth doing. **Rollback is a weight change** — seconds, no
> rebuild. A rollback that requires a rebuild is not a rollback, it is a hope. And
> **bake time is not superstition**: most regressions that unit tests and evals miss
> are load-dependent, and they need real traffic to appear.
>
> The judgement call is the bake window. Too short and you promote a regression; too
> long and every release takes a day and people start batching changes, which is worse.
> Fifteen minutes at Redcare's volume gives a usable signal on the SLOs; I would tune
> it from the data rather than defend the number.

### Q11.4 — How do you keep CI fast?

> Order by cost, cache aggressively, and be honest about what has to be blocking.
>
> Ordering: lint is 20 seconds and catches the most common failure. There is no reason
> for a formatting error to cost a full eval run.
>
> Caching: pip cache keyed on the lockfile, Docker layer cache in the registry rather
> than on the runner, and `concurrency` with `cancel-in-progress` so a new push
> supersedes the old run — reviewers should never be reading results from a commit
> that no longer exists.
>
> Honesty about blocking: the eval suite is 16 cases in mock mode, which is seconds. If
> it grew to 300 cases against real models, I would keep a fast subset blocking on PRs
> and run the full suite nightly and pre-release. A gate everyone waits twenty minutes
> for is a gate people start bypassing.
>
> And `LLM_MODE=mock` is what makes the whole suite hermetic: no key, no network, no
> cost, identical on a laptop and a runner. A test suite that needs a provider key is a
> test suite that will be skipped.

### Q11.5 — How do you manage GitHub as a platform, not just a repo host?

> Four things I would treat as platform surface.
>
> **Repository templates** — the golden path is a template repo, so a new agent starts
> with CI, Dockerfile, evals and the Terraform stanza already correct.
>
> **Reusable workflows** — tenant repos call a shared workflow rather than copying
> 300 lines of YAML that then drifts. When the platform improves the pipeline,
> everyone gets it.
>
> **Rulesets and branch protection as code** — required checks, required reviewers,
> signed commits, no force-push to main, applied consistently rather than
> per-repository by hand.
>
> **Environments with protection rules** — this is where production approval actually
> lives, and it is the control that makes "the pipeline is the only path to production"
> true rather than aspirational.
>
> Plus Dependabot, secret scanning with push protection, and CodeQL — all of which are
> org-level settings, not per-repo decisions.

### Q11.6 — A tenant team wants to skip the eval gate to ship a hotfix. What do you say?

> Yes, with a receipt.
>
> There is a break-glass path — an admin can bypass a required check — and pretending
> otherwise just means people find a worse route. What I care about is that using it is
> *visible and costly enough to be deliberate*: it is logged, it notifies the platform
> channel, and it creates a follow-up issue that has to be closed within 24 hours with
> the eval case that would have caught the problem.
>
> Then I would look at why it happened. If teams need break-glass regularly, the gate
> is either too slow or wrong, and that is a platform defect. One bypass is an
> incident; five bypasses is a roadmap item.

---

## 12. DevOps practices and platform engineering

> *JD: "DevOps practices, and platform engineering"*

### Q12.1 — What is the difference between DevOps and platform engineering?

> DevOps is a set of practices and a culture: the people who build it run it, small
> frequent changes, automation over ceremony, blameless learning from failure.
>
> Platform engineering is what you do when "you build it, you run it" stops scaling.
> Once you have thirty teams, each one independently solving networking, secrets, CI,
> observability and compliance is enormous duplicated effort and thirty different
> answers to every security question. The platform team builds the paved road so the
> product teams keep the autonomy without the toil.
>
> The failure mode is a platform team that becomes the old ops team with a new name —
> a ticket queue between developers and production. The test is self-service: if a
> team needs you to deploy, you have rebuilt the thing DevOps was reacting against.

### ★ Q12.2 — How do you measure the platform team's own performance?

> DORA metrics for the delivery properties, adoption metrics for whether it is
> actually a platform, and one qualitative signal.
>
> **DORA** — deployment frequency, lead time for change, change failure rate, time to
> restore. Not because they are fashionable, but because a platform whose own pipeline
> is slow will produce tenants with slow pipelines.
>
> **Adoption** — agents on the paved road, share of spend through the gateway, time to
> first token, scorecard distribution.
>
> **The qualitative one** — how much of the platform team's week goes to onboarding
> and support versus building. If onboarding the tenth team costs the same as the
> second, it is a consultancy, not a platform. That ratio is the single best early
> warning I know of.

### Q12.3 — What is your on-call and incident philosophy?

> Alert on symptoms, page only for things worth waking someone, and make the postmortem
> about the system rather than the person.
>
> Concretely: burn-rate alerts against SLOs, not CPU thresholds. Every page has a
> runbook link. Anything that can wait until morning is a ticket; anything that cannot
> be acted on is a dashboard.
>
> For a platform team specifically, on-call has to cover the gateway, because it is on
> the critical path of every AI feature. The agents themselves can be tenant-owned —
> which is the right ownership boundary, and it is only fair if the platform gives them
> the observability to hold it.
>
> On postmortems: blameless, and with an action item that is a *system* change rather
> than "be more careful". If the fix is a person being more careful, the real fix has
> not been found yet.

### Q12.4 — How do you handle technical debt on a platform?

> Budget it explicitly rather than promising to get to it. Roughly 20% of capacity,
> defended, because platform debt compounds faster than product debt — every tenant
> inherits it.
>
> I prioritise it by blast radius rather than age: debt in the gateway affects every
> team, debt in one tenant's tooling affects one. And I keep a visible register with
> the cost of *not* fixing each item stated in the same terms as feature work, because
> "we should refactor this" loses every prioritisation argument and "this will cost us
> two days per new team onboarded" wins some of them.

---

## 13. Security

> *JD: "security"*

### Q13.1 — How do you think about security for a platform, not just an application?

> The platform's job is to make the secure path the default path, so that a tenant team
> gets most of their security posture by adopting the golden path rather than by
> reading a policy.
>
> Concretely, a team on the paved road gets private networking, managed identity, no
> secrets in code, guardrails, audit logging, image signing and dependency scanning
> without writing any of it. The platform owns those controls and improves them once,
> for everyone.
>
> The corollary is that the platform must make it *hard to accidentally leave*. That is
> what the OPA policies are: a team can leave the road deliberately, but they cannot do
> it by forgetting.

### Q13.2 — Walk me through the security controls in this repo and what each defends against.

> Mapped to a threat rather than to a checklist:
>
> | Control | Threat |
> |---|---|
> | Workload identity + OIDC | Credential theft — no long-lived credential exists |
> | Two identities (agent, gateway) | Blast radius — a compromised agent cannot read provider keys |
> | Key Vault RBAC, purge protection, private endpoint | Secret exfiltration; unrecoverable deletion |
> | NSG egress deny to internet | A compromised agent posting customer data outward |
> | Private endpoints + private DNS zones | Traffic silently leaving the VNet |
> | Prompt-injection guardrail | Instruction override through customer text |
> | Tool output treated as data | Indirect injection through a retrieved document |
> | PII redaction pre-call | Health data leaving the VNet or landing in a log |
> | Output secret scan | The model repeating a credential it saw |
> | Tool scopes on the virtual key | Excessive agency — the agent is not told about tools it may not use |
> | HITL on side-effecting tools | An agent acting on a system of record alone |
> | SBOM, Trivy, cosign, content trust | Supply-chain compromise; unsigned images cannot run |
> | gitleaks over full history | A key committed and force-pushed away |
> | Conftest/Checkov on the plan | Compliant-looking HCL producing a public resource |

### Q13.3 — What is the OWASP Top 10 for LLM applications, and which ones actually worry you?

> The three I would spend real effort on here.
>
> **Prompt injection**, direct and indirect. Indirect is the one that keeps me up:
> malicious text inside a retrieved document or an order note. There is no complete
> defence, so the strategy is layered — detect, treat tool output as data, and
> constrain what the agent can do so a successful injection has nowhere to go.
>
> **Excessive agency.** The most effective mitigation is not detection, it is design:
> scopes on the key, the approval gate, and a tool surface that is as small as the job
> allows. An agent that cannot issue a refund cannot be tricked into issuing one.
>
> **Sensitive information disclosure.** Both directions — data going into the model and
> data coming back out. Redaction pre-call, a secret scan post-call, and egress denied
> at the network so exfiltration has no route.
>
> The others matter, but insecure output handling, supply chain and denial of wallet
> are largely covered by ordinary engineering discipline — output encoding, SBOM
> scanning and rate limits with budgets.

### Q13.4 — How would you run a security review of a new agent?

> Five questions, in this order, and it should take under an hour for a normal agent.
>
> 1. **What can it do?** The tool registry answers this, with systems touched, side
>    effects and data classification. If a team cannot list it, that is the finding.
> 2. **What data does it see?** Classification of inputs, retrieved content and tool
>    responses. Drives the residency and retention answers.
> 3. **What is the worst case if it is fully persuaded?** Assume the injection
>    succeeds. If the answer is "it issues refunds", the design needs to change, not
>    the guardrail.
> 4. **Who reviews the irreversible actions?** And is that queue realistic, or a
>    rubber stamp?
> 5. **How would we know?** Traces, audit records, alerts. If we could not detect the
>    worst case, it is not controlled.
>
> Most of the mechanical checks — image signing, secrets, network posture — are
> already automated in CI, which is exactly what makes it possible to keep the human
> review to five questions.

---

## 14. Data/AI platform technologies

> *JD: "Data/AI platform technologies"*

### Q14.1 — How does the data platform relate to the AI platform?

> The AI platform is a consumer of the data platform, and treating it as anything else
> creates duplication that becomes contradiction.
>
> Retrieval indexes are built from governed data products — the policy corpus, the
> product catalogue, the drug database. If the AI platform builds its own pipelines,
> you get two versions of the truth and the AI one will be the stale one.
>
> So the seam I would define is: the data platform owns ingestion, quality, lineage and
> the contract; the AI platform owns embedding, indexing, retrieval quality and
> serving. The handoff is a versioned dataset with a schema contract, which is also
> what makes an index reproducible six months later when someone complains about an
> answer.
>
> The organisational version of that: the AI platform PM and the data platform PM need
> a shared roadmap item, or the seam becomes a queue.

### Q14.2 — Explain RAG and where it typically goes wrong.

> Retrieve relevant passages, put them in the prompt, have the model answer from them
> and cite them. The value is grounding and freshness without retraining.
>
> Where it goes wrong, in the order I actually see it:
>
> **Retrieval, not generation.** If the right passage was not retrieved, no model can
> save the answer. Most "the model hallucinated" reports are retrieval failures, and
> the fix is chunking, hybrid search or a reranker — not a better model.
>
> **Chunking.** Too small and context is lost; too large and precision drops. For
> policy documents, chunking on semantic boundaries with overlap beats a fixed token
> window every time.
>
> **Stale indexes.** A policy changed and the index did not. This is why index builds
> need the same release discipline as code.
>
> **No provenance.** If the answer does not carry which document and which version, you
> cannot defend it. In this repo every retrieval result carries a policy id, a source
> reference and the index version.
>
> **Evaluating the whole thing end to end only.** Retrieval quality and answer quality
> need separate metrics, or you cannot tell which half regressed.

### Q14.3 — When is RAG the wrong answer?

> Three cases.
>
> When the answer needs **computation over structured data** — "how many orders shipped
> late last month" is a SQL query, not a retrieval problem, and stuffing rows into a
> prompt is both expensive and unreliable. That should be a tool.
>
> When the answer needs the **whole corpus**, not a passage — summarising every
> complaint this quarter is a batch pipeline, not a RAG turn.
>
> When the knowledge is **procedural rather than factual** — teaching a model a house
> style or a specific output format is prompting or fine-tuning territory, not
> retrieval.
>
> The general shape: RAG answers "what does the document say", tools answer "what is
> the current state", and neither answers "what should we do", which is where the
> human belongs.

### Q14.4 — Would you fine-tune?

> Not first, and probably not for a while. The order I would exhaust is: prompting,
> then retrieval, then tools, then routing, and only then fine-tuning.
>
> Fine-tuning is worth it for a narrow, stable, high-volume task where a smaller model
> can match a larger one — a classifier, a formatting task, a domain vocabulary
> problem. The economics are real at volume.
>
> What it costs is a lifecycle: training data curation, versioning, a retraining
> trigger, evaluation against a base model, and a deprecation story when the base model
> moves. That is a permanent commitment, and I would want a clear model of the saving
> before taking it on.
>
> What it is *not* is a fix for hallucination or for stale knowledge. Fine-tuning
> teaches behaviour, retrieval provides facts, and confusing the two is the most
> common expensive mistake in this space.

---

## 15. Bringing structure: requirements, stakeholders, prioritisation

> *JD: "Bring structure to a fast-evolving AI platform landscape by defining
> requirements, aligning stakeholders, prioritising opportunities, and helping teams
> move from ideas to real impact."*

### ★ Q15.1 — How do you prioritise a platform backlog?

> I score on three axes and then argue about the result rather than the framework.
>
> **Leverage** — how many teams does this unblock, and how much per team? Platform work
> is multiplicative, so this dominates.
>
> **Risk reduction** — what is the cost of the incident this prevents, times how likely
> it is? This is how governance work competes with feature work honestly rather than by
> appeal to fear.
>
> **Adoption impact** — does this reduce time to first token or remove a reason teams
> route around us?
>
> Then I sanity-check with a question the frameworks miss: *if I do nothing here for
> six months, what breaks?* Some things are genuinely fine to defer, and saying so out
> loud is how you protect capacity for the things that are not.
>
> RICE and WSJF both work. The number is a conversation starter; the value is that
> everyone sees the same inputs.

### Q15.2 — Two teams want opposite things from the platform. How do you resolve it?

> Find the level at which they agree, which is usually one level up from where they are
> arguing.
>
> A concrete version: the AI team wants every new model available immediately; security
> wants each one reviewed before use. Those look opposed. One level up they agree that
> new capability should reach teams quickly *and* safely. So the resolution is a
> tiered model catalogue — a pre-approved set available instantly, and an evaluation
> track with a defined SLA for anything new. Both get most of what they wanted, and
> the disagreement becomes a number (the SLA) rather than a principle.
>
> When there genuinely is no shared level — which is rarer than it feels — I make the
> tradeoff explicit, take the decision, write down what it cost, and revisit it on a
> date. What I avoid is a compromise that satisfies nobody and quietly makes the
> platform worse.

### Q15.3 — How do you help teams move from an idea to real impact?

> Most AI ideas die in one of three places, and each needs a different intervention.
>
> **The demo trap.** A prototype works on ten examples and nobody knows if it works on
> a thousand. Intervention: make them write the golden set *before* the demo. It is a
> forcing function for "what does good look like" and it is the artefact that turns a
> demo into a product conversation.
>
> **The last-mile gap.** It works but has no observability, no cost model and no
> escalation path, so nobody will let it near a customer. Intervention: the golden
> path, which supplies all three by default.
>
> **The no-owner problem.** It ships and then degrades because nobody owns it.
> Intervention: refuse to onboard an agent without a named owner, a budget and an
> escalation path. That is not bureaucracy, it is the difference between a product and
> an artefact.

### Q15.4 — How do you say no?

> Quickly, with a reason, and with the nearest thing I can say yes to.
>
> Slow noes are the expensive ones — they burn a team's quarter while they wait. A fast
> no with a reason lets them do something else.
>
> The three noes I expect to give most: *not this shape* (the want is fine, the design
> creates unacceptable risk — offer the alternative); *not yet* (right idea, wrong
> sequence — say what has to be true first, and put it on the roadmap); and *not us*
> (a real need that belongs to another team — make the introduction rather than
> absorbing it).
>
> The one I would never give is a vague maybe. That is how shadow AI gets built, and
> shadow AI is what the platform exists to prevent.

### Q15.5 — How do you communicate technical platform work to non-technical stakeholders?

> Lead with the outcome, offer the mechanism only if they want it, and keep one
> artefact per audience.
>
> Not "we implemented semantic caching with a 0.93 similarity threshold" but "repeat
> questions now cost nothing, which cut our per-conversation cost by about a fifth" —
> and then the mechanism is there if they ask.
>
> For the board: cost per resolved conversation, adoption, and one risk statement.
> For engineering leadership: DORA, SLOs, error budgets and the debt register.
> For compliance: the governance endpoint and the audit trail, live rather than
> narrated.
>
> The trick I would use most is the demo. Ten minutes in the playground — ask the agent
> something, watch the guardrail block an injection, approve a pharmacist handover —
> does more for stakeholder understanding than any deck, because they can see the
> control working rather than being told it exists.

---

## 16. Product management in technical platform environments

> *JD: "solid product management experience in technical platform environments and
> enjoy turning complex engineering topics into clear product decisions."*

### ★ Q16.1 — What is different about being a PM for a platform versus a customer-facing product?

> Five things, and the first one changes everything else.
>
> **Your users can build it themselves.** A consumer cannot write their own banking
> app; an engineering team absolutely can write their own gateway. So the product has
> to be better than what they would build in a week, or they will build it in a week.
>
> **Success is invisible when it works.** Nobody praises the platform for the incident
> that did not happen. You have to instrument your own value or you will be defunded by
> a team shipping something visible.
>
> **Adoption is voluntary and reversible.** A team can leave. That keeps you honest in
> a way a captive audience does not.
>
> **The roadmap is mostly non-functional.** Reliability, security, cost, developer
> experience. These are genuinely harder to prioritise against each other than
> features, because none of them has a launch date.
>
> **You are often wrong about what teams need**, because you are not doing their job.
> Which is why I weight telemetry over surveys and treat "teams built around us" as the
> strongest possible signal.

### Q16.2 — How technical does a platform PM need to be?

> Deep enough to be *wrong specifically*.
>
> The bar is not writing production code. It is: can you read a design doc and ask the
> question that changes it? Can you tell when an estimate is an estimate and when it is
> a guess? Can you hold a conversation about failover, quotas or retrieval without
> needing a translator, and then explain the same tradeoff to a compliance officer?
>
> Concretely, for this role I would expect to be able to read the Terraform, understand
> what each Azure service costs and fails at, write and defend eval thresholds, and
> debug a trace. Which is roughly what building this repository required.
>
> The failure mode on the other side is a PM who is technical enough to have opinions
> but not senior enough to know they are cheap. My job is to make sure the best
> engineer is working on the right thing, not to be the best engineer.

### Q16.3 — Tell me about a time you got a technical decision wrong.

> *(Substitute your own; here is the shape and a worked example from this repository.)*
>
> Structure: the decision, why it looked right, how you found out, what it cost, what
> you changed in the *process* rather than just the outcome.
>
> Worked example from building this: I originally put the container registry in the
> compute module and the Container Apps environment in the gateway module, because that
> is where each was used. It reads naturally and it is wrong: the gateway needs a
> registry to pull from and the agents need the gateway's URL, so the two modules
> depend on each other and Terraform cannot build a graph at all.
>
> I found it with a static graph check rather than at apply time, which was luck as
> much as design. The fix was not a workaround but the correct decomposition — a shared
> `runtime` module owning the compute fabric that both sit on, with ownership following
> the same line.
>
> What I changed in the process: that graph check is now part of CI, so the next person
> finds it in twenty seconds instead of at 2am during a first apply. The lesson I take
> is that module boundaries should follow *ownership*, not usage, and that a dependency
> cycle is usually a boundary drawn in the wrong place rather than a technical
> nuisance.

### Q16.4 — How do you work with engineers day to day?

> Close, and mostly by removing ambiguity rather than adding process.
>
> I write the problem statement and the acceptance criteria; they own the design. I
> come to design reviews having read the code, not to approve it but to ask the
> questions that surface an assumption. I take the stakeholder and compliance
> conversations off their plate entirely, because that is genuinely my job and it is
> the part that fragments their week.
>
> The things I would not do: assign tasks, estimate on their behalf, or negotiate scope
> in a meeting they are not in. And I would rather be asked "why are we doing this?"
> than not, because if I cannot answer it in one sentence the item is not ready.

---

## 17. How these areas connect in practice

> *JD: "You have worked across a mix of cloud, MLOps, LLMOps, platform engineering,
> DevOps, security, and observability and know how these areas connect in practice."*

### ★ Q17.1 — Show me how these areas connect. Pick one thread.

> Take one thread: **a customer asks about a drug interaction.**
>
> **Cloud** decides where it runs and what it can reach — Container Apps in a VNet,
> private endpoints, an NSG that denies internet egress, so a compromised agent has
> nowhere to send data.
>
> **The AI gateway** decides which model serves it, whether the team is entitled to
> that model, whether they are within budget, and where the call goes when Sweden
> Central is degraded. It writes the cost line attributed to a cost centre.
>
> **LLMOps** decided the prompt version in force, and the eval gate is why this build
> was allowed to serve traffic at all.
>
> **Security** decided the agent holds a virtual key rather than a provider key, that
> tool scopes limit what it is even told about, and that the pharmacist handover cannot
> execute without a human.
>
> **MLOps** decided which index version answered the policy lookup and which embedding
> model built it — which is what makes the answer reproducible in six months.
>
> **Observability** ties it together: one trace carrying the routing reason, the
> guardrail verdicts, the tool calls, the cost and the outcome. That single artefact is
> a debugging tool for engineering, a quality signal for the AI team, a cost line for
> finance and an audit record for the DPO.
>
> **DevOps and IaC** are why every one of those is reproducible: the whole estate is
> Terraform, the pipeline is the only path to production, and rollback is a traffic
> weight.
>
> They connect because they are not seven concerns. They are seven views of one
> question — *can we trust this system in production?*

### Q17.2 — Which of those areas is your weakest, and what are you doing about it?

> Deep Kubernetes and low-level networking. I can reason about the Azure networking
> design — subnets, private endpoints, DNS zones, NSG rules — and I know why each is
> there, but I have not operated a large AKS estate and I would not pretend the
> judgement is the same as someone who has.
>
> What I do about it: I choose managed services where the depth is not the
> differentiator, which is exactly why this design is Container Apps rather than AKS.
> And when the decision genuinely needs that depth, I bring in the person who has it
> and make sure the tradeoff is written down rather than absorbed.
>
> The honest framing: my job is to know where my judgement runs out. Being specific
> about that is more useful than claiming an even distribution.

---

## 18. System design and curveballs

### ★ Q18.1 — Design an agentic AI platform for us. You have a whiteboard.

> I would start by asking two questions, because the answers change the design more
> than anything else: *how many teams will build agents in year one*, and *is any of
> this customer-facing with health data?* Assume ten teams and yes.
>
> Then four layers, drawn bottom-up:
>
> **Foundation** — Azure landing zone, VNet with private endpoints, Entra ID, Key
> Vault, all Terraform, GitHub Actions with OIDC. Nothing AI-specific yet, and that is
> the point: this is the part that is boring and non-negotiable.
>
> **Model access** — the AI gateway. Azure OpenAI in two EU regions behind it, virtual
> keys per team, budgets, failover, semantic cache, cost attribution. This is the first
> thing I would build, because nothing else is enforceable until it exists.
>
> **Agent runtime** — Container Apps, the golden-path template, the shared tool
> registry, guardrails, the approval flow, session and transcript stores.
>
> **Operate and govern** — OTel to Azure Monitor and Grafana, the four metric families,
> SLOs with burn-rate alerts, the eval harness and gate, the audit table, the
> scorecard.
>
> Then I would say what I am *not* building and why: no multi-agent framework, no
> fine-tuning pipeline, no self-hosted models, no Kubernetes. Each is a *not yet* with a
> stated trigger. Knowing what you are not building is most of the job.

### Q18.2 — Your AI spend tripled last month. Go.

> Diagnose before acting, because three of the four causes have completely different
> fixes.
>
> **Where?** The spend ledger breaks down by tenant, model and cost centre. That
> immediately separates "one team launched something" from "everything got more
> expensive".
>
> **Volume or unit cost?** Turns per day versus cost per turn. If volume tripled and
> unit cost held, that may be success rather than a problem, and the conversation is
> about capacity and budget rather than efficiency.
>
> If unit cost moved, four usual suspects: the router upshifting to the deep tier more
> often (check the tier distribution), the cache hit rate collapsing (Redis, or someone
> tuned the threshold), prompt growth (a longer system prompt or bigger retrieved
> context on every call), or a loop regression showing up as steps per turn.
>
> **Then act.** Short term: tighten the budget on the offending key, which the gateway
> enforces immediately. Medium term: fix the actual cause. Long term: whatever it was
> becomes an alert, so the next occurrence is caught in an hour rather than a month.
>
> The thing I would resist is the reflex "switch everyone to a cheaper model". That
> trades a cost problem for a quality problem you cannot see yet.

### Q18.3 — The agent gave a customer dangerous advice and it is on social media. Now what?

> Hour one is containment, not explanation.
>
> **Contain.** Traffic weight to zero on the agent, or fall back to the human queue.
> This is a product decision I would have pre-agreed with customer care so that nobody
> is debating it under pressure.
>
> **Establish the facts.** Pull the trace. Prompt version, model, region, tools called,
> guardrail verdicts, the exact output. This is the moment the audit design either pays
> for itself or does not exist.
>
> **Determine the class.** Did a guardrail fail, or was there no guardrail for this?
> Those are very different remediations and very different statements to make publicly.
>
> **Remediate and prove.** Fix, add the case to the golden set, and re-run the full
> suite. The regression test is what lets you say "this specific failure cannot recur"
> rather than "we have improved our processes".
>
> **Communicate.** Internally first with facts and a timeline; externally with what
> happened, what was done and what changed — no speculation before the facts are in.
>
> **Afterwards.** Blameless postmortem with a systems action item. And honestly: a
> pre-agreed kill switch and a rehearsed comms path are worth more in that hour than
> any amount of prevention, because prevention is never complete.

### Q18.4 — How would you handle a team that wants to use a model we have not approved?

> Treat it as a demand signal, not a violation.
>
> First, find out what they need that the catalogue does not give them — usually a
> capability (longer context, better code, cheaper at volume) rather than a brand
> preference. If the catalogue genuinely has a gap, that is my backlog item, not their
> problem.
>
> Then run it through the evaluation track: does it meet the data-residency
> requirement, what is the sub-processor and DPA position, how does it score on the
> relevant eval suites, and what does it cost at our volume. That is a defined process
> with an SLA rather than a debate.
>
> If it passes, it goes in the catalogue and everyone benefits. If it fails, the answer
> is a specific reason — "it processes outside the EU and we handle Art. 9 data" — not
> "it is not approved". A reason can be argued with and sometimes I will be wrong; a
> policy cannot, and that is how teams learn to route around you.

### Q18.5 — What is the hardest part of this role?

> Holding the tension between enablement and control without collapsing into either.
>
> Collapse toward control and you get a platform nobody adopts, so the AI happens
> anyway, ungoverned, in places you cannot see. Collapse toward enablement and you get
> speed until the first incident, and then a freeze that costs more than the caution
> would have.
>
> The way through is to make the safe path the fast path, so that the tension mostly
> resolves in design rather than in negotiation. That is the whole thesis of the golden
> path, and it is why I would spend the first quarter on enforcement and measurement
> before self-service — you cannot make the safe path fast until you know what "safe"
> costs.
>
> The second-hardest part is that the technology moves faster than the platform can
> absorb, so a lot of the job is deciding what *not* to chase, and being able to defend
> that in a room where somebody read something exciting last week.

---

## 19. Questions to ask them

Ordered so you can pick three or four depending on time. Each one is chosen to tell
you something you would actually act on.

**About the platform's current state**
1. What exists today — is there a gateway, or are teams calling Azure OpenAI directly?
2. How many teams are building with AI right now, and how many are on something
   central versus their own?
3. What is the biggest source of friction those teams complain about?

**About the role**
4. Is this a platform being built, or one being scaled? Those are different jobs.
5. Who owns the agents — the platform team or the tenant teams? Where do you want that
   boundary to be in a year?
6. What does the first six months look like if it goes well?

**About decisions and constraints**
7. Where has the AI Act landed internally — is there a classification process, and who
   owns the sign-off?
8. What is the current appetite on the enablement-versus-control dial, and has anything
   recently moved it?
9. Is there an incident or a near-miss that shaped how the company thinks about this?

**About the team**
10. How is the platform team structured, and how does it interact with the AI and data
    teams?
11. What is the split between building and supporting today?
12. What would make you say, a year from now, that hiring for this role was clearly
    the right call?

**The one worth saving for the end**
13. What is the thing about this platform that you would fix tomorrow if you could?

---

## 20. The 30-second answers

Crib sheet. If you can say these cleanly, you can hold any of the longer conversations.

| Topic | The answer in one breath |
|---|---|
| **Why a gateway** | It is the only thing that makes budgets, entitlement, failover, caching, cost attribution and audit *enforceable* instead of advisory. |
| **Virtual key** | A revocable, budgeted, scoped credential per team. Onboarding is issuing one; offboarding is revoking one. |
| **Routing order** | Entitlement, then complexity tier, then health. Governance first, cost second, reliability third — and it returns the reason. |
| **Why evals** | For a non-deterministic system, tests prove the plumbing and evals prove the behaviour. Safety gated at 1.00. |
| **Groundedness** | Every factual claim must trace to a tool observation. It is the hallucination metric, and it is cheap and explainable. |
| **HITL placement** | Gate the side effect, not the reasoning. Read and draft freely; stop before changing a system of record. |
| **Four signal families** | RED (is it up), agent (is it behaving), quality (is it right), FinOps (is it affordable). |
| **SLOs for non-determinism** | Rate objectives with error budgets, not per-request guarantees. 97% grounded over 7 days. |
| **Why Container Apps** | Revisions, traffic splitting, autoscaling and managed identity without operating Kubernetes. The exit stays cheap. |
| **Why Terraform** | Two questions you cannot otherwise answer during an incident: what changed, and is staging the same as prod. |
| **Why OIDC** | The best way to protect a credential is for it not to exist. |
| **Progressive delivery** | 10% canary, bake against SLOs, promote or roll back. Rollback is a traffic weight — seconds. |
| **Prompt injection** | Layered: detect, treat tool output as data, and constrain the agent so a successful injection has nowhere to go. |
| **EU AI Act** | Limited-risk. Four articles, four code paths — disclosure, audit log, approval gate, eval gate. |
| **GDPR** | Art. 9 data, EU-only residency enforced twice, redact before the call, split retention. |
| **Cost levers** | Tier routing, semantic cache, bounded context, hard ceilings. Measure cost per *resolved conversation*. |
| **Platform vs tenant** | Needed by more than one team and expensive to get wrong → platform. Otherwise → tenant. |
| **Success metrics** | Adoption, time to first token, quality and safety rates, unit economics. |
| **Platform failing** | Teams building around you; the platform team becoming a ticket queue; nobody running the evals. |
| **Hardest part** | Holding enablement against control by making the safe path the fast path. |
