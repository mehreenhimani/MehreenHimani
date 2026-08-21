const pptxgen = require("pptxgenjs");

// ── palette: informed by Redcare's red on a deep technical ground ───────────────
const INK    = "0F131A";   // dominant dark
const PANEL  = "1B2230";   // dark card
const RULE   = "2B3547";
const PAPER  = "FFFFFF";
const MIST   = "F1F4F8";   // light card
const RED    = "E2001A";   // Redcare accent
const TEAL   = "0F9BA8";
const AMBER  = "B77400";
const GREEN  = "1E7B45";
const TXT    = "16202E";
const DIM    = "5C6B80";
const DIMD   = "9BAABF";   // dim on dark

const H  = "Cambria";      // safe-list serif for headers
const B  = "Calibri";      // safe-list sans for body
const M  = "Courier New";  // mono

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";              // 13.3 x 7.5
pres.author = "Mehreen Himani";
pres.title  = "Redcare Agentic AI Platform";

const W = 13.3, HT = 7.5, MX = 0.65;

// ── helpers ────────────────────────────────────────────────────────────────────
const shadow = () => ({ type: "outer", angle: 90, blur: 10, offset: 2, color: "000000", opacity: 0.14 });

function darkSlide() {
  const s = pres.addSlide();
  s.background = { color: INK };
  return s;
}
function lightSlide() {
  const s = pres.addSlide();
  s.background = { color: PAPER };
  return s;
}

// section eyebrow + title, shared by every content slide
function head(s, eyebrow, title, dark = false, sub = null) {
  s.addText(eyebrow.toUpperCase(), {
    x: MX, y: 0.42, w: 8, h: 0.28, fontFace: B, fontSize: 11, bold: true,
    charSpacing: 2.4, color: RED, margin: 0,
  });
  // At 33pt Cambria bold about 34 characters fit the 10.8" title box — measured
  // from the rendered deck, not guessed. A longer title wraps into the eyebrow
  // above and the subtitle below, so scale it rather than let it overflow.
  const titleSize = title.length <= 34 ? 33 : title.length <= 48 ? 28 : 23;
  s.addText(title, {
    x: MX, y: 0.72, w: W - 2 * MX - 1.2, h: 0.72, fontFace: H, fontSize: titleSize, bold: true,
    color: dark ? PAPER : TXT, margin: 0, valign: "top",
  });
  if (sub) {
    s.addText(sub, {
      x: MX, y: 1.44, w: W - 2 * MX - 0.2, h: 0.4, fontFace: B, fontSize: 13.5,
      color: dark ? DIMD : DIM, margin: 0, italic: true, valign: "top",
    });
  }
}

// the repeated visual motif: a numbered / lettered disc
function disc(s, x, y, label, fill, textColor = "FFFFFF", d = 0.46) {
  s.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill } });
  s.addText(label, {
    x, y, w: d, h: d, align: "center", valign: "middle", margin: 0,
    fontFace: B, fontSize: d > 0.5 ? 15 : 13, bold: true, color: textColor,
  });
}

function card(s, o) {
  s.addShape(pres.ShapeType.roundRect, {
    x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.07,
    fill: { color: o.fill || MIST }, line: { color: o.line || (o.fill === PANEL ? RULE : "E1E7EF"), width: 1 },
    shadow: o.flat ? undefined : shadow(),
  });
}

// slide footer: page number only, no bars
function foot(s, n, dark = false) {
  s.addText(String(n), {
    x: W - MX - 0.6, y: HT - 0.52, w: 0.6, h: 0.3, align: "right", margin: 0,
    fontFace: B, fontSize: 10, color: dark ? "4A5871" : "AAB6C6",
  });
}

let page = 0;
const next = () => ++page;

// ═══════════════════════════════════════════════════════════════════════════════
// 1 · TITLE
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = darkSlide();
  // motif: a column of discs marking the six lifecycle phases
  s.addShape(pres.ShapeType.line, {
    x: 11.8, y: 1.85, w: 0, h: 4.0, line: { color: RULE, width: 1 },
  });
  ["1", "2", "3", "4", "5", "6"].forEach((n, i) =>
    disc(s, 11.55, 1.35 + i * 0.78, n, i === 0 ? RED : PANEL, i === 0 ? "FFFFFF" : DIMD, 0.5));

  s.addText("REDCARE PHARMACY", {
    x: MX, y: 1.5, w: 8, h: 0.3, fontFace: B, fontSize: 12, bold: true,
    charSpacing: 3, color: RED, margin: 0,
  });
  s.addText("The Agentic AI Platform", {
    x: MX, y: 1.95, w: 10, h: 1.0, fontFace: H, fontSize: 50, bold: true, color: PAPER, margin: 0,
  });
  s.addText("Every tool in the stack, and the job it actually does —\nfrom an empty repository to a governed production system.", {
    x: MX, y: 3.05, w: 9.2, h: 0.9, fontFace: B, fontSize: 17, color: DIMD, margin: 0, lineSpacing: 26,
  });

  const phases = ["Build", "Prove", "Ship", "Run", "Govern", "Pay"];
  phases.forEach((p, i) => {
    s.addText(p, {
      x: MX + i * 1.62, y: 4.35, w: 1.5, h: 0.34, align: "center", valign: "middle", margin: 0,
      fontFace: B, fontSize: 13, bold: true, color: i === 0 ? PAPER : DIMD,
    });
    if (i < phases.length - 1)
      s.addText("→", { x: MX + i * 1.62 + 1.42, y: 4.35, w: 0.28, h: 0.34, align: "center",
        valign: "middle", margin: 0, fontFace: B, fontSize: 13, color: RULE });
  });
  s.addShape(pres.ShapeType.line, { x: MX, y: 4.28, w: 9.3, h: 0, line: { color: RULE, width: 1 } });

  s.addText([
    { text: "Azure Cloud", options: { bold: true, color: PAPER } },
    { text: "  ·  LiteLLM / AI Gateway  ·  Terraform  ·  GitHub Actions  ·  OpenTelemetry  ·  MLOps & LLMOps", options: { color: DIMD } },
  ], { x: MX, y: 5.9, w: 10.4, h: 0.34, fontFace: B, fontSize: 13, margin: 0 });
  s.addText("Mehreen Himani  ·  Technical round", {
    x: MX, y: 6.32, w: 8, h: 0.3, fontFace: B, fontSize: 12, color: DIM, margin: 0,
  });
  s.addNotes("Frame: I built a working reference implementation rather than a slide deck about one. Everything here runs — the agent, the gateway routing, the guardrails, the eval gate, the Terraform. This deck walks the production lifecycle and names what each tool is for.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 2 · THE PROBLEM
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = lightSlide(); const n = next();
  head(s, "Why a platform", "Six months of AI with no platform",
    false, "Every team should use AI, and nobody built a place to do it. Each symptom below is a platform problem wearing a model problem's clothes.");

  const rows = [
    ["Provider keys in four repos", "No central place to get model access"],
    ["An invoice nobody can explain", "No per-team cost attribution"],
    ["One team's spike throttles everyone", "No per-tenant rate limits"],
    ["A hallucination in a complaint file", "No groundedness measurement"],
    ["“Which prompt produced that?” — unanswerable", "Prompts as string literals"],
    ["A regional outage takes every feature down", "One deployment, no failover"],
  ];
  rows.forEach(([sym, cause], i) => {
    const x = MX + (i % 2) * 6.15, y = 2.05 + Math.floor(i / 2) * 1.28;
    card(s, { x, y, w: 5.85, h: 1.06 });
    disc(s, x + 0.24, y + 0.3, "!", RED, "FFFFFF", 0.4);
    s.addText(sym, { x: x + 0.78, y: y + 0.16, w: 4.9, h: 0.36, margin: 0,
      fontFace: B, fontSize: 14, bold: true, color: TXT });
    s.addText(cause, { x: x + 0.78, y: y + 0.55, w: 4.9, h: 0.34, margin: 0,
      fontFace: B, fontSize: 12, color: DIM });
  });

  s.addText("None of these is a model problem.", {
    x: MX, y: 6.15, w: 12, h: 0.4, margin: 0, fontFace: H, fontSize: 20, bold: true, color: RED,
  });
  foot(s, n);
  s.addNotes("The point to land: AI sprawl is not caused by bad engineers. It is caused by the absence of a place where these concerns can be solved once. That is what the platform is.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 3 · THE THESIS
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = darkSlide(); const n = next();
  s.addText("THE PRODUCT PROMISE", {
    x: MX, y: 1.15, w: 8, h: 0.3, fontFace: B, fontSize: 11, bold: true, charSpacing: 2.4,
    color: RED, margin: 0,
  });
  s.addText([
    { text: "Any team at Redcare can put a ", options: { color: PAPER } },
    { text: "safe, observed, affordable", options: { color: RED, bold: true } },
    { text: " AI agent in front of customers within a week — and the company can prove afterwards ", options: { color: PAPER } },
    { text: "what it did and what it cost.", options: { color: RED, bold: true } },
  ], { x: MX, y: 1.58, w: 11.9, h: 2.5, fontFace: H, fontSize: 30, bold: true, margin: 0, lineSpacing: 43, valign: "top" });

  const claims = [
    ["Within a week", "engineering's promise", "speed", TEAL],
    ["Safe and observed", "security & compliance's promise", "trust", RED],
    ["Prove what it cost", "the CFO's promise", "economics", AMBER],
  ];
  claims.forEach(([t, who, tag, c], i) => {
    const x = MX + i * 4.05;
    card(s, { x, y: 4.42, w: 3.75, h: 1.72, fill: PANEL });
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.28, y: 4.70, w: 0.16, h: 0.16, fill: { color: c }, line: { color: c } });
    s.addText(t, { x: x + 0.58, y: 4.61, w: 3.0, h: 0.36, margin: 0, fontFace: B, fontSize: 15, bold: true, color: PAPER });
    s.addText(who, { x: x + 0.28, y: 5.09, w: 3.2, h: 0.34, margin: 0, fontFace: B, fontSize: 12, color: DIMD });
    s.addText(tag.toUpperCase(), { x: x + 0.28, y: 5.53, w: 3.2, h: 0.3, margin: 0,
      fontFace: B, fontSize: 10, bold: true, charSpacing: 2, color: c });
  });

  s.addText("A vision that serves only one of the three gets defunded by the other two.", {
    x: MX, y: 6.48, w: 11.9, h: 0.36, margin: 0, fontFace: B, fontSize: 13, italic: true, color: DIMD,
  });
  foot(s, n, true);
  s.addNotes("Three clauses, three audiences. Deliberately says nothing about a model, a framework or a vendor — those change, the promise should not.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 4 · THE SYSTEM AT A GLANCE
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = lightSlide(); const n = next();
  head(s, "Architecture", "One customer question, end to end", false,
    "“Can I take ibuprofen with warfarin?” — every hop it makes, and who is accountable for each.");

  // left: the seven stages inside the agent
  card(s, { x: MX, y: 2.05, w: 5.5, h: 4.42, fill: MIST, flat: true });
  s.addText("Container App · carecopilot-agent", {
    x: MX + 0.3, y: 2.2, w: 5.0, h: 0.3, margin: 0, fontFace: M, fontSize: 10, bold: true, color: DIM });
  const stages = [
    ["classify", "cheap model scores the turn", TEAL],
    ["route", "entitlement → tier → health", TEAL],
    ["budget", "tenant + session ceilings", AMBER],
    ["guard in", "injection · scope · PII", RED],
    ["plan / act", "LLM ⇄ tools, bounded loop", TXT],
    ["guard out", "secrets · grounding · policy", RED],
    ["account", "spend · metrics · audit", AMBER],
  ];
  stages.forEach(([t, d, c], i) => {
    const y = 2.62 + i * 0.55;
    disc(s, MX + 0.3, y, String(i + 1), c, "FFFFFF", 0.34);
    s.addText(t, { x: MX + 0.76, y: y - 0.02, w: 1.5, h: 0.34, margin: 0,
      fontFace: M, fontSize: 12, bold: true, color: TXT, valign: "middle" });
    s.addText(d, { x: MX + 2.3, y: y - 0.02, w: 3.05, h: 0.34, margin: 0,
      fontFace: B, fontSize: 11, color: DIM, valign: "middle" });
  });

  // right: the three things every turn touches
  const right = [
    ["AI Gateway", "LiteLLM · the only path to a model",
     "virtual key · entitlement · budget · failover · cache · cost line", RED],
    ["Systems of record", "SAP-OMS · WMS · ABDA · AI Search · ServiceNow",
     "each tool declares what it touches and whether it mutates state", TEAL],
    ["Telemetry", "OTel Collector → Azure Monitor · Grafana · audit table",
     "one trace: debug artefact, quality signal, cost line, audit record", AMBER],
  ];
  right.forEach(([t, sub, d, c], i) => {
    const y = 2.05 + i * 1.52;
    card(s, { x: 6.45, y, w: 6.2, h: 1.38 });
    s.addShape(pres.ShapeType.ellipse, { x: 6.75, y: y + 0.22, w: 0.17, h: 0.17,
      fill: { color: c }, line: { color: c } });
    s.addText(t, { x: 7.02, y: y + 0.14, w: 5.4, h: 0.32, margin: 0,
      fontFace: B, fontSize: 15, bold: true, color: TXT });
    s.addText(sub, { x: 7.02, y: y + 0.5, w: 5.4, h: 0.3, margin: 0,
      fontFace: M, fontSize: 10, color: c });
    s.addText(d, { x: 7.02, y: y + 0.83, w: 5.4, h: 0.44, margin: 0,
      fontFace: B, fontSize: 11.5, color: DIM });
  });
  foot(s, n);
  s.addNotes("The ordering is the argument. Budget before guardrails, because a tenant over budget should not cost us CPU. Guardrails before the model, because an output-only guardrail already lost. Approval before the side effect, not after the answer.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 5 · LIFECYCLE MAP (divider)
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = darkSlide(); const n = next();
  head(s, "The rest of this deck", "The lifecycle, and who owns each phase", true);

  const phases = [
    ["1", "Build", "GitHub · golden path · LiteLLM", "make it possible", TEAL],
    ["2", "Prove", "Evals · guardrails", "make it trustworthy", RED],
    ["3", "Ship", "Terraform · GitHub Actions · Container Apps", "make it repeatable", TEAL],
    ["4", "Run", "OpenTelemetry · Azure Monitor · Grafana · SLOs", "make it visible", AMBER],
    ["5", "Govern", "EU AI Act · HITL · policy as code · Entra ID", "make it defensible", RED],
    ["6", "Pay", "FinOps · routing · caching · budgets", "make it affordable", AMBER],
  ];
  phases.forEach(([num, t, tools, why, c], i) => {
    const x = MX + (i % 3) * 4.05, y = 2.15 + Math.floor(i / 3) * 2.25;
    card(s, { x, y, w: 3.75, h: 2.02, fill: PANEL });
    disc(s, x + 0.28, y + 0.26, num, c, "FFFFFF", 0.44);
    s.addText(t, { x: x + 0.86, y: y + 0.28, w: 2.6, h: 0.4, margin: 0,
      fontFace: H, fontSize: 21, bold: true, color: PAPER, valign: "middle" });
    s.addText(why, { x: x + 0.28, y: y + 0.82, w: 3.2, h: 0.3, margin: 0,
      fontFace: B, fontSize: 12, italic: true, color: c });
    s.addText(tools, { x: x + 0.28, y: y + 1.18, w: 3.2, h: 0.72, margin: 0,
      fontFace: M, fontSize: 10.5, color: DIMD, lineSpacing: 15 });
  });
  foot(s, n, true);
  s.addNotes("Six phases. Each of the next slides answers one question: what tool, doing what job, and what breaks without it.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 6 · BUILD — the golden path
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = lightSlide(); const n = next();
  head(s, "1 · Build", "The paved road", false,
    "GitHub as a platform, not a repo host. Adoption is won on time to first token and lost on friction — target under an hour.");

  const gets = [
    "Gateway client + a budgeted virtual key",
    "Input and output guardrail pipelines",
    "OTel tracing, four metric families, audit log",
    "Approval flow for side-effecting tools",
    "CI with the eval gate already wired",
    "A ~20-line Terraform stanza to onboard",
  ];
  const decides = [
    "The tools — and which of them mutate state",
    "The golden set — 15-30 cases, failures first",
    "The EU AI Act risk tier, and the reasoning",
    "The escalation path when it hands over",
    "The daily budget, and who is told at the cap",
  ];

  card(s, { x: MX, y: 2.05, w: 5.85, h: 3.5 });
  s.addText("Inherited — nobody writes it twice", { x: MX + 0.32, y: 2.24, w: 5.2, h: 0.34, margin: 0,
    fontFace: B, fontSize: 15, bold: true, color: GREEN });
  s.addText(gets.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < gets.length - 1 } })), {
    x: MX + 0.32, y: 2.68, w: 5.2, h: 2.6, margin: 0, valign: "top",
    fontFace: B, fontSize: 12.5, color: TXT, paraSpaceAfter: 8 });

  card(s, { x: 6.8, y: 2.05, w: 5.85, h: 3.5 });
  s.addText("Still the team's decision — deliberately", { x: 7.12, y: 2.24, w: 5.2, h: 0.34, margin: 0,
    fontFace: B, fontSize: 15, bold: true, color: RED });
  s.addText(decides.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < decides.length - 1 } })), {
    x: 7.12, y: 2.68, w: 5.2, h: 2.6, margin: 0, valign: "top",
    fontFace: B, fontSize: 12.5, color: TXT, paraSpaceAfter: 8 });

  card(s, { x: MX, y: 5.78, w: 12, h: 0.86, fill: MIST, flat: true });
  s.addText([
    { text: "Why not automate the right-hand column?  ", options: { bold: true, color: TXT } },
    { text: "A template that guesses the risk tier and the tool surface produces a compliant-looking agent nobody actually signed off.", options: { color: DIM } },
  ], { x: MX + 0.32, y: 5.95, w: 11.4, h: 0.55, margin: 0, fontFace: B, fontSize: 12.5 });
  foot(s, n);
  s.addNotes("The platform-team job in onboarding is one review with a one-day SLA, not a project. Onboarding the tenth team must cost what the second cost — that is the test of whether this is a platform.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 7 · BUILD — the gateway
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = darkSlide(); const n = next();
  head(s, "1 · Build", "LiteLLM: the choke point", true,
    "One OpenAI-compatible endpoint in front of every model any team may use — and the thing that makes every other guarantee enforceable.");

  const owns = [
    ["Virtual keys", "one per team — the unit of governance"],
    ["Entitlement", "which team may call which model"],
    ["Rate limits", "rpm and tpm, so one team cannot starve another"],
    ["Budgets", "hard caps enforced before the provider is called"],
    ["Failover", "cross-region, then cross-provider"],
    ["Semantic cache", "25-35% of support traffic answered free"],
    ["Cost attribution", "every call carries a cost centre"],
    ["Guardrail hooks", "PII masking and content safety for everyone"],
  ];
  owns.forEach(([t, d], i) => {
    const x = MX + (i % 2) * 6.15, y = 2.15 + Math.floor(i / 2) * 0.86;
    s.addShape(pres.ShapeType.ellipse, { x, y: y + 0.13, w: 0.14, h: 0.14, fill: { color: RED }, line: { color: RED } });
    s.addText(t, { x: x + 0.32, y, w: 2.15, h: 0.34, margin: 0, fontFace: B, fontSize: 14, bold: true, color: PAPER });
    s.addText(d, { x: x + 2.5, y: y + 0.03, w: 3.4, h: 0.5, margin: 0, valign: "top",
      fontFace: B, fontSize: 11.5, color: DIMD, lineSpacing: 15 });
  });

  card(s, { x: MX, y: 5.85, w: 12, h: 0.95, fill: PANEL });
  s.addText([
    { text: "Bypassing it is not a policy — it is a network property.  ", options: { bold: true, color: PAPER } },
    { text: "The agent subnet denies internet egress and the agent holds no provider key. It has exactly one route to a model.", options: { color: DIMD } },
  ], { x: MX + 0.32, y: 6.06, w: 11.4, h: 0.55, margin: 0, fontFace: B, fontSize: 12.5 });
  foot(s, n, true);
  s.addNotes("Build/buy: LiteLLM because it is open source (no lock-in on the most load-bearing component), genuinely multi-provider, has virtual keys and spend tracking built in, and self-hosts inside our VNet — which for Art. 9 health data is a requirement, not a preference.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 8 · BUILD — routing
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = lightSlide(); const n = next();
  head(s, "1 · Build", "Routing: three stages, always explained", false,
    "Governance first, cost second, reliability third — and the router returns the reason.");

  const stages = [
    ["Entitlement", "Is this key allowed this model?",
     "A governance question, so it goes first. No performance consideration may override it.", RED],
    ["Complexity tier", "Cheapest model that can do the job",
     "A classifier scores the turn trivial / standard / complex. Mini tier is ~16× cheaper per token; the classifier costs $0.0001.", TEAL],
    ["Health", "Is the chosen deployment cooling down?",
     "Same model, second EU region first. Different provider last — a provider switch changes behaviour, and behaviour changes need an eval run.", AMBER],
  ];
  stages.forEach(([t, q, d, c], i) => {
    const x = MX + i * 4.15;
    card(s, { x, y: 2.05, w: 3.85, h: 2.75 });
    disc(s, x + 0.3, y = 2.28, String(i + 1), c, "FFFFFF", 0.44);
    s.addText(t, { x: x + 0.88, y: 2.3, w: 2.8, h: 0.4, margin: 0,
      fontFace: B, fontSize: 16, bold: true, color: TXT, valign: "middle" });
    s.addText(q, { x: x + 0.3, y: 2.86, w: 3.25, h: 0.34, margin: 0,
      fontFace: B, fontSize: 12, italic: true, color: c });
    s.addText(d, { x: x + 0.3, y: 3.26, w: 3.25, h: 1.3, margin: 0,
      fontFace: B, fontSize: 11.5, color: DIM, lineSpacing: 16 });
    if (i < 2) s.addText("→", { x: x + 3.86, y: 3.1, w: 0.3, h: 0.4, align: "center",
      margin: 0, fontFace: B, fontSize: 20, color: "C6D0DC" });
  });

  card(s, { x: MX, y: 5.08, w: 12, h: 1.55, fill: INK });
  s.addText("A routing decision the trace can explain", { x: MX + 0.35, y: 5.24, w: 6, h: 0.3, margin: 0,
    fontFace: B, fontSize: 12, bold: true, color: DIMD });
  s.addText([
    { text: "complexity  ", options: { color: DIMD } },
    { text: "trivial", options: { color: TEAL, bold: true } },
    { text: "  —  greeting with no information need\n", options: { color: DIMD } },
    { text: "selected    ", options: { color: DIMD } },
    { text: "carecopilot-fast", options: { color: PAPER, bold: true } },
    { text: "   →  azure/gpt-4o-mini @ swedencentral\n", options: { color: DIMD } },
    { text: "why         ", options: { color: DIMD } },
    { text: "classifier scored the turn 'trivial' → downshift to fast tier", options: { color: AMBER } },
  ], { x: MX + 0.35, y: 5.56, w: 11.4, h: 0.95, margin: 0, fontFace: M, fontSize: 11.5, lineSpacing: 16 });
  foot(s, n);
  s.addNotes("A routing decision you cannot explain is one you cannot debug, and cannot defend in a cost review. The playground renders this reason chain on every turn.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 9 · PROVE — evals
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = lightSlide(); const n = next();
  head(s, "2 · Prove", "Evals are the release gate", false,
    "For a non-deterministic system, unit tests prove the plumbing and evals prove the behaviour. Only one of those blocks a bad answer.");

  s.addChart(pres.ChartType.bar, [
    { name: "Score", labels: ["Task success", "Safety", "Groundedness", "Efficiency"], values: [1.0, 1.0, 1.0, 1.0] },
    { name: "Gate threshold", labels: ["Task success", "Safety", "Groundedness", "Efficiency"], values: [0.85, 1.0, 0.95, 0.90] },
  ], {
    x: MX, y: 2.0, w: 6.5, h: 3.5, barDir: "bar", barGrouping: "clustered",
    chartColors: [GREEN, "C6D0DC"], showTitle: true, title: "Golden set — 16 cases, current build",
    titleFontSize: 13, titleColor: TXT, titleFontFace: B,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0%",
    dataLabelFontSize: 10, dataLabelFontFace: B, dataLabelColor: TXT,
    valAxisMinVal: 0, valAxisMaxVal: 1.2, valAxisMajorUnit: 0.25,
    valAxisLabelFormatCode: "0%",
    catAxisLabelColor: DIM, valAxisLabelColor: DIM,
    catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
    catAxisLabelFontFace: B, valAxisLabelFontFace: B,
    valGridLine: { color: "EDF1F6", size: 1 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 10, legendColor: DIM,
  });

  const notes = [
    ["Safety is gated at 1.00", "A 0.95 safety threshold says one customer in twenty may receive an unsafe answer. That is not a statement I would sign.", RED],
    ["Groundedness, not vibes", "Every factual claim must trace to a tool observation. Cheap, deterministic, and it names the unsupported claim.", TEAL],
    ["16 cases, seconds to run", "A suite too slow for every PR gets moved to nightly — and a nightly gate is not a gate.", AMBER],
    ["Every incident becomes a case", "The rule that makes the suite worth more each year rather than less.", GREEN],
  ];
  notes.forEach(([t, d, c], i) => {
    const y = 2.0 + i * 1.15;
    s.addShape(pres.ShapeType.ellipse, { x: 7.4, y: y + 0.11, w: 0.15, h: 0.15, fill: { color: c }, line: { color: c } });
    s.addText(t, { x: 7.72, y, w: 4.9, h: 0.32, margin: 0, fontFace: B, fontSize: 14, bold: true, color: TXT });
    s.addText(d, { x: 7.72, y: y + 0.34, w: 4.95, h: 0.72, margin: 0, fontFace: B, fontSize: 11.5, color: DIM, lineSpacing: 15 });
  });

  s.addText("The same suite runs in GitHub Actions on every pull request, and again against the deployed revision after every release.", {
    x: MX, y: 6.35, w: 12, h: 0.36, margin: 0, fontFace: B, fontSize: 12.5, italic: true, color: DIM });
  foot(s, n);
  s.addNotes("Four scorer families matching the four ways a turn goes wrong. Cases come from: intended happy paths, adversarial writing, sampled production traffic, and past incidents.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 10 · PROVE — guardrails
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = darkSlide(); const n = next();
  head(s, "2 · Prove", "Guardrails belong to the platform", true,
    "Not to each team. A tenant should not have to reimplement PII redaction to ship — they get it by adopting the road.");

  card(s, { x: MX, y: 2.1, w: 5.85, h: 3.2, fill: PANEL });
  s.addText("INPUT PIPELINE", { x: MX + 0.32, y: 2.3, w: 4, h: 0.3, margin: 0,
    fontFace: B, fontSize: 11, bold: true, charSpacing: 2, color: RED });
  [["Prompt injection", "block", "instruction override, exfiltration"],
   ["Topic policy", "block", "outside the pharmacy support scope"],
   ["PII redaction", "redact", "IBAN, email, phone, card, DOB — before the call"]]
  .forEach(([t, a, d], i) => {
    const y = 2.72 + i * 0.83;
    s.addText(t, { x: MX + 0.32, y, w: 3.0, h: 0.32, margin: 0, fontFace: B, fontSize: 13.5, bold: true, color: PAPER });
    s.addText(a, { x: MX + 4.55, y, w: 1.1, h: 0.3, margin: 0, align: "right",
      fontFace: M, fontSize: 11, bold: true, color: a === "block" ? RED : AMBER });
    s.addText(d, { x: MX + 0.32, y: y + 0.32, w: 5.2, h: 0.36, margin: 0, fontFace: B, fontSize: 11, color: DIMD });
  });

  card(s, { x: 6.8, y: 2.1, w: 5.85, h: 3.2, fill: PANEL });
  s.addText("OUTPUT PIPELINE", { x: 7.12, y: 2.3, w: 4, h: 0.3, margin: 0,
    fontFace: B, fontSize: 11, bold: true, charSpacing: 2, color: RED });
  [["Secret egress", "block", "credential-shaped strings in the answer"],
   ["Groundedness", "annotate", "every claim traced to a tool observation"],
   ["Medical-advice policy", "escalate", "individualised clinical instruction → pharmacist"],
   ["AI disclosure", "annotate", "EU AI Act Art. 50, on every reply"]]
  .forEach(([t, a, d], i) => {
    const y = 2.72 + i * 0.63;
    s.addText(t, { x: 7.12, y, w: 3.2, h: 0.28, margin: 0, fontFace: B, fontSize: 13, bold: true, color: PAPER });
    s.addText(a, { x: 11.45, y, w: 1.05, h: 0.28, margin: 0, align: "right",
      fontFace: M, fontSize: 10.5, bold: true,
      color: a === "block" ? RED : a === "escalate" ? AMBER : TEAL });
    s.addText(d, { x: 7.12, y: y + 0.26, w: 5.2, h: 0.3, margin: 0, fontFace: B, fontSize: 10.5, color: DIMD });
  });

  card(s, { x: MX, y: 5.6, w: 12, h: 1.05, fill: INK, line: RED });
  s.addText([
    { text: "The trust boundary that matters most:  ", options: { bold: true, color: RED } },
    { text: "tool output is data, never instruction. A policy document, an order note or a product description can carry text engineered to look like a system prompt — so the guardrail runs over content before the agent uses it.", options: { color: DIMD } },
  ], { x: MX + 0.35, y: 5.8, w: 11.35, h: 0.7, margin: 0, fontFace: B, fontSize: 12.5, lineSpacing: 17 });
  foot(s, n, true);
  s.addNotes("Indirect prompt injection is the hard one — the malicious text arrives inside a tool result. There is no complete defence, so the strategy is layered: detect, treat tool output as data, and constrain the agent so a successful injection has nowhere to go.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 11 · SHIP — Terraform
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = lightSlide(); const n = next();
  head(s, "3 · Ship", "Terraform answers two questions", false,
    "“What changed?” and “is staging the same as production?” get asked during every incident, and neither is answerable without IaC.");

  const mods = [
    ["network", "VNet, subnets, NSGs, 8 private DNS zones"],
    ["identity", "managed identities, RBAC, GitHub OIDC federation"],
    ["security", "Key Vault, secret slots, Content Safety, Defender"],
    ["data", "Azure OpenAI ×2, AI Search, Storage, Postgres, Redis"],
    ["runtime", "Container Apps environment + ACR — the shared fabric"],
    ["gateway", "the LiteLLM container app"],
    ["compute", "the agents, as a map — onboarding is a map entry"],
    ["observability", "Log Analytics, App Insights, Grafana, alerts"],
  ];
  mods.forEach(([m, d], i) => {
    const y = 2.05 + i * 0.52;
    s.addText(m, { x: MX, y, w: 1.75, h: 0.34, margin: 0, fontFace: M, fontSize: 12.5, bold: true, color: RED, valign: "middle" });
    s.addText(d, { x: MX + 1.85, y, w: 4.5, h: 0.34, margin: 0, fontFace: B, fontSize: 11, color: DIM, valign: "middle" });
  });

  const points = [
    ["The module graph is a design signal", "The gateway needs a registry; the agents need the gateway's URL. Put those in the wrong modules and Terraform refuses to build a graph at all. The fix was the correct decomposition, not a workaround."],
    ["dev and prod are the same code", "What differs is size and cost. What never differs is posture — private networking, managed identity, guardrails, audit. If a control had to be switched on for prod, dev is the weak link."],
    ["The plan is the review artefact", "A reviewer approves a diff of resources, not a diff of HCL. Those are different things, and the gap between them is where production surprises live."],
  ];
  points.forEach(([t, d], i) => {
    const y = 2.05 + i * 1.55;
    card(s, { x: 7.15, y, w: 5.5, h: 1.4 });
    s.addText(t, { x: 7.45, y: y + 0.15, w: 4.95, h: 0.32, margin: 0, fontFace: B, fontSize: 13.5, bold: true, color: TXT });
    s.addText(d, { x: 7.45, y: y + 0.5, w: 4.95, h: 0.82, margin: 0, fontFace: B, fontSize: 10.8, color: DIM, lineSpacing: 14 });
  });
  foot(s, n);
  s.addNotes("State: Azure Storage with blob leasing, one container per environment, private endpoint only, versioning and soft delete. Secret values never enter state — the module creates the slot and ignores the value.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 12 · SHIP — the pipeline
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = darkSlide(); const n = next();
  head(s, "3 · Ship", "The only path to production", true,
    "GitHub Actions. Nobody holds standing write access to the Azure subscriptions — the pipeline gets minutes of it, via OIDC.");

  const flow = [
    ["Pull request", ["lint", "test", "evals ★", "terraform", "security", "→ one gate job"], TEAL],
    ["Plan on PR", ["terraform plan", "Checkov + tfsec", "Conftest on the plan JSON", "posted as a comment"], TEAL],
    ["Merge → main", ["build + SBOM", "Trivy scan", "cosign sign", "dev deploy + smoke"], AMBER],
    ["Production", ["canary at 10%", "bake 15 min vs SLOs", "promote or roll back", "2 approvers on apply"], RED],
  ];
  flow.forEach(([t, items, c], i) => {
    const x = MX + i * 3.12;
    card(s, { x, y: 2.15, w: 2.85, h: 3.35, fill: PANEL });
    disc(s, x + 0.26, y = 2.38, String(i + 1), c, "FFFFFF", 0.4);
    s.addText(t, { x: x + 0.76, y: 2.4, w: 1.95, h: 0.36, margin: 0,
      fontFace: B, fontSize: 14, bold: true, color: PAPER, valign: "middle" });
    s.addText(items.map((it, j) => ({ text: it, options: { bullet: true, breakLine: j < items.length - 1,
      color: it.includes("★") ? RED : DIMD, bold: it.includes("★") } })), {
      x: x + 0.26, y: 2.88, w: 2.45, h: 2.4, margin: 0, valign: "top",
      fontFace: B, fontSize: 11.5, paraSpaceAfter: 7 });
    if (i < 3) s.addText("→", { x: x + 2.86, y: 3.6, w: 0.26, h: 0.4, align: "center", margin: 0,
      fontFace: B, fontSize: 18, color: RULE });
  });

  const facts = [
    ["★ The eval job is a required check", "Behaviour, not plumbing"],
    ["OIDC, not a client secret", "The best-protected credential is one that does not exist"],
    ["Rollback is a traffic weight", "Seconds — a rollback that needs a rebuild is a hope"],
  ];
  facts.forEach(([t, d], i) => {
    const x = MX + i * 4.05;
    s.addText(t, { x, y: 5.78, w: 3.85, h: 0.3, margin: 0, fontFace: B, fontSize: 13, bold: true, color: PAPER });
    s.addText(d, { x, y: 6.1, w: 3.85, h: 0.5, margin: 0, fontFace: B, fontSize: 11.5, color: DIMD });
  });
  foot(s, n, true);
  s.addNotes("Entra ID checks the OIDC subject exactly — a different branch, environment or fork does not match and is rejected before any Azure call. Getting that wrong with a wildcard is how a fork gets production access.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 13 · RUN — four signal families
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = lightSlide(); const n = next();
  head(s, "4 · Run", "Fast, 200, and still wrong", false,
    "An agent can be fast, return 200 and still be wrong. Classic APM covers the first row; the other three make it operable.");

  const fam = [
    ["RED", "Is the service up?", ["agent_requests_total", "agent_request_duration_seconds", "agent_errors_total"], DIM],
    ["Agent", "Is it behaving?", ["agent_steps_per_turn", "agent_tool_calls_total", "agent_loop_termination_total"], TEAL],
    ["Quality", "Is it right?", ["agent_groundedness_ratio", "guardrail_firings_total", "agent_escalations_total", "agent_eval_score"], RED],
    ["FinOps", "Is it affordable?", ["llm_cost_usd_per_turn", "llm_cache_events_total", "llm_budget_remaining_usd"], AMBER],
  ];
  fam.forEach(([t, q, metrics, c], i) => {
    const x = MX + (i % 2) * 6.15, y = 2.02 + Math.floor(i / 2) * 2.06;
    card(s, { x, y, w: 5.85, h: 1.88 });
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.32, y: y + 0.28, w: 0.19, h: 0.19,
      fill: { color: c }, line: { color: c } });
    s.addText(t, { x: x + 0.62, y: y + 0.16, w: 2.4, h: 0.38, margin: 0, fontFace: H, fontSize: 19, bold: true, color: TXT });
    s.addText(q, { x: x + 2.5, y: y + 0.22, w: 3.1, h: 0.32, margin: 0, align: "right",
      fontFace: B, fontSize: 12.5, italic: true, color: c });
    s.addText(metrics.join("\n"), { x: x + 0.34, y: y + 0.62, w: 5.2, h: 1.3, margin: 0,
      fontFace: M, fontSize: 10.5, color: DIM, lineSpacing: 15 });
  });

  card(s, { x: MX, y: 6.18, w: 12, h: 0.76, fill: MIST, flat: true });
  s.addText([
    { text: "The single most useful metric I have:  ", options: { bold: true, color: TXT } },
    { text: "why the loop stopped. A rise in max_steps_reached means the agent can no longer close conversations out — and it appears before the complaints do.", options: { color: DIM } },
  ], { x: MX + 0.32, y: 6.16, w: 11.4, h: 0.42, margin: 0, fontFace: B, fontSize: 12.5 });
  foot(s, n);
  s.addNotes("Redaction happens at the OTel collector, not in each service — prompts and completions can contain health data and a trace backend is not an approved store for it. Doing it at the collector means the guarantee holds for every service that exports through it.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 14 · RUN — SLOs
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = darkSlide(); const n = next();
  head(s, "4 · Run", "SLOs when the output is not deterministic", true,
    "You cannot promise any individual answer is right — that is the nature of the technology. You can promise a rate, measure it, and fund it.");

  const slos = [
    ["Gateway availability", "99.9%", "30d", "43.2 min", TEAL],
    ["Turn latency", "p95 < 4.0s", "30d", "43.2 min", TEAL],
    ["Groundedness", "≥ 97% grounded", "7d", "302.4 min", RED],
    ["Guardrail coverage", "100% of turns", "30d", "0 min", RED],
  ];
  // header row
  ["Objective", "Target", "Window", "Error budget"].forEach((h, i) => {
    s.addText(h.toUpperCase(), { x: MX + [0, 4.1, 6.5, 8.6][i], y: 2.15, w: 3.4, h: 0.28, margin: 0,
      fontFace: B, fontSize: 10, bold: true, charSpacing: 1.6, color: DIM });
  });
  slos.forEach(([t, tgt, win, bud, c], i) => {
    const y = 2.55 + i * 0.62;
    s.addShape(pres.ShapeType.line, { x: MX, y: y - 0.08, w: 11.9, h: 0, line: { color: RULE, width: 1 } });
    s.addShape(pres.ShapeType.ellipse, { x: MX, y: y + 0.13, w: 0.14, h: 0.14, fill: { color: c }, line: { color: c } });
    s.addText(t, { x: MX + 0.3, y, w: 3.7, h: 0.36, margin: 0, fontFace: B, fontSize: 14, bold: true, color: PAPER });
    s.addText(tgt, { x: MX + 4.1, y, w: 2.3, h: 0.36, margin: 0, fontFace: M, fontSize: 13, color: c });
    s.addText(win, { x: MX + 6.5, y, w: 1.9, h: 0.36, margin: 0, fontFace: M, fontSize: 13, color: DIMD });
    s.addText(bud, { x: MX + 8.6, y, w: 2.3, h: 0.36, margin: 0, fontFace: M, fontSize: 13, color: DIMD });
  });

  card(s, { x: MX, y: 5.3, w: 5.85, h: 1.35, fill: PANEL });
  s.addText("14.4× burn over 1 hour  →  page", { x: MX + 0.32, y: 5.5, w: 5.2, h: 0.32, margin: 0,
    fontFace: B, fontSize: 14, bold: true, color: RED });
  s.addText("2% of the 30-day budget gone within the hour. Somebody wakes up.", {
    x: MX + 0.32, y: 5.86, w: 5.2, h: 0.6, margin: 0, fontFace: B, fontSize: 11.5, color: DIMD });

  card(s, { x: 6.8, y: 5.3, w: 5.85, h: 1.35, fill: PANEL });
  s.addText("6× burn over 6 hours  →  ticket", { x: 7.12, y: 5.5, w: 5.2, h: 0.32, margin: 0,
    fontFace: B, fontSize: 14, bold: true, color: AMBER });
  s.addText("Degradation that will exhaust the budget this week. A single threshold catches one of these and misses the other.", {
    x: 7.12, y: 5.86, w: 5.2, h: 0.6, margin: 0, fontFace: B, fontSize: 11.5, color: DIMD });
  foot(s, n, true);
  s.addNotes("An SLO without an error budget is a wish. Guardrail coverage is the one hard objective with a zero budget, and it is achievable because it is a property of the code path rather than of the model.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 15 · GOVERN — EU AI Act
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = lightSlide(); const n = next();
  head(s, "5 · Govern", "Four articles, four code paths", false,
    "Not four paragraphs. A control that exists only in a document drifts, so /platform/governance serves this as live data.");

  const arts = [
    ["Art. 50", "Transparency", "Every reply carries an AI disclosure and a non-advice notice.", "guardrails.ensure_disclaimer"],
    ["Art. 12", "Record-keeping", "Append-only audit table, 7-year retention in the archive tier.", "telemetry.record_audit"],
    ["Art. 14", "Human oversight", "Side-effecting tools blocked behind an explicit human approval.", "orchestrator HITL gate"],
    ["Art. 15", "Accuracy & robustness", "Groundedness scorer plus a CI eval gate at 0.95.", "evals.suite.THRESHOLDS"],
  ];
  arts.forEach(([a, t, d, impl], i) => {
    const y = 2.05 + i * 1.02;
    card(s, { x: MX, y, w: 7.5, h: 0.88, fill: MIST, flat: true });
    s.addText(a, { x: MX + 0.28, y: y + 0.1, w: 1.0, h: 0.34, margin: 0,
      fontFace: M, fontSize: 13, bold: true, color: RED });
    s.addText(t, { x: MX + 1.35, y: y + 0.1, w: 2.6, h: 0.34, margin: 0,
      fontFace: B, fontSize: 13.5, bold: true, color: TXT });
    s.addText(d, { x: MX + 0.28, y: y + 0.46, w: 6.9, h: 0.34, margin: 0,
      fontFace: B, fontSize: 11.5, color: DIM });
    s.addText(impl, { x: MX + 4.0, y: y + 0.1, w: 3.2, h: 0.34, margin: 0, align: "right",
      fontFace: M, fontSize: 10, color: TEAL });
  });

  card(s, { x: 8.5, y: 2.05, w: 4.15, h: 3.85 });
  s.addText("Risk tier", { x: 8.8, y: 2.24, w: 3.5, h: 0.3, margin: 0,
    fontFace: B, fontSize: 11, bold: true, charSpacing: 1.6, color: DIM });
  s.addText("Limited risk", { x: 8.8, y: 2.56, w: 3.5, h: 0.46, margin: 0,
    fontFace: H, fontSize: 25, bold: true, color: RED });
  s.addText("A customer-facing informational assistant. Not a medical device and not diagnostic, because every clinical judgement is routed to a registered pharmacist — which keeps it out of Annex III.", {
    x: 8.8, y: 3.1, w: 3.55, h: 1.5, margin: 0, fontFace: B, fontSize: 11.5, color: DIM, lineSpacing: 16 });
  s.addShape(pres.ShapeType.line, { x: 8.8, y: 4.62, w: 3.55, h: 0, line: { color: "E1E7EF", width: 1 } });
  s.addText("The classification is a decision, made on the record. The moment the agent could give a dose, it is a different tier with a conformity assessment attached.", {
    x: 8.8, y: 4.76, w: 3.55, h: 1.0, margin: 0, fontFace: B, fontSize: 11.5, italic: true, color: TXT, lineSpacing: 16 });

  s.addText([
    { text: "Human-in-the-loop placement:  ", options: { bold: true, color: TXT } },
    { text: "gate the side effect, not the reasoning. The agent may read and draft freely; it stops before changing a system of record. A rubber-stamp queue at 400 approvals an hour satisfies Art. 14 on paper and nothing in practice.", options: { color: DIM } },
  ], { x: MX, y: 6.2, w: 12, h: 0.6, margin: 0, fontFace: B, fontSize: 12.5, lineSpacing: 17 });
  foot(s, n);
  s.addNotes("GDPR alongside: Art. 9 special-category data, lawful basis 6(1)(b) and 9(2)(h), EU-only residency enforced twice — a Terraform variable validation and an OPA policy — redaction before the call, and split retention: transcripts 90 days, audit 7 years.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 16 · GOVERN — security
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = darkSlide(); const n = next();
  head(s, "5 · Govern", "A confused deputy with a credential", true,
    "An agent is a confused deputy with a credential — design for the day it is fully persuaded. Each control is mapped to a threat, not a checklist.");

  const rows = [
    ["Workload identity + OIDC federation", "Credential theft — no long-lived credential exists"],
    ["Two identities: agent and gateway", "A compromised agent still cannot read provider keys"],
    ["NSG denies internet egress", "A compromised agent has nowhere to send data"],
    ["Private endpoints + private DNS zones", "Traffic silently leaving the VNet"],
    ["Tool scopes on the virtual key", "Excessive agency — it is not told about tools it may not use"],
    ["Approval gate on side effects", "An agent acting on a system of record alone"],
    ["SBOM · Trivy · cosign · content trust", "Supply chain — an unsigned image cannot run"],
    ["Conftest / Checkov on the plan JSON", "Compliant-looking HCL that produces a public resource"],
  ];
  rows.forEach(([c, threat], i) => {
    const y = 2.2 + i * 0.55;
    s.addShape(pres.ShapeType.line, { x: MX, y: y - 0.07, w: 11.9, h: 0, line: { color: RULE, width: 1 } });
    s.addText(c, { x: MX, y, w: 5.4, h: 0.36, margin: 0, fontFace: B, fontSize: 13, bold: true, color: PAPER });
    s.addText(threat, { x: MX + 5.6, y: y + 0.02, w: 6.3, h: 0.34, margin: 0, fontFace: B, fontSize: 12, color: DIMD });
  });

  s.addText("There is no long-lived secret anywhere in the delivery chain. That is achievable, and it is the bar.", {
    x: MX, y: 6.7, w: 11.9, h: 0.36, margin: 0, fontFace: B, fontSize: 13, italic: true, color: RED });
  foot(s, n, true);
  s.addNotes("The three OWASP LLM risks I would spend real effort on: prompt injection (especially indirect, arriving inside a tool result), excessive agency, and sensitive information disclosure in both directions.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 17 · PAY — FinOps
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = lightSlide(); const n = next();
  head(s, "6 · Pay", "Cost per turn is the number", false,
    "Everything else is a proxy for it. Four levers, in the order I would pull them, each visible in the playground and on the dashboard.");

  s.addChart(pres.ChartType.bar, [{
    name: "Cost per 1,000 turns (USD)",
    labels: ["No levers", "+ tier routing", "+ semantic cache", "+ bounded context"],
    values: [28.0, 12.4, 8.6, 7.1],
  }], {
    x: MX, y: 2.05, w: 6.6, h: 3.3, barDir: "col",
    chartColors: [RED], showTitle: true, title: "Illustrative — same traffic mix, levers applied in order",
    titleFontSize: 12, titleColor: DIM, titleFontFace: B,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '"$"0.0',
    dataLabelFontSize: 11, dataLabelFontFace: B, dataLabelColor: TXT,
    catAxisLabelColor: DIM, valAxisLabelColor: DIM,
    catAxisLabelFontSize: 10.5, valAxisLabelFontSize: 10,
    catAxisLabelFontFace: B, valAxisLabelFontFace: B,
    valAxisMinVal: 0, valAxisMaxVal: 30, valAxisMajorUnit: 10,
    valGridLine: { color: "EDF1F6", size: 1 }, catGridLine: { style: "none" },
    showLegend: false,
  });

  const levers = [
    ["Tier routing", "A greeting on the mini tier is ~16× cheaper per token than the flagship. The classifier that decides costs $0.0001."],
    ["Semantic cache", "“Where is my order”, “order status?”, “has it shipped” are one question. 25-35% hit rates are ordinary in support."],
    ["Bounded context", "A rolling window stops prompt growth across a long session — the quiet cause of most cost regressions."],
    ["Hard ceilings", "Per request, per session, per tenant per day. A runaway loop stops itself; the gateway is the backstop."],
  ];
  levers.forEach(([t, d], i) => {
    const y = 2.05 + i * 1.12;
    s.addText(`${i + 1}`, { x: 7.5, y: y + 0.02, w: 0.35, h: 0.34, margin: 0,
      fontFace: H, fontSize: 20, bold: true, color: RED });
    s.addText(t, { x: 7.95, y: y + 0.06, w: 4.6, h: 0.3, margin: 0, fontFace: B, fontSize: 13.5, bold: true, color: TXT });
    s.addText(d, { x: 7.95, y: y + 0.4, w: 4.7, h: 0.68, margin: 0, fontFace: B, fontSize: 11, color: DIM, lineSpacing: 14 });
  });

  s.addText([
    { text: "Measured per resolved conversation, not per call.  ", options: { bold: true, color: TXT } },
    { text: "An agent that is cheap per call and never resolves anything is expensive.", options: { color: DIM } },
  ], { x: MX, y: 6.35, w: 12, h: 0.36, margin: 0, fontFace: B, fontSize: 12.5 });
  foot(s, n);
  s.addNotes("The reflex I would resist in a cost incident is 'move everyone to a cheaper model'. That trades a cost problem you can see for a quality problem you cannot.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 18 · THE FULL MAP
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = darkSlide(); const n = next();
  head(s, "Summary", "Every tool, and the job it does", true);

  const map = [
    ["Azure Container Apps", "Runs agents and the gateway — revisions, traffic splitting, autoscaling, managed identity, without operating Kubernetes."],
    ["Azure OpenAI ×2 EU regions", "The models. The second region is failover and a second quota pool."],
    ["LiteLLM", "The only path to a model. Keys, entitlement, limits, budgets, failover, cache, cost attribution."],
    ["Terraform", "Every Azure resource, reviewed as a plan diff, applied only by the pipeline."],
    ["GitHub Actions", "The only path to production. Eval gate, plan on PR, OIDC apply, signed images, canary release."],
    ["OpenTelemetry · Azure Monitor · Grafana", "Four signal families, and one trace that serves four different readers."],
    ["Key Vault + Entra ID", "No long-lived secret exists anywhere in the chain."],
    ["Azure AI Search", "Hybrid retrieval behind grounded answers, with a versioned index."],
    ["OPA · Checkov · Trivy · cosign", "Policy and supply chain, enforced in the pipeline rather than reviewed at the end."],
  ];
  map.forEach(([t, d], i) => {
    const y = 1.65 + i * 0.58;
    s.addShape(pres.ShapeType.ellipse, { x: MX, y: y + 0.12, w: 0.13, h: 0.13, fill: { color: RED }, line: { color: RED } });
    s.addText(t, { x: MX + 0.3, y, w: 4.5, h: 0.36, margin: 0, fontFace: B, fontSize: 12, bold: true, color: PAPER });
    s.addText(d, { x: MX + 4.95, y: y + 0.02, w: 6.95, h: 0.34, margin: 0, fontFace: B, fontSize: 11.5, color: DIMD });
  });
  foot(s, n, true);
  s.addNotes("They connect because they are not nine concerns. They are nine views of one question: can we trust this system in production?");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 19 · FIRST 90 DAYS
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = lightSlide(); const n = next();
  head(s, "The plan", "First 90 days", false,
    "Enforcement, then measurement, then self-service — sequenced by what unblocks the most other work, not by what demos best.");

  const days = [
    ["Days 1-30", "Make model access safe and countable",
     "Stand up the gateway. Issue virtual keys to the teams already calling providers directly, then revoke their provider keys. Nothing else is enforceable until every call goes through one place.",
     "100% of AI spend attributable to a key and a cost centre, on one dashboard.", RED],
    ["Days 31-60", "Make quality measurable",
     "Ship the eval harness and the guardrail library as platform capabilities. Make the eval gate a required check on the first tenant repo.",
     "A team physically cannot merge a change that regresses safety — and can see exactly why on the PR.", TEAL],
    ["Days 61-90", "Make onboarding cheap",
     "Golden-path template, the agents map in Terraform, the adoption scorecard published in the internal catalogue.",
     "Zero to a traced, guarded, evaluated agent in dev in under a day — one platform review, not a platform project.", AMBER],
  ];
  days.forEach(([d, t, what, success, c], i) => {
    const x = MX + i * 4.15;
    card(s, { x, y: 2.05, w: 3.85, h: 3.95 });
    s.addText(d.toUpperCase(), { x: x + 0.3, y: 2.24, w: 3.2, h: 0.3, margin: 0,
      fontFace: B, fontSize: 11, bold: true, charSpacing: 1.8, color: c });
    s.addText(t, { x: x + 0.3, y: 2.58, w: 3.25, h: 0.75, margin: 0,
      fontFace: H, fontSize: 17, bold: true, color: TXT, lineSpacing: 22, valign: "top" });
    s.addText(what, { x: x + 0.3, y: 3.42, w: 3.25, h: 1.55, margin: 0,
      fontFace: B, fontSize: 11.5, color: DIM, lineSpacing: 16 });
    s.addShape(pres.ShapeType.line, { x: x + 0.3, y: 5.02, w: 3.25, h: 0, line: { color: "E1E7EF", width: 1 } });
    s.addText("SUCCESS LOOKS LIKE", { x: x + 0.3, y: 5.12, w: 3.25, h: 0.26, margin: 0,
      fontFace: B, fontSize: 9.5, bold: true, charSpacing: 1.4, color: DIM });
    s.addText(success, { x: x + 0.3, y: 5.4, w: 3.25, h: 0.55, margin: 0,
      fontFace: B, fontSize: 11, color: TXT, lineSpacing: 14 });
  });

  s.addText("Self-service built on unmeasured, unenforced access just multiplies the problem faster.", {
    x: MX, y: 6.28, w: 12, h: 0.36, margin: 0, fontFace: B, fontSize: 13, italic: true, color: RED });
  foot(s, n);
  s.addNotes("If asked why enforcement first: because you cannot make the safe path fast until you know what safe costs, and you cannot measure quality on traffic you cannot see.");
}

// ═══════════════════════════════════════════════════════════════════════════════
// 20 · CLOSING
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = darkSlide(); const n = next();
  s.addText("WHAT THIS IS", {
    x: MX, y: 1.2, w: 8, h: 0.3, fontFace: B, fontSize: 11, bold: true, charSpacing: 2.4, color: RED, margin: 0 });
  s.addText("Not a deck about a platform.\nA platform, with a deck about it.", {
    x: MX, y: 1.62, w: 11.9, h: 1.5, fontFace: H, fontSize: 38, bold: true, color: PAPER, margin: 0, lineSpacing: 50 });

  const proof = [
    ["76", "tests passing", "86% coverage"],
    ["16", "eval cases", "all four scorers at 100%"],
    ["2,561", "lines of Terraform", "8 modules, 2 environments"],
    ["21", "policy rules", "OPA, against the plan JSON"],
  ];
  proof.forEach(([num, label, sub], i) => {
    const x = MX + i * 3.05;
    s.addText(num, { x, y: 3.5, w: 2.8, h: 0.85, margin: 0, fontFace: H, fontSize: 46, bold: true, color: RED });
    s.addText(label, { x, y: 4.34, w: 2.8, h: 0.3, margin: 0, fontFace: B, fontSize: 14, bold: true, color: PAPER });
    s.addText(sub, { x, y: 4.64, w: 2.8, h: 0.3, margin: 0, fontFace: B, fontSize: 11.5, color: DIMD });
  });
  s.addShape(pres.ShapeType.line, { x: MX, y: 5.3, w: 11.9, h: 0, line: { color: RULE, width: 1 } });

  s.addText([
    { text: "The hardest part of this role  ", options: { bold: true, color: PAPER } },
    { text: "is holding enablement against control without collapsing into either. Collapse toward control and nobody adopts it, so the AI happens anyway where you cannot see it. Collapse toward enablement and you get speed until the first incident, then a freeze that costs more than the caution would have.", options: { color: DIMD } },
  ], { x: MX, y: 5.55, w: 11.9, h: 1.1, margin: 0, fontFace: B, fontSize: 14, lineSpacing: 22 });
  s.addText("The way through is to make the safe path the fast path.", {
    x: MX, y: 6.68, w: 11.9, h: 0.36, margin: 0, fontFace: B, fontSize: 14, bold: true, italic: true, color: RED });
  foot(s, n, true);
  s.addNotes("Close by offering the demo: ten minutes in the playground — ask the agent something, watch a guardrail block an injection, approve a pharmacist handover, run the eval gate. Seeing the control work does more than any slide.");
}

pres.writeFile({ fileName: "Redcare-Agentic-AI-Platform.pptx" })
  .then(f => console.log("wrote", f, "·", page + 1, "slides"));

// ── how this file is used ──────────────────────────────────────────────────────
// The deck is generated, not hand-built, so a correction is a one-line edit and a
// rebuild rather than twenty slides of manual nudging:
//
//   npm install pptxgenjs
//   node docs/build-deck.js
//
// Then validate and eyeball the render before sharing:
//   python scripts/office/validate.py Redcare-Agentic-AI-Platform.pptx
//   soffice --headless --convert-to pdf Redcare-Agentic-AI-Platform.pptx
//   pdftoppm -jpeg -r 110 Redcare-Agentic-AI-Platform.pdf slide
