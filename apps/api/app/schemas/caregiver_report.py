"""Caregiver report, voice and confirmation schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import (
    CaregiverReportMode,
    ObservationType,
)
from app.schemas.common import ORMModel
from app.schemas.observation import ObservationOut
from app.services.ai.schemas import ExtractedObservation


def _strip(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


class CaregiverReportCreate(BaseModel):
    patient_id: str
    mode: CaregiverReportMode
    reported_at: datetime | None = None

    pain_level: int | None = Field(default=None, ge=0, le=10)
    sleep_hours: str | None = Field(default=None, max_length=32)
    food_intake: str | None = Field(default=None, max_length=128)
    mobility: str | None = Field(default=None, max_length=128)
    mood: str | None = Field(default=None, max_length=128)
    breathing: str | None = Field(default=None, max_length=128)
    energy: str | None = Field(default=None, max_length=128)
    general_concern: str | None = None

    notes: str | None = None
    transcript: str | None = None
    audio_duration_seconds: int | None = Field(default=None, ge=0)

    @field_validator(
        "sleep_hours",
        "food_intake",
        "mobility",
        "mood",
        "breathing",
        "energy",
        "general_concern",
        "notes",
        "transcript",
        mode="before",
    )
    @classmethod
    def _clean(cls, value):
        return _strip(value)


class CaregiverReportUpdate(BaseModel):
    pain_level: int | None = Field(default=None, ge=0, le=10)
    sleep_hours: str | None = Field(default=None, max_length=32)
    food_intake: str | None = Field(default=None, max_length=128)
    mobility: str | None = Field(default=None, max_length=128)
    mood: str | None = Field(default=None, max_length=128)
    breathing: str | None = Field(default=None, max_length=128)
    energy: str | None = Field(default=None, max_length=128)
    general_concern: str | None = None
    notes: str | None = None
    transcript: str | None = None

    @field_validator(
        "sleep_hours",
        "food_intake",
        "mobility",
        "mood",
        "breathing",
        "energy",
        "general_concern",
        "notes",
        "transcript",
        mode="before",
    )
    @classmethod
    def _clean(cls, value):
        return _strip(value)


class CaregiverReportOut(ORMModel):
    id: str
    patient_id: str
    recorded_by: str | None
    recorded_by_name: str | None = None
    reported_at: datetime
    mode: str
    status: str

    pain_level: int | None
    sleep_hours: str | None
    food_intake: str | None
    mobility: str | None
    mood: str | None
    breathing: str | None
    energy: str | None
    general_concern: str | None

    notes: str | None
    transcript: str | None
    audio_duration_seconds: int | None

    ai_generated: bool
    provider: str | None
    model: str | None
    model_version: str | None
    confidence: float | None

    human_verified: bool
    confirmed_at: datetime | None
    confirmed_by: str | None
    cancelled_at: datetime | None
    cancelled_by: str | None
    cancellation_reason: str | None

    created_at: datetime
    updated_at: datetime


class CaregiverReportList(BaseModel):
    items: list[CaregiverReportOut]
    total: int


class VoiceTranscriptOut(BaseModel):
    report_id: str
    patient_id: str
    transcript: str
    language: str | None
    service: str


class AISummaryOut(BaseModel):
    provider: str
    model: str | None
    model_version: str
    confidence: float | None


class ExtractionOut(BaseModel):
    report: CaregiverReportOut
    observations: list[ExtractedObservation]
    not_mentioned: list[str]
    ai: AISummaryOut


class ConfirmedObservation(BaseModel):
    """The human-approved version of one extracted observation (may be edited)."""

    type: ObservationType
    value: str | None = Field(default=None, max_length=255)
    unit: str | None = Field(default=None, max_length=32)
    notes: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("value")
    @classmethod
    def _clean_value(cls, value):
        return _strip(value)


class ObservationConfirm(BaseModel):
    report_id: str
    observations: list[ConfirmedObservation] = Field(default_factory=list)
    reported_at: datetime | None = None


class ObservationConfirmOut(BaseModel):
    report: CaregiverReportOut
    observations: list[ObservationOut]


class ChangeItem(BaseModel):
    """Descriptive, neutral comparison of the two most recent observations of a type."""

    type: str
    current_value: str | None
    current_unit: str | None
    current_observed_at: datetime | None
    previous_value: str | None
    previous_unit: str | None
    previous_observed_at: datetime | None
    comparison: str  # first | unchanged | increased | decreased | changed


class RecentChangesOut(BaseModel):
    items: list[ChangeItem]
