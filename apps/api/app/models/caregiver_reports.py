"""Caregiver report entities.

A caregiver report is the caregiver's structured (or free-form, or voice
derived) update about a patient's day. Manual submissions are confirmed
immediately - the caregiver is the human source. Voice submissions go through
a transcript review + machine-extraction step and require explicit human
confirmation before any observation is persisted.

Phase 3 keeps this intentionally simple: a dedicated table for the
DRAFT -> REVIEW_REQUIRED -> CONFIRMED lifecycle plus transcript/AI metadata,
with extracted observations linked back via
``Observation.source_reference``.
"""

import uuid
from datetime import datetime
from typing import Annotated

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.enums import CaregiverReportMode, CaregiverReportStatus
from app.models.mixins import OrganizationScopedMixin, TimestampMixin

StrUUID = Annotated[uuid.UUID, mapped_column(Uuid, nullable=True)]


class CaregiverReport(OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "caregiver_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recorded_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    mode: Mapped[CaregiverReportMode] = mapped_column(
        Enum(CaregiverReportMode, native_enum=False, length=32), nullable=False
    )
    status: Mapped[CaregiverReportStatus] = mapped_column(
        Enum(CaregiverReportStatus, native_enum=False, length=32),
        nullable=False,
        default=CaregiverReportStatus.DRAFT,
        index=True,
    )

    # Structured fields (QUICK_STATUS / STRUCTURED / extracted from VOICE).
    pain_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sleep_hours: Mapped[str | None] = mapped_column(String(32), nullable=True)
    food_intake: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mobility: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mood: Mapped[str | None] = mapped_column(String(128), nullable=True)
    breathing: Mapped[str | None] = mapped_column(String(128), nullable=True)
    energy: Mapped[str | None] = mapped_column(String(128), nullable=True)
    general_concern: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Free-form notes (TEXT mode) or transcript (VOICE mode).
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Sound data is not stored; only duration is retained.
    audio_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # AI provenance. Always None for purely manual submissions.
    ai_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    extraction: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Review outcome.
    human_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    observations: Mapped[list["Observation"]] = relationship(
        back_populates="caregiver_report"  # type: ignore[name-defined]
    )
