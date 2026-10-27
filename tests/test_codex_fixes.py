import unittest
from ats_tailor.taxonomy import has_token, find_matches
from ats_tailor.postings import extract_keywords
from ats_tailor.resume import tailor, _append
from ats_tailor.ledger import Ledger, Pet
import helpers


class CodexReviewFixesTests(unittest.TestCase):
    def test_canonical_overlap_presence_checks(self):
        # React Query is TanStack Query, not React
        self.assertFalse(has_token("Experience with React Query for state management", "React", "React"))
        # Redux Toolkit is Redux Toolkit, not plain Redux
        self.assertFalse(has_token("Uses Redux Toolkit for slices", "Redux", "Redux"))
        # Plain React should still match
        self.assertTrue(has_token("Experience with React and Next.js", "React", "React"))
        self.assertTrue(has_token("React.js developer", "React.js", "React"))

    def test_nested_nice_to_have_headings(self):
        posting = """# Job
## Nice to have
### Bonus Tools
- Docker
### Other Preferred
- Redis
## Requirements
- Python
"""
        kws = {k.canonical: k.required for k in extract_keywords(posting)}
        self.assertTrue(kws["Python"])
        self.assertFalse(kws["Docker"])
        self.assertFalse(kws["Redis"])

    def test_pet_stack_filters_unconfirmed_skills(self):
        ledger = Ledger()
        ledger.add("Python", "personal", "pet projects")
        ledger.add("Kafka", "not", "Kafka NOT confirmed")
        ledger.pets = [Pet("pet-app", "https://github.com/example/pet-app", ["Python", "Kafka"], "Pet line")]

        resume = "# Name\n\n## Technical Skills\n**Frontend:** React\n\n## Education\nUniv\n"
        job = "## Requirements\n- Python\n"
        out, report = tailor(job, resume, ledger)
        self.assertIn("https://github.com/example/pet-app", out)
        # Python is personal and allowed
        self.assertIn("Stack: Python", out)
        # Kafka is unconfirmed/not and must NOT be injected in the stack
        self.assertNotIn("Kafka", out)

    def test_skills_section_without_bold_category_rows(self):
        # A resume with ## Technical Skills but only plain text or bullets
        resume = "# Name\n\n## Technical Skills\nReact, TypeScript, GraphQL\n\n## Education\nUniv\n"
        ledger = Ledger()
        ledger.add("Python", "confirmed", "silpo.ua")
        job = "## Requirements\n- Python\n"
        out, report = tailor(job, resume, ledger)
        self.assertIn("**Backend:** Python", out)

    def test_cli_report_path_collisions(self):
        import subprocess
        import sys
        # report equals resume
        res = subprocess.run([
            sys.executable, "-m", "ats_tailor", "tailor",
            "--job", helpers.fx("posting_a.md"),
            "--resume", helpers.fx("resume_base.md"),
            "--out", "/tmp/out.md",
            "--report", helpers.fx("resume_base.md"),
            "--inventory", helpers.fx("inventory.md"),
            "--pets", helpers.fx("pets.md"),
        ], capture_output=True, text=True)
        self.assertEqual(res.returncode, 2)
        self.assertIn("--report equals --resume", res.stderr)

        # report equals out
        res2 = subprocess.run([
            sys.executable, "-m", "ats_tailor", "tailor",
            "--job", helpers.fx("posting_a.md"),
            "--resume", helpers.fx("resume_base.md"),
            "--out", "/tmp/out.md",
            "--report", "/tmp/out.md",
            "--inventory", helpers.fx("inventory.md"),
            "--pets", helpers.fx("pets.md"),
        ], capture_output=True, text=True)
        self.assertEqual(res2.returncode, 2)
        self.assertIn("--report equals --out", res2.stderr)


if __name__ == "__main__":
    unittest.main()
