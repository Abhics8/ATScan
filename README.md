---
title: ATS Agent
emoji: 📄
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# ATS Agent

A resume → ATS evaluation pipeline, structured like
[interviewstreet/hiring-agent](https://github.com/interviewstreet/hiring-agent)
but for the **candidate** side and built on **Claude**.

Upload/point at a resume PDF (and optionally a job description); the agent
simulates how a generic ATS parses it, predicts which fields it would capture,
scores keyword match against the JD, and lists concrete fixes.

## Pipeline (same shape as hiring-agent)

```
pdf.py        # PyMuPDF: extract text the way a dumb ATS does + flag parse-breakers
prompts/      # Jinja prompt templates (system.jinja, evaluate.jinja)
models.py     # Pydantic schemas for structured output
llm_utils.py  # render prompts + call Claude (structured output, dev-mode caching)
evaluator.py  # the one entry point: ParsedResume (+JD) -> Evaluation
config.py     # env config (.env): model, provider, DEV_MODE
score.py      # CLI orchestrator
web.py        # thin website over the same pipeline (for convenience)
static/       # web frontend
```

The CLI and the website call the **same** `evaluator.evaluate()` — the website
is just a convenience wrapper, not a second implementation.

## Setup (free)

Uses Google **Gemini free tier** by default (no credit card).

```bash
pip install -r requirements.txt
cp .env.example .env
# get a free key at https://aistudio.google.com/apikey, then put it in .env:
#   LLM_PROVIDER=gemini
#   GEMINI_API_KEY=AIza...
```

To use paid Claude instead, set `LLM_PROVIDER=anthropic` + `ANTHROPIC_API_KEY`.

## Use it — CLI

```bash
python score.py resume.pdf
python score.py resume.pdf --jd job.txt
python score.py resume.pdf --jd job.txt --json report.json
```

## Use it — website

```bash
python web.py               # http://localhost:8011
```

Upload a PDF, paste a JD, get the same report in the browser.

## Notes

- **DEV_MODE** (default on) caches LLM responses in `.cache/` so re-running on the
  same resume doesn't re-bill. Set `DEV_MODE=0` to disable.
- Every company's ATS parser is proprietary; this simulates the ~90% of behavior
  common to Workday / Greenhouse / Lever / Taleo / iCIMS.
- Model defaults to `claude-opus-4-8` (override with `DEFAULT_MODEL`).
```
