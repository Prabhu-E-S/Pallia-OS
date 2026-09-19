"""Clinical operational entities.

Observation, MedicationPlan, Visit and CareTask.
"""

import uuid
from datetime import datetime
from typing import Annotated

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.enums import (
    CareTaskPriority,
    CareTaskStatus,
    CareTaskType,
    MedicationPlanStatus,
    ObservationSource,
    ObservationType,
    VisitStatus,
)
from app.models.mixins import OrganizationScopedMixin, TimestampMixin

StrUUID = Annotated[uuid.UUID, mapped_column(Uuid, nullable=True)]


class Observation(OrganizationScopedMixin, TimestampMixin):
    """A single patient observation. Future Care Radar logic builds on this.

    ``value`` is a free-form string on purpose: different observation types
    record different shapes (a pain scale number, sleep hours, free text mood).
    """

    __tablename__ = "observations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recorded_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    type: Mapped[ObservationType] = mapped_column(
        Enum(ObservationType, native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    source: Mapped[ObservationSource] = mapped_column(
        Enum(ObservationSource, native_enum=False, length=32),
        nullable=False,
        default=ObservationSource.MANUAL,
    )

    # Provenance (Phase 3): where the value came from and whether an AI model
    # proposed it. ``human_verified`` records explicit human confirmation.
    source_reference: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("caregiver_reports.id", ondelete="SET NULL"), nullable=True, index=True
    )
    ai_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    human_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    patient: Mapped["Patient"] = relationship(back_populates="observations")
    caregiver_report: Mapped["CaregiverReport | None"] = relationship(back_populates="observations")


class MedicationPlan(OrganizationScopedMixin, TimestampMixin):
    """An authorized medication plan for a patient.

    Phase 1 does NOT generate prescriptions or medication recommendations.
    """

    __tablename__ = "medication_plans"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[MedicationPlanStatus] = mapped_column(
        Enum(MedicationPlanStatus, native_enum=False, length=32),
        nullable=False,
        default=MedicationPlanStatus.ACTIVE,
    )


class Visit(OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "visits"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_to: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[VisitStatus] = mapped_column(
        Enum(VisitStatus, native_enum=False, length=32),
        nullable=False,
        default=VisitStatus.SCHEDULED,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)


class CareTask(OrganizationScopedMixin, TimestampMixin):
    """A discrete care task.

    This entity is an explicit extension point for future Codex OS style
    event-driven integration: status transitions map naturally to domain
    events (e.g. ``care_task.created``, ``followup_overdue``).
    """

    __tablename__ = "care_tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_to: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_type: Mapped[CareTaskType] = mapped_column(
        Enum(CareTaskType, native_enum=False, length=32),
        nullable=False,
        default=CareTaskType.GENERAL,
    )
    priority: Mapped[CareTaskPriority] = mapped_column(
        Enum(CareTaskPriority, native_enum=False, length=32),
        nullable=False,
        default=CareTaskPriority.NORMAL,
        index=True,
    )
    status: Mapped[CareTaskStatus] = mapped_column(
        Enum(CareTaskStatus, native_enum=False, length=32),
        nullable=False,
        default=CareTaskStatus.CREATED,
        index=True,
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
