"""Object-level authorization.

Staff roles (ADMIN, CARE_COORDINATOR, NURSE, DOCTOR) operate org-wide, matching
the Phase 1 policy. CAREGIVER is restricted to patients they are linked to via
``patient_caregivers``. PATIENT is restricted to the record linked through
``User.patient_id``.

Scope violations surface as 404s so a caller cannot distinguish "this record
does not exist" from "you are not allowed to see it".
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models import Caregiver, Patient, PatientCaregiver, User
from app.models.enums import UserRole

STAFF_ROLES = frozenset(
    {UserRole.ADMIN, UserRole.CARE_COORDINATOR, UserRole.NURSE, UserRole.DOCTOR}
)


def is_staff(actor: User) -> bool:
    return actor.role in STAFF_ROLES


def scoped_patient_ids(db: Session, actor: User) -> set[uuid.UUID] | None:
    """Patient ids an actor may see, or ``None`` for org-wide access.

    ``None`` means "everything in this organization"; a (possibly empty) set
    means "only these patient ids".
    """
    if is_staff(actor):
        return None
    if actor.role == UserRole.CAREGIVER:
        caregiver_ids = list(db.scalars(select(Caregiver.id).where(Caregiver.user_id == actor.id)))
        if not caregiver_ids:
            return set()
        rows = db.scalars(
            select(PatientCaregiver.patient_id).where(
                PatientCaregiver.caregiver_id.in_(caregiver_ids)
            )
        ).all()
        return set(rows)
    if actor.role == UserRole.PATIENT:
        return {actor.patient_id} if actor.patient_id else set()
    return None


def ensure_patient_access(db: Session, actor: User, patient: Patient) -> Patient:
    """Confirm the actor may access ``patient``, otherwise raise 404."""
    allowed = scoped_patient_ids(db, actor)
    if allowed is None or patient.id in allowed:
        return patient
    raise NotFoundError("Patient not found")


def where_patient_scope(stmt, patient_id_column, allowed: set[uuid.UUID] | None):
    """Restrict a query to the actor's visible patients when scoped.

    Pass the entity's ``patient_id`` column and the result of
    ``scoped_patient_ids``; ``None`` (staff) leaves the query org-wide.
    """
    if allowed is not None:
        stmt = stmt.where(patient_id_column.in_(allowed))
    return stmt
