/* Shared drawing kit for the architecture deck.
   Everything is built from these primitives so the diagrams stay consistent. */
const pptxgen = require("pptxgenjs");

const W = 13.3, H = 7.5, MX = 0.6;

/* ── the six layers. This key is the deck's whole navigation system: learn it
      once and every box on every diagram is readable before you read its label. */
const L = {
  edge:    { c: "44546A", w: "EEF1F5", n: "Edge",            d: "Front Door, WAF" },
  agent:   { c: "C9001B", w: "FCEDEF", n: "Agent",           d: "Container Apps, the loop" },
  gateway: { c: "A85B00", w: "FBF1E3", n: "Gateway",         d: "LiteLLM" },
  data:    { c: "0E6E80", w: "E6F2F5", n: "Data & AI",       d: "OpenAI, Search, Postgres, Redis" },
  obs:     { c: "5B34AF", w: "F0EBFA", n: "Observability",   d: "OTel, Monitor, Grafana" },
  gov:     { c: "15703C", w: "E8F4EC", n: "Governance",      d: "Entra, Key Vault, policy, HITL" },
};

const INK = "111A24", INK2 = "35455A", MUTED = "6B7C93";
const PAPER = "FFFFFF", GROUND = "F7F9FC", LINE = "D9E1EB";
const RED = "C9001B";

const H_FONT = "Cambria", B = "Calibri", M = "Courier New";

function deck() {
  const p = new pptxgen();
  p.layout = "LAYOUT_WIDE";
  p.author = "Mehreen Himani";
  p.title = "Redcare Agentic AI Platform — Architecture";
  return p;
}

const shadow = () => ({ type: "outer", angle: 90, blur: 9, offset: 2, color: "8FA0B5", opacity: 0.22 });

/* a labelled box in a layer colour — the deck's atom */
function box(s, p, o) {
  const lay = L[o.layer] || L.agent;
  s.addShape(p.ShapeType.roundRect, {
    x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.06,
    fill: { color: o.solid ? lay.c : (o.fill || lay.w) },
    line: { color: lay.c, width: o.solid ? 0 : 1 },
    shadow: o.flat ? undefined : shadow(),
  });
  const tc = o.solid ? "FFFFFF" : INK;
  // A tall box centres its title into whatever else it contains, so `top` anchors
  // the title and subtitle to the top edge instead.
  const titleY = o.top ? o.y + 0.14 : (o.sub ? o.y + (o.h - 0.62) / 2 : o.y);
  s.addText(o.t, {
    x: o.x + 0.1, y: (o.sub || o.top) ? titleY : o.y,
    w: o.w - 0.2, h: (o.sub || o.top) ? 0.32 : o.h,
    align: "center", valign: "middle", margin: 0,
    fontFace: o.mono ? M : B, fontSize: o.fs || 12, bold: true, color: tc,
  });
  if (o.sub) {
    s.addText(o.sub, {
      x: o.x + 0.08, y: titleY + 0.3, w: o.w - 0.16, h: 0.32,
      align: "center", valign: "top", margin: 0,
      fontFace: o.subMono ? M : B, fontSize: o.subFs || 9.5,
      color: o.solid ? "FFFFFF" : MUTED,
    });
  }
}

/* arrow between two points */
function arrow(s, p, x1, y1, x2, y2, o = {}) {
  s.addShape(p.ShapeType.line, {
    x: Math.min(x1, x2), y: Math.min(y1, y2),
    w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
    line: {
      color: o.color || "9AAABE", width: o.width || 1.25,
      dashType: o.dash || "solid",
      beginArrowType: o.both ? "triangle" : "none",
      endArrowType: o.none ? "none" : "triangle",
    },
    flipH: x2 < x1, flipV: y2 < y1,
  });
  if (o.label) {
    s.addText(o.label, {
      x: (x1 + x2) / 2 - (o.lw || 1.1) / 2, y: (y1 + y2) / 2 - 0.16,
      w: o.lw || 1.1, h: 0.3, align: "center", valign: "middle", margin: 0,
      fontFace: M, fontSize: o.lfs || 8.5, color: o.color || MUTED,
      fill: { color: o.lfill || PAPER },
    });
  }
}

/* small filled disc — the repeated motif */
function dot(s, p, x, y, color, d = 0.15) {
  s.addShape(p.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color }, line: { color } });
}

/* numbered disc for ordered steps */
function num(s, p, x, y, n, color, d = 0.34) {
  s.addShape(p.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color }, line: { color } });
  s.addText(String(n), {
    x, y, w: d, h: d, align: "center", valign: "middle", margin: 0,
    fontFace: B, fontSize: 11, bold: true, color: "FFFFFF",
  });
}

/* slide chrome */
function light(p) { const s = p.addSlide(); s.background = { color: PAPER }; return s; }
function tinted(p) { const s = p.addSlide(); s.background = { color: GROUND }; return s; }
function dark(p) { const s = p.addSlide(); s.background = { color: INK }; return s; }

function head(s, p, eyebrow, title, sub, isDark = false) {
  s.addText(eyebrow.toUpperCase(), {
    x: MX, y: 0.36, w: 9, h: 0.26, margin: 0,
    fontFace: B, fontSize: 10.5, bold: true, charSpacing: 2.2, color: RED,
  });
  const size = title.length <= 34 ? 30 : title.length <= 46 ? 26 : 22;
  s.addText(title, {
    x: MX, y: 0.62, w: W - 2 * MX, h: 0.56, margin: 0, valign: "top",
    fontFace: H_FONT, fontSize: size, bold: true, color: isDark ? "FFFFFF" : INK,
  });
  if (sub) s.addText(sub, {
    x: MX, y: 1.2, w: W - 2 * MX, h: 0.42, margin: 0, valign: "top",
    fontFace: B, fontSize: 12.5, italic: true, color: isDark ? "AEBCCD" : INK2,
  });
}

/* the legend strip, repeated on every diagram slide so the key is never far away */
function legend(s, p, y, only = null) {
  const keys = only || Object.keys(L);
  const gap = (W - 2 * MX) / keys.length;
  keys.forEach((k, i) => {
    const x = MX + i * gap;
    dot(s, p, x, y + 0.06, L[k].c, 0.13);
    s.addText(L[k].n, {
      x: x + 0.2, y, w: gap - 0.25, h: 0.26, margin: 0, valign: "middle",
      fontFace: B, fontSize: 10, bold: true, color: INK2,
    });
  });
}

function foot(s, n, isDark = false) {
  s.addText(String(n), {
    x: W - MX - 0.5, y: H - 0.46, w: 0.5, h: 0.26, align: "right", margin: 0,
    fontFace: B, fontSize: 9.5, color: isDark ? "44546A" : "AFBDCC",
  });
}

/* a caption line under a diagram — where the "why" lives */
function why(s, x, y, w, text, isDark = false) {
  s.addText(text, {
    x, y, w, h: 0.5, margin: 0, valign: "top",
    fontFace: B, fontSize: 11.5, color: isDark ? "AEBCCD" : INK2,
  });
}

module.exports = { pptxgen, W, H, MX, L, INK, INK2, MUTED, PAPER, GROUND, LINE, RED,
  H_FONT, B, M, deck, box, arrow, dot, num, light, tinted, dark, head, legend, foot, why, shadow };
