"""Evaluation stage: turn a ParsedResume (+ optional JD) into an Evaluation.

This is the single entry point shared by both the CLI (score.py) and the
website (web.py).
"""

from __future__ import annotations

import llm_utils
from models import Evaluation
from pdf import ParsedResume


def evaluate(resume: ParsedResume, job_description: str | None = None) -> Evaluation:
    system = llm_utils.render("system.jinja")
    user = llm_utils.render(
        "evaluate.jinja",
        resume=resume,
        job_description=(job_description or "").strip() or None,
    )
    return llm_utils.complete(system, user, Evaluation)
