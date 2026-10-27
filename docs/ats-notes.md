# ATS notes: parsing and keyword matching (practical)

Research date: 2026-10-26. Method: based on web snippets, ATS vendor observations, and NotebookLM queries against comprehensive career strategy course transcripts ("Professional Career Strategy: LinkedIn, Portfolio, and Interview Mastery").

Confidence labels:
- **[vendor]** documented by the ATS vendor (needs a docs check before relying on it; none verified here)
- **[anecdote]** recruiter/blog/resume-tool report; commercially biased sources
- **[unverified]** inference or conflicting sources

## 1. Literal vs semantic matching

- Most modern ATS (Greenhouse, Lever, Ashby, Workday, SmartRecruiters) parse the resume into structured fields
  (name, contact, jobs, skills) and store the raw text. Recruiters then search that index. They do not "score"
  a resume the way resume-checker tools do. [anecdote]
- Auto-reject on resume keywords is rare in Greenhouse/Lever/Ashby. Rejection comes from application
  questions (knockouts) or human triage. [anecdote]
- Taleo and iCIMS are the legacy cases with scoring or knockout mechanics.
  - Taleo has knockout questions with point values and a keyword-based ranking ("Req Rank"), with recruiter cutoffs. [anecdote]
  - iCIMS lets recruiters mark answers as "Do Not Qualify", which auto-rejects the applicant. [anecdote, plausibly vendor-documented]
- Semantic/synonym matching: blogs claim Greenhouse, Workday and Ashby use "semantic" or LLM matching. Sources
  disagree, give no evidence, and the claims are marketing-flavored. [unverified]
- Taleo is described as exact or near-exact. [anecdote]
- "React" vs "React.js" vs "ReactJS": no source found. Assume search is token/stem based at best, so
  `React.js` may not match a recruiter's `React` query, and `ReactJS` may not match either. [unverified]
  Safe policy: include the posting's exact spelling and the common variants somewhere in the text.
- Alias handling is the recruiter's burden: good recruiters OR their variants by hand (`"React" OR "React.js" OR ReactJS`). [anecdote]
- Consequence: treat the posting's own spelling as canonical (it is what the recruiter typed into the req), and
  add variants as cheap insurance.

## 2. What a text-layer parser sees

- A PDF needs a real selectable text layer. Image-only or scanned PDFs yield nothing. [anecdote, near-universal]
- Text PDF vs DOCX: sources split on "DOCX safest" vs "text PDF fine". Modern parsers handle both. The real risk
  is how the PDF was generated. [anecdote]
  - LaTeX/odd fonts can produce `(cid:NN)` garbage or broken ligatures (fi, fl). [anecdote]
  - Headless-Chrome PDFs with web fonts are usually fine, but verify by extraction.
- Multi-column layouts and sidebars: parsers rebuild reading order from x/y coordinates, so columns can
  interleave (skills text merged into job text). This is the most agreed-on risk. [anecdote]
- Tables and text boxes: labels can detach from values. [anecdote]
- Headers/footers: many parsers ignore or drop them, so keep email and phone in the body. [anecdote]
- Icons (phone/mail glyphs) can extract as junk or as nothing. Write `Email:` / `Phone:` as literal text. [anecdote]
- Non-standard headings ("My toolbox") can break section detection. Use `Experience`, `Skills`, `Education`, `Projects`. [anecdote]
- Dates in plain `Mon YYYY - Mon YYYY` format parse most reliably (used for years-of-experience). [anecdote]
- Only a plain-text extraction (`pdftotext`) proves anything. A resume that looks fine can extract badly.

## 3. Skills section, variants, acronyms, frequency

- A dedicated `Skills` section helps because parsers map it to a skills field that recruiters can filter on. [anecdote]
  Also keep skills in experience bullets: context proves use, and some systems weigh recency and position. [unverified]
- Use the posting's spelling for each skill, then add the other common form once.
  Example: `React (React.js)`, `JavaScript (JS)`, `Continuous Integration (CI)`. [anecdote]
- Acronym plus full form once each covers both recruiter query styles. Do not repeat beyond that. [anecdote]
- Frequency: if a tool counts keywords, one to three mentions is enough. Beyond that is spam with no
  documented benefit. [unverified; sources only say "repeat key terms naturally"]
- Spelling variants worth tracking: `Node.js`/`NodeJS`/`Node`, `TypeScript`/`TS`, `Next.js`/`NextJS`,
  `PostgreSQL`/`Postgres`, `Kubernetes`/`K8s`, `CI/CD`, `GraphQL`, `AWS` vs `Amazon Web Services`,
  `LLM`/`Large Language Model`, `RAG`, `MCP`.
- Punctuation hurts tokenization: `CI/CD`, `Node.js`, `C#`, `.NET` can tokenize oddly. Include a plain variant
  (`CI CD`, `NodeJS`, `dotnet`) if the posting uses one. [unverified]

## 4. Knockouts, required skills, how recruiters search

- Knockouts live in application-form questions (work authorization, location, years with X, "do you have X").
  They are explicit yes/no or numeric. A resume cannot satisfy them, and answering falsely is the real risk. [anecdote; iCIMS/Taleo behavior plausibly vendor-documented]
- A form question like "Are you authorized to work in the U.S.?" is a reliable sign of a region restriction
  regardless of the posting text (same rule as in the repo CLAUDE.md).
- Recruiter search: Boolean (AND/OR/NOT, quotes, parentheses, wildcards) on the resume text and parsed fields,
  usually 2 to 5 must-have terms plus filters (location, title). [anecdote]
- Search is typically over the whole candidate pool, not just this req. Old and new resumes compete on recency
  and term hits. [unverified]
- Most shortlists are still human-read. The first scan is about 6 to 10 seconds on title, employer, recent
  bullets. [anecdote]
- Workday and SmartRecruiters specifics: nothing found. [unverified]

## 5. Honest practice

- Keyword stuffing of unconfirmed skills backfires at three stages: [anecdote, logical]
  1. Phone screen or tech interview probes it, and a miss costs the whole application.
  2. Skills tests and take-homes expose it.
  3. A later reference or background check, or a re-read by a different recruiter, finds the mismatch.
  Hidden white text is detectable on plain-text extraction and is treated as fraud by many recruiters. [anecdote]
- Never add a skill the user has not confirmed. A missing required keyword is a real gap: disclose it in the
  cover letter (repo rule) rather than editing the resume to pass a script.
- Personal projects are legitimate experience if labeled as what they are:
  - Put them in a `Projects` (or `Personal Projects`) section, separate from employment. Never inside a job's bullets.
  - Name the repo, the stack, and what was built (public link if possible). State "personal" or "open source".
  - Do not claim production use, users, scale, or team context that did not exist. Do not use frequency words
    ("daily", "weekly") unless documented.
  - Keywords from such projects may appear in `Skills`, but the skill should be traceable to the project line.
  - Reasonable framing: "built and shipped a working MCP server (personal project)" beats an inflated bullet
    under an employer.

## 6. Insights from NotebookLM Career Strategy Materials

Synthesized from course lessons on ATS optimization, skills structuring, and AI-driven job search:

- **Skills section as an ATS SEO engine**:
  - The skills block functions primarily as an index for ATS search algorithms.
  - **Avoid dividing into Hard Skills vs. Soft Skills**: Soft skills (*communication, teamwork, problem solving, leadership*) should **never** be listed as standalone words in the skills block. They do not pass recruiter scrutiny unless demonstrated through context, metrics, and achievements in experience bullets.
  - **Categorized technical skills**: Group by domain (e.g., *Frontend, Backend, Infrastructure, AI & Automation, Tools, Practices*).
  - Exclude baseline computer literacy (e.g., *Microsoft Office, Google Docs*) — focus on specialized domain tools.
- **AI & Automation Category**:
  - Explicitly include modern AI-assisted engineering and tooling (*Claude Code, MCP, LLM, RAG, Cursor, vibe coding*) as a dedicated domain rather than burying them under generic tools.
- **Pet Projects (Zero-to-One proof)**:
  - Demonstrates initiative, product thinking, and ability to handle ambiguity when commercial zero-to-one experience is lacking.
  - Showcases real working artifacts (repositories, live deployments) with explicit trade-offs and honest stack attribution.
- **Handling Gaps & Cover Letters**:
  - Unconfirmed required skills must never be fabricated. Address gaps by highlighting *transferable skills* and adjacent domain experience in the cover letter.

## Implications for ats-tailor

1. **Spelling-variant injection**
   - Source of truth is the posting's spelling. Inject variants only for skills already in the user's
     inventory (`info/skills-inventory.md` or equivalent), never for unconfirmed skills.
   - Inject once, in the Skills section, as `Canonical (Variant)` or as a second token. Do not repeat in bullets.
   - Cap at about 1 to 3 mentions per term in the whole resume. Flag, do not auto-fix, any term over the cap.
2. **Alias table design**
   - Flat JSON/YAML: `canonical -> [aliases]`, e.g. `react: ["React.js","ReactJS"]`, `postgresql: ["Postgres"]`.
   - Normalize on lowercase and strip punctuation for matching only. Output keeps the original casing and the posting's spelling.
   - Entries carry a `confirmed` flag from the user's inventory. Aliases of unconfirmed skills never get
     injected, only reported as gaps.
   - Include acronym <-> full form pairs. Treat uncertain pairs (e.g. `Go`/`Golang`) as aliases but never as
     license to claim.
   - Start small (about 50 entries from the user's actual stack) and grow by observed misses.
3. **Personal-projects section**
   - A separate `Projects` section, generated only from a user-maintained list (name, link, stack, one factual line).
   - The tool may reorder or select projects by posting relevance but must not rewrite claims to add keywords.
   - Tag each as "personal" to keep the honesty rule machine-checkable. No scale or production wording.
4. **Gap disclosure**
   - Compute coverage: required keywords in posting minus keywords present in the resume (with aliases).
   - Missing + confirmed-by-user -> add via the allowed variants. Missing + not confirmed -> list as a gap and draft one honest line for the cover letter.
   - Never auto-edit the resume to raise a score.
5. **Verification**
   - Always run the plain-text extraction check on the final PDF: no `(cid:` markers, email and phone literal,
     single-column order intact, keyword coverage report. (The repo already has `scripts/verify-resume-pdf.sh`.)
   - Re-verify the claims in sections 1 and 4 against vendor docs (Greenhouse/Lever/Ashby/Workday/Taleo/iCIMS
     support sites) before encoding any matching assumption as a hard rule.
