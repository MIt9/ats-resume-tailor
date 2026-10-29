"""Job posting -> keywords (required vs nice-to-have) and unrecognized tech-looking tokens."""
import re
from dataclasses import dataclass, field

from .taxonomy import find_matches

_NICE = re.compile(r"nice to have|nice-to-have|bonus|preferred|a plus|plus:|good to have|would be great|буде плюсом|плюсом буде|бажано|перевагою буде|буде перевагою|додатково|von vorteil|wünschenswert|atout", re.I)
_BULLET = re.compile(r"^\s*([-*•🔹▪✔✅➤]|\d+[.)])\s")
_HEAD = re.compile(r"^(#+)\s")


@dataclass
class Keyword:
    canonical: str
    spelling: str
    required: bool
    count: int
    spellings: list = field(default_factory=list)
    unrecognized: bool = False


def _classify_lines(text):
    """Shared generator: yields (line, required: bool) for each line in text.

    Section-level state machine:
    - A heading containing a nice-to-have marker opens a nice section until the
      next heading of equal-or-higher level that doesn't contain such a marker.
    - A non-bullet, non-heading line containing a nice-to-have marker opens a
      plain-text nice section (nice_level=99) until a new non-bullet label line
      ending in ':' resets it.
    - A bullet line (or an emoji-bullet line) containing a nice-to-have marker
      is one-line-only: only that single line is demoted; the state is NOT changed.
    - Headings always switch state; bullet-level markers never switch state.
    """
    nice_level = None  # heading level or 99 for plain-text section
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
                # A nice-to-have marker on a bullet/emoji-bullet line only
                # affects that single line — do NOT change nice_level.
                one_line = True
            else:
                nice_level = 99
        elif nice_level == 99 and line.strip().endswith(":") and not _BULLET.match(line):
            nice_level = None  # a new plain-text label such as "Responsibilities:"
        required = nice_level is None and not one_line
        if h and marker:
            required = False
        yield line, required


def extract_keywords(text):
    found = {}  # canonical -> {sp: [(spelling, required)], ...}
    for line, required in _classify_lines(text):
        for m in find_matches(line):
            found.setdefault(m.canonical, []).append((m.spelling, required))
    out = []
    for c, occ in found.items():
        spellings = list(dict.fromkeys(s for s, _ in occ))
        req = [s for s, r in occ if r]
        out.append(Keyword(c, req[0] if req else occ[0][0], bool(req), len(occ), spellings))
    return out


_STOP = set("""AND THE FOR NOT YOU REMOTE USA API ATS CTO CEO CFO COO HR B2B KPI OKR SLA ASAP PTO ALL ANY ARE BUT CAN NEW OUR
OUT WILL WITH YOUR USD EUR UTC EST PST CET FAQ URL PDF ETC TEAM ROLE WORK JOB EMEA APAC LATAM FULL PART TIME DEVOPS
ABOUT STACK GOOD FIT HIRING PROCESS ROLES RESPONSIBILITIES REQUIREMENTS QUALIFICATIONS EXPERIENCE BENEFITS PERKS
OVERVIEW SUMMARY LOCATION SALARY COMPENSATION COMPANY CANDIDATE CANDIDATES APPLY APPLICANT APPLICANTS WHAT WHO HOW WHY
WHEN WHERE INTERVIEW NOTES NOTE DETAILS DESCRIPTION EXPECTATIONS OFFER JOIN MISSION VALUES CULTURE PLUS BONUS NICE TECH YES
LLC INC LTD CORP GMBH PLC LLP KPMG PWC DELOITTE NDA EEO VAT EIN ESG SAAS PAAS IAAS""".split())
_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)*")
_CAMEL = re.compile(r"[a-z][A-Z]|\.js$|JS$")
_BRANDS = {"LinkedIn", "GitHub", "YouTube", "DevOps", "iOS", "PhD", "JavaScript", "Djinni", "Teamtailor"}
_COUNTRY_LINE = re.compile(r"\b(Country of residence|Countries we consider|Країни, де розглядаємо)\b", re.I)

_COUNTRIES = {
    "afghanistan", "albania", "algeria", "andorra", "angola", "anguilla", "antarctica",
    "argentina", "armenia", "aruba", "australia", "austria", "azerbaijan", "bahamas", "bahrain",
    "bangladesh", "barbados", "belarus", "belgium", "belize", "benin", "bermuda", "bhutan", "bolivia",
    "bosnia", "botswana", "brazil", "brunei", "bulgaria", "burkina", "burundi", "cambodia", "cameroon",
    "canada", "chile", "china", "colombia", "comoros", "congo", "croatia", "cuba", "cyprus", "czech",
    "denmark", "djibouti", "dominica", "ecuador", "egypt", "eritrea", "estonia", "ethiopia", "fiji",
    "finland", "france", "gabon", "gambia", "georgia", "germany", "ghana", "gibraltar", "greece",
    "greenland", "grenada", "guam", "guatemala", "guernsey", "guinea", "guyana", "haiti", "honduras",
    "hungary", "iceland", "india", "indonesia", "iran", "iraq", "ireland", "israel", "italy", "jamaica",
    "japan", "jersey", "jordan", "kazakhstan", "kenya", "kuwait", "kyrgyzstan", "laos", "latvia",
    "lebanon", "lesotho", "liberia", "libya", "liechtenstein", "lithuania", "luxembourg", "madagascar",
    "malawi", "malaysia", "maldives", "mali", "malta", "martinique", "mauritania", "mauritius", "mayotte",
    "mexico", "micronesia", "moldova", "monaco", "mongolia", "montenegro", "montserrat", "morocco",
    "mozambique", "myanmar", "namibia", "nauru", "nepal", "netherlands", "nicaragua", "niger", "nigeria",
    "norway", "oman", "pakistan", "palau", "palestine", "panama", "paraguay", "peru", "philippines",
    "poland", "portugal", "qatar", "romania", "russia", "rwanda", "samoa", "senegal", "serbia",
    "seychelles", "singapore", "slovakia", "slovenia", "somalia", "spain", "sudan", "suriname", "sweden",
    "switzerland", "syria", "taiwan", "tajikistan", "tanzania", "thailand", "togo", "tonga", "tunisia",
    "turkey", "turkmenistan", "tuvalu", "uganda", "ukraine", "uruguay", "uzbekistan", "vanuatu",
    "venezuela", "vietnam", "yemen", "zambia", "zimbabwe", "islands", "island", "republic", "democratic",
    "kingdom", "states", "territory", "british", "american", "south", "north", "saint", "herzegovina",
}


def extract_company_names(text):
    """Extract likely company names from the first 25 lines of a posting.

    Kept patterns (Djinni-style title + LLC/Inc/Ltd/GmbH):
    - Cyrillic job title: "в CompanyName –"
    - Trailing dash in title: "Title – CompanyName" (title line only)
    - Legal suffix: "CompanyName LLC|Inc|Ltd|GmbH"
    - "About X" / "at X" prefix (first word of a non-bullet line)

    Removed patterns that swallow real tech names:
    - "X is/was an ..." sentences (dropped PostHog, ClickHouse, etc.)
    - " - X" end-of-line pattern (dropped ClickHouse in "Stack: Node.js - ClickHouse")
    """
    names = set()
    first_lines = text.split("\n")[:25]
    for line in first_lines:
        line_s = line.strip()
        if not line_s or _BULLET.match(line_s):
            continue
        if line_s.startswith("#") and re.search(r"\b(requirements|qualifications|skills|responsibilities|tech stack)\b", line_s, re.I):
            break
        # Djinni Cyrillic "в CompanyName –" pattern
        m = re.search(r"\bв\s+([A-Za-z0-9_]+(?:\s+[A-Za-z0-9_]+)?)\s+[–-]", line)
        if m:
            for w in m.group(1).split():
                names.add(w)
        # Legal suffix pattern (very reliable)
        m = re.search(r"\b([A-Za-z0-9_]+)\s+(?:LLC|Inc\.?|Ltd\.?|Corp\.?|Corporation|GmbH|PLC)\b", line, re.I)
        if m:
            names.add(m.group(1))
        # "and our selected partners" pattern
        m = re.search(r"\b([A-Za-z0-9_]+)\s+and our selected partners\b", line, re.I)
        if m:
            names.add(m.group(1))
        # "About X" / "at X" prefix (first word, non-bullet lines only)
        m = re.match(r"^(?:about|at)\s+([A-Za-z0-9_]+)\b", line_s, re.I)
        if m:
            names.add(m.group(1))
    return names


def _is_noise(t, companies):
    if t.upper() in _STOP or t in _BRANDS or t in companies:
        return True
    if len(re.findall(r"[a-z][A-Z]", t)) >= 4 or len(t) > 30:
        return True
    tl = t.lower()
    hits = sum(1 for c in _COUNTRIES if c in tl)
    if hits >= 2 or (hits >= 1 and (len(t) > 18 or len(re.findall(r"[a-z][A-Z]", t)) >= 2)):
        return True
    return False


def extract_unrecognized_classified(text, known_spans):
    """Return list of (token, is_required) for unrecognized tech-like tokens."""
    companies = extract_company_names(text)
    seen = {}
    offset = 0

    for line, required in _classify_lines(text):
        if not _COUNTRY_LINE.search(line):
            for m in _TOKEN.finditer(line):
                tok_start = offset + m.start()
                tok_end = offset + m.end()
                if any(tok_start < e and s < tok_end for s, e in known_spans):
                    continue
                t = m.group()
                if (_CAMEL.search(t) or re.fullmatch(r"[A-Z]{3,8}", t)) and not _is_noise(t, companies):
                    if t not in seen:
                        seen[t] = required
                    elif required:
                        seen[t] = True

        offset += len(line) + 1

    return list(seen.items())


def extract_unrecognized(text, known_spans):
    return [t for t, _ in extract_unrecognized_classified(text, known_spans)]
