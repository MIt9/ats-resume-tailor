import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, "tests", "fixtures")
OVERRIDES = os.path.join(ROOT, "ats_tailor", "data", "overrides.json")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def fx(name):
    return os.path.join(FIX, name)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def make_ledger():
    """Single point of API guess (SPEC: load_ledger(inv, overrides), load_pets(path), Ledger.pets_for).
    Most literal reading: pets are attached to the ledger via the `pets` attribute."""
    from ats_tailor.ledger import load_ledger, load_pets
    ledger = load_ledger(fx("inventory.md"), OVERRIDES)
    ledger.pets = load_pets(fx("pets.md"))
    return ledger


def skills_block(text):
    """(before, block, after) around the '## Technical Skills' section."""
    i = text.index("## Technical Skills")
    j = text.index("\n## ", i + 1)
    return text[:i], text[i:j], text[j:]
