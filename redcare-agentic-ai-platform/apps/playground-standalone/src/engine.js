/* ============================================================================
   The platform, ported to the browser.

   This is a faithful port of apps/agent-service — the same model catalogue,
   routing rules, guardrail patterns, tool contracts, agent loop, scorers and
   thresholds. The Python service is the reference implementation; this exists so
   the whole thing can be opened and operated without installing anything.

   Nothing here calls a network. The "model" is the same deterministic decision
   table the Python service uses in LLM_MODE=mock, which is what makes the agent
   loop legible and the eval suite repeatable.
   ============================================================================ */

/* ── model catalogue ────────────────────────────────────────────────────────
   Mirrors gateway/litellm/config.yaml. Prices are USD per 1M tokens.        */
const CATALOG = {
  "carecopilot-fast": {
    name: "carecopilot-fast", provider: "azure", upstream: "azure/gpt-4o-mini-2024-07-18",
    region: "swedencentral", tier: "fast", inUsd: 0.15, outUsd: 0.60,
    context: 128000, p50: 420, fallbacks: ["carecopilot-balanced"], zone: "eu",
  },
  "carecopilot-balanced": {
    name: "carecopilot-balanced", provider: "azure", upstream: "azure/gpt-4o-2024-11-20",
    region: "swedencentral", tier: "balanced", inUsd: 2.50, outUsd: 10.0,
    context: 128000, p50: 980,
    fallbacks: ["carecopilot-balanced-westeu", "carecopilot-deep"], zone: "eu",
  },
  "carecopilot-balanced-westeu": {
    name: "carecopilot-balanced-westeu", provider: "azure", upstream: "azure/gpt-4o-2024-11-20",
    region: "westeurope", tier: "balanced", inUsd: 2.50, outUsd: 10.0,
    context: 128000, p50: 1040, fallbacks: ["carecopilot-deep"], zone: "eu",
  },
  "carecopilot-deep": {
    name: "carecopilot-deep", provider: "anthropic", upstream: "anthropic/claude-sonnet-4-5",
    region: "eu-central", tier: "deep", inUsd: 3.0, outUsd: 15.0,
    context: 200000, p50: 1800, fallbacks: ["carecopilot-balanced"], zone: "eu",
  },
  "carecopilot-embed": {
    name: "carecopilot-embed", provider: "azure", upstream: "azure/text-embedding-3-large",
    region: "swedencentral", tier: "embedding", inUsd: 0.13, outUsd: 0,
    context: 8191, p50: 90, fallbacks: [], zone: "eu",
  },
};
const cost = (m, i, o) => (i * m.inUsd + o * m.outUsd) / 1e6;

/* ── virtual keys: the unit of governance ────────────────────────────────── */
const KEYS = {
  "sk-carecopilot-dev": {
    alias: "carecopilot-dev", tenant: "pharmacy-care", costCentre: "cc-4711-customer-care",
    // The regional twin of an entitled model is entitled too — otherwise the key
    // has a fallback chain it is not allowed to use, and a Sweden Central outage
    // takes the tenant down instead of failing over.
    models: ["carecopilot-fast", "carecopilot-balanced", "carecopilot-balanced-westeu", "carecopilot-embed"],
    rpm: 60, tpm: 120000, dailyUsd: 25, group: "grp-ai-pharmacy-care",
    classification: "confidential-health",
  },
  "sk-carecopilot-prod": {
    alias: "carecopilot-prod", tenant: "pharmacy-care", costCentre: "cc-4711-customer-care",
    models: Object.keys(CATALOG), rpm: 600, tpm: 1500000, dailyUsd: 900,
    group: "grp-ai-pharmacy-care", classification: "confidential-health",
  },
  "sk-marketing-dev": {
    alias: "marketing-dev", tenant: "growth-marketing", costCentre: "cc-8802-growth",
    models: ["carecopilot-fast"], rpm: 30, tpm: 40000, dailyUsd: 5,
    group: "grp-ai-growth", classification: "internal",
  },
};

/* ── routing: entitlement → tier → health, and it always says why ─────────── */
function resolveModel(requested, keyId, complexity, unhealthy) {
  const reasons = [];
  const key = KEYS[keyId];
  if (!key) return { selected: null, denied: true, reasons: ["virtual key not recognised"] };

  let candidate = CATALOG[requested] ? requested : "carecopilot-balanced";
  if (candidate !== requested)
    reasons.push(`'${requested}' not in catalogue → default 'carecopilot-balanced'`);

  // 2. complexity tiering — the cheapest model that can do the job
  if (complexity === "trivial" && key.models.includes("carecopilot-fast")) {
    if (candidate !== "carecopilot-fast")
      reasons.push("classifier scored the turn 'trivial' → downshift to fast tier");
    candidate = "carecopilot-fast";
  } else if (complexity === "complex" && key.models.includes("carecopilot-deep")) {
    if (candidate !== "carecopilot-deep")
      reasons.push("classifier scored the turn 'complex' → upshift to deep tier");
    candidate = "carecopilot-deep";
  }

  // 1. entitlement — a governance question, so nothing may override it
  if (!key.models.includes(candidate)) {
    const allowed = key.models.filter(m => CATALOG[m]);
    if (!allowed.length)
      return { selected: null, denied: true,
               reasons: [...reasons, `key '${key.alias}' entitled to no catalogue model`] };
    reasons.push(`key '${key.alias}' not entitled to '${candidate}' → '${allowed[0]}'`);
    candidate = allowed[0];
  }

  // 3. health — cross-region before cross-provider
  let hops = 0;
  while (unhealthy.has(candidate) && hops < 4) {
    const next = (CATALOG[candidate].fallbacks || []).find(f => key.models.includes(f));
    if (!next) break;
    reasons.push(`'${candidate}' unhealthy → failover to '${next}'`);
    candidate = next; hops++;
  }

  if (!reasons.length) reasons.push("requested model served directly");
  return { selected: candidate, entry: CATALOG[candidate], reasons, denied: false,
           tenant: key.tenant, costCentre: key.costCentre };
}

/* ── guardrails ─────────────────────────────────────────────────────────────
   Same patterns as app/guardrails/engine.py. Order matters and is deliberate:
   input  : injection → scope → PII redaction
   output : secrets → grounding → medical-advice → PII egress → disclosure    */
const PII = [
  ["EMAIL", /\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b/g],
  ["IBAN", /\b[A-Z]{2}\d{2} ?(?:[A-Z0-9]{4} ?){2,7}[A-Z0-9]{1,4}\b/g],
  // No leading \b: a word boundary cannot match before "+", so "+49 170 …" slips through.
  ["PHONE_DE", /(?<![\d+])(?:\+49|0049|0)[ -]?\d{2,5}[ -]?\d{3,9}\b/g],
  ["INSURANCE_NO", /\b[A-Z]\d{9}\b/g],
  ["CARD", /\b(?:\d{4}[ -]?){3}\d{4}\b/g],
  ["DOB", /\b(?:0?[1-9]|[12]\d|3[01])[./](?:0?[1-9]|1[0-2])[./](?:19|20)\d{2}\b/g],
];
const INJECTION = new RegExp([
  "ignore (?:all |any )?(?:previous|prior|above) (?:instructions|prompts|rules)",
  "disregard (?:the )?(?:system|previous) (?:prompt|message|instructions)",
  "you are now (?:a|an|in) \\w+", "reveal (?:your|the) (?:system )?prompt",
  "print (?:your|the) (?:instructions|system prompt|rules)",
  "developer mode|do anything now|\\bDAN\\b", "(?:new|updated) instructions?\\s*:",
  "</?(?:system|assistant)>", "repeat (?:everything|the text) above",
  "act as (?:if you (?:are|were)|a) (?:unrestricted|uncensored|jailbroken)",
].map(p => `(?:${p})`).join("|"), "gi");
const EXFIL = /\b(?:send|post|upload|forward|exfiltrate)\b.{0,40}\b(?:http|https|webhook|curl)\b/gi;
const MEDICAL = /\b(?:you should take|take \d+\s*(?:mg|ml|tablets?|pills?)|increase your dose|stop taking|double the dose|safe to take .* while pregnant|i diagnose|you (?:probably )?have\b.{0,30}(?:infection|condition|disease))/gi;
const OFFTOPIC = /\b(?:write me a (?:poem|song|essay)|python script|stock tip|who will win the|political opinion|translate this contract)\b/gi;
const SECRET = /\b(?:sk-[A-Za-z0-9]{8,}|Bearer\s+[A-Za-z0-9._-]{16,}|AKIA[0-9A-Z]{16}|(?:api[_-]?key|password)\s*[:=]\s*\S{6,})/gi;

const V = (check, action, triggered, detail, severity = "info", evidence = []) =>
  ({ check, action, triggered, detail, severity, evidence: evidence.slice(0, 5) });

const BLOCK_MSG = "I can't help with that request. If you were asking about an order, " +
  "a product, or one of our policies, please rephrase it and I'll take another look.";
const DISCLAIMER = "\n\n_Redcare CareCopilot provides general pharmacy information, not " +
  "medical advice. A registered pharmacist reviews anything clinical._";

function redactPII(text) {
  const found = []; let out = text;
  for (const [label, re] of PII) {
    out = out.replace(new RegExp(re.source, re.flags), m => {
      found.push(`${label}:${m.slice(0, 4)}…`); return `[${label}_REDACTED]`;
    });
  }
  return found.length
    ? [out, V("pii_redaction", "redact", true,
        `Redacted ${found.length} identifier(s) before the model call.`, "medium", found)]
    : [out, V("pii_redaction", "allow", false, "No direct identifiers found.")];
}

function runInputGuardrails(text, enabled = true, redact = true) {
  if (!enabled) return { text, verdicts: [V("guardrails", "allow", false, "disabled")], blocked: false };
  const verdicts = [];
  const inj = [...text.matchAll(INJECTION)].map(m => m[0].slice(0, 80));
  const exf = [...text.matchAll(EXFIL)].map(m => m[0].slice(0, 80));
  if (inj.length || exf.length) {
    verdicts.push(V("prompt_injection", "block", true,
      "Instruction-override or exfiltration pattern detected.", "high", [...inj, ...exf]));
    return { text: BLOCK_MSG, verdicts, blocked: true, reason: "prompt_injection" };
  }
  verdicts.push(V("prompt_injection", "allow", false, "No override pattern found."));

  const off = [...text.matchAll(OFFTOPIC)].map(m => m[0]);
  if (off.length) {
    verdicts.push(V("topic_policy", "block", true,
      "Request falls outside the pharmacy support scope.", "medium", off));
    return { text: BLOCK_MSG, verdicts, blocked: true, reason: "topic_policy" };
  }
  verdicts.push(V("topic_policy", "allow", false, "Within supported scope."));

  let out = text;
  if (redact) { const [t, v] = redactPII(text); out = t; verdicts.push(v); }
  return { text: out, verdicts, blocked: false };
}

function checkGrounding(text, observations) {
  const claims = [...new Set(text.match(
    /\b(?:RC\d{8}|in_stock|out_of_stock|low_stock|in_transit|delivered|POL-[A-Z]{2,4}-\d{3}|HIGH_RISK|MODERATE_RISK)\b/g) || [])];
  if (!claims.length) return V("grounding", "allow", false, "No verifiable claim asserted.");
  const corpus = JSON.stringify(observations);
  const unsupported = claims.filter(c => !corpus.includes(c));
  return unsupported.length
    ? V("grounding", "annotate", true, "Claims not present in any tool observation.", "high", unsupported)
    : V("grounding", "allow", false, `All ${claims.length} claim(s) trace to a tool observation.`);
}

function runOutputGuardrails(text, observations, enabled = true) {
  if (!enabled) return { text, verdicts: [V("guardrails", "allow", false, "disabled")], blocked: false, escalate: false };
  const verdicts = [];
  const sec = [...text.matchAll(SECRET)].map(m => m[0].slice(0, 20) + "…");
  if (sec.length) {
    verdicts.push(V("secret_leak", "block", true, "Credential-shaped string in model output.", "high", sec));
    return { text: BLOCK_MSG, verdicts, blocked: true, reason: "secret_leak", escalate: false };
  }
  verdicts.push(V("secret_leak", "allow", false, "No credential pattern in output."));
  verdicts.push(checkGrounding(text, observations));

  const med = [...text.matchAll(MEDICAL)].map(m => m[0].slice(0, 80));
  const escalate = med.length > 0;
  verdicts.push(escalate
    ? V("medical_advice_policy", "escalate", true,
        "Output reads as individualised medical advice — routing to a pharmacist.", "high", med)
    : V("medical_advice_policy", "allow", false, "No individualised clinical instruction detected."));

  let [out, pv] = redactPII(text); pv.check = "pii_egress"; verdicts.push(pv);

  if (/not medical advice|keine medizinische/i.test(out)) {
    verdicts.push(V("disclaimer", "allow", false, "Disclaimer already present."));
  } else {
    out += DISCLAIMER;
    verdicts.push(V("disclaimer", "annotate", true,
      "Appended the regulatory disclosure (EU AI Act Art. 50).", "low"));
  }
  return { text: out, verdicts, blocked: false, escalate };
}

/* ── tools ──────────────────────────────────────────────────────────────────
   Production contracts backed by fixtures: same names, schemas, failure shapes
   and governance metadata as app/tools/pharmacy.py.                          */
const ORDERS = {
  RC10045821: { status: "in_transit", carrier: "DHL", days: 1, value: 24.8, rx: false,
                items: ["Ibuprofen 400mg x20", "Vitamin D3 1000IU x60"] },
  RC10045822: { status: "awaiting_prescription", carrier: "-", days: null, value: 18.2, rx: true,
                items: ["Metformin 850mg x100"] },
  RC10045823: { status: "delivered", carrier: "DPD", days: -3, value: 11.4, rx: true,
                items: ["Omeprazole 20mg x30"] },
  RC10045824: { status: "returned", carrier: "Hermes", days: -1, value: 59.0, rx: false,
                items: ["Blood pressure monitor"] },
};
const STOCK = {
  ibuprofen: [1420, "in_stock", "same day"], paracetamol: [86, "low_stock", "1-2 days"],
  amoxicillin: [0, "out_of_stock", "restock 2026-09-04"], "vitamin d": [3300, "in_stock", "same day"],
  metformin: [640, "in_stock", "same day"], warfarin: [95, "low_stock", "1-2 days"],
  omeprazole: [770, "in_stock", "same day"], sertraline: [210, "in_stock", "same day"],
  insulin: [48, "low_stock", "cold chain, 2 days"], simvastatin: [410, "in_stock", "same day"],
  aspirin: [2100, "in_stock", "same day"],
};
const INTERACTIONS = {
  "ibuprofen|warfarin": ["HIGH_RISK", "NSAIDs markedly increase bleeding risk with vitamin-K antagonists."],
  "aspirin|warfarin": ["HIGH_RISK", "Additive antiplatelet and anticoagulant effect — bleeding risk."],
  "aspirin|ibuprofen": ["MODERATE_RISK", "Ibuprofen can blunt the cardioprotective effect of low-dose aspirin."],
  "ibuprofen|sertraline": ["MODERATE_RISK", "SSRI plus NSAID raises gastrointestinal bleeding risk."],
  "metformin|omeprazole": ["LOW_RISK", "Minor absorption interaction; clinically rarely significant."],
  "amoxicillin|simvastatin": ["LOW_RISK", "No significant interaction expected."],
};
const POLICIES = [
  { id: "POL-RET-014", title: "Returns of non-prescription products", source: "Redcare Returns Policy v7 §3.2",
    body: "Unopened non-prescription products may be returned within 14 days of delivery for a full refund. Medicines that require cold-chain storage and opened hygiene products are excluded for safety reasons." },
  { id: "POL-RET-021", title: "Returns of prescription medicines", source: "AMG §47 / Redcare Returns Policy v7 §4.1",
    body: "Prescription-only medicines cannot be returned once dispatched, except where the product is defective or was dispatched in error. German pharmaceutical law prohibits re-entry into the supply chain." },
  { id: "POL-RX-003", title: "Electronic prescriptions (E-Rezept)", source: "Redcare Prescription Handling v3 §2",
    body: "An E-Rezept token must be redeemed through the gematik TI before the order can be released. Orders wait in 'awaiting_prescription' for up to 28 days, after which they are cancelled and any pre-authorisation released." },
  { id: "POL-GDPR-009", title: "Health data handling and erasure", source: "GDPR Art. 9 / Art. 17, Redcare DPA v4",
    body: "Order and medication history is special-category data under GDPR Art. 9. It is retained for 10 years under pharmacy record-keeping duties; erasure requests are honoured for marketing and analytics stores only." },
  { id: "POL-INS-002", title: "Statutory insurance reimbursement", source: "SGB V §129, Redcare Reimbursement Guide v2",
    body: "For statutorily insured customers the fixed co-payment applies and Redcare bills the fund directly. Private insurance customers pay upfront and receive an invoice suitable for reimbursement." },
  { id: "POL-CAN-005", title: "Order cancellation window", source: "Redcare Terms of Sale v9 §6",
    body: "Orders can be cancelled free of charge until the picking process starts, typically within 45 minutes of placement. After dispatch the returns policy applies instead." },
];

const isoDay = d => new Date(Date.now() + d * 864e5).toISOString().slice(0, 10);

const TOOLS = {
  lookup_order: {
    description: "Look up the status, carrier, ETA and contents of a Redcare order by its order number.",
    sideEffect: false, requiresApproval: false, classification: "confidential-health",
    systems: ["SAP-OMS"], owner: "team-order-management", slo: 400, scopes: ["orders:read"],
    params: { order_id: "Order number, e.g. RC10045821" },
    run: ({ order_id }) => {
      const key = String(order_id || "").toUpperCase().replace(/[\s-]/g, "");
      const r = ORDERS[key];
      if (!r) return { error: "not_found", order_id: key, detail: "No order with that number on this account." };
      return { order_id: key, status: r.status, carrier: r.carrier,
        eta: r.status === "awaiting_prescription" ? "blocked"
             : (r.days === null || r.days < 0 ? "delivered" : isoDay(r.days)),
        items: r.items, value_eur: r.value, prescription_required: r.rx, source_system: "SAP-OMS" };
    },
  },
  check_stock: {
    description: "Check availability, unit count and shipping window for a product.",
    sideEffect: false, requiresApproval: false, classification: "internal",
    systems: ["WMS-Sevenum"], owner: "team-supply-chain", slo: 250, scopes: ["catalogue:read"],
    params: { product: "Product or active ingredient name" },
    run: ({ product }) => {
      const k = String(product || "").trim().toLowerCase();
      const match = Object.keys(STOCK).find(s => s.includes(k) || k.includes(s));
      if (!match) return { error: "unknown_product", product, detail: "Not in the catalogue under that name." };
      const [units, availability, ships] = STOCK[match];
      return { product: match, availability, units_available: units, ships_in: ships, source_system: "WMS-Sevenum" };
    },
  },
  check_interactions: {
    description: "Screen two or more medications for known interactions. Returns a severity band and per-pair findings. Screening only — never a therapy decision.",
    sideEffect: false, requiresApproval: false, classification: "confidential-health",
    systems: ["ABDA-DACON"], owner: "team-clinical-data", slo: 600, scopes: ["clinical:screen"],
    params: { medications: "Array of active ingredient names (at least two)" },
    run: ({ medications }) => {
      const names = [...new Set((medications || []).map(m => String(m).trim().toLowerCase()).filter(Boolean))].sort();
      if (names.length < 2)
        return { error: "insufficient_input", detail: "At least two medications are needed for an interaction check." };
      const order = { NO_KNOWN_RISK: 0, LOW_RISK: 1, MODERATE_RISK: 2, HIGH_RISK: 3 };
      let worst = "NO_KNOWN_RISK"; const findings = [];
      for (let i = 0; i < names.length; i++)
        for (let j = i + 1; j < names.length; j++) {
          const [sev, note] = INTERACTIONS[[names[i], names[j]].sort().join("|")]
            || ["NO_KNOWN_RISK", "No documented interaction."];
          findings.push({ pair: [names[i], names[j]], severity: sev, note });
          if (order[sev] > order[worst]) worst = sev;
        }
      return { severity: worst,
        summary: (findings.find(f => f.severity === worst) || {}).note || "No documented interaction.",
        findings, dataset: "ABDA-DB snapshot 2026-07-01",
        disclaimer: "Screening only. A pharmacist must confirm before any change in therapy.",
        source_system: "ABDA-DACON" };
    },
  },
  search_policy: {
    description: "Retrieve grounded passages from Redcare policy and regulatory documents (returns, prescriptions, GDPR, reimbursement, cancellation).",
    sideEffect: false, requiresApproval: false, classification: "internal",
    systems: ["AzureAISearch"], owner: "team-knowledge", slo: 350, scopes: ["knowledge:read"],
    params: { query: "Natural-language question", top_k: "How many passages (default 3)" },
    run: ({ query, top_k = 3 }) => {
      const q = new Set(String(query || "").toLowerCase().replace(/\?/g, " ").split(/\s+/).filter(w => w.length > 3));
      const scored = POLICIES.map(d => {
        const hay = (d.title + " " + d.body).toLowerCase();
        return [[...q].filter(w => hay.includes(w)).length, d];
      }).filter(([s]) => s > 0).sort((a, b) => b[0] - a[0]);
      const results = scored.slice(0, top_k).map(([s, d]) => ({
        id: d.id, title: d.title, source: d.source, snippet: d.body,
        score: +(s / Math.max(q.size, 1)).toFixed(3) }));
      return { query, results, retrieved: results.length, index: "policies-v12", source_system: "AzureAISearch" };
    },
  },
  escalate_to_pharmacist: {
    description: "Hand the conversation to a registered pharmacist. Use for anything involving dosage, contraindications, symptoms or a HIGH_RISK screen.",
    sideEffect: true, requiresApproval: true, classification: "confidential-health",
    systems: ["ServiceNow"], owner: "team-customer-care", slo: 900, scopes: ["escalation:write"],
    params: { reason: "Why a pharmacist is needed", summary: "Handover summary", priority: "low | normal | urgent" },
    run: ({ reason, summary, priority = "normal" }) => {
      let h = 0; const src = String(reason) + String(summary);
      for (let i = 0; i < src.length; i++) { h = (h * 31 + src.charCodeAt(i)) >>> 0; }
      const sla = { urgent: "15 minutes", normal: "2 hours", low: "1 business day" };
      return { ticket_id: "PHARM-" + h.toString(16).toUpperCase().padStart(6, "0").slice(0, 6),
        queue: "pharmacist-review", priority, sla: sla[priority] || "2 hours",
        reason, handover_summary: summary, source_system: "ServiceNow" };
    },
  },
};

/* ── the "model" ────────────────────────────────────────────────────────────
   Rule-based and intentionally legible: you can read exactly why it chose a
   tool. That makes this a teaching instrument rather than a black box, and it
   makes the eval suite deterministic.                                        */
const ORDER_RE = /\b(?:RC|ORD)[- ]?(\d{6,10})\b/i;
const PRODUCTS = ["ibuprofen", "paracetamol", "aspirin", "warfarin", "metformin",
  "omeprazole", "sertraline", "amoxicillin", "vitamin d", "insulin", "simvastatin"];
const RISKY = ["dose", "dosage", "dosier", "overdose", "how many mg", "how much should",
  "should i take", "how many tablets", "pregnan", "schwanger", "breastfeed",
  "chest pain", "bleeding", "side effect", "nebenwirkung", "allergic", "allergisch", "is it safe to"];

let seed = 7;
const rand = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };

function mockComplete(model, messages, granted) {
  const entry = CATALOG[model] || CATALOG["carecopilot-balanced"];
  const userMsg = [...messages].reverse().find(m => m.role === "user");
  const text = userMsg ? String(userMsg.content) : "";
  const low = text.toLowerCase();
  const called = new Set(messages.filter(m => m.role === "tool").map(m => m.name));
  const obs = {}; messages.filter(m => m.role === "tool").forEach(m => { obs[m.name] = m.content; });

  const call = (name, args) => [{ id: "call_" + Math.floor(rand() * 16 ** 6).toString(16).padStart(6, "0"),
    type: "function", function: { name, arguments: JSON.stringify(args) } }];

  let toolCalls = [], content = "";
  const om = text.match(ORDER_RE);
  const prods = PRODUCTS.filter(p => low.includes(p));
  const has = n => granted.has(n) && !called.has(n);

  if (om && has("lookup_order")) toolCalls = call("lookup_order", { order_id: "RC" + om[1] });
  else if (prods.length >= 2 && has("check_interactions"))
    toolCalls = call("check_interactions", { medications: prods.slice(0, 4) });
  else if (prods.length && /stock|available|in stock|delivery|when can|order/.test(low) && has("check_stock"))
    toolCalls = call("check_stock", { product: prods[0] });
  else if (/return|refund|prescription|rezept|policy|gdpr|data|cancel|insurance|reimburse/.test(low) && has("search_policy"))
    toolCalls = call("search_policy", { query: text.slice(0, 160) });
  else if ((RISKY.some(w => low.includes(w)) || String(obs.check_interactions || "").includes("HIGH_RISK"))
           && has("escalate_to_pharmacist"))
    toolCalls = call("escalate_to_pharmacist", { reason: "clinical judgement required", summary: text.slice(0, 200) });
  else content = answer(text, obs);

  const inTok = Math.max(40, Math.round(messages.reduce((a, m) =>
    a + String(m.content || "").length, 0) / 4));
  const outTok = Math.max(12, Math.round((content.length + JSON.stringify(toolCalls).length) / 4));
  const jitter = 0.75 + rand() * 0.6;

  return { content, toolCalls, model, inTok, outTok,
    latency: Math.round(entry.p50 * jitter * (toolCalls.length ? 1.6 : 1)),
    cost: cost(entry, inTok, outTok),
    finish: toolCalls.length ? "tool_calls" : "stop" };
}

function summarise(name, d) {
  if (name === "lookup_order") return `order ${d.order_id} is **${d.status}**, carrier ${d.carrier}, ETA ${d.eta}`;
  if (name === "check_stock") return `${d.product} — ${d.availability}, ${d.units_available} units, ships ${d.ships_in}`;
  if (name === "check_interactions") return `severity **${d.severity}** — ${d.summary || "see detail"}`;
  if (name === "search_policy") return (d.results || []).slice(0, 2).map(h => `${h.title} (${h.source})`).join("; ") || "no match";
  if (name === "escalate_to_pharmacist") return `ticket ${d.ticket_id} raised, SLA ${d.sla}`;
  return JSON.stringify(d).slice(0, 180);
}

function answer(text, obs) {
  const keys = Object.keys(obs);
  if (!keys.length)
    return "I can help with order status, product availability, medication interaction checks, " +
      "and our returns or prescription policies. Could you tell me the order number or the products involved?";
  const parts = ["Here is what I found:"];
  for (const name of keys) {
    let d; try { d = JSON.parse(obs[name]); } catch { d = { result: obs[name] }; }
    parts.push(`- **${name}**: ${summarise(name, d)}`);
  }
  parts.push("\nThis is general pharmacy information, not medical advice. For anything about " +
    "dosage or your personal treatment, a registered pharmacist will confirm before we act.");
  return parts.join("\n");
}
