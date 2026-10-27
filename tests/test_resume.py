import re
import unittest

import helpers
from helpers import fx, read, make_ledger, skills_block
from ats_tailor.resume import analyze, tailor

POSTING = read(fx("posting_a.md"))
BASE = read(fx("resume_base.md"))
NOPERS = read(fx("resume_nopersonal.md"))
GAPS = ["Kafka", "Terraform", "Vitest", "Stripe", "Svelte", "FooBarDB"]


def st(report):
    return {k["canonical"]: k["status"] for k in report["keywords"]}


class TailorBaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.L = make_ledger()
        cls.out, cls.rep = tailor(POSTING, BASE, cls.L)

    def test_statuses(self):
        s = st(self.rep)
        self.assertEqual(s["React"], "variant_added")
        for c in ["TypeScript", "Node.js", "GraphQL", "Docker", "NestJS", "Kubernetes", "Redis"]:
            self.assertEqual(s[c], "present", c)
        for c in ["Kafka", "Terraform", "Vitest", "Stripe", "Svelte"]:
            self.assertEqual(s[c], "gap", c)

    def test_levels(self):
        lv = {k["canonical"]: k["level"] for k in self.rep["keywords"]}
        self.assertEqual(lv["React"], "confirmed")
        self.assertEqual(lv["NestJS"], "personal")
        self.assertIn(lv["Vitest"], ["not"])
        self.assertIn(lv["Stripe"], ["not"])
        self.assertIn(lv["Kafka"], ["not", "unknown"])
        self.assertIn(lv["Terraform"], ["not", "unknown"])
        self.assertIn(lv["Svelte"], ["not", "unknown"])

    def test_exact_frontend_line(self):
        self.assertIn("**Frontend:** React.js, React, Redux", self.out)
        self.assertEqual(self.out.count("React.js, React"), 1)

    def test_honesty_invariant(self):
        for g in GAPS:
            if g.lower() not in BASE.lower():
                self.assertNotIn(g.lower(), self.out.lower(), g)

    def test_honesty_generic(self):
        for g in self.rep["gaps"]:
            if g["spelling"].lower() not in BASE.lower():
                self.assertNotIn(g["spelling"].lower(), self.out.lower())

    def test_report_shape(self):
        self.assertEqual(set(self.rep), {"keywords", "coverage", "added", "gaps", "needs_review", "unrecognized", "next_steps"})
        self.assertEqual(self.rep["unrecognized"], ["FooBarDB"])
        self.assertEqual(sorted(g["canonical"] for g in self.rep["gaps"]),
                         ["Kafka", "Stripe", "Svelte", "Terraform", "Vitest"])
        for g in self.rep["gaps"]:
            self.assertEqual(set(g), {"canonical", "spelling", "required", "disclosure"})
            self.assertIn(g["canonical"], g["disclosure"])
        self.assertEqual(self.rep["needs_review"], [])
        self.assertEqual(self.rep["added"], ["React.js"])
        for k in self.rep["keywords"]:
            self.assertTrue({"canonical", "spelling", "required", "level", "status", "evidence"} <= set(k))
        req = {k["canonical"]: k["required"] for k in self.rep["keywords"]}
        self.assertFalse(req["Redis"] or req["Svelte"] or req["Docker"])
        self.assertTrue(req["React"])

    def test_coverage(self):
        c = self.rep["coverage"]
        self.assertEqual(c["before"], {"matched": 7, "total": 13, "required_matched": 5, "required_total": 10})
        self.assertEqual(c["after"], {"matched": 8, "total": 13, "required_matched": 6, "required_total": 10})
        self.assertLess(c["before"]["matched"], c["after"]["matched"])
        self.assertLess(c["after"]["matched"], c["after"]["total"])

    def test_only_skills_block_changes(self):
        b0, blk0, a0 = skills_block(BASE)
        b1, blk1, a1 = skills_block(self.out)
        self.assertEqual((b0, a0), (b1, a1))
        self.assertNotEqual(blk0, blk1)

    def test_idempotent(self):
        out2, rep2 = tailor(POSTING, self.out, self.L)
        self.assertEqual(out2, self.out)
        self.assertEqual(st(rep2)["React"], "present")
        self.assertFalse({"variant_added", "skill_added", "personal_added"} & set(st(rep2).values()))
        self.assertEqual(rep2["added"], [])

    def test_analyze_matches_and_does_not_change(self):
        rep = analyze(POSTING, BASE, self.L)
        self.assertEqual(st(rep)["React"], "variant_added")
        self.assertEqual(rep["coverage"], self.rep["coverage"])


class TailorNoPersonalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.L = make_ledger()
        cls.out, cls.rep = tailor(POSTING, NOPERS, cls.L)

    def test_personal_added(self):
        s = st(self.rep)
        for c in ["NestJS", "Kubernetes", "Redis"]:
            self.assertEqual(s[c], "personal_added", c)
        self.assertEqual(s["React"], "variant_added")

    def test_row_recreated_after_last_skills_line(self):
        lines = self.out.split("\n")
        rows = [i for i, l in enumerate(lines) if l.startswith("**Personal projects:**")]
        self.assertEqual(len(rows), 1)
        practices = [i for i, l in enumerate(lines) if l.startswith("**Practices:**")][0]
        self.assertGreater(rows[0], practices)
        for c in ["NestJS", "Kubernetes", "Redis"]:
            self.assertEqual(lines[rows[0]].count(c), 1)

    def test_no_pet_section_when_no_pets_and_no_gaps(self):
        self.assertNotIn("## Personal Projects", self.out)
        for g in GAPS:
            self.assertNotIn(g.lower(), self.out.lower())

    def test_outside_skills_unchanged_and_idempotent(self):
        b0, _, a0 = skills_block(NOPERS)
        b1, _, a1 = skills_block(self.out)
        self.assertEqual((b0, a0), (b1, a1))
        out2, _ = tailor(POSTING, self.out, self.L)
        self.assertEqual(out2, self.out)


class PersonalProjectsSectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.L = make_ledger()
        # strip every Python mention so the keyword is absent from the resume
        cls.base = BASE.replace("Python", "Scripting")
        cls.posting = "## Requirements\n- Python\n- Python 3 services\n"
        cls.out, cls.rep = tailor(cls.posting, cls.base, cls.L)

    def test_status_and_row(self):
        self.assertEqual(st(self.rep)["Python"], "personal_added")
        row = [l for l in self.out.split("\n") if l.startswith("**Personal projects:**")]
        self.assertEqual(len(row), 1)
        self.assertTrue(row[0].endswith(", Python (personal projects, PyPI packages)"))

    def test_section_placement_and_bullets(self):
        o = self.out
        i, j, k = o.index("## Open Source"), o.index("## Personal Projects"), o.index("## Education")
        self.assertTrue(i < j < k)
        sec = o[j:k]
        self.assertEqual(o.count("## Personal Projects"), 1)
        bullet = ("- **[mcp-book-lover](https://github.com/MIt9/mcp-book-lover)** — "
                  "mcp-book-lover — MCP book library manager (35+ tools, 8 sources, TTS sync) (Stack: Python, MCP)")
        self.assertIn(bullet, sec)
        for name in ["mcp-elevenreader", "workatastartup-mcp", "pexels-cli", "gifboom", "silpo-agent-cli"]:
            self.assertEqual(sec.count("github.com/MIt9/%s)" % name), 1, name)
        self.assertNotIn("silpo-mcp", o)
        # laya-cli already in Open Source with its github url -> no duplicate bullet
        self.assertEqual(o.count("github.com/MIt9/laya-cli"), 1)
        self.assertNotIn("github.com/MIt9/laya-cli", sec)
        urls = re.findall(r"\]\((https://github\.com/MIt9/[^)]+)\)", sec)
        self.assertEqual(len(urls), len(set(urls)))

    def test_outside_unchanged(self):
        j = self.out.index("## Personal Projects")
        k = self.out.index("## Education")
        stripped = self.out[:j] + self.out[k:]
        b0, _, a0 = skills_block(self.base)
        b1, _, a1 = skills_block(stripped)
        self.assertEqual((b0, a0), (b1, a1))

    def test_idempotent(self):
        out2, _ = tailor(self.posting, self.out, self.L)
        self.assertEqual(out2, self.out)


class OtherRulesTests(unittest.TestCase):
    def test_skill_added_confirmed_goes_to_category_line(self):
        # Express/RabbitMQ are confirmed; remove Express from resume, expect append to **Backend:** line
        L = make_ledger()
        base = BASE.replace("Express, ", "")
        out, rep = tailor("## Requirements\n- Express\n", base, L)
        self.assertEqual(st(rep)["Express"], "skill_added")
        line = [l for l in out.split("\n") if l.startswith("**Backend:**")][0]
        self.assertTrue(line.endswith(", Express"))

    def test_gap_only_posting_changes_nothing(self):
        L = make_ledger()
        out, rep = tailor("## Requirements\n- Kafka\n- Terraform\n", BASE, L)
        self.assertEqual(out, BASE)
        self.assertEqual(rep["added"], [])


if __name__ == "__main__":
    unittest.main()
