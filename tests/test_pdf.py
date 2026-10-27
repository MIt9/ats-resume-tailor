import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ats_tailor.pdf import find_chrome, markdown_to_html, build_pdf, verify_pdf
import helpers


class PdfModuleTests(unittest.TestCase):
    def test_markdown_to_html_formatting(self):
        md = """# John Doe
**Frontend Engineer**
Email: test@example.com | Phone: +1 234 567 890

---

## Technical Skills
**Frontend:** React, TypeScript, Redux
**Backend:** Node.js, Express

## Experience
### Senior Developer
TEMABIT · *2020 – Present*
- Built SPA features
- Improved performance by **40%**
"""
        html = markdown_to_html(md, title="John Doe — Resume")
        self.assertIn("<title>John Doe — Resume</title>", html)
        self.assertIn("<h1>John Doe</h1>", html)
        self.assertIn("<strong>Frontend:</strong> React, TypeScript, Redux", html)
        self.assertIn("<h2>Technical Skills</h2>", html)
        self.assertIn("<li>Built SPA features</li>", html)
        self.assertIn("mailto:test@example.com", html)

    def test_find_chrome(self):
        chrome = find_chrome()
        # On macOS or machines with Chrome installed, it should locate the executable
        if chrome is not None:
            self.assertTrue(Path(chrome).is_file())

    def test_build_and_verify_pdf(self):
        chrome = find_chrome()
        if not chrome:
            self.skipTest("Chrome / Chromium not installed in test environment")
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_pdf = Path(tmp_dir) / "resume.pdf"
            pdf_path = build_pdf(helpers.fx("resume_base.md"), str(out_pdf))
            self.assertTrue(Path(pdf_path).is_file())
            report = verify_pdf(pdf_path, keywords=["React", "TypeScript", "Node.js"])
            self.assertTrue(report["passed"])
            if report.get("supported"):
                self.assertTrue(report["checks"]["has_email"])
                self.assertTrue(report["checks"]["no_cid_glyphs"])

    def test_cli_pdf_and_verify_commands(self):
        chrome = find_chrome()
        if not chrome:
            self.skipTest("Chrome / Chromium not installed in test environment")
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_pdf = Path(tmp_dir) / "cli_resume.pdf"
            # ats-tailor pdf
            res = subprocess.run([
                sys.executable, "-m", "ats_tailor", "pdf",
                "--resume", helpers.fx("resume_base.md"),
                "--out", str(out_pdf),
            ], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            self.assertIn("Wrote", res.stdout)
            self.assertTrue(out_pdf.is_file())

            # ats-tailor verify-pdf
            res2 = subprocess.run([
                sys.executable, "-m", "ats_tailor", "verify-pdf",
                "--pdf", str(out_pdf),
                "--keywords", "React", "TypeScript",
            ], capture_output=True, text=True)
            self.assertEqual(res2.returncode, 0)
            self.assertIn("OVERALL: PASS", res2.stdout)


if __name__ == "__main__":
    unittest.main()
