---
title: ATS Agent
emoji: 📄
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# 📄 ATS Resume Checker

### Find out if your resume actually makes it past the robots — before you apply.

When you apply for a job online, a human usually isn't the first one to read your
resume. A piece of software called an **ATS** (Applicant Tracking System) scans it
first, pulls out your details, and decides whether you even reach a recruiter.
The problem: these systems are picky. A nice-looking resume can confuse them, and
good candidates get filtered out for reasons that have nothing to do with their
skills.

**This tool shows you what that software sees.** Upload your resume, optionally
paste the job posting, and in a few seconds you get a plain-English report card.

👉 **Try it here:** https://ab0202000-ats-agent.hf.space

---

## What you get

- **An ATS readiness score (0–100)** — how cleanly the software can read your
  resume.
- **A keyword match score** — if you paste the job description, how well your
  resume lines up with what the employer is looking for.
- **What the system actually captured** — your name, contact info, job titles,
  education, and skills, *exactly as the software pulled them*. If something is
  missing or jumbled here, that's a red flag.
- **A clear list of fixes** — specific, prioritized changes you can make, in
  everyday language.
- **Warnings about common mistakes** — like using two columns, tables, images, or
  putting your phone number in the page header (all things that quietly trip up
  these systems).

## Why it matters

You could have the perfect background and still get auto-rejected because:

- Your resume uses **two columns**, and the software reads straight across,
  scrambling your sentences.
- Your **contact details are in the header**, which some systems ignore entirely.
- Your resume is really an **image** (or was scanned), so the software reads
  almost nothing.

This tool catches those issues so you can fix them *before* they cost you an
interview.

## How to use it

1. Open the link above.
2. Drag in your resume (PDF).
3. (Optional) Paste the job posting you're applying to.
4. Click **Analyze** and read your report.

A simple rule of thumb:

| Score | What to do |
|-------|------------|
| **85+** | You're good — apply as-is. |
| **70–84** | Fix the flagged issues first, then apply. |
| **Below 70** | Likely getting filtered out — fix before applying anywhere. |

---

## For developers

A small, modular pipeline with both a web app and a command-line version sharing
one engine:

```
pdf.py        Reads the PDF the way an ATS does + detects layout problems
prompts/      Prompt templates
models.py     Structured output schemas
llm_utils.py  Prompt rendering, model calls, response caching, fallback
evaluator.py  Single entry point: parsed resume (+ job) → evaluation
config.py     Settings loaded from the environment (.env)
score.py      Command-line version
web.py        Web app (FastAPI)
static/       Web frontend
```

**Tech:** Python · FastAPI · PyMuPDF · Jinja2 · Pydantic · Google Gemini API · Docker

**Run locally:**

```bash
git clone https://github.com/Abhics8/ats-agent
cd ats-agent
pip install -r requirements.txt

cp .env.example .env   # add a free key from https://aistudio.google.com/apikey
python web.py          # open http://localhost:8011
```

Command line:

```bash
python score.py resume.pdf --jd job.txt
```

**Deploy:** includes a `Dockerfile` (port 7860). Push to any container host and set
`GEMINI_API_KEY` and `LLM_PROVIDER=gemini` as secrets. Runs as-is on Hugging Face
Spaces.

## A note on privacy

Resumes you upload are sent to the AI provider's API to be analyzed. If you'd
rather keep your documents on your own computer, run it locally.

## License

MIT
