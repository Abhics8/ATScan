"""Central configuration, loaded from the environment (.env supported).

Mirrors the hiring-agent layout: a single config module other modules import.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# --- LLM ---
# Provider: "gemini" (free tier) or "anthropic" (paid, highest quality).
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

# Paid provider
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Free provider (Google AI Studio — free key, no credit card)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Model defaults to a sensible per-provider choice unless overridden.
_DEFAULT_MODELS = {"anthropic": "claude-opus-4-8", "gemini": "gemini-2.5-flash"}
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL") or _DEFAULT_MODELS.get(LLM_PROVIDER, "gemini-2.5-flash")

# --- Behavior ---
# DEV_MODE caches LLM responses to disk so repeated runs on the same resume
# don't re-bill. Set DEV_MODE=0 to disable.
DEV_MODE = os.getenv("DEV_MODE", "1") not in ("0", "false", "False", "")
CACHE_DIR = os.getenv("CACHE_DIR", ".cache")
