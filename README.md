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

**Will your resume survive a company's Applicant Tracking System?**

Most resumes are filtered by software before a human ever sees them. ATS Resume
Checker simulates how a generic ATS parses your PDF — stripping the visual
layout and reading the raw text the way the parser does — then tells you which
fields it can actually extract, how well you match a job posting, and exactly
what to fix.

🔗 **Live demo:** https://ab0202000-ats-agent.hf.space

---

## What it does

- **Parse simulation** — extracts your resume the way an ATS does (no visual
  layout), so you can see what the machine *actually* reads vs. what you see.
- **Structural diagnostics** — flags the things that break real parsers:
  multi-column layouts, tables, text-in-images, header/footer contact info, and
  non-standard fonts.
- **Field extraction** — shows which fields (name, contact, titles, employers,
  education, skills) the parser can reliably pull, and which come out garbled or
  missing.
- **Keyword matching** — paste a job description and get a match score plus the
  important terms you're missing.
- **Actionable fixes** — a prioritized, concrete list of changes to raise your
  ATS readiness.

Works for the parsing behavior common to Workday, Greenhouse, Lever, Taleo, and
iCIMS. (Every vendor's parser is proprietary, so scores are guidance, not a
guarantee.)

## Two ways to use it

| Interface | Command |
|-----------|---------|
| **Web app** | `python web.py` → open http://localhost:8011 |
| **CLI** | `python score.py resume.pdf --jd job.txt` |

Both share the same evaluation engine — the website is just a convenience layer
over the pipeline.

## Architecture

A small, modular pipeline — each stage is independently testable:

```
pdf.py        PDF → ATS-style raw text + parse-breaker detection (PyMuPDF)
prompts/      Prompt templates (Jinja2)
models.py     Typed output schemas (Pydantic)
llm_utils.py  Prompt rendering + model call + response caching
evaluator.py  The single entry point: ParsedResume (+JD) → Evaluation
config.py     Environment-driven config (.env)
score.py      CLI orchestrator
web.py        FastAPI website over the same pipeline
static/       Frontend (HTML / CSS / JS)
```

The LLM layer is **provider-agnostic** (set via `LLM_PROVIDER`) and resilient —
it retries transient errors and falls back across models if one is overloaded.

## Tech stack

Python · FastAPI · PyMuPDF · Jinja2 · Pydantic · Google Gemini API · Docker

## Quick start

```bash
git clone https://github.com/Abhics8/ats-agent
cd ats-agent
pip install -r requirements.txt

cp .env.example .env
# add your free Google AI Studio key (https://aistudio.google.com/apikey):
#   LLM_PROVIDER=gemini
#   GEMINI_API_KEY=...
```

Run the website:

```bash
python web.py            # http://localhost:8011
```

Or the CLI:

```bash
python score.py resume.pdf
python score.py resume.pdf --jd job.txt --json report.json
```

## Deploy

Ships with a `Dockerfile` (listens on port 7860). Deploy to any container host:
push the repo and set `GEMINI_API_KEY` + `LLM_PROVIDER=gemini` as environment
secrets. The included config runs as-is on Hugging Face Spaces (Docker SDK).

## Privacy note

Uploaded resumes are sent to the configured model provider's API for analysis.
Run locally if you'd rather keep your documents on your own machine.

## License

MIT
