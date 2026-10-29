# ats-resume-tailor

> **Honest ATS resume tailoring CLI designed for software engineers and autonomous AI agents.**

`ats-resume-tailor` tailors a candidate's Markdown resume against a target job posting by surgically injecting verified keywords and spelling variants where the candidate actually has proven experience. Missing requirements are never hallucinated — they are flagged as gaps with actionable cover letter disclosure strategies.

---

## The Core "Honesty Invariant"

Most resume optimization tools encourage keyword stuffing or fabricate experience to artificially game ATS match scores. This approach reliably collapses during recruiter screens, technical assessments, and background checks.

`ats-resume-tailor` operates on a strict **Honesty Invariant**:

- **No Hallucinations:** A technology unconfirmed in the candidate's skill ledger is **never** added to the resume.
- **Evidence-Tiered Injection:**
  - `confirmed` &rarr; Injected into the appropriate category in the **Technical Skills** section (e.g., `**Frontend:**`, `**Backend:**`).
  - `personal` &rarr; Injected into the `**Personal projects:**` skills row and, if a qualifying public repository exists, added to `## Personal Projects`.
  - `partial` / `not` / `unknown` &rarr; **Never added to the resume.** Explicitly logged as `needs_review` or `gap`.
- **Honest Gap Disclosures:** For missing required technologies, the CLI generates candid, professional cover letter talking points highlighting adjacent transferable skills.
- **Soft Skills Separation:** Abstract soft skills (*communication, teamwork, problem solving, leadership*) and basic office suites (*MS Office, Google Suite*) are excluded from the taxonomy. Authentic soft skills belong in experience bullets as quantified achievements, not keyword lists.

---

## Key Features

- **Zero External Dependencies:** Built entirely with Python 3.11+ standard library. No third-party packages, no heavy NLP frameworks, no network calls, and zero telemetry.
- **Deterministic Alias & Variant Matching:**
  - Longest-alias-first token boundary matcher prevents greedy subtoken collisions (e.g., `Redux Toolkit` is never misclassified as `Redux`; `React Query` maps to `TanStack Query`, not `React`; `Next.js` never yields `Node.js` or `JS`).
  - Preserves the recruiter's exact job posting spelling (e.g., `React.js` vs `ReactJS` vs `React`) to match ATS token-search indices.
  - Context-aware heuristics for ambiguous tokens (e.g., `Go` vs English verb "go", `Node` vs node graphs).
- **Candidate Skill Ledger Integration:**
  - Reads candidate proof tables from Markdown inventories (e.g., `skills-inventory.md`).
  - Integrates structured pet project registries (`pets.md` / `open-source-repositories.md`).
  - Supports fine-grained precedence overrides via `overrides.json`.
- **Surgical, Non-Destructive Markdown Modification:**
  - Touches **only** the `## Technical Skills` block and, when applicable, adds a clean `## Personal Projects` section.
  - Every other line, bullet point, date, and link remains **byte-identical** to the source resume.
  - Strictly **idempotent**: running against an already tailored resume produces zero changes.
- **Agent-Ready CLI Design:**
  - Clean separation: stdout streams pure payload (tailored Markdown or formatted JSON) for easy piping into AI agent workflows.
  - Human-readable Markdown tables and summaries emitted to stderr.
  - Deterministic exit codes (`0` on success, `2` on bad inputs, `1` on unexpected errors) with single-line error messages and suppressed tracebacks.

---

## Installation & Quick Start

### Requirements
- Python 3.11 or newer

### Installation

Clone the repository:
```bash
git clone https://github.com/your-org/ats-resume-tailor.git
cd ats-resume-tailor
```

You can run the CLI directly via the executable wrapper script:
```bash
./bin/ats-tailor --help
```

Or install it in editable mode:
```bash
pip install -e .
ats-tailor --help
```

Or run via Python's module launcher:
```bash
python3 -m ats_tailor --help
```

---

## CLI Commands & Usage

### 1. `keywords` — Extract and Classify Posting Terms
Extracts all technical skills from a job posting, identifies whether they are required or nice-to-have, preserves the exact spelling, and flags unrecognized technology-like tokens.

```bash
ats-tailor keywords --job posting.md
```
*(Accepts `--job -` to read from stdin).*

Example JSON output:
```json
[
  {
    "canonical": "React",
    "spelling": "React.js",
    "required": true,
    "count": 2,
    "unrecognized": false
  },
  {
    "canonical": "Redis",
    "spelling": "Redis",
    "required": false,
    "count": 1,
    "unrecognized": false
  }
]
```

---

### 2. `analyze` — Pre-flight Coverage Analysis (Read-Only)
Compares a base resume against a job posting without modifying any files. Outputs a comprehensive coverage delta.

#### Human-Readable Markdown (Default)
```bash
ats-tailor analyze --job posting.md --resume resume.md
```

Outputs:
```markdown
# ats-tailor report

Coverage: 6/12 keywords (required 5/9) -> 9/12 (required 8/9)

| Keyword | Posting spelling | Required | Level | Status |
|---|---|---|---|---|
| React | React.js | yes | confirmed | variant_added |
| TypeScript | TypeScript | yes | confirmed | present |
| Docker | Docker | yes | confirmed | present |
| NestJS | NestJS | yes | personal | personal_added |
| Kafka | Kafka | yes | not | gap |
| Redis | Redis | no | personal | personal_added |

Gaps (not added, disclose in the cover letter):
- Kafka: No hands-on Kafka experience; say so plainly and name the closest real experience.

Unrecognized: FooBarDB
```

#### JSON Output (For Automation / Agents)
```bash
ats-tailor analyze --job posting.md --resume resume.md --json
```

---

### 3. `score` — Resume-to-Job Match Scoring & Gap Analysis
Calculates a deterministic 0–100 ATS compatibility score, classifies gaps by severity, and provides actionable tailoring recommendations.

#### Scoring Algorithm
- **Weighted Requirements:** Required skills carry 3x higher weight than nice-to-have skills (75% / 25% balance).
- **Status Credit:**
  - **Present (100%):** Present in the resume (either verified in candidate ledger as `confirmed` / `personal` with status `present`, or literally present in resume claims without ledger verification as `present_unverified`).
  - **Tailorable (75%):** Verified in candidate ledger, but missing from the resume (can be added honestly via `ats-tailor tailor`).
  - **Partial (30%):** Limited or partial competence in candidate ledger (`partial`).
  - **Gap (0%):** Missing from both resume and candidate ledger, or explicitly denied in ledger (`not` or `unknown`).
- **Grades:**
  - `Excellent` (90+), `Good` (75–89), `Moderate` (60–74), `Low` (<60)
  - **Upper-Bound Caveat:** If the posting contains unrecognized tech-like tokens anywhere outside a nice-to-have section (this includes page text such as company blurbs and footers, so the flag can fire on noise), the score is an upper bound. Only CamelCase and ALL-CAPS tokens are detected: lowercase or single-capital names (e.g. Bun, Deno, Zod) are not, so `upper_bound: false` does not guarantee every term was evaluated. The report flags `Score is an upper bound: N unrecognized terms not evaluated` and sets `upper_bound: true` in JSON. The grade itself remains one of `Excellent|Good|Moderate|Low` — unchanged.
  - **Unrecognized Terms & Noise Filtering:** Candidate terms extracted outside the taxonomy appear under `### Unrecognized Terms` and in `--json` output as `unrecognized_required` / `unrecognized_warning`. Obvious noise (concatenated country dropdowns, section headings like `ABOUT`/`STACK`/`HIRING PROCESS`, company names, and corporate acronyms like `LLC`, `KPMG`) is filtered deterministically. Compliance/security terms (HIPAA, GDPR, SOC, ISO, PCI, DSS) are **not** filtered and surface as unrecognized terms when not in the taxonomy.
- **Taxonomy Additions:**
  - Includes canonical technologies with alias matching:
    - **Frontend:** `Angular CDK`
    - **Backend:** `SQL`, `Supabase`, `PostGIS`, `MikroORM`, `Fastify`, `BullMQ`
    - **Infrastructure:** `AWS CDK`, `Cognito` (AWS Cognito), `ArgoCD`
    - **AI:** `OpenAI API`
    - **Tools:** `SonarQube`, `Testcontainers`, `Rush.js`
- **Gap Classifications:**
  - `CRITICAL`: Missing required skill with no ledger backing. Action: Disclose honestly via cover letter highlighting transferable capabilities.
  - `ACTIONABLE`: Verified skill in candidate ledger missing from resume. Action: Run `ats-tailor tailor` to inject it honestly.
  - `SECONDARY`: Missing nice-to-have skill. Action: Optional bonus; highlight adjacent experience where applicable.
  - `REVIEW`: Skill with partial evidence. Action: Verify hands-on depth before claiming in technical interviews.

#### Human-Readable Markdown Report
```bash
ats-tailor score --job posting.md --resume resume.md
```

Example output:
```markdown
# ATS Resume-to-Job Match Score

**Score:** 78.5/100 — **Good**

### Score Breakdown
- **Required Skills:** 18.0 / 24.0 pts (75.0%)
- **Nice-to-Have Skills:** 2.0 / 3.0 pts (66.7%)
- **Matched Keywords (Present):** 6
- **Tailorable Keywords (In Ledger):** 2
- **Needs Review (Partial):** 0
- **Gaps (Missing from Ledger):** 2

### Gaps & Action Items
- **[ACTIONABLE] NestJS** (required, spelling: `NestJS`): In ledger as personal; tailor resume to include it.
- **[CRITICAL] Kafka** (required, spelling: `Kafka`): Missing required skill (Kafka confirmed not experienced); disclose via transferable skills in cover letter.
- **[SECONDARY] Svelte** (nice-to-have, spelling: `Svelte`): Nice-to-have skill (Svelte) not in ledger; optional, address as bonus if candidate has adjacent exposure.

### Recommendations
1. Tailor resume: 2 verified skills can be added honestly (NestJS, Kubernetes). Run 'ats-tailor tailor'.
2. Cover letter disclosures: 1 missing required skills must be disclosed honestly (Kafka). Do not add to resume.
```

#### JSON Output (For Automation & Agents)
```bash
ats-tailor score --job posting.md --resume resume.md --json
```

#### Detailed Keyword Breakdown Table
```bash
ats-tailor score --job posting.md --resume resume.md --detailed
```

---

### 4. `tailor` — Surgically Update Markdown Resume
Updates the resume with verified skills and spelling variants.

```bash
ats-tailor tailor \
  --job posting.md \
  --resume base_resume.md \
  --out tailored_resume.md \
  --pdf tailored_resume.pdf \
  --report report.json
```

- `--out`: Destination file path or `-` for stdout. Refuses to overwrite `--resume` unless `--force` is supplied.
- `--pdf`: Optional path to automatically compile the tailored resume into an ATS-compliant PDF and verify its text layer.
- `--report`: Optional path to write the full JSON report.
- Custom ledger files can be passed via `--inventory <path>`, `--pets <path>`, and `--overrides <path>`.

---

### 5. `pdf` — Compile Resume to ATS-Optimized PDF
Converts a Markdown or HTML resume into an ATS-friendly, single-column PDF using headless Chrome/Chromium across macOS, Linux, and Windows:

```bash
ats-tailor pdf --resume tailored_resume.md --out tailored_resume.pdf
```

---

### 6. `verify-pdf` — Verify Embedded PDF Text Layer
Extracts the text layer using `pdftotext` (what ATS systems parse) and checks for garbled `(cid:NN)` glyphs, replacement characters, literal contact info, and mandatory keywords:

```bash
ats-tailor verify-pdf --pdf tailored_resume.pdf --keywords React TypeScript Node.js
```

---

### 7. `schema` — Print JSON Report Contract
Prints the canonical JSON schema for integration into automated pipelines and LLM agent tool definitions:

```bash
ats-tailor schema
```

---

## Configuration & Environment Variables

Default file paths can be customized via CLI flags or environment variables:

| Setting | CLI Flag | Environment Variable | Default Fallback |
|---|---|---|---|
| Skill Inventory | `--inventory` | `ATS_TAILOR_INVENTORY` | `~/work/resume/info/skills-inventory.md` |
| Pet Projects | `--pets` | `ATS_TAILOR_PETS` | `~/work/resume/info/open-source-repositories.md` |
| Overrides | `--overrides` | — | `ats_tailor/data/overrides.json` |

### Candidate Skill Ledger Format
The inventory is parsed from standard Markdown tables:
```markdown
| Skill | Status | Evidence |
|---|---|---|
| React, TypeScript, Node.js | confirmed | 5+ years production experience |
| NestJS | confirmed | pet projects only |
| Kafka | NOT confirmed | Evaluated in POC; no production use |
| Progressive Web Apps | PARTIAL | Built basic offline caching |
```

### Pet Projects Registry Format
Pet projects are extracted from Markdown lists:
```markdown
### my-mcp-server
- **GitHub:** https://github.com/candidate/my-mcp-server
- **Стек:** TypeScript, Node.js, MCP
- **Рядок для резюме:** `Standalone MCP server for developer tool integration`
```
*(Private repositories or items marked `private` are automatically skipped).*

---

## Architecture & Pipeline Overview

```
                        ┌────────────────────────┐
                        │   Target Job Posting   │
                        └───────────┬────────────┘
                                    │
                                    ▼
┌──────────────────┐    ┌────────────────────────┐
│  Taxonomy Matrix │───▶│      postings.py       │  (Extracts required/bonus keywords,
│ (taxonomy.json)  │    │  (extract_keywords)    │   normalizes tokens, detects unknowns)
└──────────────────┘    └───────────┬────────────┘
                                    │ Keywords + Exact Spellings
                                    ▼
┌──────────────────┐    ┌────────────────────────┐
│ Candidate Ledger │───▶│       resume.py        │  (Applies Honesty Invariant,
│(inventory/pets)  │    │   (analyze / tailor)   │   injects skills into skills block,
└──────────────────┘    └───────────┬────────────┘   adds personal projects, logs gaps)
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
        ┌───────────────────┐               ┌───────────────────┐
        │  Tailored Resume  │               │   Audit Report    │
        │  (Markdown text)  │               │  (JSON / Summary) │
        └───────────────────┘               └───────────────────┘
```

- **`ats_tailor/taxonomy.py`**: Manages the canonical technology dictionary and alias graph across categories (`frontend`, `backend`, `infra`, `ai`, `tools`, `practices`). Executes token-bounded matching.
- **`ats_tailor/ledger.py`**: Ingests candidate skill matrices and pet project repositories, resolving levels (`confirmed` > `personal` > `partial` > `not` > `unknown`).
- **`ats_tailor/postings.py`**: Parses job postings into structured keyword requirements, detecting section importance (required vs nice-to-have) and flagging unrecognized tech tokens.
- **`ats_tailor/resume.py`**: Orchestrates the tailoring engine. Injects exact spelling variants, creates or appends category lines, anchors verified personal project entries, and computes honest ATS coverage metrics.
- **`ats_tailor/scorer.py`**: Computes weighted match scores (0–100 scale), classifies gaps (`critical`, `actionable`, `secondary`, `review`), and generates actionable application recommendations.
- **`ats_tailor/cli.py`**: Handles command-line arguments, file streaming, stdin/stdout piping, and agent-friendly error handling.

---

## Verification & Testing

The suite uses Python's standard `unittest` framework with zero external dependencies:

```bash
python3 -m unittest discover -s tests -v
```

The test suite covers:
- **Honesty invariant guarantees:** Verifies that no unconfirmed, partial, or unknown skill is ever written into output resumes.
- **Surgical edits:** Verifies that all resume sections outside `## Technical Skills` and `## Personal Projects` remain byte-identical.
- **Idempotence:** Verifies that running repeated tailoring passes produces no text drift.
- **Token boundaries:** Confirms edge cases such as `React.js` vs `React`, `Redux Toolkit` vs `Redux`, `TanStack Query` vs `React`, and `Go`/`Node` disambiguation.
- **CLI edge cases:** Stdin handling, stdout payload cleanliness, missing arguments, and refusal to overwrite input files without `--force`.

---

## License

This project is licensed under the [MIT License](LICENSE).
