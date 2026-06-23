"""Pydantic schemas for structured LLM output."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedFields(BaseModel):
    """What an ATS would manage to pull out of the parsed text. Empty/garbled
    fields are exactly what the ATS would fail to populate in its database."""

    name: str | None = Field(None, description="Full name, or null if not parseable")
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    most_recent_title: str | None = None
    most_recent_employer: str | None = None
    years_experience: str | None = Field(None, description="Estimate, e.g. '5 years'")
    education: str | None = None
    skills: list[str] = Field(default_factory=list)
    parse_problems: list[str] = Field(
        default_factory=list,
        description="Fields that look garbled, merged, or impossible to extract cleanly",
    )


class KeywordMatch(BaseModel):
    matched: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    match_score: int = Field(..., ge=0, le=100, description="JD keyword coverage, 0-100")


class Evaluation(BaseModel):
    ats_readiness_score: int = Field(..., ge=0, le=100)
    summary: str = Field(..., description="2-3 sentence plain-English verdict")
    extracted: ExtractedFields
    keyword_match: KeywordMatch | None = None
    fixes: list[str] = Field(default_factory=list, description="Prioritized, concrete fixes")
