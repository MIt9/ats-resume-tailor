"""Job posting -> keywords (required vs nice-to-have) and unrecognized tech-looking tokens."""
import re
from dataclasses import dataclass, field

from .taxonomy import find_matches

_NICE = re.compile(r"nice to have|nice-to-have|bonus|preferred|a plus|plus:|good to have|would be great|буде плюсом|плюсом буде|бажано|перевагою буде|буде перевагою|додатково|von vorteil|wünschenswert|atout", re.I)
_BULLET = re.compile(r"^\s*([-*•]|\d+[.)])\s")
_HEAD = re.compile(r"^(#+)\s")


@dataclass
class Keyword:
    canonical: str
    spelling: str
    required: bool
    count: int
    spellings: list = field(default_factory=list)
    unrecognized: bool = False


def extract_keywords(text):
    nice_level = None  # heading level that opened the current nice section (99 = plain line)
    found = {}  # canonical -> {"sp": [(spelling, required)], ...}
    for line in text.split("\n"):
        h = _HEAD.match(line)
        marker = bool(_NICE.search(line))
        one_line = False
        if h:
            lvl = len(h.group(1))
            if marker:
                if nice_level is None or nice_level == 99:
                    nice_level = lvl
                else:
                    nice_level = min(nice_level, lvl)
            elif nice_level is not None and lvl <= nice_level:
                nice_level = None
        elif marker:
            if _BULLET.match(line):
                one_line = True  # "Redis is a plus" must not demote the rest of the section
            else:
                nice_level = 99
        elif nice_level == 99 and line.strip().endswith(":") and not _BULLET.match(line):
            nice_level = None  # a new plain-text label such as "Responsibilities:"
        required = nice_level is None and not one_line
        if h and marker:
            required = False
        for m in find_matches(line):
            found.setdefault(m.canonical, []).append((m.spelling, required))
    out = []
    for c, occ in found.items():
        spellings = list(dict.fromkeys(s for s, _ in occ))
        req = [s for s, r in occ if r]
        out.append(Keyword(c, req[0] if req else occ[0][0], bool(req), len(occ), spellings))
    return out


_STOP = set("""AND THE FOR NOT YOU REMOTE USA API ATS CTO CEO CFO COO HR B2B KPI OKR SLA ASAP PTO ALL ANY ARE BUT CAN NEW OUR
OUT WILL WITH YOUR USD EUR UTC EST PST CET FAQ URL PDF ETC TEAM ROLE WORK JOB EMEA APAC LATAM FULL PART TIME DEVOPS""".split())
_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)*")
_CAMEL = re.compile(r"[a-z][A-Z]|\.js$|JS$")
_BRANDS = {"LinkedIn", "GitHub", "YouTube", "DevOps", "iOS", "PhD", "JavaScript"}


def extract_unrecognized(text, known_spans):
    out = []
    for m in _TOKEN.finditer(text):
        t = m.group()
        if any(m.start() < e and s < m.end() for s, e in known_spans) or t in _BRANDS:
            continue
        if (_CAMEL.search(t) or re.fullmatch(r"[A-Z]{3,8}", t)) and t.upper() not in _STOP and t not in out:
            out.append(t)
    return out
