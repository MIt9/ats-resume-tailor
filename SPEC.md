# ats-tailor — SPEC (source of truth for tests and implementation)

Purpose: CLI for AI agents. Input = job posting + base resume (markdown). Output = resume markdown whose
skills carry the posting's keywords **only where the candidate truly has the skill**, plus a machine-readable report.

## Honesty invariant (hard rule, most important test)
A keyword is written into the resume ONLY if the ledger says the candidate has it:
- level `confirmed`  → add to the matching skills line;
- level `personal`   → add to the `**Personal projects:**` skills row and (if a public pet project uses it) to the `## Personal Projects` section;
- level `partial` / `not` / `unknown` → NEVER added. Reported as `gap` or `needs_review`.
A technology unconfirmed anywhere is never written as a skill. Test: no gap keyword appears in tailored output unless it was already in the base resume.
Soft skills invariant: abstract soft skills (e.g. Communication, Teamwork, Leadership, Problem Solving) are intentionally excluded from the taxonomy and skills block. They belong exclusively in experience bullets as quantified achievements (Scope/Context + Result). Baseline office computer tools (e.g. MS Office, Google Suite) are likewise excluded.

## Layout
```
ats_tailor/__init__.py
ats_tailor/__main__.py        # python -m ats_tailor
ats_tailor/taxonomy.py        # alias matching
ats_tailor/ledger.py          # inventory.md + pets.md -> levels, pet projects
ats_tailor/postings.py        # posting -> keywords
ats_tailor/resume.py          # analyze + inject into resume markdown
ats_tailor/scorer.py          # resume-to-job matching & point scoring
ats_tailor/cli.py             # argparse
ats_tailor/data/taxonomy.json
ats_tailor/data/overrides.json
bin/ats-tailor                # tiny shell/python launcher (executable)
tests/ (unittest, stdlib only; run: python3 -m unittest discover -s tests -v)
```
Python 3.11+, stdlib only. No network.

## data/taxonomy.json
List of `{"canonical": str, "category": "frontend|backend|infra|ai|tools|practices", "aliases": [str,...]}`.
Aliases include the canonical. Must include at least (with spelling variants):
React [React, React.js, ReactJS, React JS]; Redux [Redux]; Redux Toolkit; TypeScript [TypeScript]; JavaScript [JavaScript, ES6];
Next.js [Next.js, NextJS, Next]; Angular [Angular, AngularJS? no — Angular only]; Vue [Vue, Vue.js, VueJS]; Svelte [Svelte, SvelteKit];
Node.js [Node.js, NodeJS, Node]; Express [Express, Express.js, ExpressJS]; NestJS [NestJS, Nest.js]; GraphQL; REST API [REST, REST API, RESTful];
Python; FastAPI; Django; Go [Go, Golang]; Java; Kotlin; Ruby on Rails [Ruby on Rails, Rails]; PHP; C#; .NET;
PostgreSQL [PostgreSQL, Postgres]; MongoDB [MongoDB, Mongo]; DynamoDB; Redis; Elasticsearch [Elasticsearch, ElasticSearch, Elastic]; MySQL; Kafka [Kafka, Apache Kafka]; RabbitMQ; SQS;
Docker; Kubernetes [Kubernetes, K8s]; Terraform; Helm; AWS [AWS, Amazon Web Services]; GCP [GCP, Google Cloud]; Azure; Cloudflare;
CI/CD [CI/CD, CICD, CI-CD]; GitLab CI [GitLab CI, GitLab]; Azure DevOps; Sentry; Grafana;
Jest; Vitest; Playwright; Cypress; Storybook; Webpack; Vite; Tailwind CSS [Tailwind CSS, Tailwind]; CSS Modules; Stylus; HTML5; CSS3;
Prisma; TypeORM; Drizzle; Stripe; Zustand; TanStack Query [TanStack Query, React Query]; Lit [Lit, Lit Web Components]; Web Components; NX [NX, Nx]; Turborepo;
Claude Code; MCP [MCP, Model Context Protocol]; LLM; RAG; Figma; WebSockets [WebSocket, WebSockets]; SSR [SSR, Server-Side Rendering]; SEO; A/B Testing [A/B testing, AB testing, split testing]; Accessibility [Accessibility, WCAG, a11y]; Git; Agile [Agile, Scrum].
Matching rules (taxonomy.py `find_matches(text) -> list[Match]`, Match = canonical, spelling (exact text found), start, end):
- case-insensitive; token boundary: not preceded by `[A-Za-z0-9_]` and not followed by `[A-Za-z0-9_+#]`; a following `.` is allowed only if NOT followed by a word char (so "React." end of sentence matches `React`, but "React.js" is matched whole as alias React.js).
- longest alias first, non-overlapping (so "Redux Toolkit" is never also a "Redux" match; "React Query" is TanStack Query, not React; "Next.js" never yields "Node"/"JS").
- `Go` alias matches only case-sensitively as `Go` or `Golang` and only when followed/preceded by tech context? Simplify: match `Golang` always, `Go` only when capitalized exactly and the line also contains one of: backend, golang, service, microservice, API, `(Go`, `Go,`, `Go)`. (Prevents "Go to market".)
- `Node` alias matches only capitalized "Node" not followed by a word like "modules"? Simplify: `Node` bare matches only as `Node` followed by `.js`, `,`, `/`, ` and `, `)`, or end of line — otherwise ignored.
- `spelling` preserves the posting's exact casing/form (e.g. "React.js", "ReactJS").

## ledger.py
`load_ledger(inventory_path, overrides_path) -> Ledger`:
Parse markdown table rows (`| Skill | Status | Evidence |`) of the inventory (3 columns; also 4-col "Item | Status | Evidence"; ignore header/separator rows).
For each row: find taxonomy canonicals in the Skill cell (taxonomy.find_matches). Level per row from the Status cell (first match wins):
1. starts with `NOT` (case-sensitive upper "NOT") → `not`
2. the Status cell OR the Evidence cell contains `personal projects only`, `pet projects only`, `pet project` or `(personal` (case-insens.) → `personal` (e.g. NestJS: Status "confirmed", Evidence "pet projects only" → personal). Rows listing mixed work/personal items (e.g. "TypeORM (work), Prisma (personal)") are resolved by overrides.json, not by this rule.
3. contains `PARTIAL` or `limited` → `partial`
4. otherwise (`documented`, `confirmed`, `applied`, …) → `confirmed`
Also scan the Evidence cell for sentences of the form `<names> NOT confirmed` (e.g. "Vitest NOT confirmed", "Stripe NOT confirmed", "Turborepo NOT confirmed", "Drizzle NOT confirmed", "Kafka/SQS NOT confirmed", "Stencil.js NOT confirmed"): every taxonomy canonical found in the clause immediately before `NOT confirmed` (split on `.`/`;`) gets level `not` **unless it already has a stronger level from a row Skill cell**.
Merge across rows by precedence confirmed > personal > partial > not > unknown (canonical absent from every row = `unknown`).
`Ledger.level(canonical) -> str`, `Ledger.evidence(canonical) -> str` (the Evidence cell of the winning row, trimmed), `Ledger.wording(canonical) -> str|None`.
`data/overrides.json`: `{"Python": {"level": "personal", "wording": "Python (personal projects, PyPI packages)"}}` — overrides win over inventory. Also: `"Cypress": {"level":"confirmed"}`? (Cypress is in resumes.) Overrides: Python (personal, wording above) and Prisma (`{"level":"personal"}`). Taxonomy must also include PWA [PWA, Progressive Web App] (category frontend) so the "limited" status row resolves to `partial`. The ledger exposes pets via `ledger.pets` (list set by `load_ledger` when a pets path is given, or assignable attribute); `Ledger.pets_for(c)` filters it. Report is a plain dict.
Pet projects: `load_pets(pets_path) -> list[Pet]`, Pet = name, github (url), stack (list of taxonomy canonicals found in the `**Стек:**` line), line (text inside backticks after `**Рядок для резюме:**`). Skip projects whose heading contains `private` or whose GitHub field says `private`. `Ledger.pets_for(canonical) -> list[Pet]`.

## postings.py
`extract_keywords(text) -> list[Keyword]`, Keyword = canonical, spelling (first occurrence's exact form), required (bool), count (occurrences), unrecognized=False.
- Sections: a markdown heading or line (lowercased) containing `nice to have|nice-to-have|bonus|preferred|a plus|plus:|good to have|would be great` starts a "nice" section until the next heading of equal-or-higher level that doesn't contain those words; everything else is required. If a canonical appears in both, required wins.
- Same canonical with several spellings: keep the spelling of the first occurrence in a **required** line if any, else first overall; also expose `spellings` (ordered unique list).
- `extract_unrecognized(text, known_spans) -> list[str]`: tokens that look like technology names but match no alias: CamelCase/mixed-case words with an inner capital (FooBarDB), tokens ending in `.js`/`JS`, ALLCAPS 3–8 letters not in a small stoplist (AND, THE, FOR, NOT, YOU, REMOTE, EU, USA, API?…, add reasonable stoplist: common English/business words, years, ATS, CTO, CEO, HR, B2B, KPI, OKR, SLA, ASAP, PTO). They are reported as `unrecognized`, level `unknown`, never added.

## resume.py
`analyze(job_text, resume_text, ledger) -> Report` and `tailor(...) -> (new_resume_text, Report)`.
For each posting keyword K (canonical C, posting spelling S):
1. `present`: base resume text contains S (token-bounded, case-insens.).
2. `variant_added`: resume contains another alias of C but not S → in the line of the **Technical Skills** section that contains that alias (first such line), insert `S, ` immediately before the first token occurrence of that alias. Allowed only if ledger level of C is confirmed/personal OR C was already in the resume (it was). Example: `**Frontend:** React, Redux` + posting "React.js" → `**Frontend:** React.js, React, Redux`.
   If the alias in the resume is only in prose (not in a skills line) append `S` to the category's skills line instead, per rule 3.
3. C absent from resume entirely:
   - ledger `confirmed` → `skill_added`: append `, wording-or-S` to the end of the skills line whose bold prefix matches the category (frontend→`**Frontend:**`, backend→`**Backend:**`, infra→`**Infrastructure:**`, ai→`**AI/LLM:**`, tools→`**Tools:**`, practices→`**Practices:**`); if that line is missing create it after the last skills line.
   - ledger `personal` → `personal_added`: append `, wording-or-S` to the `**Personal projects:**` line (create after the last skills line if missing; do not duplicate if C already listed there). If `ledger.pets_for(C)` is non-empty and the pet's github url is not yet in the resume → add the pet to the `## Personal Projects` section: heading inserted right after the end of the `## Open Source` section if present, else right before `## Education`, else at end; bullet format `- **[name](github)** — line (Stack: A, B, C)`; one bullet per pet, no duplicates, even for several keywords.
   - ledger `partial` → `needs_review` (NOT added; report includes ledger evidence).
   - ledger `not` or `unknown` → `gap` (NOT added; report includes a one-line `disclosure` suggestion for the cover letter framing transferable skills, e.g. "No hands-on Kafka experience; say so plainly and name the closest real experience.").
4. Unrecognized tokens → `unrecognized` list in report (not added).
Idempotence: tailoring an already-tailored resume with the same posting changes nothing (all keywords `present`).
Everything outside the Technical Skills block and the new Personal Projects section is byte-identical to the input.

## Report (JSON, `report.schema`)
```
{
 "keywords": [{"canonical","spelling","required","level","status","evidence","target_line"?}],
 "coverage": {"before":{"matched":int,"total":int,"required_matched":int,"required_total":int}, "after":{...}},
 "added": [spellings written],
 "gaps": [{"canonical","spelling","required","disclosure"}],
 "needs_review": [{"canonical","spelling","evidence"}],
 "unrecognized": [str],
 "next_steps": [str]
}
```
`status` ∈ present|present_unverified|variant_added|skill_added|personal_added|needs_review|gap. `coverage.after` counts keywords present in the tailored text (gaps stay unmatched → coverage honestly < 100%).

## scorer.py (Resume-to-Job Match Scoring)
`calculate_score(job_text, resume_text, ledger) -> ScoreResult`
Evaluates candidate match on a 0–100 scale:
- **Keyword extraction:** Job keywords extracted via `extract_keywords(job_text)` partitioned into required vs nice-to-have.
- **Presence check:** Evaluates resume claims text (`_claims(resume_text)`) using `has_token(claims, spelling)` (exact spelling) and `find_matches(claims)` (alias matches). If exact spelling or an alias is present in the resume claims, the skill is considered present.
- **Status & Credits:**
  - `present`: in resume claims AND ledger level in `(confirmed, personal)` → full credit (1.0).
  - `tailorable`: in ledger level `(confirmed, personal)` but NOT yet in resume → 75% credit (0.75).
  - `partial`: ledger level `partial` → 30% credit (0.30).
  - `gap`: ledger level `not` or `unknown` → 0% credit (0.0).
- **Weighting:**
  - Required keywords: weight 3.0.
  - Nice-to-have keywords: weight 1.0.
  - Total score: `(sum(earned_weight) / sum(total_weight)) * 100` (rounded to 1 decimal place).
- **Grades:**
  - `Excellent`: 90.0–100.0
  - `Good`: 75.0–89.9
  - `Moderate`: 60.0–74.9
  - `Low`: < 60.0
- **Gap Classification (`gaps` list):**
  - `critical`: required & not in ledger (`not` or `unknown`). Action: disclose honestly via cover letter with transferable skills.
  - `actionable`: required & in ledger (`confirmed` or `personal`) but missing from resume. Action: tailor resume using `ats-tailor tailor`.
  - `secondary`: nice-to-have gap (missing from resume or ledger). Action: optional skill, tailor if in ledger or address as bonus.
  - `review`: partial competence (ledger `partial`). Action: verify depth before claiming or address in interview.
- **Score Schema (JSON):**
```json
{
  "score": float,
  "grade": "Excellent|Good|Moderate|Low",
  "breakdown": {
    "score": float,
    "grade": str,
    "required_points": float,
    "required_total": float,
    "required_score": float,
    "nice_to_have_points": float,
    "nice_to_have_total": float,
    "nice_to_have_score": float,
    "matched_count": int,
    "tailorable_count": int,
    "partial_count": int,
    "gap_count": int,
    "critical_count": int,
    "actionable_count": int,
    "secondary_count": int,
    "review_count": int,
    "total_keywords": int,
    "matched": int,
    "tailorable": int,
    "gap": int,
    "review": int
  },
  "gaps": [
    {
      "canonical": str,
      "spelling": str,
      "required": bool,
      "level": "confirmed|personal|partial|not|unknown",
      "type": "critical|actionable|secondary|review",
      "description": str
    }
  ],
  "recommendations": [str],
  "keywords": [
    {
      "canonical": str,
      "spelling": str,
      "required": bool,
      "level": str,
      "evidence": str,
      "status": "present|present_unverified|tailorable|partial|gap",
      "is_present": bool,
      "weight": float,
      "credit": float,
      "earned": float
    }
  ],
  "unrecognized": [str]
}
```

## CLI (`ats-tailor`, `python -m ats_tailor`)
- `keywords --job FILE|-` → JSON list of extracted keywords.
- `analyze --job FILE|- --resume FILE [--inventory F] [--pets F] [--overrides F] [--json]` → report (human summary markdown by default, JSON with `--json`). No file writes.
- `score --job FILE|- --resume FILE [--inventory F] [--pets F] [--overrides F] [--json] [--detailed]` → match score & gap report (human markdown summary by default, JSON with `--json`, optional keyword table with `--detailed`).
- `tailor --job FILE|- --resume FILE --out FILE|- [--pdf FILE] [--report FILE] [--inventory F] [--pets F]` → writes tailored resume; optional `--pdf` compiles directly to PDF and verifies text layer; report JSON to `--report` if given, else a short summary to stderr. `--out` equal to `--resume` is refused (exit 2) unless `--force`.
- `pdf --resume FILE [--out FILE] [--title STR] [--json]` → compiles markdown or HTML resume directly to ATS-friendly PDF via headless Chrome/Chromium.
- `verify-pdf --pdf FILE [--keywords K1 K2 ...] [--json]` → checks text layer using `pdftotext` for broken glyphs `(cid:NN)`, replacement chars, literal contacts, and required keywords.
- `schema` → prints the report JSON shape.
- Defaults: inventory `$ATS_TAILOR_INVENTORY` or `~/work/resume/info/skills-inventory.md`; pets `$ATS_TAILOR_PETS` or `~/work/resume/info/open-source-repositories.md`.
- Exit codes: 0 success; 2 bad input (missing file, unreadable, empty posting); 1 unexpected error. Errors go to stderr, one line, no traceback.
- stdout carries only the payload (JSON or markdown) so agents can pipe it.

## Test fixtures (frozen, in tests/fixtures)
`inventory.md`, `pets.md`, `resume_base.md` (React written as "React" only), `posting_a.md`.
Expected on `posting_a.md` + `resume_base.md` + `inventory.md` + `pets.md`:
- React.js → `variant_added` (resume now has `React.js, React, Redux`)
- TypeScript, Node.js, GraphQL, Docker → `present`
- NestJS, Kubernetes, Redis → `personal_added` (already in Personal projects row of the base resume → treat as `present`; the base resume row lists them, so expected status `present`). Therefore add a second resume fixture `resume_nopersonal.md` = base minus the whole `**Personal projects:**` line, where NestJS, Kubernetes, Redis become `personal_added` and the row is recreated.
- Kafka, Terraform, Vitest, Stripe, Svelte → `gap` (not added; Vitest/Stripe level `not`, Kafka/Terraform/Svelte level `not` or `unknown`)
- FooBarDB → in `unrecognized`
- nice-to-have: Redis, Svelte, Docker have `required=false`.
