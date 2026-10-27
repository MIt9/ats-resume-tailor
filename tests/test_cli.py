import json
import os
import subprocess
import sys
import tempfile
import unittest

from helpers import ROOT, fx, read

INV = ["--inventory", fx("inventory.md"), "--pets", fx("pets.md")]
JOB = fx("posting_a.md")
RES = fx("resume_base.md")


def run(*args, stdin=None):
    return subprocess.run([sys.executable, "-m", "ats_tailor", *args], cwd=ROOT, input=stdin,
                          capture_output=True, text=True)


def snapshot():
    out = {}
    for d in (ROOT, os.path.join(ROOT, "tests", "fixtures")):
        out[d] = sorted(os.listdir(d))
    return out


class CliTests(unittest.TestCase):
    def assert_bad_input(self, r):
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertEqual(r.stdout, "")
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(len(r.stderr.strip().splitlines()), 1)

    def test_keywords_file_and_stdin(self):
        r = run("keywords", "--job", JOB)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        by = {k["canonical"]: k for k in data}
        self.assertEqual(by["React"]["spelling"], "React.js")
        self.assertFalse(by["Redis"]["required"])
        self.assertTrue(by["Kafka"]["required"])
        r2 = run("keywords", "--job", "-", stdin=read(JOB))
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertEqual(json.loads(r2.stdout), data)

    def test_analyze_json_no_writes(self):
        before = snapshot()
        r = run("analyze", "--job", JOB, "--resume", RES, *INV, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(r.stdout)
        self.assertEqual(set(rep), {"keywords", "coverage", "added", "gaps", "needs_review", "unrecognized", "next_steps"})
        self.assertEqual({k["canonical"]: k["status"] for k in rep["keywords"]}["React"], "variant_added")
        self.assertEqual(rep["unrecognized"], ["FooBarDB"])
        self.assertEqual(snapshot(), before)

    def test_analyze_default_is_markdown_not_json(self):
        r = run("analyze", "--job", JOB, "--resume", RES, *INV)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.strip())
        with self.assertRaises(ValueError):
            json.loads(r.stdout)
        self.assertIn("Kafka", r.stdout)

    def test_tailor_to_file_with_report(self):
        with tempfile.TemporaryDirectory() as d:
            out, rp = os.path.join(d, "out.md"), os.path.join(d, "rep.json")
            r = run("tailor", "--job", JOB, "--resume", RES, "--out", out, "--report", rp, *INV)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout, "")
            self.assertIn("**Frontend:** React.js, React, Redux", read(out))
            rep = json.loads(read(rp))
            self.assertEqual(rep["added"], ["React.js"])
            self.assertEqual(read(RES), read(fx("resume_base.md")))  # input untouched

    def test_tailor_stdout_only_payload(self):
        r = run("tailor", "--job", JOB, "--resume", RES, "--out", "-", *INV)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith("# Dmytro Bilukha"))
        self.assertIn("**Frontend:** React.js, React, Redux", r.stdout)
        self.assertTrue(r.stderr.strip())  # short summary on stderr when no --report
        self.assertNotIn("Traceback", r.stderr)

    def test_tailor_nopersonal_recreates_row(self):
        r = run("tailor", "--job", JOB, "--resume", fx("resume_nopersonal.md"), "--out", "-", *INV)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("**Personal projects:**", r.stdout)

    def test_schema(self):
        r = run("schema")
        self.assertEqual(r.returncode, 0, r.stderr)
        for key in ["keywords", "coverage", "added", "gaps", "needs_review", "unrecognized", "next_steps"]:
            self.assertIn('"%s"' % key, r.stdout)

    def test_missing_resume(self):
        self.assert_bad_input(run("analyze", "--job", JOB, "--resume", "/nonexistent/r.md", *INV))

    def test_missing_job(self):
        self.assert_bad_input(run("keywords", "--job", "/nonexistent/j.md"))

    def test_missing_inventory(self):
        self.assert_bad_input(run("analyze", "--job", JOB, "--resume", RES,
                                  "--inventory", "/nonexistent/i.md", "--pets", fx("pets.md")))

    def test_empty_posting(self):
        with tempfile.TemporaryDirectory() as d:
            e = os.path.join(d, "empty.md")
            open(e, "w").close()
            self.assert_bad_input(run("keywords", "--job", e))
            self.assert_bad_input(run("tailor", "--job", e, "--resume", RES, "--out", "-", *INV))
            self.assert_bad_input(run("keywords", "--job", "-", stdin=""))

    def test_out_equals_resume_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.md")
            with open(p, "w", encoding="utf-8") as f:
                f.write(read(RES))
            self.assert_bad_input(run("tailor", "--job", JOB, "--resume", p, "--out", p, *INV))
            self.assertEqual(read(p), read(RES))


if __name__ == "__main__":
    unittest.main()
