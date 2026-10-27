"""Alias matching: find known technology names in text."""
import json
import re
from dataclasses import dataclass
from pathlib import Path

with open(Path(__file__).parent / "data" / "taxonomy.json", encoding="utf-8") as _f:
    ENTRIES = json.load(_f)
CATEGORY = {e["canonical"]: e["category"] for e in ENTRIES}
# Common-word aliases match only with exact capitalisation (all-caps aliases too).
_CS = {"Lit", "Express", "Rails", "Elastic", "Helm", "Go", "Node"}
_GO_CTX = re.compile(r"\b(backend|golang|services?|microservices?|api)\b", re.I)


@dataclass(frozen=True)
class Match:
    canonical: str
    spelling: str
    start: int
    end: int


def _regex(alias):
    """Token-bounded regex for a literal alias (also used for presence checks)."""
    core = re.escape(alias).replace(r"\ ", r"\s+")
    # bare "Node" only counts in list-like positions ("Node, ", "React/Node", "Node and", "Node)", end of line)
    tail = r"(?=,|/| and |\)|$)" if alias == "Node" else r"(?![A-Za-z0-9_+#])(?!\.\w)"
    cs = alias in _CS or alias == alias.upper()
    flags = re.M | (0 if cs else re.I)
    return re.compile(r"(?<![A-Za-z0-9_])" + core + tail, flags)


_PATTERNS = [(e["canonical"], a, _regex(a)) for e in ENTRIES for a in e["aliases"]]


def has_token(text, s, canonical=None):
    if canonical:
        return any(m.canonical == canonical and m.spelling.lower() == s.lower() for m in find_matches(text))
    matches = find_matches(text)
    if any(m.spelling.lower() == s.lower() for m in matches):
        return True
    return _regex(s).search(text) is not None


def find_matches(text):
    cands = []
    for canonical, alias, rx in _PATTERNS:
        for m in rx.finditer(text):
            if alias == "Go":
                ls = text.rfind("\n", 0, m.start()) + 1
                le = text.find("\n", m.end())
                line = text[ls:le if le >= 0 else len(text)]
                if not (_GO_CTX.search(line) or any(x in line for x in ("(Go", "Go,", "Go)"))):
                    continue
            cands.append(Match(canonical, m.group(), m.start(), m.end()))
    cands.sort(key=lambda m: (m.start - m.end, m.start))  # longest first
    picked = []
    for c in cands:
        if all(c.end <= p.start or c.start >= p.end for p in picked):
            picked.append(c)
    return sorted(picked, key=lambda m: m.start)
