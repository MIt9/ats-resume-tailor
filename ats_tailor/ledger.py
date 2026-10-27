"""Skills ledger (inventory.md + overrides) and public pet projects (pets.md)."""
import json
import re
from dataclasses import dataclass

from .taxonomy import find_matches

RANK = {"confirmed": 4, "personal": 3, "partial": 2, "not": 1, "unknown": 0}
_PERSONAL = ("personal projects only", "pet projects only", "pet project", "(personal")
_SENTENCE = re.compile(r"\.(?=\s|$)|;")


@dataclass
class Pet:
    name: str
    github: str
    stack: list
    line: str


class Ledger:
    def __init__(self):
        self._lv = {}  # canonical -> (level, evidence)
        self._wording = {}
        self.pets = []

    def add(self, canonical, level, evidence):
        if RANK[level] > RANK[self.level(canonical)]:
            self._lv[canonical] = (level, evidence)

    def level(self, canonical):
        return self._lv.get(canonical, ("unknown", ""))[0]

    def evidence(self, canonical):
        return self._lv.get(canonical, ("unknown", ""))[1]

    def wording(self, canonical):
        return self._wording.get(canonical)

    def pets_for(self, canonical):
        return [p for p in self.pets if canonical in p.stack]


def _row_level(status, evidence):
    if status.startswith("NOT"):
        return "not"
    first = _SENTENCE.split(evidence)[0].lower()  # later sentences often talk about other skills
    if any(p in status.lower() or p in first for p in _PERSONAL):
        return "personal"
    if "PARTIAL" in status or "limited" in status:
        return "partial"
    return "confirmed"


def load_ledger(inventory_path, overrides_path, pets_path=None):
    ledger = Ledger()
    with open(inventory_path, encoding="utf-8") as f:
        rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in f if ln.lstrip().startswith("|")]
    for cells in rows:
        if len(cells) < 3 or set(cells[0]) <= set("-: ") or cells[0] in ("Skill", "Item"):
            continue
        skill, status, evidence = cells[0], cells[1], " | ".join(cells[2:])
        level = _row_level(status, evidence)
        for m in find_matches(skill):
            ledger.add(m.canonical, level, evidence)
        for clause in _SENTENCE.split(evidence):  # "<names> NOT confirmed"
            if "NOT confirmed" in clause:
                for m in find_matches(clause.split("NOT confirmed")[0]):
                    ledger.add(m.canonical, "not", evidence)
    with open(overrides_path, encoding="utf-8") as f:
        for canonical, o in json.load(f).items():
            ledger._lv[canonical] = (o["level"], o.get("evidence", ledger.evidence(canonical)))
            if "wording" in o:
                ledger._wording[canonical] = o["wording"]
    if pets_path:
        ledger.pets = load_pets(pets_path)
    return ledger


def load_pets(pets_path):
    with open(pets_path, encoding="utf-8") as f:
        text = f.read()
    pets = []
    for block in re.split(r"^### ", text, flags=re.M)[1:]:
        head, _, body = block.partition("\n")
        gh = re.search(r"\*\*GitHub:\*\*\s*(\S+)", body)
        stack = re.search(r"\*\*(?:Stack|Стек):\*\*(.*)", body, re.I)
        line = re.search(r"\*\*(?:Resume line|Рядок для резюме):\*\*\s*`([^`]+)`", body, re.I)
        if not (gh and line) or "private" in head.lower() or "private" in gh.group(1).lower():
            continue
        names = [m.canonical for m in find_matches(stack.group(1))] if stack else []
        pets.append(Pet(head.split()[0], gh.group(1), list(dict.fromkeys(names)), line.group(1)))
    return pets
