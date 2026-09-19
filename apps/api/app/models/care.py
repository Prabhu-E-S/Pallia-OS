"""Patient-centric entities.

Patient, Caregiver, PatientCaregiver association, CareTeam,
PatientCareTeamMember, CarePlan and CareGoal.
"""

import uuid
from datetime import date
from typing import Annotated

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.enums import (
    CaregiverRelationship,
    CareGoalPriority,
    CareGoalStatus,
    CarePlanStatus,
    Gender,
    PatientStatus,
    UserRole,
)
from app.models.mixins import OrganizationScopedMixin, TimestampMixin

StrUUID = Annotated[uuid.UUID, mapped_column(Uuid, nullable=True)]


class Patient(OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[Gender | None] = mapped_column(
        Enum(Gender, native_enum=False, length=32), nullable=True
    )
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[PatientStatus] = mapped_column(
        Enum(PatientStatus, native_enum=False, length=32),
        nullable=False,
        default=PatientStatus.ACTIVE,
        index=True,
    )

    care_plans: Mapped[list["CarePlan"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    caregivers: Mapped[list["PatientCaregiver"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    observations: Mapped[list["Observation"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )


class Caregiver(OrganizationScopedMixin, TimestampMixin):
    """A caregiver account linked to a user."""

    __tablename__ = "caregivers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type: Mapped[CaregiverRelationship] = mapped_column(
        "relationship",
        Enum(CaregiverRelationship, native_enum=False, length=32),
        nullable=False,
        default=CaregiverRelationship.FAMILY,
    )

    user: Mapped["User"] = relationship(back_populates="caregivers")


class PatientCaregiver(TimestampMixin):
    """Many-to-many link between patients and caregivers."""

    __tablename__ = "patient_caregivers"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("patients.id", ondelete="CASCADE"), primary_key=True
    )
    caregiver_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("caregivers.id", ondelete="CASCADE"), primary_key=True
    )
    relationship_type: Mapped[CaregiverRelationship | None] = mapped_column(
        "relationship",
        Enum(CaregiverRelationship, native_enum=False, length=32),
        nullable=True,
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    patient: Mapped["Patient"] = relationship(back_populates="caregivers")
    caregiver: Mapped["Caregiver"] = relationship()


class CareTeam(OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "care_teams"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    members: Mapped[list["PatientCareTeamMember"]] = relationship(
        back_populates="care_team", cascade="all, delete-orphan"
    )


class PatientCareTeamMember(TimestampMixin):
    __tablename__ = "patient_care_team_members"

    care_team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("care_teams.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=32), nullable=False
    )

    care_team: Mapped["CareTeam"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship()


class CarePlan(OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "care_plans"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[CarePlanStatus] = mapped_column(
        Enum(CarePlanStatus, native_enum=False, length=32),
        nullable=False,
        default=CarePlanStatus.DRAFT,
        index=True,
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    patient: Mapped["Patient"] = relationship(back_populates="care_plans")
    goals: Mapped[list["CareGoal"]] = relationship(
        back_populates="care_plan", cascade="all, delete-orphan"
    )


class CareGoal(TimestampMixin):
    __tablename__ = "care_goals"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    care_plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("care_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CareGoalStatus] = mapped_column(
        Enum(CareGoalStatus, native_enum=False, length=32),
        nullable=False,
        default=CareGoalStatus.OPEN,
    )
    priority: Mapped[CareGoalPriority] = mapped_column(
        Enum(CareGoalPriority, native_enum=False, length=32),
        nullable=False,
        default=CareGoalPriority.NORMAL,
    )

    care_plan: Mapped["CarePlan"] = relationship(back_populates="goals")
