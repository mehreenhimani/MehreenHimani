# Deck sources

Both decks are generated, not hand-built, so a correction is a one-line edit and a
rebuild rather than twenty slides of manual nudging.

| Script | Produces | What it is for |
|---|---|---|
| `build-lifecycle-deck.js` | `Redcare-Agentic-AI-Platform.pptx` | The production lifecycle: build → prove → ship → run → govern → pay. Card- and table-led. |
| `build-architecture-deck.js` + `lib.js` | `Redcare-Architecture-Visual.pptx` | The architecture, drawn. Diagram-led, on a six-colour layer key. |

```bash
npm install pptxgenjs
node docs/deck-src/build-architecture-deck.js
```

Then validate and look at every slide before sharing:

```bash
python scripts/office/validate.py Redcare-Architecture-Visual.pptx
soffice --headless --convert-to pdf Redcare-Architecture-Visual.pptx
pdftoppm -jpeg -r 105 Redcare-Architecture-Visual.pdf s
```

## The layer key

`lib.js` holds the whole visual system. The six layers and their colours are the
architecture deck's navigation: learn the key once and every box on every diagram
is readable before you read its label.

| Layer | Colour | Owns |
|---|---|---|
| Edge | slate | Front Door, WAF |
| Agent | Redcare red | Container Apps, the plan/act loop |
| Gateway | ochre | LiteLLM |
| Data & AI | teal | Azure OpenAI, AI Search, Postgres, Redis |
| Observability | violet | OTel, Azure Monitor, Grafana |
| Governance | green | Entra ID, Key Vault, policy, HITL |

Everything is drawn from four primitives in `lib.js` — `box`, `arrow`, `dot`, `num` —
so the diagrams stay consistent with each other. Add a slide by composing those,
not by inventing new shapes.
