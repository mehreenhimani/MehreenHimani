const K = require("./lib.js");
const { W, H, MX, L, INK, INK2, MUTED, PAPER, GROUND, RED, H_FONT, B, M } = K;
const p = K.deck();
let pg = 0; const n = () => ++pg;

/* ═══ 1 · TITLE ═══════════════════════════════════════════════════════════ */
{
  const s = K.dark(p);
  s.addText("REDCARE PHARMACY  ·  ARCHITECTURE", {
    x: MX, y: 1.15, w: 9, h: 0.3, margin: 0,
    fontFace: B, fontSize: 11.5, bold: true, charSpacing: 2.6, color: RED });
  s.addText("The Agentic AI Platform,\ndrawn rather than described", {
    x: MX, y: 1.55, w: 8.6, h: 1.9, margin: 0,
    fontFace: H_FONT, fontSize: 40, bold: true, color: "FFFFFF", lineSpacing: 50 });
  s.addText("Every diagram uses the same six-colour layer key. Learn it once on the next page and the rest of the deck reads itself.", {
    x: MX, y: 3.55, w: 7.6, h: 0.8, margin: 0,
    fontFace: B, fontSize: 14, color: "AEBCCD", lineSpacing: 22 });

  // a miniature of the system, as the hero
  const mini = [["edge", "Edge"], ["agent", "Agent"], ["gateway", "Gateway"], ["data", "Models"]];
  mini.forEach(([lay, t], i) => {
    const x = MX + i * 1.9;
    K.box(s, p, { layer: lay, x, y: 4.55, w: 1.6, h: 0.62, t, fs: 11, solid: true, flat: true });
    if (i < 3) K.arrow(s, p, x + 1.62, 4.86, x + 1.88, 4.86, { color: "44546A" });
  });
  K.box(s, p, { layer: "obs", x: MX, y: 5.42, w: 3.5, h: 0.55, t: "Observability", fs: 10.5, solid: true, flat: true });
  K.box(s, p, { layer: "gov", x: MX + 3.6, w: 3.5, y: 5.42, h: 0.55, t: "Governance", fs: 10.5, solid: true, flat: true });

  s.addText("Mehreen Himani  ·  Product Manager, Agentic AI Platform", {
    x: MX, y: 6.5, w: 9, h: 0.3, margin: 0, fontFace: B, fontSize: 11.5, color: "6B7C93" });
  s.addNotes("This deck is the architecture document turned into pictures. Same content, arranged so it can be studied rather than read. The one thing to hold onto is the colour key.");
}

/* ═══ 2 · THE COLOUR KEY ═════════════════════════════════════════════════ */
{
  const s = K.light(p); const i = n();
  K.head(s, p, "The key", "Six layers, six colours",
    "Every box in this deck carries one of these colours. It tells you which layer owns the thing, and therefore who is accountable for it.");

  const rows = [
    ["edge",    "Everything hostile arrives here", "Front Door with a WAF terminates TLS, filters OWASP and geo, and absorbs DDoS before anything reaches the VNet."],
    ["agent",   "Where the reasoning happens",     "Container Apps running the plan/act loop. Holds no provider key and cannot reach the internet."],
    ["gateway", "The only path to a model",        "LiteLLM. Owns virtual keys, entitlement, rate limits, budgets, failover, caching and cost attribution."],
    ["data",    "Models and knowledge",            "Azure OpenAI in two EU regions, AI Search for retrieval, Postgres for spend and transcripts, Redis for cache."],
    ["obs",     "How the platform sees itself",    "OTel to Azure Monitor and Grafana. Four signal families, one trace per turn, an append-only audit table."],
    ["gov",     "What keeps it defensible",        "Entra ID, Key Vault, policy as code, and the human-approval gate on anything irreversible."],
  ];
  rows.forEach(([key, title, body], idx) => {
    const y = 1.95 + idx * 0.83;
    const lay = L[key];
    s.addShape(p.ShapeType.roundRect, { x: MX, y, w: W - 2 * MX, h: 0.72, rectRadius: 0.05,
      fill: { color: lay.w }, line: { color: lay.w } });
    K.dot(s, p, MX + 0.24, y + 0.29, lay.c, 0.16);
    s.addText(lay.n, { x: MX + 0.52, y: y + 0.06, w: 1.7, h: 0.3, margin: 0,
      fontFace: B, fontSize: 13, bold: true, color: lay.c });
    s.addText(lay.d, { x: MX + 0.52, y: y + 0.36, w: 1.9, h: 0.3, margin: 0,
      fontFace: M, fontSize: 8.5, color: MUTED });
    s.addText(title, { x: MX + 2.55, y: y + 0.06, w: 3.0, h: 0.6, margin: 0, valign: "middle",
      fontFace: B, fontSize: 12.5, bold: true, color: INK });
    s.addText(body, { x: MX + 5.7, y: y + 0.06, w: W - MX - 5.95, h: 0.62, margin: 0, valign: "middle",
      fontFace: B, fontSize: 11, color: INK2 });
  });
  K.foot(s, i);
  s.addNotes("If you remember nothing else, remember that the gateway is the only path from any workload to any model. Every other guarantee the platform makes is enforced there.");
}

/* ═══ 3 · THE WHOLE SYSTEM ═══════════════════════════════════════════════ */
{
  const s = K.tinted(p); const i = n();
  K.head(s, p, "One page", "The whole system",
    "Solid lines carry a request. Dotted lines carry telemetry. Nothing in the AI plane is reachable from the internet.");

  K.box(s, p, { layer: "edge", x: MX, y: 2.35, w: 1.5, h: 0.85, t: "Customer", sub: "HTTPS", subMono: true, fs: 11.5 });
  K.box(s, p, { layer: "edge", x: 2.35, y: 2.35, w: 1.5, h: 0.85, t: "Front Door", sub: "WAF · DDoS", fs: 11.5, subFs: 9 });
  K.box(s, p, { layer: "agent", x: 4.2, y: 2.05, w: 2.5, h: 1.45, t: "CareCopilot agent", sub: "Container Apps\nplan → act → verify", fs: 12.5, subFs: 9.5 });
  K.box(s, p, { layer: "gateway", x: 7.05, y: 2.05, w: 2.3, h: 1.45, t: "AI Gateway", sub: "LiteLLM\nkeys · budgets · failover", fs: 12.5, subFs: 9.5 });

  // models
  const models = [["Azure OpenAI", "Sweden Central"], ["Azure OpenAI", "West Europe"], ["Anthropic", "EU inference"]];
  models.forEach(([t, sub], j) => {
    K.box(s, p, { layer: "data", x: 9.75, y: 1.72 + j * 0.72, w: 2.95, h: 0.62, t, sub, fs: 10.5, subFs: 8.5 });
    K.arrow(s, p, 9.37, 2.78, 9.73, 2.03 + j * 0.72, { color: L.data.c });
  });

  // systems of record
  const sysY = 4.35;
  ["SAP-OMS", "WMS", "ABDA-DACON", "AI Search", "ServiceNow"].forEach((t, j) => {
    K.box(s, p, { layer: "data", x: MX + j * 1.72, y: sysY, w: 1.55, h: 0.5, t, fs: 9.5, mono: true, flat: true });
    K.arrow(s, p, 5.45, 3.52, MX + j * 1.72 + 0.77, sysY - 0.02, { color: L.data.c, width: 1 });
  });
  s.addText("systems of record — every tool declares what it touches", {
    x: MX, y: sysY + 0.54, w: 8.6, h: 0.26, margin: 0, fontFace: B, fontSize: 9.5, color: MUTED });

  // observability + governance rails
  K.box(s, p, { layer: "obs", x: 9.75, y: 4.15, w: 2.95, h: 0.95, t: "OTel Collector", sub: "→ Azure Monitor · Grafana\n→ audit table (7y)", fs: 11.5, subFs: 9 });
  K.arrow(s, p, 5.45, 3.52, 9.72, 4.4, { color: L.obs.c, dash: "dash" });
  K.arrow(s, p, 8.2, 3.52, 9.72, 4.55, { color: L.obs.c, dash: "dash" });

  K.box(s, p, { layer: "gov", x: MX, y: 5.55, w: 5.9, h: 0.72, t: "Key Vault · Entra ID · managed identity", sub: "no long-lived secret exists anywhere in the chain", fs: 11.5, subFs: 9 });
  K.box(s, p, { layer: "gov", x: 6.7, y: 5.55, w: 6.0, h: 0.72, t: "Human approval on side-effecting tools", sub: "the pharmacist ticket does not exist until someone approves it", fs: 11.5, subFs: 9 });

  // request path
  K.arrow(s, p, 2.12, 2.78, 2.33, 2.78);
  K.arrow(s, p, 3.87, 2.78, 4.18, 2.78);
  K.arrow(s, p, 6.72, 2.78, 7.03, 2.78, { color: L.gateway.c, width: 1.6 });

  K.legend(s, p, 6.55);
  K.foot(s, i);
  s.addNotes("Walk it left to right: customer, edge, agent, gateway, models. Then the two rails underneath — observability watching everything, governance constraining it. The agent's subnet denies internet egress, so the gateway is not a convention, it is the only route.");
}

/* ═══ 4 · THE REQUEST PATH ═══════════════════════════════════════════════ */
{
  const s = K.light(p); const i = n();
  K.head(s, p, "The request path", "One question, every hop",
    "“Can I take ibuprofen with warfarin?” — and what happens to it, in order.");

  const steps = [
    ["classify",  "agent",   "A cheap classifier scores the turn trivial, standard or complex.", "costs $0.0001"],
    ["route",     "gateway", "Entitlement, then tier, then health. The router returns the reason.", "→ balanced tier"],
    ["budget",    "gov",     "Tenant daily cap and session ceiling checked before anything is spent.", "pre-flight"],
    ["guard in",  "gov",     "Injection → scope → PII redaction, before the model reads a word.", "3 checks"],
    ["plan / act","agent",   "LLM proposes a tool, the tool runs, the result comes back. Repeat, bounded.", "≤ 6 steps"],
    ["guard out", "gov",     "Secrets → grounding → medical-advice policy → PII egress → disclosure.", "5 checks"],
    ["account",   "obs",     "Spend ledger, four metric families, append-only audit record.", "1 trace"],
  ];
  const bw = (W - 2 * MX - 6 * 0.16) / 7;
  steps.forEach(([t, layer, body, tag], j) => {
    const x = MX + j * (bw + 0.16);
    K.box(s, p, { layer, x, y: 1.95, w: bw, h: 0.66, t, fs: 11.5, mono: true, solid: true, flat: true });
    K.num(s, p, x + bw / 2 - 0.17, 2.75, j + 1, L[layer].c, 0.34);
    s.addText(tag, { x, y: 3.2, w: bw, h: 0.26, align: "center", margin: 0,
      fontFace: M, fontSize: 8.5, color: L[layer].c });
    s.addText(body, { x, y: 3.5, w: bw, h: 1.15, margin: 0, valign: "top",
      fontFace: B, fontSize: 10, color: INK2, lineSpacing: 13 });
    if (j < 6) K.arrow(s, p, x + bw + 0.02, 2.28, x + bw + 0.14, 2.28, { color: "9AAABE", width: 1 });
  });

  const notes = [
    ["Budget before guardrails", "Guardrails cost CPU. A tenant already over budget should be refused before the platform spends anything on them — including its own compute."],
    ["Guardrails before the model", "Injection has to be caught before the model reads it, and PII removed before the prompt leaves the VNet. An output-only guardrail already lost."],
    ["Approval before the side effect", "The agent may read and draft freely. It stops before changing a system of record. That is EU AI Act Art. 14 as a code path."],
  ];
  notes.forEach(([t, body], j) => {
    const x = MX + j * 4.17;
    s.addShape(p.ShapeType.roundRect, { x, y: 5.15, w: 3.95, h: 1.72, rectRadius: 0.05,
      fill: { color: GROUND }, line: { color: "E3E9F1" } });
    s.addText(t, { x: x + 0.22, y: 5.33, w: 3.5, h: 0.3, margin: 0,
      fontFace: B, fontSize: 12, bold: true, color: RED });
    s.addText(body, { x: x + 0.22, y: 5.66, w: 3.55, h: 1.06, margin: 0, valign: "top",
      fontFace: B, fontSize: 10.5, color: INK2, lineSpacing: 14 });
  });
  K.foot(s, i);
  s.addNotes("The ordering is the argument. Anyone can list these seven stages; being able to say why each sits where it does is the difference between describing a design and having made one.");
}

/* ═══ 5 · THE GATEWAY ════════════════════════════════════════════════════ */
{
  const s = K.tinted(p); const i = n();
  K.head(s, p, "The choke point", "Why every call goes through one door",
    "Without it: N codebases holding provider keys, N retry policies, no cost story, no way to revoke a team's access today.");

  // teams on the left
  const teams = [["Pharmacy care", "sk-carecopilot-prod"], ["Growth marketing", "sk-marketing-dev"], ["Supply chain", "sk-supply-dev"], ["Clinical data", "sk-clinical-dev"]];
  teams.forEach(([t, k], j) => {
    const y = 2.05 + j * 0.78;
    K.box(s, p, { layer: "agent", x: MX, y, w: 2.6, h: 0.62, t, sub: k, fs: 11, subFs: 8.5, subMono: true });
    K.arrow(s, p, 3.24, y + 0.31, 4.28, 3.6, { color: L.agent.c, width: 1 });
  });

  K.box(s, p, { layer: "gateway", x: 4.35, y: 2.05, w: 2.55, h: 3.05, t: "LiteLLM",
    sub: "one endpoint · no bypass", fs: 17, subFs: 9.5, solid: true, top: true });

  const owns = ["virtual keys", "entitlement", "rpm / tpm limits", "budgets, pre-call",
    "retries + failover", "semantic cache", "cost attribution", "guardrail hooks", "OTel callbacks"];
  owns.forEach((t, j) => {
    s.addText("•  " + t, { x: 4.6, y: 3.12 + j * 0.215, w: 2.1, h: 0.22, margin: 0,
      fontFace: M, fontSize: 9, color: "FFFFFF" });
  });

  // models on the right
  const outs = [["carecopilot-fast", "gpt-4o-mini · Sweden"], ["carecopilot-balanced", "gpt-4o · Sweden"],
    ["carecopilot-balanced-westeu", "gpt-4o · West Europe"], ["carecopilot-deep", "claude-sonnet-4-5 · EU"],
    ["carecopilot-embed", "text-embedding-3-large"]];
  outs.forEach(([t, sub], j) => {
    const y = 2.05 + j * 0.63;
    K.box(s, p, { layer: "data", x: 7.65, y, w: 5.05, h: 0.52, t, sub, fs: 10.5, subFs: 8.5, mono: true, subMono: true });
    K.arrow(s, p, 6.93, 3.6, 7.62, y + 0.26, { color: L.data.c, width: 1 });
  });

  K.why(s, MX, 5.5, W - 2 * MX,
    "Bypassing it is not a policy — it is a network property. The agent subnet denies internet egress and the agent holds no provider key, so it has exactly one route to a model. Tenants ask for 'carecopilot-balanced', never 'gpt-4o-2024-11-20', which is what makes swapping the model underneath a config change rather than a migration.");
  K.foot(s, i);
  s.addNotes("Build vs buy: LiteLLM because it is open source — no lock-in on the most load-bearing component — genuinely multi-provider, has virtual keys and spend tracking built in, and self-hosts inside our VNet, which for Art. 9 health data is a requirement rather than a preference.");
}

/* ═══ 6 · ROUTING ════════════════════════════════════════════════════════ */
{
  const s = K.light(p); const i = n();
  K.head(s, p, "Routing", "Three gates, in this order, always explained",
    "Governance first, cost second, reliability third. Reversing any two of these is a different platform.");

  const gates = [
    ["gov",     "1  Entitlement", "Is this key allowed this model?",
      "A governance question, so it goes first. No performance consideration may override it — that is what makes the entitlement real rather than advisory."],
    ["gateway", "2  Complexity tier", "Cheapest model that can do the job",
      "A classifier scores the turn trivial / standard / complex. The mini tier is ~16× cheaper per token; the classifier that decides costs $0.0001 and pays for itself the first time it keeps a greeting off the deep model."],
    ["data",    "3  Health", "Is the chosen deployment cooling down?",
      "Same model in the second EU region first. A different provider is the last resort, because a provider switch changes behaviour and behaviour changes need an eval run."],
  ];
  gates.forEach(([layer, t, q, body], j) => {
    const x = MX + j * 4.17;
    K.box(s, p, { layer, x, y: 1.95, w: 3.95, h: 0.6, t, fs: 14, solid: true, flat: true });
    s.addText(q, { x, y: 2.68, w: 3.95, h: 0.32, margin: 0, align: "center",
      fontFace: B, fontSize: 11.5, italic: true, color: L[layer].c });
    s.addText(body, { x: x + 0.1, y: 3.06, w: 3.75, h: 1.5, margin: 0, valign: "top",
      fontFace: B, fontSize: 11, color: INK2, lineSpacing: 15 });
    if (j < 2) K.arrow(s, p, x + 3.98, 2.25, x + 4.14, 2.25, { color: "9AAABE" });
  });

  // worked example
  s.addShape(p.ShapeType.roundRect, { x: MX, y: 4.7, w: W - 2 * MX, h: 1.72, rectRadius: 0.06,
    fill: { color: INK }, line: { color: INK } });
  s.addText("A decision the trace can explain", { x: MX + 0.32, y: 4.88, w: 6, h: 0.28, margin: 0,
    fontFace: B, fontSize: 11.5, bold: true, color: "AEBCCD" });
  s.addText([
    { text: "complexity  ", options: { color: "8595A9" } },
    { text: "trivial", options: { color: "5FD3A0", bold: true } },
    { text: "   —  greeting with no information need\n", options: { color: "8595A9" } },
    { text: "selected    ", options: { color: "8595A9" } },
    { text: "carecopilot-fast", options: { color: "FFFFFF", bold: true } },
    { text: "   →  azure/gpt-4o-mini @ swedencentral\n", options: { color: "8595A9" } },
    { text: "why         ", options: { color: "8595A9" } },
    { text: "classifier scored the turn 'trivial' → downshift to fast tier", options: { color: "E5A93B" } },
  ], { x: MX + 0.32, y: 5.2, w: W - 2 * MX - 0.6, h: 1.05, margin: 0,
       fontFace: M, fontSize: 11, lineSpacing: 17 });
  K.foot(s, i);
  s.addNotes("A routing decision you cannot explain is one you cannot debug and cannot defend in a cost review. The reason chain is returned on every turn and rendered in the console.");
}

/* ═══ 7 · FAILOVER ═══════════════════════════════════════════════════════ */
{
  const s = K.tinted(p); const i = n();
  K.head(s, p, "Reliability", "What happens when a region goes down",
    "Two EU regions and two providers. The second region is failover and a second quota pool — quota is allocated per region.");

  K.box(s, p, { layer: "agent", x: MX, y: 2.9, w: 1.9, h: 0.8, t: "Agent", sub: "one URL", fs: 13, subFs: 9 });
  K.box(s, p, { layer: "gateway", x: 2.95, y: 2.9, w: 2.1, h: 0.8, t: "Gateway", sub: "latency-based", fs: 13, subFs: 9 });
  K.arrow(s, p, 2.52, 3.3, 2.92, 3.3);

  const tiers = [
    ["Sweden Central", "gpt-4o · primary", "data", 1.95, "healthy"],
    ["West Europe",    "gpt-4o · same model", "data", 2.95, "failover 1"],
    ["Anthropic EU",   "claude-sonnet-4-5", "data", 3.95, "failover 2"],
  ];
  tiers.forEach(([t, sub, layer, y, tag], j) => {
    K.box(s, p, { layer, x: 5.9, y, w: 3.1, h: 0.72, t, sub, fs: 11.5, subFs: 9,
                  solid: j === 0 });
    K.arrow(s, p, 5.07, 3.3, 5.87, y + 0.36,
      { color: L.data.c, width: j === 0 ? 1.8 : 1, dash: j ? "dash" : "solid" });
    s.addText(tag, { x: 9.1, y: y + 0.2, w: 1.3, h: 0.3, margin: 0,
      fontFace: M, fontSize: 9, color: j === 0 ? L.data.c : MUTED });
  });

  const rules = [
    ["Region before provider", "Same model in a second region keeps behaviour identical. A provider switch does not — so it is last, and it needs an eval run behind it."],
    ["3 failures, 60s cooldown", "A deployment that fails three times is taken out of rotation for a minute, then probed again. 429s do not count: backpressure is not ill health."],
    ["Context and content fallbacks", "A prompt too long for 128k routes to the 200k model. A provider content-filter block gets a second opinion rather than an error."],
  ];
  rules.forEach(([t, body], j) => {
    const y = 4.95 + j * 0.0;
    const x = MX + j * 4.17;
    s.addText(t, { x, y: 4.95, w: 3.9, h: 0.3, margin: 0,
      fontFace: B, fontSize: 12, bold: true, color: INK });
    s.addText(body, { x, y: 5.28, w: 3.9, h: 1.0, margin: 0, valign: "top",
      fontFace: B, fontSize: 10.5, color: INK2, lineSpacing: 14 });
  });
  K.why(s, MX, 6.45, W - 2 * MX,
    "A single region is a single point of failure for every AI feature in the company. That is the whole argument for the second one — and it is also where the extra quota comes from.");
  K.foot(s, i);
  s.addNotes("In the console you can mark a deployment unhealthy and send another turn — the trace shows the failover hop and the reason. It is a ten-second reliability drill.");
}

/* ═══ 8 · NETWORK ════════════════════════════════════════════════════════ */
{
  const s = K.light(p); const i = n();
  K.head(s, p, "Trust boundary", "No public ingress, no unmonitored egress",
    "The rule that shapes every other Azure decision. For a workload handling Art. 9 health data this is the baseline a DPO signs, not hardening.");

  // VNet container
  s.addShape(p.ShapeType.roundRect, { x: MX, y: 1.9, w: W - 2 * MX, h: 3.1, rectRadius: 0.08,
    fill: { color: "F4F8FB" }, line: { color: L.data.c, width: 1.5, dashType: "dash" } });
  s.addText("VNet  10.44.0.0/16", { x: MX + 0.22, y: 1.99, w: 3, h: 0.28, margin: 0,
    fontFace: M, fontSize: 10, bold: true, color: L.data.c });

  const subnets = [
    ["snet-apps", "/23 · delegated to Container Apps", "agent", ["carecopilot-agent", "litellm-gateway"]],
    ["snet-private-endpoints", "/24 · one NIC per PaaS service", "data", ["Key Vault", "OpenAI", "Search", "Redis", "ACR"]],
    ["snet-data", "/24 · delegated to Postgres", "data", ["postgres-flexible"]],
  ];
  subnets.forEach(([t, sub, layer, items], j) => {
    const x = MX + 0.25 + j * 4.05;
    s.addShape(p.ShapeType.roundRect, { x, y: 2.36, w: 3.8, h: 2.5, rectRadius: 0.06,
      fill: { color: PAPER }, line: { color: "D9E1EB" } });
    s.addText(t, { x: x + 0.18, y: 2.47, w: 3.4, h: 0.28, margin: 0,
      fontFace: M, fontSize: 10.5, bold: true, color: INK });
    s.addText(sub, { x: x + 0.18, y: 2.75, w: 3.4, h: 0.26, margin: 0,
      fontFace: B, fontSize: 9.5, color: MUTED });
    items.forEach((it, k) => {
      K.box(s, p, { layer, x: x + 0.18, y: 3.09 + k * 0.345, w: 3.44, h: 0.29, t: it,
        fs: 9.5, mono: true, flat: true });
    });
  });

  // the four rules
  const rules = [
    ["gov",  "Deny inbound from the internet", "Ingress only from the Front Door subnet, on 443."],
    ["gov",  "Deny outbound to the internet",  "Egress allowed to the AzureCloud service tag only — a compromised agent has nowhere to send data."],
    ["data", "Private endpoint per dependency", "Key Vault, OpenAI, Search, Redis, Postgres, ACR, Storage, Monitor."],
    ["data", "A private DNS zone for each one", "Without it the endpoint resolves to its public IP and traffic silently leaves the VNet — the most commonly missed control in Azure private networking, and it fails quietly."],
  ];
  rules.forEach(([layer, t, body], j) => {
    const x = MX + (j % 2) * 6.35;
    const y = 5.22 + Math.floor(j / 2) * 0.82;
    K.dot(s, p, x, y + 0.08, L[layer].c, 0.14);
    s.addText(t, { x: x + 0.24, y, w: 5.9, h: 0.28, margin: 0,
      fontFace: B, fontSize: 11.5, bold: true, color: INK });
    s.addText(body, { x: x + 0.24, y: y + 0.28, w: 5.9, h: 0.5, margin: 0, valign: "top",
      fontFace: B, fontSize: 10, color: INK2, lineSpacing: 13 });
  });
  K.foot(s, i);
  s.addNotes("The private DNS zone point is the one worth landing in an interview. A private endpoint without its zone still resolves publicly, so you believe you are private and you are not — and nothing errors.");
}

/* ═══ 9 · IDENTITY ═══════════════════════════════════════════════════════ */
{
  const s = K.tinted(p); const i = n();
  K.head(s, p, "Identity", "There is no long-lived secret anywhere",
    "Two flows, and neither of them ends in a password sitting in a settings page.");

  // flow 1
  s.addText("GitHub Actions → Azure", { x: MX, y: 2.0, w: 6, h: 0.3, margin: 0,
    fontFace: B, fontSize: 13, bold: true, color: INK });
  const f1 = [["GitHub run", "gov"], ["OIDC token", "gov"], ["Entra ID", "gov"], ["Azure", "data"]];
  f1.forEach(([t, layer], j) => {
    const x = MX + j * 1.62;
    K.box(s, p, { layer, x, y: 2.4, w: 1.42, h: 0.6, t, fs: 10.5, flat: true });
    if (j < 3) K.arrow(s, p, x + 1.44, 2.7, x + 1.6, 2.7, { color: "9AAABE", width: 1 });
  });
  s.addText("Entra checks the token's subject against an exact federated credential — a different branch, environment or fork does not match and is rejected before any Azure call. The token lives minutes. Nothing exists to leak or rotate.", {
    x: MX, y: 3.12, w: 6.05, h: 1.0, margin: 0, valign: "top",
    fontFace: B, fontSize: 10.5, color: INK2, lineSpacing: 14 });

  // flow 2
  s.addText("Running app → its secrets", { x: 6.95, y: 2.0, w: 6, h: 0.3, margin: 0,
    fontFace: B, fontSize: 13, bold: true, color: INK });
  const f2 = [["Container App", "agent"], ["Managed identity", "gov"], ["Key Vault", "gov"]];
  f2.forEach(([t, layer], j) => {
    const x = 6.95 + j * 1.95;
    K.box(s, p, { layer, x, y: 2.4, w: 1.75, h: 0.6, t, fs: 10.5, flat: true });
    if (j < 2) K.arrow(s, p, x + 1.77, 2.7, x + 1.93, 2.7, { color: "9AAABE", width: 1 });
  });
  s.addText("The app holds nothing. It presents a managed identity and Key Vault decides. The gateway and the agent have separate identities, so “the agent was compromised” and “the provider keys were compromised” stay different sentences.", {
    x: 6.95, y: 3.12, w: 5.75, h: 1.0, margin: 0, valign: "top",
    fontFace: B, fontSize: 10.5, color: INK2, lineSpacing: 14 });

  // what each identity may do
  s.addShape(p.ShapeType.roundRect, { x: MX, y: 4.3, w: W - 2 * MX, h: 2.05, rectRadius: 0.06,
    fill: { color: PAPER }, line: { color: "E3E9F1" } });
  const grants = [
    ["Deploy identity", "gov", "Contributor on one resource group. Explicitly barred from granting Owner or User Access Administrator — no privilege-escalation path."],
    ["Agent identity", "agent", "Key Vault Secrets User · AcrPull · Search Index Data Reader. Cannot read a provider key. Cannot change infrastructure."],
    ["Gateway identity", "gateway", "The only identity in the platform permitted to call the model endpoints. That is what makes the gateway's governance non-optional."],
  ];
  grants.forEach(([t, layer, body], j) => {
    const x = MX + 0.3 + j * 4.05;
    K.dot(s, p, x, 4.58, L[layer].c, 0.15);
    s.addText(t, { x: x + 0.24, y: 4.5, w: 3.5, h: 0.3, margin: 0,
      fontFace: B, fontSize: 12, bold: true, color: L[layer].c });
    s.addText(body, { x: x + 0.24, y: 4.84, w: 3.5, h: 1.3, margin: 0, valign: "top",
      fontFace: B, fontSize: 10.5, color: INK2, lineSpacing: 14 });
  });
  K.why(s, MX, 6.5, W - 2 * MX,
    "The tenant holds a virtual key, not a provider key: revocable, budgeted, scoped, and rotatable without redeploying anything.");
  K.foot(s, i);
  s.addNotes("The best way to protect a credential is for it not to exist. That sentence covers OIDC federation, managed identity and virtual keys all at once.");
}

/* ═══ 10 · TERRAFORM ═════════════════════════════════════════════════════ */
{
  const s = K.light(p); const i = n();
  K.head(s, p, "Infrastructure as code", "The module graph is a design signal",
    "Eight modules, two environments, one dependency rule — and the bug that proved the rule.");

  const mods = [
    ["network", 0, 0, "VNet, subnets, NSGs, 8 DNS zones"],
    ["identity", 0, 1, "managed identities, RBAC, OIDC"],
    ["security", 0, 2, "Key Vault, secret slots, Defender"],
    ["observability", 1, 0, "Log Analytics, App Insights, alerts"],
    ["data", 1, 1, "OpenAI ×2, Search, Postgres, Redis"],
    ["runtime", 1, 2, "Container Apps env + ACR"],
    ["gateway", 2, 0, "the LiteLLM container app"],
    ["compute", 2, 1, "the agents, as a map"],
  ];
  const colX = [MX, MX + 3.3, MX + 6.6];
  mods.forEach(([t, col, row, sub]) => {
    K.box(s, p, { layer: col === 0 ? "gov" : col === 1 ? "data" : "agent",
      x: colX[col], y: 2.05 + row * 0.82, w: 3.05, h: 0.68, t, sub, fs: 12, subFs: 8.5, mono: true });
  });
  K.arrow(s, p, MX + 3.08, 2.72, MX + 3.28, 2.72, { color: "9AAABE", width: 1 });
  K.arrow(s, p, MX + 6.38, 2.72, MX + 6.58, 2.72, { color: "9AAABE", width: 1 });
  s.addText("foundation", { x: colX[0], y: 4.55, w: 3.05, h: 0.26, align: "center", margin: 0,
    fontFace: B, fontSize: 10, bold: true, color: L.gov.c });
  s.addText("shared fabric", { x: colX[1], y: 4.55, w: 3.05, h: 0.26, align: "center", margin: 0,
    fontFace: B, fontSize: 10, bold: true, color: L.data.c });
  s.addText("workloads", { x: colX[2], y: 4.55, w: 3.05, h: 0.26, align: "center", margin: 0,
    fontFace: B, fontSize: 10, bold: true, color: L.agent.c });

  s.addShape(p.ShapeType.roundRect, { x: MX, y: 5.0, w: 6.2, h: 1.7, rectRadius: 0.06,
    fill: { color: "FCEDEF" }, line: { color: "FCEDEF" } });
  s.addText("The cycle that taught the boundary", { x: MX + 0.28, y: 5.16, w: 5.6, h: 0.3, margin: 0,
    fontFace: B, fontSize: 12, bold: true, color: RED });
  s.addText("The gateway needs a registry to pull from; the agents need the gateway's URL. Put the registry in compute and the environment in gateway and the two modules depend on each other — Terraform refuses to build a graph at all. The fix was not a workaround: the compute fabric is shared infrastructure both sit on, so it became its own module. Module boundaries follow ownership, not usage.", {
    x: MX + 0.28, y: 5.48, w: 5.7, h: 1.1, margin: 0, valign: "top",
    fontFace: B, fontSize: 10.5, color: INK2, lineSpacing: 14 });

  s.addShape(p.ShapeType.roundRect, { x: 7.1, y: 5.0, w: 5.6, h: 1.7, rectRadius: 0.06,
    fill: { color: GROUND }, line: { color: "E3E9F1" } });
  s.addText("dev and prod are the same code", { x: 7.38, y: 5.16, w: 5.0, h: 0.3, margin: 0,
    fontFace: B, fontSize: 12, bold: true, color: INK });
  s.addText("What differs is size and cost: smaller SKUs, no zone redundancy, scale-to-zero. What never differs is posture — private networking, managed identity, no public data access, guardrails on, audit on. If a control had to be switched on for production, dev would be the weak link an attacker uses.", {
    x: 7.38, y: 5.48, w: 5.1, h: 1.1, margin: 0, valign: "top",
    fontFace: B, fontSize: 10.5, color: INK2, lineSpacing: 14 });
  K.foot(s, i);
  s.addNotes("This is the best 'tell me about a technical mistake' story in the whole project: a dependency cycle is usually a boundary drawn in the wrong place, and the fix belongs in the design rather than in a workaround.");
}

/* ═══ 11 · PIPELINE ══════════════════════════════════════════════════════ */
{
  const s = K.tinted(p); const i = n();
  K.head(s, p, "Delivery", "The only path to production",
    "Nobody holds standing write access to the Azure subscriptions. The pipeline gets minutes of it, via OIDC.");

  const stages = [
    ["Pull request", "gov", ["lint", "test", "evals ★", "terraform", "security"]],
    ["Plan on PR", "gov", ["terraform plan", "Checkov + tfsec", "OPA on plan JSON", "posted as a comment"]],
    ["Merge → main", "gateway", ["build + SBOM", "Trivy scan", "cosign sign", "dev deploy + smoke"]],
    ["Production", "agent", ["canary at 10%", "bake 15 min vs SLOs", "promote or roll back", "2 approvers"]],
  ];
  const sw = (W - 2 * MX - 3 * 0.35) / 4;
  stages.forEach(([t, layer, items], j) => {
    const x = MX + j * (sw + 0.35);
    K.box(s, p, { layer, x, y: 2.05, w: sw, h: 0.6, t, fs: 13, solid: true, flat: true });
    items.forEach((it, k) => {
      const star = it.includes("★");
      s.addText((star ? "" : "·  ") + it, {
        x: x + 0.12, y: 2.85 + k * 0.34, w: sw - 0.24, h: 0.3, margin: 0, valign: "middle",
        fontFace: star ? B : M, fontSize: star ? 11 : 9.5,
        bold: star, color: star ? RED : INK2 });
    });
    if (j < 3) K.arrow(s, p, x + sw + 0.06, 2.35, x + sw + 0.3, 2.35, { color: "9AAABE" });
  });

  const facts = [
    ["★ The eval job is a required check", "For a non-deterministic system, unit tests prove the plumbing and evals prove the behaviour. Safety is thresholded at 1.00 — one miss fails the build."],
    ["The plan is the review artefact", "A reviewer approves a diff of resources, not a diff of HCL. Those are different things, and the gap between them is where production surprises live."],
    ["Rollback is a traffic weight", "Seconds, no rebuild. A rollback that needs a rebuild is not a rollback, it is a hope."],
  ];
  facts.forEach(([t, body], j) => {
    const x = MX + j * 4.17;
    s.addShape(p.ShapeType.roundRect, { x, y: 4.5, w: 3.95, h: 1.85, rectRadius: 0.06,
      fill: { color: PAPER }, line: { color: "E3E9F1" } });
    s.addText(t, { x: x + 0.22, y: 4.68, w: 3.5, h: 0.55, margin: 0, valign: "top",
      fontFace: B, fontSize: 12, bold: true, color: INK });
    s.addText(body, { x: x + 0.22, y: 5.22, w: 3.55, h: 1.0, margin: 0, valign: "top",
      fontFace: B, fontSize: 10.5, color: INK2, lineSpacing: 14 });
  });
  K.foot(s, i);
  s.addNotes("Nightly drift detection runs a plan against both environments and opens an issue if it is not empty. Drift means something changed outside the pipeline — either an incident or a bug, and both are worth closing.");
}

/* ═══ 12 · GUARDRAILS ════════════════════════════════════════════════════ */
{
  const s = K.light(p); const i = n();
  K.head(s, p, "Safety", "Two pipelines the tenant never writes",
    "Shared, so a team does not have to reimplement PII redaction to ship. They get it by adopting the paved road.");

  const inp = [["prompt_injection", "block", "instruction override, exfiltration"],
    ["topic_policy", "block", "outside the pharmacy support scope"],
    ["pii_redaction", "redact", "IBAN, email, phone, card, DOB"]];
  const out = [["secret_leak", "block", "credential-shaped strings in the answer"],
    ["grounding", "annotate", "every claim traced to a tool observation"],
    ["medical_advice", "escalate", "individualised clinical instruction"],
    ["pii_egress", "redact", "identifiers on the way back out"],
    ["disclosure", "annotate", "EU AI Act Art. 50, on every reply"]];

  const panel = (x, title, rows, tag) => {
    s.addShape(p.ShapeType.roundRect, { x, y: 1.95, w: 6.05, h: 3.15, rectRadius: 0.06,
      fill: { color: GROUND }, line: { color: "E3E9F1" } });
    s.addText(title, { x: x + 0.25, y: 2.1, w: 4, h: 0.3, margin: 0,
      fontFace: B, fontSize: 12.5, bold: true, color: L.gov.c });
    s.addText(tag, { x: x + 4.3, y: 2.12, w: 1.5, h: 0.28, align: "right", margin: 0,
      fontFace: M, fontSize: 9, color: MUTED });
    rows.forEach(([nme, act, why], j) => {
      const y = 2.5 + j * 0.5;
      const c = act === "block" ? "B3121F" : act === "escalate" ? "A85B00" : "0E6E80";
      s.addText(nme, { x: x + 0.25, y, w: 2.3, h: 0.28, margin: 0,
        fontFace: M, fontSize: 10, bold: true, color: INK });
      s.addText(act, { x: x + 2.6, y, w: 0.9, h: 0.28, margin: 0,
        fontFace: M, fontSize: 9.5, bold: true, color: c });
      s.addText(why, { x: x + 3.55, y, w: 2.3, h: 0.28, margin: 0, valign: "top",
        fontFace: B, fontSize: 9.5, color: MUTED });
    });
  };
  panel(MX, "Input pipeline — before the model reads a word", inp, "3 checks");
  panel(6.85, "Output pipeline — before the customer sees it", out, "5 checks");

  s.addShape(p.ShapeType.roundRect, { x: MX, y: 5.35, w: W - 2 * MX, h: 1.15, rectRadius: 0.06,
    fill: { color: "FCEDEF" }, line: { color: "FCEDEF" } });
  s.addText("The trust boundary that matters most in an agentic system", {
    x: MX + 0.3, y: 5.5, w: 8, h: 0.3, margin: 0,
    fontFace: B, fontSize: 12.5, bold: true, color: RED });
  s.addText("Tool output is data, never instruction. A policy document, an order note or a product description can carry text engineered to look like a system prompt — that is indirect prompt injection, and it is the hard one. There is no complete defence, so the strategy is layered: detect it, treat tool content as data, and constrain the agent so a successful injection has nowhere to go.", {
    x: MX + 0.3, y: 5.82, w: W - 2 * MX - 0.6, h: 0.6, margin: 0, valign: "top",
    fontFace: B, fontSize: 11, color: INK2, lineSpacing: 14 });
  K.foot(s, i);
  s.addNotes("An agent is a confused deputy with a credential. Design for the day it is fully persuaded — which is why least privilege on the tool surface matters more than any single detector.");
}

/* ═══ 13 · OBSERVABILITY ═════════════════════════════════════════════════ */
{
  const s = K.tinted(p); const i = n();
  K.head(s, p, "Observability", "Four families, and one trace with four readers",
    "An agent can be fast, return 200, and still be wrong, ungrounded, unaffordable or looping. Classic APM covers only the first row.");

  const fams = [
    ["RED", "Is the service up?", ["agent_requests_total", "agent_request_duration_seconds", "agent_errors_total"], "44546A"],
    ["Agent", "Is it behaving?", ["agent_steps_per_turn", "agent_tool_calls_total", "agent_loop_termination_total"], L.agent.c],
    ["Quality", "Is it right?", ["agent_groundedness_ratio", "guardrail_firings_total", "agent_eval_score"], L.gov.c],
    ["FinOps", "Is it affordable?", ["llm_cost_usd_per_turn", "llm_cache_events_total", "llm_budget_remaining_usd"], L.gateway.c],
  ];
  fams.forEach(([t, q, ms, c], j) => {
    const x = MX + (j % 2) * 6.35;
    const y = 1.95 + Math.floor(j / 2) * 1.55;
    s.addShape(p.ShapeType.roundRect, { x, y, w: 6.05, h: 1.38, rectRadius: 0.06,
      fill: { color: PAPER }, line: { color: "E3E9F1" } });
    K.dot(s, p, x + 0.25, y + 0.24, c, 0.17);
    s.addText(t, { x: x + 0.52, y: y + 0.12, w: 2.2, h: 0.34, margin: 0,
      fontFace: H_FONT, fontSize: 16, bold: true, color: INK });
    s.addText(q, { x: x + 2.7, y: y + 0.16, w: 3.1, h: 0.3, align: "right", margin: 0,
      fontFace: B, fontSize: 11.5, italic: true, color: c });
    s.addText(ms.join("\n"), { x: x + 0.52, y: y + 0.52, w: 5.3, h: 0.76, margin: 0, valign: "top",
      fontFace: M, fontSize: 9.5, color: MUTED, lineSpacing: 13 });
  });

  // one trace, four readers
  s.addShape(p.ShapeType.roundRect, { x: MX, y: 5.1, w: W - 2 * MX, h: 1.35, rectRadius: 0.06,
    fill: { color: "F0EBFA" }, line: { color: "F0EBFA" } });
  s.addText("One trace, four readers", { x: MX + 0.3, y: 5.24, w: 3, h: 0.3, margin: 0,
    fontFace: B, fontSize: 12.5, bold: true, color: L.obs.c });
  const readers = [["Engineering", "a debugging artefact"], ["AI team", "a quality signal"],
    ["Finance", "a cost line"], ["The DPO", "an audit record"]];
  readers.forEach(([who, what], j) => {
    const x = MX + 0.3 + j * 3.05;
    s.addText(who, { x, y: 5.62, w: 2.9, h: 0.28, margin: 0,
      fontFace: B, fontSize: 11.5, bold: true, color: INK });
    s.addText(what, { x, y: 5.9, w: 2.9, h: 0.28, margin: 0,
      fontFace: B, fontSize: 10.5, color: INK2 });
  });
  K.foot(s, i);
  s.addNotes("Redaction happens at the collector, not in each service — prompts can carry health data and a trace backend is not an approved store for it. Doing it at the collector means the guarantee holds for every service that ever exports through it.");
}

/* ═══ 14 · SLOs ══════════════════════════════════════════════════════════ */
{
  const s = K.light(p); const i = n();
  K.head(s, p, "Promises", "SLOs when the output is not deterministic",
    "You cannot promise any individual answer is right. You can promise a rate, measure it, and put an error budget behind it.");

  const slos = [
    ["Gateway availability", "99.9%", "30d", "43.2 min", "44546A"],
    ["Agent turn latency", "p95 < 4.0s", "30d", "43.2 min", "44546A"],
    ["Groundedness", "≥ 97% grounded", "7d", "302.4 min", L.gov.c],
    ["Guardrail coverage", "100% of turns", "30d", "0 min", L.gov.c],
  ];
  ["Objective", "Target", "Window", "Error budget"].forEach((h, j) => {
    s.addText(h.toUpperCase(), { x: MX + [0, 4.3, 6.6, 8.7][j], y: 2.0, w: 3, h: 0.26, margin: 0,
      fontFace: B, fontSize: 9.5, bold: true, charSpacing: 1.4, color: MUTED });
  });
  slos.forEach(([t, tgt, win, bud, c], j) => {
    const y = 2.4 + j * 0.62;
    s.addShape(p.ShapeType.rect, { x: MX, y: y - 0.08, w: W - 2 * MX, h: 0.01,
      fill: { color: "E3E9F1" }, line: { color: "E3E9F1" } });
    K.dot(s, p, MX, y + 0.12, c, 0.14);
    s.addText(t, { x: MX + 0.26, y, w: 3.9, h: 0.34, margin: 0,
      fontFace: B, fontSize: 13, bold: true, color: INK });
    s.addText(tgt, { x: MX + 4.3, y, w: 2.2, h: 0.34, margin: 0, fontFace: M, fontSize: 12, color: c });
    s.addText(win, { x: MX + 6.6, y, w: 1.9, h: 0.34, margin: 0, fontFace: M, fontSize: 12, color: INK2 });
    s.addText(bud, { x: MX + 8.7, y, w: 2.3, h: 0.34, margin: 0, fontFace: M, fontSize: 12, color: INK2 });
  });

  const alerts = [["page", "14.4× burn over 1 hour", "2% of the 30-day budget gone within the hour. Somebody wakes up.", "B3121F"],
    ["ticket", "6× burn over 6 hours", "Degradation that will exhaust the budget this week. A single threshold catches one of these and misses the other.", "A85B00"]];
  alerts.forEach(([sev, cond, why, c], j) => {
    const x = MX + j * 6.35;
    s.addShape(p.ShapeType.roundRect, { x, y: 5.15, w: 6.05, h: 1.35, rectRadius: 0.06,
      fill: { color: GROUND }, line: { color: "E3E9F1" } });
    s.addText(sev.toUpperCase(), { x: x + 0.25, y: 5.3, w: 1.0, h: 0.28, margin: 0,
      fontFace: M, fontSize: 10, bold: true, color: c });
    s.addText(cond, { x: x + 1.3, y: 5.3, w: 4.5, h: 0.28, margin: 0,
      fontFace: B, fontSize: 12.5, bold: true, color: INK });
    s.addText(why, { x: x + 0.25, y: 5.64, w: 5.55, h: 0.72, margin: 0, valign: "top",
      fontFace: B, fontSize: 10.5, color: INK2, lineSpacing: 14 });
  });
  K.foot(s, i);
  s.addNotes("An SLO without an error budget is a wish. Guardrail coverage is the one hard objective with a zero budget, and it is achievable because it is a property of the code path rather than of the model.");
}

/* ═══ 15 · GOVERNANCE ════════════════════════════════════════════════════ */
{
  const s = K.tinted(p); const i = n();
  K.head(s, p, "Governance", "Four articles, four code paths",
    "A control that exists only in a document drifts. Each of these is a runtime object the service exposes.");

  const arts = [
    ["Art. 50", "Transparency", "Every reply carries an AI disclosure and a non-advice notice.", "guardrails.ensure_disclaimer"],
    ["Art. 12", "Record-keeping", "Append-only audit table, 7-year retention in the archive tier.", "telemetry.record_audit"],
    ["Art. 14", "Human oversight", "Side-effecting tools blocked behind an explicit human approval.", "orchestrator HITL gate"],
    ["Art. 15", "Accuracy & robustness", "Groundedness scorer plus a CI eval gate at 0.95.", "evals.suite.THRESHOLDS"],
  ];
  arts.forEach(([a, t, c, impl], j) => {
    const y = 1.95 + j * 0.9;
    s.addShape(p.ShapeType.roundRect, { x: MX, y, w: 7.5, h: 0.78, rectRadius: 0.05,
      fill: { color: "E8F4EC" }, line: { color: "E8F4EC" } });
    s.addText(a, { x: MX + 0.25, y: y + 0.08, w: 0.95, h: 0.3, margin: 0,
      fontFace: M, fontSize: 12, bold: true, color: L.gov.c });
    s.addText(t, { x: MX + 1.3, y: y + 0.08, w: 2.6, h: 0.3, margin: 0,
      fontFace: B, fontSize: 12.5, bold: true, color: INK });
    s.addText(impl, { x: MX + 3.9, y: y + 0.1, w: 3.4, h: 0.28, align: "right", margin: 0,
      fontFace: M, fontSize: 9, color: L.gov.c });
    s.addText(c, { x: MX + 0.25, y: y + 0.42, w: 7.0, h: 0.3, margin: 0,
      fontFace: B, fontSize: 10.5, color: INK2 });
  });

  s.addShape(p.ShapeType.roundRect, { x: 8.4, y: 1.95, w: 4.3, h: 3.58, rectRadius: 0.06,
    fill: { color: PAPER }, line: { color: "E3E9F1" } });
  s.addText("Risk tier", { x: 8.68, y: 2.12, w: 3.7, h: 0.28, margin: 0,
    fontFace: B, fontSize: 10, bold: true, charSpacing: 1.4, color: MUTED });
  s.addText("Limited risk", { x: 8.68, y: 2.42, w: 3.7, h: 0.5, margin: 0,
    fontFace: H_FONT, fontSize: 25, bold: true, color: L.gov.c });
  s.addText("A customer-facing informational assistant. Not a medical device and not diagnostic, because every clinical judgement is routed to a registered pharmacist — which keeps it out of Annex III.", {
    x: 8.68, y: 2.98, w: 3.75, h: 1.35, margin: 0, valign: "top",
    fontFace: B, fontSize: 10.5, color: INK2, lineSpacing: 14 });
  s.addText("The classification is a decision, made on the record. The moment the agent could give a dose, it is a different tier with a conformity assessment attached.", {
    x: 8.68, y: 4.3, w: 3.75, h: 1.1, margin: 0, valign: "top",
    fontFace: B, fontSize: 10.5, italic: true, color: INK, lineSpacing: 14 });

  s.addText("GDPR: Art. 9 special-category data · basis 6(1)(b) + 9(2)(h) · EU-only residency enforced twice, by a Terraform variable validation and an OPA policy · redaction before the model call · transcripts 90 days, audit 7 years.", {
    x: MX, y: 5.75, w: W - 2 * MX, h: 0.7, margin: 0, valign: "top",
    fontFace: B, fontSize: 11, color: INK2, lineSpacing: 15 });
  K.foot(s, i);
  s.addNotes("Human-in-the-loop placement is the design decision: gate the side effect, not the reasoning. A rubber-stamp queue at 400 approvals an hour satisfies Art. 14 on paper and nothing in practice.");
}

/* ═══ 16 · FINOPS ════════════════════════════════════════════════════════ */
{
  const s = K.light(p); const i = n();
  K.head(s, p, "Unit economics", "Cost per turn is the number",
    "Everything else is a proxy for it. Four levers, in the order I would pull them.");

  s.addChart(p.ChartType.bar, [{
    name: "Cost per 1,000 turns (USD)",
    labels: ["No levers", "+ tier routing", "+ semantic cache", "+ bounded context"],
    values: [28.0, 12.4, 8.6, 7.1],
  }], {
    x: MX, y: 1.95, w: 6.3, h: 3.3, barDir: "col",
    chartColors: [L.gateway.c],
    showTitle: true, title: "Illustrative — same traffic mix, levers applied in order",
    titleFontSize: 11.5, titleColor: MUTED, titleFontFace: B,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '"$"0.0',
    dataLabelFontSize: 11, dataLabelFontFace: B, dataLabelColor: INK,
    catAxisLabelColor: MUTED, valAxisLabelColor: MUTED,
    catAxisLabelFontSize: 10, valAxisLabelFontSize: 9.5,
    catAxisLabelFontFace: B, valAxisLabelFontFace: B,
    valAxisMinVal: 0, valAxisMaxVal: 30, valAxisMajorUnit: 10,
    valGridLine: { color: "EDF1F6", size: 1 }, catGridLine: { style: "none" },
    showLegend: false,
  });

  const levers = [
    ["Tier routing", "A greeting on the mini tier is ~16× cheaper per token than the flagship. The classifier that decides costs $0.0001."],
    ["Semantic cache", "“Where is my order”, “order status?” and “has it shipped” are one question. 25-35% hit rates are ordinary in support."],
    ["Bounded context", "A rolling window stops prompt growth across a long session — the quiet cause of most cost regressions."],
    ["Hard ceilings", "Per request, per session, per tenant per day. A runaway loop stops itself; the gateway is the backstop."],
  ];
  levers.forEach(([t, body], j) => {
    const y = 1.95 + j * 1.1;
    K.num(s, p, 7.2, y + 0.02, j + 1, L.gateway.c, 0.32);
    s.addText(t, { x: 7.65, y, w: 4.9, h: 0.3, margin: 0,
      fontFace: B, fontSize: 12.5, bold: true, color: INK });
    s.addText(body, { x: 7.65, y: y + 0.32, w: 5.0, h: 0.72, margin: 0, valign: "top",
      fontFace: B, fontSize: 10.5, color: INK2, lineSpacing: 14 });
  });

  K.why(s, MX, 5.55, W - 2 * MX,
    "Measured per resolved conversation, not per call — an agent that is cheap per call and never resolves anything is expensive. The reflex to resist in a cost incident is “move everyone to a cheaper model”: that trades a cost problem you can see for a quality problem you cannot.");
  K.foot(s, i);
  s.addNotes("Budgets are enforced at the gateway before the provider is called, and mirrored in the app so a runaway loop stops itself. When the budget is gone the agent degrades to a human handover rather than an error page — a deliberate product decision about who absorbs the failure.");
}

/* ═══ 17 · NOT BUILT ═════════════════════════════════════════════════════ */
{
  const s = K.tinted(p); const i = n();
  K.head(s, p, "Scope", "What is deliberately not here",
    "Each is a “not yet” with a stated trigger, not a “never”. Knowing what you are not building is most of platform product management.");

  const nots = [
    ["Multi-agent orchestration framework", "Two agents that need to coordinate usually mean one workflow was decomposed wrong. Earn it with a real case."],
    ["Fine-tuning pipeline", "Retrieval and prompting exhaust their headroom long before fine-tuning is the cheapest next move — and it brings a permanent lifecycle with it."],
    ["Self-hosted models on GPUs", "The economics only work at a volume Redcare does not have yet, and it moves a large operational burden onto a small team."],
    ["A bespoke vector database", "AI Search covers hybrid retrieval and is already inside the security perimeter."],
    ["Kubernetes", "Container Apps covers the requirements. AKS is a second product to operate, and the exit stays cheap because the unit of deployment is a plain OCI image."],
    ["Agent-to-agent protocols", "The standards are still moving. Committing early is expensive to undo."],
  ];
  nots.forEach(([t, body], j) => {
    const x = MX + (j % 2) * 6.35;
    const y = 2.0 + Math.floor(j / 2) * 1.5;
    s.addShape(p.ShapeType.roundRect, { x, y, w: 6.05, h: 1.3, rectRadius: 0.06,
      fill: { color: PAPER }, line: { color: "E3E9F1" } });
    s.addText(t, { x: x + 0.25, y: y + 0.14, w: 5.5, h: 0.32, margin: 0,
      fontFace: B, fontSize: 12.5, bold: true, color: INK });
    s.addText(body, { x: x + 0.25, y: y + 0.5, w: 5.55, h: 0.7, margin: 0, valign: "top",
      fontFace: B, fontSize: 10.5, color: INK2, lineSpacing: 14 });
  });
  K.foot(s, i);
  s.addNotes("Being able to say why you are not building something, in one sentence, is a stronger signal of product judgement than anything on the roadmap.");
}

/* ═══ 18 · RECALL ════════════════════════════════════════════════════════ */
{
  const s = K.dark(p); const i = n();
  s.addText("THE SIXTY-SECOND VERSION", {
    x: MX, y: 0.75, w: 9, h: 0.3, margin: 0,
    fontFace: B, fontSize: 11, bold: true, charSpacing: 2.4, color: RED });
  s.addText("If you remember eight things", {
    x: MX, y: 1.08, w: 11, h: 0.6, margin: 0,
    fontFace: H_FONT, fontSize: 30, bold: true, color: "FFFFFF" });

  const recall = [
    ["gateway", "The gateway is the whole thesis", "It is the only path to a model, which is what makes budgets, entitlement, failover, caching, cost attribution and audit enforceable rather than advisory."],
    ["agent", "Ordering is the argument", "Budget before guardrails. Guardrails before the model. Approval before the side effect."],
    ["gov", "Gate the side effect, not the reasoning", "Read and draft freely; stop before changing a system of record. Art. 14 as a code path."],
    ["gov", "Evals are the release gate", "Tests prove the plumbing, evals prove the behaviour. Safety thresholded at 1.00."],
    ["obs", "Four signal families, not one", "Up, behaving, right, affordable. A platform that ships only RED is trusted until the first bad answer."],
    ["data", "Region before provider", "Failover keeps behaviour identical first. A provider switch changes behaviour and needs an eval run."],
    ["edge", "No public ingress, no unmonitored egress", "And a private DNS zone for every private endpoint, or the traffic quietly leaves the VNet."],
    ["agent", "Cost per resolved conversation", "Not per call. An agent that is cheap per call and never resolves anything is expensive."],
  ];
  recall.forEach(([layer, t, body], j) => {
    const x = MX + (j % 2) * 6.35;
    const y = 2.0 + Math.floor(j / 2) * 1.22;
    K.dot(s, p, x, y + 0.09, L[layer].c, 0.16);
    s.addText(t, { x: x + 0.28, y, w: 5.7, h: 0.32, margin: 0,
      fontFace: B, fontSize: 12.5, bold: true, color: "FFFFFF" });
    s.addText(body, { x: x + 0.28, y: y + 0.34, w: 5.75, h: 0.8, margin: 0, valign: "top",
      fontFace: B, fontSize: 10.5, color: "AEBCCD", lineSpacing: 14 });
  });
  K.foot(s, i, true);
  s.addNotes("Close by offering the console: ten minutes clicking through it does more than any slide, because they can see the guardrail refuse and the approval gate hold.");
}

p.writeFile({ fileName: "Redcare-Architecture-Visual.pptx" })
  .then(f => console.log("wrote", f, "·", pg + 1, "slides"));
