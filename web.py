"""Thin website over the same pipeline used by score.py.

Run:  python web.py            (or: uvicorn web:app --port 8011)
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import config
import pdf
from evaluator import evaluate

STATIC = Path(__file__).parent / "static"
MAX_BYTES = 10 * 1024 * 1024

app = FastAPI(title="ATS Agent")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


def _provider_key() -> str | None:
    return config.GEMINI_API_KEY if config.LLM_PROVIDER == "gemini" else config.ANTHROPIC_API_KEY


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True, "provider": config.LLM_PROVIDER, "has_api_key": bool(_provider_key())}


@app.post("/api/evaluate")
async def api_evaluate(resume: UploadFile = File(...), job_description: str = Form("")) -> JSONResponse:
    if not _provider_key():
        raise HTTPException(500, f"Server is missing the API key for provider '{config.LLM_PROVIDER}'.")
    data = await resume.read()
    if not data:
        raise HTTPException(400, "Empty file.")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "File too large (max 10 MB).")
    try:
        parse = pdf.extract(data)
    except Exception as exc:
        raise HTTPException(400, f"Could not read PDF: {exc}")
    try:
        ev = evaluate(parse, job_description)
    except Exception as exc:
        raise HTTPException(502, f"Evaluation failed: {exc}")
    return JSONResponse({
        "evaluation": ev.model_dump(),
        "parse": {"warnings": parse.warnings, "text": parse.text,
                  "page_count": parse.page_count, "word_count": parse.word_count},
    })


app.mount("/static", StaticFiles(directory=STATIC), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web:app", host="0.0.0.0", port=8011, reload=True)
