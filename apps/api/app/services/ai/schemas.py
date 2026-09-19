"""Schemas for the AI extraction contract.

These live beside the prompt so the provider input/output contract stays in
one place. They mirror a subset of ``app/schemas/observation.py`` but use
``confidence`` (0..1) instead of requiring a verified value.
"""

from pydantic import BaseModel, Field, field_validator

from app.models.enums import ObservationType

CONFIDENCE_RANGE = (0.0, 1.0)


class ExtractedObservation(BaseModel):
    type: ObservationType
    value: str | None = Field(default=None, max_length=255)
    unit: str | None = Field(default=None, max_length=32)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    note: str | None = Field(default=None, max_length=512)

    @field_validator("value")
    @classmethod
    def _strip_value(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ExtractionOutput(BaseModel):
    """What a provider returns for one transcript."""

    observations: list[ExtractedObservation] = Field(default_factory=list)
    not_mentioned: list[str] = Field(default_factory=list)
    summary: str | None = Field(default=None, max_length=512)
