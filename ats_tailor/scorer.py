"""Resume-to-job matching & scoring tool (ats-tailor score).

Calculates a 0-100 match score based on verified candidate skills in ledger,
existing resume claims, and job posting requirements. Categorizes gaps into
critical, actionable, secondary, and review items.
"""
import dataclasses
import re
from dataclasses import dataclass, field
from typing import Any

from .postings import extract_keywords, extract_unrecognized_classified
from .resume import _claims
from .taxonomy import find_matches, has_token

# Weightings and credit multipliers
REQUIRED_WEIGHT = 3.0
NICE_WEIGHT = 1.0

CREDIT_PRESENT = 1.0
CREDIT_TAILORABLE = 0.75
CREDIT_PARTIAL = 0.30
CREDIT_GAP = 0.0


@dataclass
class ScoreResult:
    score: float
    grade: str
    breakdown: dict[str, Any]
    gaps: list[dict[str, Any]]
    recommendations: list[str]
    keywords: list[dict[str, Any]] = field(default_factory=list)
    unrecognized: list[str] = field(default_factory=list)
    upper_bound: bool = False
    unrecognized_required: list[str] = field(default_factory=list)
    unrecognized_warning: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "grade": self.grade,
            "breakdown": self.breakdown,
            "gaps": self.gaps,
            "recommendations": self.recommendations,
            "keywords": self.keywords,
            "unrecognized": self.unrecognized,
            "upper_bound": self.upper_bound,
            "unrecognized_required": self.unrecognized_required,
            "unrecognized_warning": self.unrecognized_warning,
        }

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def __contains__(self, item: str) -> bool:
        return hasattr(self, item)


def grade_for_score(score: float) -> str:
    if score >= 90.0:
        return "Excellent"
    if score >= 75.0:
        return "Good"
    if score >= 60.0:
        return "Moderate"
    return "Low"


def calculate_score(job_text: str, resume_text: str, ledger: Any) -> ScoreResult:
    keywords = extract_keywords(job_text)
    claims = _claims(resume_text)

    # All canonical skills mentioned in candidate resume claims
    resume_matches = find_matches(claims)
    resume_canonicals = {m.canonical for m in resume_matches}

    classified = []
    gaps = []
    variant_spellings = []

    for k in keywords:
        c, s = k.canonical, k.spelling
        lv = ledger.level(c)
        ev = ledger.evidence(c)

        has_exact = has_token(claims, s, c)
        has_alias = c in resume_canonicals
        is_present = has_exact or (has_alias and lv in ("confirmed", "personal"))

        if has_alias and not has_exact and lv in ("confirmed", "personal"):
            variant_spellings.append((c, s))

        # Status and point calculation
        if is_present and lv in ("confirmed", "personal"):
            status = "present"
            credit = CREDIT_PRESENT
        elif has_exact and lv == "unknown":
            # Candidate wrote it in the resume and the ledger has no row; a ledger
            # "partial"/"not" is a denial and must stay a gap/review item.
            status = "present_unverified"
            credit = CREDIT_PRESENT
        elif lv in ("confirmed", "personal"):
            status = "tailorable"
            credit = CREDIT_TAILORABLE
        elif lv == "partial":
            status = "partial"
            credit = CREDIT_PARTIAL
        else:
            status = "gap"
            credit = CREDIT_GAP

        weight = REQUIRED_WEIGHT if k.required else NICE_WEIGHT
        earned = weight * credit

        item = {
            "canonical": c,
            "spelling": s,
            "required": k.required,
            "level": lv,
            "evidence": ev,
            "status": status,
            "is_present": is_present,
            "weight": weight,
            "credit": credit,
            "earned": earned,
        }
        classified.append(item)

        # Gap classification
        if status not in ("present", "present_unverified"):
            if lv == "partial":
                gap_type = "review"
                desc = (
                    f"Partial competence recorded in ledger ({ev or 'limited'}); "
                    "verify hands-on depth before claiming, or address in interview."
                )
            elif k.required:
                if lv in ("confirmed", "personal"):
                    gap_type = "actionable"
                    desc = f"In ledger as {lv}; tailor resume to include it."
                else:
                    gap_type = "critical"
                    if lv == "not":
                        desc = (
                            f"Missing required skill ({c} confirmed not experienced); "
                            "disclose via transferable skills in cover letter."
                        )
                    else:
                        desc = (
                            f"Missing required skill ({c} not in ledger); "
                            "disclose via transferable skills in cover letter."
                        )
            else:
                gap_type = "secondary"
                if lv in ("confirmed", "personal"):
                    desc = f"In ledger as {lv}; optional nice-to-have skill, tailor resume to include it."
                else:
                    desc = f"Nice-to-have skill ({c}) not in ledger; optional, address as bonus if candidate has adjacent exposure."

            gaps.append({
                "canonical": c,
                "spelling": s,
                "required": k.required,
                "level": lv,
                "type": gap_type,
                "description": desc,
            })

    # Points summation
    req_items = [item for item in classified if item["required"]]
    nice_items = [item for item in classified if not item["required"]]

    req_total = sum(item["weight"] for item in req_items)
    req_earned = sum(item["earned"] for item in req_items)

    nice_total = sum(item["weight"] for item in nice_items)
    nice_earned = sum(item["earned"] for item in nice_items)

    total_weight = req_total + nice_total
    total_earned = req_earned + nice_earned

    raw_score = (total_earned / total_weight * 100.0) if total_weight > 0 else 0.0
    score = round(raw_score, 1)
    grade = grade_for_score(score)

    # Unrecognized terms & required status
    spans = [(m.start, m.end) for m in find_matches(job_text)]
    unrec_classified = extract_unrecognized_classified(job_text, spans)
    unrecognized = [t for t, _ in unrec_classified]
    unrec_required = [t for t, req in unrec_classified if req]

    upper_bound = bool(unrec_required)
    unrec_warning: str | None = None
    if unrec_required:
        unrec_warning = f"Score is an upper bound: {len(unrec_required)} unrecognized terms not evaluated"

    matched_count = sum(1 for item in classified if item["status"] in ("present", "present_unverified"))
    tailorable_count = sum(1 for item in classified if item["status"] == "tailorable")
    partial_count = sum(1 for item in classified if item["status"] == "partial")
    gap_count = sum(1 for item in classified if item["status"] == "gap")

    critical_count = sum(1 for g in gaps if g["type"] == "critical")
    actionable_count = sum(1 for g in gaps if g["type"] == "actionable")
    secondary_count = sum(1 for g in gaps if g["type"] == "secondary")
    review_count = sum(1 for g in gaps if g["type"] == "review")

    breakdown = {
        "score": score,
        "grade": grade,
        "required_points": round(req_earned, 1),
        "required_total": round(req_total, 1),
        "required_score": round((req_earned / req_total * 100.0), 1) if req_total else 100.0,
        "nice_to_have_points": round(nice_earned, 1),
        "nice_to_have_total": round(nice_total, 1),
        "nice_to_have_score": round((nice_earned / nice_total * 100.0), 1) if nice_total else 100.0,
        "matched_count": matched_count,
        "tailorable_count": tailorable_count,
        "partial_count": partial_count,
        "gap_count": gap_count,
        "critical_count": critical_count,
        "actionable_count": actionable_count,
        "secondary_count": secondary_count,
        "review_count": review_count,
        "total_keywords": len(classified),
        # Aliases for convenience
        "matched": matched_count,
        "tailorable": tailorable_count,
        "gap": gap_count,
        "review": review_count,
        # Always-present unrecognized keys
        "upper_bound": upper_bound,
        "unrecognized_required": unrec_required,
        "unrecognized_warning": unrec_warning,
    }

    # Recommendations
    recs = []
    actionables = [g for g in gaps if g["type"] == "actionable"]
    criticals = [g for g in gaps if g["type"] == "critical"]
    reviews = [g for g in gaps if g["type"] == "review"]
    secondaries = [g for g in gaps if g["type"] == "secondary"]

    if actionables:
        names = ", ".join(g["canonical"] for g in actionables)
        recs.append(f"Tailor resume: {len(actionables)} verified skills can be added honestly ({names}). Run 'ats-tailor tailor'.")

    if variant_spellings:
        v_str = ", ".join(f"{s} (for {c})" for c, s in variant_spellings)
        recs.append(f"Spelling variants: {len(variant_spellings)} skills exist under alternate spellings ({v_str}). Run 'ats-tailor tailor' to align.")

    if criticals:
        names = ", ".join(g["canonical"] for g in criticals)
        recs.append(f"Cover letter disclosures: {len(criticals)} missing required skills must be disclosed honestly ({names}). Do not add to resume.")

    if reviews:
        names = ", ".join(g["canonical"] for g in reviews)
        recs.append(f"Needs review: {len(reviews)} skills have partial evidence ({names}). Confirm hands-on proficiency before claiming.")

    if secondaries:
        names = ", ".join(g["canonical"] for g in secondaries)
        recs.append(f"Optional skills: {len(secondaries)} nice-to-have skills are missing ({names}). Highlight adjacent exposure where possible.")

    # High-level assessment
    if score >= 90.0:
        recs.append("Strong match (90+). Resume strongly matches posting requirements.")
    elif score >= 75.0:
        recs.append("Good match (75-89). Tailoring actionable skills will maximize ATS compatibility.")
    elif score >= 60.0:
        recs.append("Moderate match (60-74). Address critical skill gaps thoughtfully in cover letter.")
    else:
        recs.append("Low match (<60). High gap density; evaluate role fit and emphasize transferable capabilities.")

    # Unrecognized terms recommendations
    if unrec_required:
        recs.append(f"Warning: {unrec_warning} ({', '.join(unrec_required)}).")
    elif unrecognized:
        recs.append("Check unrecognized terms by hand against posting: " + ", ".join(unrecognized))

    return ScoreResult(
        score=score,
        grade=grade,
        breakdown=breakdown,
        gaps=gaps,
        recommendations=recs,
        keywords=classified,
        unrecognized=unrecognized,
        upper_bound=upper_bound,
        unrecognized_required=unrec_required,
        unrecognized_warning=unrec_warning,
    )


def format_score_report(result: ScoreResult, detailed: bool = False) -> str:
    """Format human-friendly markdown / terminal report."""
    b = result.breakdown
    unrec_warning = result.unrecognized_warning
    lines = [
        "# ATS Resume-to-Job Match Score",
        "",
        f"**Score:** {result.score:.1f}/100 — **{result.grade}**",
    ]
    # Show the caveat line at EVERY grade level when there are unrecognized required terms
    if unrec_warning:
        lines.append(f"*({unrec_warning})*")

    lines += [
        "",
        "### Score Breakdown",
        f"- **Required Skills:** {b['required_points']:.1f} / {b['required_total']:.1f} pts ({b['required_score']:.1f}%)",
        f"- **Nice-to-Have Skills:** {b['nice_to_have_points']:.1f} / {b['nice_to_have_total']:.1f} pts ({b['nice_to_have_score']:.1f}%)",
        f"- **Matched Keywords (Present):** {b['matched_count']}",
        f"- **Tailorable Keywords (In Ledger):** {b['tailorable_count']}",
        f"- **Needs Review (Partial):** {b['review_count']}",
        f"- **Gaps (Missing from Ledger):** {b['gap_count']}",
    ]

    if result.gaps:
        lines += ["", "### Gaps & Action Items"]
        for g in result.gaps:
            tag = g["type"].upper()
            req_str = "required" if g["required"] else "nice-to-have"
            lines.append(f"- **[{tag}] {g['canonical']}** ({req_str}, spelling: `{g['spelling']}`): {g['description']}")

    if detailed and result.keywords:
        lines += [
            "",
            "### Detailed Keyword Analysis",
            "| Keyword | Posting spelling | Required | Level | Status | Weight | Earned |",
            "|---|---|---|---|---|---|---|",
        ]
        for k in result.keywords:
            lines.append(
                f"| {k['canonical']} | {k['spelling']} | {'yes' if k['required'] else 'no'} | "
                f"{k['level']} | {k['status']} | {k['weight']:.1f} | {k['earned']:.1f} |"
            )

    if result.unrecognized:
        lines += ["", "### Unrecognized Terms"]
        if unrec_warning:
            lines.append(f"Warning: {unrec_warning}.")
        lines.append("- " + ", ".join(result.unrecognized))

    if result.recommendations:
        lines += ["", "### Recommendations"]
        for idx, r in enumerate(result.recommendations, 1):
            lines.append(f"{idx}. {r}")

    return "\n".join(lines) + "\n"
