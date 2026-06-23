"""LLM provider utilities: render Jinja prompts and call the model with
structured output. Provider-agnostic shape, Anthropic (Claude) implementation.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Type, TypeVar

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel

import config

_PROMPTS = Path(__file__).parent / "prompts"
_env = Environment(
    loader=FileSystemLoader(_PROMPTS),
    autoescape=select_autoescape(enabled_extensions=()),  # plain text prompts
    trim_blocks=True,
    lstrip_blocks=True,
)

T = TypeVar("T", bound=BaseModel)


def render(template: str, **ctx) -> str:
    return _env.get_template(template).render(**ctx)


def _cache_path(key: str) -> Path:
    d = Path(config.CACHE_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{key}.json"


def complete(system: str, user: str, schema: Type[T], model: str | None = None) -> T:
    """Call the model and parse the response into `schema`.

    In DEV_MODE, responses are cached to disk keyed by (model, system, user, schema)
    so repeated runs on the same resume don't re-bill.
    """
    model = model or config.DEFAULT_MODEL

    if config.DEV_MODE:
        key = hashlib.sha256(
            f"{model}\x00{system}\x00{user}\x00{schema.__name__}".encode()
        ).hexdigest()[:32]
        cached = _cache_path(key)
        if cached.exists():
            return schema.model_validate_json(cached.read_text())

    if config.LLM_PROVIDER == "anthropic":
        result = _anthropic(system, user, schema, model)
    elif config.LLM_PROVIDER == "gemini":
        result = _gemini(system, user, schema, model)
    else:
        raise NotImplementedError(f"Provider '{config.LLM_PROVIDER}' not implemented.")

    if config.DEV_MODE:
        _cache_path(key).write_text(result.model_dump_json())

    return result


def _anthropic(system: str, user: str, schema: Type[T], model: str) -> T:
    import anthropic

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.messages.parse(
        model=model,
        max_tokens=8000,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_format=schema,
    )
    return response.parsed_output


def _gemini(system: str, user: str, schema: Type[T], model: str) -> T:
    from google import genai
    from google.genai import types

    # We don't pass `response_schema=` because google-genai's schema converter
    # chokes on Optional nested Pydantic models. Instead we ask for JSON and
    # embed the JSON Schema in the instruction, then validate ourselves.
    schema_json = json.dumps(schema.model_json_schema())
    instruction = (
        system
        + "\n\nReturn ONLY a single JSON object that conforms to this JSON Schema. "
        + "No markdown, no code fences, no commentary.\n\nJSON Schema:\n"
        + schema_json
    )

    import time

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    cfg = types.GenerateContentConfig(
        system_instruction=instruction,
        response_mime_type="application/json",
        max_output_tokens=8000,
    )

    # Try the primary model, then fall back across other free models. Each model
    # gets a couple of retries for transient 503/429 spikes before moving on.
    candidates = [model] + [m for m in config.GEMINI_FALLBACKS if m != model]
    response = None
    last_exc: Exception | None = None
    for cand in candidates:
        for i in range(3):
            try:
                response = client.models.generate_content(model=cand, contents=user, config=cfg)
                break
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                msg = str(exc)
                transient = any(s in msg for s in ("503", "UNAVAILABLE", "429", "overloaded", "high demand"))
                if not transient or i == 2:
                    break  # give up on this model, try the next candidate
                time.sleep(2 * (i + 1))
        if response is not None:
            break
    if response is None:
        raise last_exc  # type: ignore[misc]

    text = (response.text or "").strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1] if "```" in text[3:] else text.strip("`")
        if text.lstrip().lower().startswith("json"):
            text = text.lstrip()[4:]
    return schema.model_validate_json(text)
