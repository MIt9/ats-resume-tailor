"""Cross-platform PDF building and ATS text-layer verification (stdlib only)."""
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


DEFAULT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}}</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  font-size: 10.5pt;
  line-height: 1.45;
  color: #222;
  max-width: 210mm;
  margin: 0 auto;
  padding: 12mm 15mm;
  background: #fff;
}
@media print {
  body { padding: 8mm 12mm; }
  @page { margin: 0; size: A4; }
}
h1 {
  font-size: 20pt;
  color: #111;
  margin-bottom: 2px;
  font-weight: 700;
}
.header { margin-bottom: 14px; }
.contacts {
  font-size: 9.5pt;
  color: #444;
  line-height: 1.6;
  margin-top: 4px;
}
.contacts a, a { color: #2b5b84; text-decoration: none; }
h2 {
  font-size: 12pt;
  color: #2b5b84;
  border-bottom: 1.5px solid #2b5b84;
  padding-bottom: 3px;
  margin: 14px 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
h3 {
  font-size: 11pt;
  color: #111;
  margin: 9px 0 3px;
  font-weight: 600;
}
h4 {
  font-size: 10pt;
  color: #333;
  margin: 7px 0 3px;
  font-weight: 600;
}
p { margin-bottom: 6px; }
ul {
  padding-left: 18px;
  margin-bottom: 8px;
}
li {
  margin-bottom: 3px;
}
li strong, p strong {
  color: #111;
}
em {
  color: #555;
  font-style: italic;
}
hr {
  border: none;
  border-top: 1px solid #e0e0e0;
  margin: 12px 0;
}
.skills-line {
  margin-bottom: 4px;
  font-size: 10pt;
}
</style>
</head>
<body>
{{BODY}}
</body>
</html>
"""


def find_chrome():
    """Find Google Chrome or Chromium executable across macOS, Linux, and Windows."""
    env_bin = os.environ.get("CHROME_BIN") or os.environ.get("CHROME_PATH")
    if env_bin and os.path.isfile(env_bin) and os.access(env_bin, os.X_OK):
        return env_bin

    # Standard locations by platform
    candidates = []
    if sys.platform == "darwin":
        candidates.extend([
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ])
    elif sys.platform == "win32":
        for base in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")):
            if base:
                candidates.extend([
                    os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"),
                    os.path.join(base, "Chromium", "Application", "chrome.exe"),
                ])
    else:  # Linux / Unix
        for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "brave-browser"):
            p = shutil.which(name)
            if p:
                candidates.append(p)
        candidates.extend([
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
        ])

    for c in candidates:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def markdown_to_html(md_text, title=None, template=None):
    """Convert standard markdown resume text to clean, printable HTML."""
    lines = md_text.splitlines()
    body_parts = []
    in_list = False
    doc_title = title or "Resume"

    def format_inline(text):
        # Links: [text](url)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        # Bold: **text**
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        # Italic: *text* (excluding already bold or list marks)
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
        # Email autolinks
        text = re.sub(r'(?<!href=")(?<!mailto:)\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b', r'<a href="mailto:\1">\1</a>', text)
        return text

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            if in_list:
                body_parts.append("</ul>")
                in_list = False
            i += 1
            continue

        # Skip image badges if photo file is omitted, or render image
        img_m = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)', line)
        if img_m:
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^(?:---|\*\*\*|___)$', line):
            if in_list:
                body_parts.append("</ul>")
                in_list = False
            body_parts.append("<hr>")
            i += 1
            continue

        # Headings
        if line.startswith("# "):
            if in_list:
                body_parts.append("</ul>")
                in_list = False
            heading = html.escape(line[2:].strip())
            if not title:
                doc_title = heading
            body_parts.append(f"<h1>{heading}</h1>")
            i += 1
            continue
        elif line.startswith("## "):
            if in_list:
                body_parts.append("</ul>")
                in_list = False
            body_parts.append(f"<h2>{html.escape(line[3:].strip())}</h2>")
            i += 1
            continue
        elif line.startswith("### "):
            if in_list:
                body_parts.append("</ul>")
                in_list = False
            body_parts.append(f"<h3>{format_inline(line[4:].strip())}</h3>")
            i += 1
            continue
        elif line.startswith("#### "):
            if in_list:
                body_parts.append("</ul>")
                in_list = False
            body_parts.append(f"<h4>{format_inline(line[5:].strip())}</h4>")
            i += 1
            continue

        # List items
        list_m = re.match(r'^[-*•]\s+(.*)', line)
        if list_m:
            if not in_list:
                body_parts.append("<ul>")
                in_list = True
            body_parts.append(f"<li>{format_inline(list_m.group(1))}</li>")
            i += 1
            continue

        # Normal paragraph or skills row
        if in_list:
            body_parts.append("</ul>")
            in_list = False

        if line.startswith("**") and ":**" in line:
            body_parts.append(f'<div class="skills-line">{format_inline(line)}</div>')
        else:
            body_parts.append(f'<p>{format_inline(line)}</p>')
        i += 1

    if in_list:
        body_parts.append("</ul>")

    body_html = "\n".join(body_parts)
    tmpl = template or DEFAULT_TEMPLATE
    return tmpl.replace("{{TITLE}}", html.escape(doc_title)).replace("{{BODY}}", body_html)


def build_pdf(input_path, output_pdf_path, title=None, chrome_bin=None):
    """Compile a Markdown or HTML resume into a professional PDF using headless Chrome."""
    chrome = chrome_bin or find_chrome()
    if not chrome:
        raise RuntimeError(
            "Google Chrome / Chromium not found. Please install Chrome or set the CHROME_BIN environment variable."
        )

    in_path = Path(input_path)
    if not in_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    content = in_path.read_text(encoding="utf-8")
    is_html = in_path.suffix.lower() in (".html", ".htm") or "<body" in content.lower()

    out_pdf = Path(output_pdf_path).resolve()
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        if is_html:
            html_file = Path(tmp_dir) / "resume.html"
            html_file.write_text(content, encoding="utf-8")
        else:
            rendered = markdown_to_html(content, title=title)
            html_file = Path(tmp_dir) / "resume.html"
            html_file.write_text(rendered, encoding="utf-8")

        cmd = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={str(out_pdf)}",
            html_file.resolve().as_uri(),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0 or not out_pdf.is_file():
            # Fallback without =new for older Chrome versions
            cmd[1] = "--headless"
            res2 = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res2.returncode != 0 or not out_pdf.is_file():
                err = res2.stderr or res.stderr or "Chrome failed to generate PDF"
                raise RuntimeError(f"PDF generation failed: {err}")

    return str(out_pdf)


def verify_pdf(pdf_path, keywords=None):
    """Verify PDF text layer for ATS compliance using pdftotext (if available)."""
    pdf = Path(pdf_path)
    if not pdf.is_file():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        return {
            "supported": False,
            "passed": True,
            "message": "pdftotext utility not found on PATH. Install poppler/pdftotext for deep text-layer verification.",
            "checks": {},
        }

    res = subprocess.run([pdftotext, "-layout", "-enc", "UTF-8", str(pdf), "-"], capture_output=True, text=True)
    if res.returncode != 0:
        return {
            "supported": True,
            "passed": False,
            "message": f"pdftotext failed with code {res.returncode}: {res.stderr}",
            "checks": {},
        }

    txt = res.stdout
    no_cid = bool(not re.search(r"\(cid:[0-9]+\)", txt))
    no_replacement = bool(not ("\ufffd" in txt or "\xef\xbf\xbd" in txt))
    has_email = bool(re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", txt))
    has_phone = bool(re.search(r"\+?[0-9\s\-()]{7,20}", txt))

    kw_checks = {}
    if keywords:
        for kw in keywords:
            kw_checks[kw] = bool(re.search(r"(?<![A-Za-z0-9_])" + re.escape(kw) + r"(?![A-Za-z0-9_+#])", txt, re.I))

    passed = no_cid and no_replacement and has_email and (all(kw_checks.values()) if keywords else True)
    return {
        "supported": True,
        "passed": passed,
        "checks": {
            "no_cid_glyphs": no_cid,
            "no_replacement_chars": no_replacement,
            "has_email": has_email,
            "has_phone": has_phone,
            "keywords": kw_checks,
        },
        "text_sample": txt[:300].strip(),
    }
