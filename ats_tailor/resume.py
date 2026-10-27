"""Analyze / tailor a markdown resume against a posting. Honesty rule: only confirmed/personal skills are written."""
import re

from .postings import extract_keywords, extract_unrecognized
from .taxonomy import CATEGORY, find_matches, has_token

SCHEMA = {
    "keywords": [{"canonical": "str", "spelling": "str (posting's form)", "required": "bool",
                  "level": "confirmed|personal|partial|not|unknown",
                  "status": "present|present_unverified|variant_added|skill_added|personal_added|needs_review|gap",
                  "evidence": "str", "target_line": "str (only when the resume was changed)"}],
    "coverage": {"before": {"matched": "int", "total": "int", "required_matched": "int", "required_total": "int"},
                 "after": "same shape as before"},
    "added": ["str: text written into the resume"],
    "gaps": [{"canonical": "str", "spelling": "str", "required": "bool", "disclosure": "str (cover-letter line)"}],
    "needs_review": [{"canonical": "str", "spelling": "str", "evidence": "str"}],
    "unrecognized": ["str"],
    "next_steps": ["str"],
}
_LABEL = re.compile(r"^\*\*([^*:\n]+):\*\*", re.M)
_SKILLS_HEAD = re.compile(r"^##\s+(?:Technical\s+Skills|Skills|Технічні навички|Навички|Ключові навички)\b", re.I)
_PREFIX = {"frontend": "**Frontend:**", "backend": "**Backend:**", "infra": "**Infrastructure:**",
           "ai": "**AI/LLM:**", "tools": "**Tools:**", "practices": "**Practices:**"}
_APPLICATIONS = re.compile(r"^## Applications submitted.*", re.M | re.S)  # bookkeeping, not claims
_PERSONAL_ROW = "**Personal projects:**"
_PERSONAL_ROWS = (_PERSONAL_ROW, "**Особисті проекти:**", "**Пет-проекти:**", "**Пет-проєкти:**")


def _skills_range(lines):
    i = next((n for n, l in enumerate(lines) if _SKILLS_HEAD.match(l)), None)
    if i is None:
        raise ValueError("resume has no '## Technical Skills' section")
    j = next((n for n in range(i + 1, len(lines)) if lines[n].startswith("## ")), len(lines))
    return i, j


def _skill_lines(lines):
    i, j = _skills_range(lines)
    return [n for n in range(i, j) if _LABEL.match(lines[n])]


def _alias_pos(lines, canonical):
    """(line index, column) of the first alias of `canonical` inside a skills line, label excluded."""
    for n in _skill_lines(lines):
        off = _LABEL.match(lines[n]).end()
        for m in find_matches(lines[n][off:]):
            if m.canonical == canonical:
                return n, off + m.start
    return None


def _append(lines, prefix, item):
    """Append `, item` to the skills line starting with `prefix`; create the line after the last skills line."""
    prefixes = _PERSONAL_ROWS if (prefix in _PERSONAL_ROWS or prefix == _PERSONAL_ROW) else (
        prefix if isinstance(prefix, (list, tuple)) else (prefix,)
    )
    for n in _skill_lines(lines):
        if any(lines[n].lower().startswith(p.lower()) for p in prefixes):
            if not has_token(lines[n], item):
                lines[n] = lines[n].rstrip() + ", " + item
            return n
    default_prefix = prefixes[0]
    skill_rows = _skill_lines(lines)
    if skill_rows:
        n = skill_rows[-1] + 1
    else:
        i, _ = _skills_range(lines)
        n = i + 1
        while n < len(lines) and lines[n].strip() == "":
            n += 1
    lines.insert(n, default_prefix + " " + item)
    return n


def _add_pets(lines, pets, ledger=None):
    text = "\n".join(lines)
    pets = list({p.github: p for p in pets}.values())
    pets = [p for p in pets if p.github not in text]
    if not pets:
        return
    bullets = []
    for p in pets:
        valid_stack = [s for s in p.stack if not ledger or ledger.level(s) in ("confirmed", "personal")]
        bullets.append("- **[%s](%s)** — %s (Stack: %s)" % (p.name, p.github, p.line, ", ".join(valid_stack)))
    heads = [n for n, l in enumerate(lines) if l.startswith("## ")]
    title = lambda n: lines[n][3:].strip().lower()
    nxt = lambda n: next((h for h in heads if h > n), len(lines))
    pp = next((n for n in heads if title(n) in ("personal projects", "особисті проекти", "пет-проекти", "пет-проєкти")), None)
    if pp is not None:  # extend an existing section
        end = nxt(pp)
        while end > pp + 1 and lines[end - 1].strip() in ("", "---"):
            end -= 1
        lines[end:end] = bullets
        return
    os_ = next((n for n in heads if title(n) in ("open source", "open-source", "open source projects", "відкритий код")), None)
    edu = next((n for n in heads if title(n) in ("education", "освіта")), None)
    at = nxt(os_) if os_ is not None else edu if edu is not None else len(lines)
    new = ["## Personal Projects", "", *bullets, "", "---", ""]
    if at == len(lines):
        while lines and lines[-1] == "":
            lines.pop()
        new = ["", "---", ""] + new[:-3] + [""]
        at = len(lines)
    lines[at:at] = new


def _claims(text):
    """Resume text that counts as a claim: no skills labels, no applications log."""
    return _LABEL.sub("", _APPLICATIONS.sub("", text))


def _count(entries, base):
    ok = [e for e in entries if base(e)]
    return {"matched": len(ok), "total": len(entries),
            "required_matched": sum(e["required"] for e in ok), "required_total": sum(e["required"] for e in entries)}


def tailor(job_text, resume_text, ledger):
    keywords = extract_keywords(job_text)
    body = _claims(resume_text)
    lines = resume_text.split("\n")
    entries, added, gaps, review, pets = [], [], [], [], []
    for k in keywords:
        c, s = k.canonical, k.spelling
        lv, ev = ledger.level(c), ledger.evidence(c)
        e = {"canonical": c, "spelling": s, "required": k.required, "level": lv, "evidence": ev}
        text = ledger.wording(c) or s
        pos = _alias_pos(lines, c) if lv in ("confirmed", "personal") else None
        if has_token(body, s, c) and lv not in ("partial", "not"):
            e["status"] = "present" if lv in ("confirmed", "personal") else "present_unverified"
        elif pos:
            n, col = pos
            lines[n] = lines[n][:col] + s + ", " + lines[n][col:]
            e["status"], e["target_line"], text = "variant_added", lines[n], s
        elif lv == "confirmed":
            n = _append(lines, _PREFIX[CATEGORY.get(c, "tools")], text)
            e["status"], e["target_line"] = "skill_added", lines[n]
        elif lv == "personal":
            n = _append(lines, _PERSONAL_ROW, text)
            pets += ledger.pets_for(c)
            e["status"], e["target_line"] = "personal_added", lines[n]
        elif lv == "partial":
            e["status"] = "needs_review"
            review.append({"canonical": c, "spelling": s, "evidence": ev})
        else:
            e["status"] = "gap"
            d = ("No hands-on %s experience; say so plainly and name the closest real experience." % c if lv == "not" else
                 "%s is not in the skills inventory; ask the candidate, else disclose it as a gap." % c)
            gaps.append({"canonical": c, "spelling": s, "required": k.required, "disclosure": d})
        if e["status"] in ("variant_added", "skill_added", "personal_added"):
            added.append(text)
        entries.append(e)
    _add_pets(lines, pets, ledger)
    out = "\n".join(lines)
    out_body = _claims(out)
    before = _count(entries, lambda e: has_token(body, e["spelling"], e["canonical"]))
    after = _count(entries, lambda e: has_token(out_body, e["spelling"], e["canonical"]))
    spans = [(m.start, m.end) for m in find_matches(job_text)]
    unrec = extract_unrecognized(job_text, spans)
    steps = []
    if added:
        steps.append("Rebuild the PDF, then run scripts/verify-resume-pdf.sh <pdf> with the added keywords: " + ", ".join(added))
    if gaps:
        steps.append("Cover letter: disclose these gaps honestly, never add them to the resume: " + ", ".join(g["canonical"] for g in gaps))
    if review:
        steps.append("Ask the candidate before claiming (partial evidence, not added): " + ", ".join(r["canonical"] for r in review))
    if unrec:
        steps.append("Check unrecognized terms by hand against the posting: " + ", ".join(unrec))
    report = {"keywords": entries, "coverage": {"before": before, "after": after}, "added": added, "gaps": gaps,
              "needs_review": review, "unrecognized": unrec, "next_steps": steps}
    return out, report


def analyze(job_text, resume_text, ledger):
    return tailor(job_text, resume_text, ledger)[1]
