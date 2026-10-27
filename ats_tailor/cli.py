"""Command line: keywords | analyze | tailor | score | schema. stdout = payload only; errors = one line on stderr."""
import argparse
import dataclasses
import json
import os
import sys
from pathlib import Path

from .ledger import load_ledger
from .pdf import build_pdf, verify_pdf
from .postings import extract_keywords
from .resume import SCHEMA, tailor
from .scorer import calculate_score, format_score_report

OVERRIDES = Path(__file__).parent / "data" / "overrides.json"


class BadInput(Exception):
    pass


def _read(path, what):
    try:
        if path == "-":
            text = sys.stdin.read()
        else:
            with open(path, encoding="utf-8") as f:
                text = f.read()
    except (OSError, UnicodeDecodeError) as e:
        raise BadInput("cannot read %s %s: %s" % (what, path, getattr(e, "strerror", None) or e))
    if not text.strip():
        raise BadInput("%s is empty: %s" % (what, path))
    return text


def _ledger(a):
    inv = a.inventory or os.environ.get("ATS_TAILOR_INVENTORY") or "~/work/resume/info/skills-inventory.md"
    pets = a.pets or os.environ.get("ATS_TAILOR_PETS") or "~/work/resume/info/open-source-repositories.md"
    inv, pets = os.path.expanduser(inv), os.path.expanduser(pets)
    ov = a.overrides or OVERRIDES
    for p, what in ((inv, "inventory"), (pets, "pets file"), (ov, "overrides")):
        if not os.path.isfile(p):
            raise BadInput("cannot read %s %s: no such file" % (what, p))
    try:
        return load_ledger(inv, ov, pets)
    except (OSError, UnicodeDecodeError, ValueError, KeyError) as e:
        raise BadInput("invalid inventory/pets/overrides: %s" % e)


def _summary(r):
    c = r["coverage"]
    lines = ["# ats-tailor report", "",
             "Coverage: %(matched)d/%(total)d keywords (required %(required_matched)d/%(required_total)d)" % c["before"]
             + " -> %(matched)d/%(total)d (required %(required_matched)d/%(required_total)d)" % c["after"], "",
             "| Keyword | Posting spelling | Required | Level | Status |", "|---|---|---|---|---|"]
    lines += ["| %s | %s | %s | %s | %s |" % (k["canonical"], k["spelling"], "yes" if k["required"] else "no", k["level"], k["status"])
              for k in r["keywords"]]
    if r["gaps"]:
        lines += ["", "Gaps (not added, disclose in the cover letter):"] + ["- %(canonical)s: %(disclosure)s" % g for g in r["gaps"]]
    if r["needs_review"]:
        lines += ["", "Needs review (not added):"] + ["- %(canonical)s: %(evidence)s" % n for n in r["needs_review"]]
    if r["unrecognized"]:
        lines += ["", "Unrecognized: " + ", ".join(r["unrecognized"])]
    if r["next_steps"]:
        lines += ["", "Next steps:"] + ["- " + s for s in r["next_steps"]]
    return "\n".join(lines) + "\n"


def _run(a):
    if a.cmd == "schema":
        print(json.dumps(SCHEMA, indent=2, ensure_ascii=False))
        return
    if a.cmd == "verify-pdf":
        v = verify_pdf(a.pdf, keywords=a.keywords)
        if a.json:
            sys.stdout.write(json.dumps(v, indent=2, ensure_ascii=False) + "\n")
        else:
            sys.stdout.write(f"ATS text-layer check: {a.pdf}\n")
            if not v.get("supported"):
                sys.stdout.write(f"NOTICE: {v.get('message')}\n")
            else:
                for check, res in v.get("checks", {}).items():
                    if check == "keywords":
                        for kw, kpres in res.items():
                            sys.stdout.write(f"{'PASS' if kpres else 'FAIL'} keyword: {kw}\n")
                    else:
                        sys.stdout.write(f"{'PASS' if res else 'FAIL'} {check}\n")
                sys.stdout.write(f"\nOVERALL: {'PASS' if v['passed'] else 'FAIL'}\n")
        return
    if a.cmd == "pdf":
        out_pdf = a.out or str(Path(a.resume).with_suffix(".pdf"))
        try:
            pdf_file = build_pdf(a.resume, out_pdf, title=a.title)
            v = verify_pdf(pdf_file)
            if a.json:
                sys.stdout.write(json.dumps({"pdf": pdf_file, "verification": v}, indent=2, ensure_ascii=False) + "\n")
            else:
                chk = "PASS" if v.get("passed", True) else "FAIL"
                sys.stdout.write(f"Wrote {pdf_file} (ATS text-layer check: {chk})\n")
        except Exception as e:
            raise BadInput(str(e))
        return
    job = _read(a.job, "posting")
    if a.cmd == "keywords":
        print(json.dumps([dataclasses.asdict(k) for k in extract_keywords(job)], indent=2, ensure_ascii=False))
        return
    if a.cmd == "tailor":
        if a.out != "-" and not a.force and os.path.realpath(a.out) == os.path.realpath(a.resume):
            raise BadInput("--out equals --resume; refusing to overwrite (use --force)")
        if a.report:
            if not a.force and os.path.realpath(a.report) == os.path.realpath(a.resume):
                raise BadInput("--report equals --resume; refusing to overwrite (use --force)")
            if a.out != "-" and os.path.realpath(a.report) == os.path.realpath(a.out):
                raise BadInput("--report equals --out; refusing to overwrite")
    resume = _read(a.resume, "resume")
    if a.cmd == "score":
        ledger = _ledger(a)
        res = calculate_score(job, resume, ledger)
        if a.json:
            sys.stdout.write(json.dumps(res.to_dict(), indent=2, ensure_ascii=False) + "\n")
        else:
            sys.stdout.write(format_score_report(res, detailed=a.detailed))
        return
    try:
        out, report = tailor(job, resume, _ledger(a))
    except ValueError as e:
        raise BadInput(str(e))
    if a.cmd == "analyze":
        sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n" if a.json else _summary(report))
        return
    if a.out == "-":
        sys.stdout.write(out)
    else:
        try:
            with open(a.out, "w", encoding="utf-8") as f:
                f.write(out)
        except OSError as e:
            raise BadInput("cannot write %s: %s" % (a.out, e.strerror))
    if a.report:
        try:
            with open(a.report, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        except OSError as e:
            raise BadInput("cannot write %s: %s" % (a.report, e.strerror))
    else:
        sys.stderr.write(_summary(report))
    if getattr(a, "pdf", None):
        try:
            import tempfile
            with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as tmp_in:
                tmp_in.write(out)
                tmp_in_path = tmp_in.name
            try:
                build_pdf(tmp_in_path, a.pdf)
            finally:
                if os.path.exists(tmp_in_path):
                    os.remove(tmp_in_path)
            v = verify_pdf(a.pdf, keywords=report.get("added"))
            if v.get("supported"):
                chk = "PASS" if v["passed"] else "FAIL"
                sys.stderr.write(f"\nWrote PDF {a.pdf} (ATS text-layer check: {chk})\n")
            else:
                sys.stderr.write(f"\nWrote PDF {a.pdf}\n")
        except Exception as e:
            raise BadInput(f"PDF build failed: {e}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="ats-tailor", description="Honest ATS keyword tailoring and scoring for markdown resumes.")
    sub = p.add_subparsers(dest="cmd", required=True)
    
    sub_help = {
        "keywords": "Extract recognized and unrecognized tech keywords from a job posting.",
        "analyze": "Analyze resume coverage against posting requirements without modifying files.",
        "tailor": "Tailor markdown resume by injecting confirmed skills and personal projects.",
        "score": "Calculate 0-100 match score with points breakdown and categorized gaps.",
        "pdf": "Compile a markdown or HTML resume into a clean PDF using headless Chrome.",
        "verify-pdf": "Verify the embedded text layer of a resume PDF for ATS compliance.",
        "schema": "Print the JSON report schema.",
    }

    for name in ("keywords", "analyze", "tailor", "score"):
        s = sub.add_parser(name, help=sub_help[name], description=sub_help[name])
        s.add_argument("--job", required=True, help="posting markdown file or - for stdin")
        if name != "keywords":
            s.add_argument("--resume", required=True, help="base markdown resume file")
            s.add_argument("--inventory", help="path to skills-inventory.md (default: $ATS_TAILOR_INVENTORY or ~/work/resume/info/skills-inventory.md)")
            s.add_argument("--pets", help="path to open-source-repositories.md (default: $ATS_TAILOR_PETS or ~/work/resume/info/open-source-repositories.md)")
            s.add_argument("--overrides", help="path to custom overrides.json (default: packaged overrides.json)")
        if name in ("analyze", "score"):
            s.add_argument("--json", action="store_true", help="output machine-readable JSON")
        if name == "score":
            s.add_argument("--detailed", action="store_true", help="include per-keyword score table in human report")
        if name == "tailor":
            s.add_argument("--out", required=True, help="output tailored markdown resume or - for stdout")
            s.add_argument("--report", help="write the JSON tailoring report to this file")
            s.add_argument("--pdf", help="optional output path to compile tailored resume into PDF")
            s.add_argument("--force", action="store_true", help="allow overwriting --resume when --out points to the same file")
    
    # Subcommand: pdf
    s_pdf = sub.add_parser("pdf", help=sub_help["pdf"], description=sub_help["pdf"])
    s_pdf.add_argument("--resume", required=True, help="input markdown or HTML resume file")
    s_pdf.add_argument("--out", help="output PDF file path (default: same name with .pdf)")
    s_pdf.add_argument("--title", help="document title for PDF metadata")
    s_pdf.add_argument("--json", action="store_true", help="output result in JSON format")

    # Subcommand: verify-pdf
    s_v = sub.add_parser("verify-pdf", help=sub_help["verify-pdf"], description=sub_help["verify-pdf"])
    s_v.add_argument("--pdf", required=True, help="path to resume PDF to verify")
    s_v.add_argument("--keywords", nargs="*", help="optional keywords that must appear in the text layer")
    s_v.add_argument("--json", action="store_true", help="output result in JSON format")
    sub.add_parser("schema", help=sub_help["schema"], description=sub_help["schema"])
    a = p.parse_args(argv)
    try:
        _run(a)
    except BadInput as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    except BrokenPipeError:
        return 0
    except Exception as e:  # no tracebacks for agents
        print("error: unexpected %s: %s" % (type(e).__name__, e), file=sys.stderr)
        return 1
    return 0
