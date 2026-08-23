# SAP Fioneer — Senior Solution Manager Application

Tailored application pack for the **Senior Solution Manager** role at SAP Fioneer
(business × AI technology, core banking: accounts, deposits, loans, payments).

## Files

| File | Purpose |
|------|---------|
| `Mehreen_Himani_CV_SAP_Fioneer_Senior_Solution_Manager.pdf` | CV — send this one (2 pages) |
| `Mehreen_Himani_CV_SAP_Fioneer_Senior_Solution_Manager.docx` | Editable CV |
| `Mehreen_Himani_Cover_Letter_SAP_Fioneer.pdf` | Cover letter — send this one (1 page) |
| `Mehreen_Himani_Cover_Letter_SAP_Fioneer.docx` | Editable cover letter |
| `cv.html`, `cover_letter.html` | Source of truth for both documents |
| `build.sh` | Renders both documents to PDF and DOCX |
| `make_docx.py` | HTML → DOCX converter used by `build.sh` |

## Phone number

**This repository is public, so the phone number is deliberately not stored in
it** — not in the sources, not in the committed PDFs or DOCX, and not in the
git history. The contact line carries a `<!--PHONE-->` marker instead.

The committed documents list location, email, LinkedIn, GitHub and portfolio,
which is a complete and normal contact block for an application.

## Rebuilding

```bash
./build.sh                       # public build — no phone number
./build.sh "+49 XXX XXXX XXX"   # private build — writes *_with_phone.*
```

The `*_with_phone.*` files are git-ignored. Build them when you want the copies
you actually send to recruiters, and keep them off the repo.

## Design

Fully monochrome (black / neutral grey — no colour), centred ruled letterhead,
letterspaced small-caps section headings, serif body. Every link in both
documents is a real clickable hyperlink in the PDF *and* in the DOCX.

### Links used

| Item | Target |
|------|--------|
| Contact | phone, email, LinkedIn, GitHub, portfolio |
| BankFlow AI | `github.com/mehreenhimani/bankflow-ai` |
| PayClear AI | `github.com/mehreenhimani/payclear-AI` |
| OnboardIQ | live demo + `github.com/mehreenhimani/KYC-Onboarding` |
| PayGuard AI | live demo + `github.com/mehreenhimani/payguard-ai` |
| PulseAI | `github.com/mehreenhimani/pulseai` |
| RegCopilot | `github.com/mehreenhimani/regcopilot` |
| ComplianceIQ | **no link** — repo is private |

`complianceiq-aml-triage` and `qa-sales-radar` are private repositories, so they
are deliberately left unlinked; a link would 404 for a recruiter. Make either
public and the link can be added.

## How the CV was tailored

Only the **Capgemini** entry was rewritten (retitled *AI Product & Solution Manager*);
all earlier roles are unchanged. The header, profile, competencies and skills blocks
were re-pointed at the job description.

Capgemini now covers, in the order the job ad asks for it:

1. Opportunity identification & business development with sales / pre-sales
2. **QA Radar** — product co-created with the sales team
3. Requirements gathering, structuring and prioritisation → solution design
4. Hands-on agentic AI: multi-agent workflows, prompt & context engineering, model configuration
5. Solution demos, prototypes and adoption at scale
6. AI evaluation, guardrails, EU AI Act / DORA governance
7. SAP S/4HANA migration test strategy & test management
8. SAP knowledge management
9. Cross-functional workshops and the business ↔ technical connector role
