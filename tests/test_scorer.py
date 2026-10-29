import json
import subprocess
import sys
import unittest

from helpers import ROOT, fx, read, make_ledger
from ats_tailor.ledger import Ledger
from ats_tailor.scorer import calculate_score, format_score_report, ScoreResult

POSTING_A = read(fx("posting_a.md"))
BASE = read(fx("resume_base.md"))
NOPERS = read(fx("resume_nopersonal.md"))


def run(*args, stdin=None):
    return subprocess.run(
        [sys.executable, "-m", "ats_tailor", *args],
        cwd=ROOT,
        input=stdin,
        capture_output=True,
        text=True,
    )


class ScorerCalculationTests(unittest.TestCase):
    def setUp(self):
        self.ledger = make_ledger()

    def test_perfect_match(self):
        job = """# Senior React & Node Engineer
## Requirements
- React
- TypeScript
- Node.js
- GraphQL

## Nice to have
- Docker
"""
        res = calculate_score(job, BASE, self.ledger)
        self.assertEqual(res.score, 100.0)
        self.assertEqual(res.grade, "Excellent")
        self.assertEqual(res.breakdown["matched_count"], 5)
        self.assertEqual(res.breakdown["tailorable_count"], 0)
        self.assertEqual(res.breakdown["gap_count"], 0)
        self.assertEqual(res.gaps, [])

    def test_supabase_extracted_and_marked_gap(self):
        job = """# Full-Stack Developer
## Requirements
- React
- TypeScript
- Supabase
"""
        res = calculate_score(job, BASE, self.ledger)
        self.assertEqual(self.ledger.level("Supabase"), "unknown")
        canonicals = [k["canonical"] for k in res.keywords]
        self.assertIn("Supabase", canonicals)
        sup_kw = next(k for k in res.keywords if k["canonical"] == "Supabase")
        self.assertEqual(sup_kw["status"], "gap")
        self.assertTrue(sup_kw["required"])
        self.assertTrue(any(g["canonical"] == "Supabase" and g["type"] == "critical" for g in res.gaps))
        self.assertLess(res.score, 100.0)
        self.assertEqual(res.score, 66.7)

    def test_score_output_includes_unrecognized_caveat(self):
        """grade must be exactly one of Excellent|Good|Moderate|Low; upper_bound=True when unrec required."""
        job = """# Senior React & Node Engineer
## Requirements
- React
- TypeScript
- Node.js
- GraphQL
- UnknownNewEngine

## Nice to have
- Docker
"""
        res = calculate_score(job, BASE, self.ledger)
        self.assertEqual(res.score, 100.0)
        # grade is ALWAYS a clean value — not mutated with a suffix
        self.assertEqual(res.grade, "Excellent")
        # upper_bound flag signals the caveat
        self.assertTrue(res.upper_bound)
        self.assertIn("UnknownNewEngine", res.unrecognized_required)
        self.assertIn("UnknownNewEngine", res.unrecognized)
        self.assertIsNotNone(res.unrecognized_warning)
        self.assertIn("Score is an upper bound: 1 unrecognized terms not evaluated", res.unrecognized_warning)
        # Report shows the caveat at every grade
        report = format_score_report(res)
        self.assertIn("Score is an upper bound: 1 unrecognized terms not evaluated", report)
        self.assertIn("Warning: Score is an upper bound: 1 unrecognized terms not evaluated.", report)
        d = res.to_dict()
        self.assertIn("UnknownNewEngine", d["unrecognized"])
        self.assertTrue(any("Score is an upper bound" in r for r in d["recommendations"]))
        # JSON always-present keys
        self.assertTrue(d["upper_bound"])
        self.assertIn("UnknownNewEngine", d["unrecognized_required"])
        self.assertIsNotNone(d["unrecognized_warning"])

    def test_grade_contract_always_clean(self):
        """grade and breakdown.grade must always be exactly one of Excellent|Good|Moderate|Low."""
        VALID_GRADES = {"Excellent", "Good", "Moderate", "Low"}
        for job_text, label in [
            ("## Requirements\n- React\n- TypeScript\n- Node.js\n- GraphQL\n- UnknownXYZ\n", "Excellent+unrec"),
            ("## Requirements\n- React\n", "Excellent no unrec"),
            ("## Requirements\n- Kafka\n", "Low"),
        ]:
            with self.subTest(label=label):
                res = calculate_score(job_text, BASE, self.ledger)
                self.assertIn(res.grade, VALID_GRADES, f"grade={res.grade!r} not a valid grade")
                self.assertIn(res.breakdown["grade"], VALID_GRADES,
                              f"breakdown.grade={res.breakdown['grade']!r} not a valid grade")

    def test_upper_bound_and_unrecognized_required_always_present(self):
        """upper_bound (bool) and unrecognized_required (list) must be present in to_dict() always."""
        job = "## Requirements\n- React\n"
        res = calculate_score(job, BASE, self.ledger)
        d = res.to_dict()
        self.assertIn("upper_bound", d)
        self.assertIn("unrecognized_required", d)
        self.assertIn("unrecognized_warning", d)
        self.assertIsInstance(d["upper_bound"], bool)
        self.assertIsInstance(d["unrecognized_required"], list)
        self.assertFalse(d["upper_bound"])
        self.assertEqual(d["unrecognized_required"], [])
        self.assertIsNone(d["unrecognized_warning"])

    def test_upper_bound_false_for_nice_to_have_only_unrec(self):
        """An unrecognized term only in nice-to-have section must NOT set upper_bound=True."""
        job = "## Requirements\n- React\n\n## Nice to have\n- UnknownXYZ\n"
        res = calculate_score(job, BASE, self.ledger)
        self.assertFalse(res.upper_bound)
        self.assertEqual(res.unrecognized_required, [])
        # unrecognized_warning is None since no required unrec terms
        self.assertIsNone(res.unrecognized_warning)
        # UnknownXYZ should still appear in unrecognized list
        self.assertIn("UnknownXYZ", res.unrecognized)

    def test_ledger_denied_skill_in_resume_stays_gap(self):
        class Denied:
            def level(self, c):
                return "not"

            def evidence(self, c):
                return "no hands-on experience"

        job = "# Lead Engineer\n## Requirements\n- Kafka\n"
        resume = "# Jane Doe\n## Experience\n- Used Kafka for event streaming\n"
        res = calculate_score(job, resume, Denied())
        self.assertEqual(res.keywords[0]["status"], "gap")
        self.assertEqual(res.breakdown["gap_count"], 1)

    def test_agile_scrum_present_not_in_ledger(self):
        # Agile is in resume as slash-separated Agile/Scrum, but NOT in ledger
        job = """# Lead Engineer
## Requirements
- Agile
"""
        resume = """# Jane Doe
## Technical Skills
**Practices:** Code Review, ADR, Agile/Scrum, Performance Engineering
"""
        res = calculate_score(job, resume, self.ledger)
        self.assertEqual(self.ledger.level("Agile"), "unknown")
        self.assertEqual(len(res.keywords), 1)
        kw = res.keywords[0]
        self.assertEqual(kw["canonical"], "Agile")
        self.assertEqual(kw["level"], "unknown")
        self.assertEqual(kw["status"], "present_unverified")
        self.assertEqual(kw["credit"], 1.0)
        self.assertEqual(kw["earned"], 3.0)
        self.assertEqual(res.score, 100.0)
        self.assertEqual(res.grade, "Excellent")
        self.assertEqual(res.breakdown["matched_count"], 1)
        self.assertEqual(res.breakdown["gap_count"], 0)
        self.assertEqual(res.gaps, [])  # Never classify as CRITICAL gap

    def test_gap_heavy_match(self):
        job = """# Systems Engineer
## Requirements
- Kafka
- Terraform
- Vitest
- Stripe

## Nice to have
- Svelte
"""
        res = calculate_score(job, BASE, self.ledger)
        self.assertEqual(res.score, 0.0)
        self.assertEqual(res.grade, "Low")
        self.assertEqual(res.breakdown["matched_count"], 0)
        self.assertEqual(res.breakdown["gap_count"], 5)
        self.assertEqual(res.breakdown["critical_count"], 4)
        self.assertEqual(res.breakdown["secondary_count"], 1)

    def test_partial_match_and_weighting(self):
        # Construct custom ledger for exact math verification
        custom_ledger = Ledger()
        custom_ledger.add("React", "confirmed", "experience")
        custom_ledger.add("NestJS", "confirmed", "experience")
        custom_ledger.add("PWA", "partial", "limited production")
        custom_ledger.add("Kafka", "not", "not experienced")

        resume = """# Jane Doe
## Technical Skills
**Frontend:** React
"""
        # Requirements:
        # React (confirmed, in resume) -> Present: weight 3, credit 1.0 -> 3.0 pts
        # NestJS (confirmed, missing from resume) -> Tailorable: weight 3, credit 0.75 -> 2.25 pts
        # PWA (partial) -> Partial: weight 3, credit 0.30 -> 0.90 pts
        # Kafka (not) -> Gap: weight 3, credit 0.0 -> 0.0 pts
        # Nice to have:
        # Docker (unknown) -> Gap: weight 1, credit 0.0 -> 0.0 pts
        # Total possible: 3 * 4 + 1 * 1 = 13.0
        # Total earned: 3.0 + 2.25 + 0.90 + 0.0 + 0.0 = 6.15
        # Score: 6.15 / 13.0 * 100 = 47.307... -> 47.3
        job = """# Fullstack Developer
## Requirements
- React
- NestJS
- PWA
- Kafka

## Nice to have
- Docker
"""
        res = calculate_score(job, resume, custom_ledger)
        self.assertEqual(res.score, 47.3)
        self.assertEqual(res.grade, "Low")
        self.assertEqual(res.breakdown["matched_count"], 1)
        self.assertEqual(res.breakdown["tailorable_count"], 1)
        self.assertEqual(res.breakdown["partial_count"], 1)
        self.assertEqual(res.breakdown["gap_count"], 2)
        self.assertEqual(res.breakdown["required_points"], 6.2)  # round(6.15, 1) = 6.1 or 6.2
        self.assertEqual(res.breakdown["required_total"], 12.0)
        self.assertEqual(res.breakdown["nice_to_have_points"], 0.0)
        self.assertEqual(res.breakdown["nice_to_have_total"], 1.0)

    def test_empty_job_posting(self):
        res = calculate_score("No tech keywords here.", BASE, self.ledger)
        self.assertEqual(res.score, 0.0)
        self.assertEqual(res.breakdown["total_keywords"], 0)
        self.assertEqual(res.gaps, [])


class GapClassificationTests(unittest.TestCase):
    def setUp(self):
        self.ledger = make_ledger()

    def test_gap_types_posting_a_with_nopersonal_resume(self):
        res = calculate_score(POSTING_A, NOPERS, self.ledger)
        by_canonical = {g["canonical"]: g for g in res.gaps}

        # NestJS & Kubernetes are required and in ledger as personal, but missing from resume
        self.assertEqual(by_canonical["NestJS"]["type"], "actionable")
        self.assertIn("In ledger as personal", by_canonical["NestJS"]["description"])
        self.assertIn("tailor resume", by_canonical["NestJS"]["description"])

        self.assertEqual(by_canonical["Kubernetes"]["type"], "actionable")
        self.assertIn("In ledger as personal", by_canonical["Kubernetes"]["description"])

        # Kafka, Terraform, Vitest, Stripe are required and not in ledger (or level not)
        for c in ["Kafka", "Terraform", "Vitest", "Stripe"]:
            self.assertEqual(by_canonical[c]["type"], "critical")
            self.assertIn("disclose", by_canonical[c]["description"].lower())

        # Redis & Svelte are nice-to-have gaps
        self.assertEqual(by_canonical["Redis"]["type"], "secondary")
        self.assertEqual(by_canonical["Svelte"]["type"], "secondary")

    def test_review_gap_type(self):
        custom_ledger = Ledger()
        custom_ledger.add("PWA", "partial", "limited production maintenance")
        job = "## Requirements\n- Progressive Web App\n"
        res = calculate_score(job, BASE, custom_ledger)
        self.assertEqual(len(res.gaps), 1)
        gap = res.gaps[0]
        self.assertEqual(gap["canonical"], "PWA")
        self.assertEqual(gap["type"], "review")
        self.assertIn("Partial competence", gap["description"])
        self.assertIn("limited production maintenance", gap["description"])

    def test_score_result_access_patterns(self):
        res = calculate_score(POSTING_A, BASE, self.ledger)
        # Dot access
        self.assertIsInstance(res.score, float)
        self.assertIsInstance(res.grade, str)
        self.assertIsInstance(res.breakdown, dict)
        self.assertIsInstance(res.gaps, list)
        self.assertIsInstance(res.recommendations, list)
        # Dict access
        self.assertEqual(res["score"], res.score)
        self.assertEqual(res["grade"], res.grade)
        self.assertEqual(res.get("score"), res.score)
        self.assertIn("score", res)
        # to_dict
        d = res.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["score"], res.score)


class CliScoreTests(unittest.TestCase):
    def test_score_human_report(self):
        r = run(
            "score",
            "--job", fx("posting_a.md"),
            "--resume", fx("resume_base.md"),
            "--inventory", fx("inventory.md"),
            "--pets", fx("pets.md"),
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("# ATS Resume-to-Job Match Score", out)
        self.assertIn("**Score:**", out)
        self.assertIn("### Score Breakdown", out)
        self.assertIn("- **Required Skills:**", out)
        self.assertIn("- **Nice-to-Have Skills:**", out)
        self.assertIn("### Gaps & Action Items", out)
        self.assertIn("[CRITICAL] Kafka", out)
        self.assertIn("### Recommendations", out)

    def test_score_detailed_flag(self):
        r = run(
            "score",
            "--job", fx("posting_a.md"),
            "--resume", fx("resume_base.md"),
            "--inventory", fx("inventory.md"),
            "--pets", fx("pets.md"),
            "--detailed",
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("### Detailed Keyword Analysis", r.stdout)
        self.assertIn("| React | React.js | yes | confirmed | present |", r.stdout)

    def test_score_json_flag(self):
        r = run(
            "score",
            "--job", fx("posting_a.md"),
            "--resume", fx("resume_base.md"),
            "--inventory", fx("inventory.md"),
            "--pets", fx("pets.md"),
            "--json",
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        # Check required keys are present (allow extra keys)
        required_keys = {"score", "grade", "breakdown", "gaps", "recommendations",
                         "keywords", "unrecognized", "upper_bound", "unrecognized_required",
                         "unrecognized_warning"}
        self.assertTrue(required_keys.issubset(data.keys()),
                        f"Missing keys: {required_keys - data.keys()}")
        self.assertIsInstance(data["score"], (int, float))
        self.assertIn(data["grade"], ["Excellent", "Good", "Moderate", "Low"])
        self.assertIsInstance(data["upper_bound"], bool)
        self.assertIsInstance(data["unrecognized_required"], list)
        self.assertGreaterEqual(len(data["gaps"]), 1)
        self.assertIn("FooBarDB", data["unrecognized"])

    def test_score_stdin_job(self):
        posting_text = read(fx("posting_a.md"))
        r = run(
            "score",
            "--job", "-",
            "--resume", fx("resume_base.md"),
            "--inventory", fx("inventory.md"),
            "--pets", fx("pets.md"),
            "--json",
            stdin=posting_text,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["score"], 60.6)

    def test_score_cli_unrecognized_warning(self):
        r = run(
            "score",
            "--job", fx("posting_a.md"),
            "--resume", fx("resume_base.md"),
            "--inventory", fx("inventory.md"),
            "--pets", fx("pets.md"),
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Score is an upper bound: 1 unrecognized terms not evaluated", r.stdout)
        self.assertIn("Warning: Score is an upper bound: 1 unrecognized terms not evaluated.", r.stdout)

    def test_score_bad_inputs(self):
        # Missing job file
        r1 = run("score", "--job", "nonexistent.md", "--resume", fx("resume_base.md"))
        self.assertEqual(r1.returncode, 2)
        self.assertIn("error:", r1.stderr)

        # Missing resume file
        r2 = run("score", "--job", fx("posting_a.md"), "--resume", "nonexistent.md")
        self.assertEqual(r2.returncode, 2)
        self.assertIn("error:", r2.stderr)


if __name__ == "__main__":
    unittest.main()
