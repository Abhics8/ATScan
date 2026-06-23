"""End-to-end CLI orchestrator.

Usage:
    python score.py resume.pdf
    python score.py resume.pdf --jd job.txt
    python score.py resume.pdf --jd job.txt --json out.json
"""

from __future__ import annotations

import argparse
import sys

import pdf
from evaluator import evaluate
from models import Evaluation


def _bar(score: int) -> str:
    filled = round(score / 10)
    return "█" * filled + "░" * (10 - filled) + f" {score}/100"


def render_report(ev: Evaluation, parse: pdf.ParsedResume) -> str:
    out = []
    out.append("=" * 60)
    out.append("ATS RESUME REPORT")
    out.append("=" * 60)
    out.append(f"ATS readiness : {_bar(ev.ats_readiness_score)}")
    if ev.keyword_match:
        out.append(f"Keyword match : {_bar(ev.keyword_match.match_score)}")
    out.append("")
    out.append(ev.summary)
    out.append("")

    if ev.fixes:
        out.append("PRIORITIZED FIXES")
        out += [f"  {i}. {f}" for i, f in enumerate(ev.fixes, 1)]
        out.append("")

    if ev.keyword_match:
        out.append("KEYWORD MATCH")
        out.append("  matched: " + (", ".join(ev.keyword_match.matched) or "none"))
        out.append("  missing: " + (", ".join(ev.keyword_match.missing) or "none"))
        out.append("")

    e = ev.extracted
    out.append("WHAT THE ATS CAPTURES")
    for label, val in [
        ("name", e.name), ("email", e.email), ("phone", e.phone),
        ("location", e.location), ("recent title", e.most_recent_title),
        ("recent employer", e.most_recent_employer),
        ("experience", e.years_experience), ("education", e.education),
        ("skills", ", ".join(e.skills)),
    ]:
        out.append(f"  {label:<16}: {val if val else '— not captured —'}")
    if e.parse_problems:
        out.append("  parse problems: " + "; ".join(e.parse_problems))
    out.append("")

    if parse.warnings:
        out.append("STRUCTURAL WARNINGS")
        out += [f"  - {w}" for w in parse.warnings]
    out.append("=" * 60)
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Simulate an ATS on a resume PDF.")
    ap.add_argument("resume", help="Path to the resume PDF")
    ap.add_argument("--jd", help="Path to a job-description text file (optional)")
    ap.add_argument("--json", dest="json_out", help="Also write the full report to this JSON file")
    args = ap.parse_args(argv)

    parse = pdf.extract_file(args.resume)
    jd = None
    if args.jd:
        with open(args.jd, encoding="utf-8") as fh:
            jd = fh.read()

    ev = evaluate(parse, jd)
    print(render_report(ev, parse))

    if args.json_out:
        import json
        payload = {"evaluation": ev.model_dump(), "parse_warnings": parse.warnings}
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        print(f"\nWrote {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
