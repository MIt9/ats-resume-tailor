---
name: ats-resume-tailor
description: >-
  Honest ATS keyword tailoring and scoring CLI for markdown resumes. Use when evaluating job postings,
  calculating 0-100 ATS match scores, identifying verified vs missing skills, tailoring resumes with
  honest candidate ledger evidence, and generating cover letter gap disclosures.
---

# ATS Resume Tailor & Scorer

A CLI tool for autonomous AI agents and engineers to match, score, and tailor markdown resumes against job postings while strictly adhering to the **Honesty Invariant** (never hallucinate or claim unconfirmed skills).

## When to Use This Skill

Activate this skill when:
- Evaluating a candidate's fit for a job posting.
- Calculating an objective ATS match score (0–100) with points breakdown.
- Auditing resume keywords for ATS parsing compatibility (alias variations, exact spellings).
- Tailoring a base markdown resume for a specific job application.
- Identifying real technology gaps and formulating honest cover letter disclosures.

---

## Core Principles & Invariants

1. **Honesty Invariant (Hard Boundary)**:
   - Skills with level `confirmed` → added to the relevant technical category row.
   - Skills with level `personal` → added to `**Personal projects:**` row and referenced in `## Personal Projects`.
   - Skills with level `partial`, `not`, or `unknown` → **NEVER** injected into the resume. Reported as `needs_review` or `gap`.
2. **Soft Skills Separation**:
   - Generic soft skills (*communication, leadership, problem solving*) are excluded from keyword injection. They belong in experience bullet points as quantified achievements (*Scope/Context + Result*), not in the ATS technical skills block.
3. **Surgical Precision**:
   - Only modifies the `## Technical Skills` section and verified `## Personal Projects`. All other sections (experience, header, education) remain byte-identical.
4. **Deterministic & Idempotent**:
   - Re-running tailor on an already-tailored resume produces identical output.

---

## Command Reference

Run via `./bin/ats-tailor` or `python3 -m ats_tailor`:

### 1. Match & Score (`ats-tailor score`)
Calculates a 0–100 match score, categorizes gaps, and generates actionable advice:
```bash
ats-tailor score --job job.md --resume resume.md [--inventory inv.md] [--pets pets.md] [--detailed] [--json]
```
- **Weights**: Required skills carry 3x weight compared to nice-to-have skills.
- **Grades**: `Excellent` (90+), `Good` (75–89), `Moderate` (60–74), `Low` (<60).
- **Gap Categories**:
  - `[CRITICAL]`: Required skill unconfirmed or level `not`. Disclose in cover letter via transferable skills.
  - `[ACTIONABLE]`: Required skill verified in ledger, but missing from current resume. Run `tailor`.
  - `[SECONDARY]`: Optional / nice-to-have skill missing.
  - `[REVIEW]`: Partial or limited evidence. Verify with candidate before claiming.

### 2. Analyze Coverage (`ats-tailor analyze`)
Dry-run check of keyword coverage and status without modifying files:
```bash
ats-tailor analyze --job job.md --resume resume.md [--inventory inv.md] [--pets pets.md] [--json]
```

### 3. Tailor Resume (`ats-tailor tailor`)
Injects confirmed skills and verified pet projects into the resume (and optionally builds PDF):
```bash
ats-tailor tailor --job job.md --resume resume.md --out tailored.md [--pdf tailored.pdf] [--report report.json]
```

### 4. Compile PDF (`ats-tailor pdf`)
Directly compiles a markdown or HTML resume into an ATS-friendly, single-column PDF:
```bash
ats-tailor pdf --resume tailored.md --out tailored.pdf
```

### 5. Verify PDF Text Layer (`ats-tailor verify-pdf`)
Checks the PDF text layer using `pdftotext` for glyph corruption, clean contacts, and keyword presence:
```bash
ats-tailor verify-pdf --pdf tailored.pdf [--keywords React TypeScript]
```

### 6. Extract Keywords (`ats-tailor keywords`)
Inspects technology keywords extracted from a job posting:
```bash
ats-tailor keywords --job job.md
```

---

## Standard Agent Workflow

```
       1. Job Posting + Candidate Ledger
                     │
                     ▼
       2. ats-tailor score --job J --resume R
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
    Score >= 75             Score < 60
         │                       │
         ▼                       ▼
3. ats-tailor tailor        Review Critical Gaps
   --out tailored.md        (Advise skip or heavy
         │                  cover letter framing)
         ▼
4. Generate Cover Letter
   (Disclose gaps honestly using transferable skills)
         │
         ▼
5. Export to PDF & Verify Plain Text
```

## Environment Variables
- `ATS_TAILOR_INVENTORY`: Default path to candidate `skills-inventory.md`.
- `ATS_TAILOR_PETS`: Default path to candidate `open-source-repositories.md`.
- `ATS_TAILOR_OVERRIDES`: Default path to custom `overrides.json`.
