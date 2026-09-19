"""Historical view of what happened across an organization.

Phase 1 simply renders available database records. Automatic summarization
is intentionally out of scope.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CareTask, Communication, Observation, User, Visit
from app.schemas.common import AuditActionOut


def _label(member) -> str:
    return member.value if hasattr(member, "value") else str(member)


def patient_timeline(db: Session, actor: User, patient_id: uuid.UUID):
    """Return a merged, chronological list of a patient's records."""
    items: list[dict] = []

    for obs in db.scalars(
        select(Observation)
        .where(
            Observation.patient_id == patient_id,
            Observation.organization_id == actor.organization_id,
        )
        .order_by(Observation.observed_at.desc())
    ):
        items.append(
            {
                "id": str(obs.id),
                "kind": "observation",
                "title": f"{_label(obs.type)} observation",
                "detail": obs.value or obs.notes or "",
                "at": obs.observed_at,
            }
        )

    for visit in db.scalars(
        select(Visit)
        .where(Visit.patient_id == patient_id, Visit.organization_id == actor.organization_id)
        .order_by(Visit.scheduled_at.desc())
    ):
        items.append(
            {
                "id": str(visit.id),
                "kind": "visit",
                "title": f"Visit {_label(visit.status)}",
                "detail": visit.notes or "",
                "at": visit.scheduled_at,
            }
        )

    for task in db.scalars(
        select(CareTask)
        .where(CareTask.patient_id == patient_id, CareTask.organization_id == actor.organization_id)
        .order_by(CareTask.created_at.desc())
    ):
        items.append(
            {
                "id": str(task.id),
                "kind": "task",
                "title": task.title,
                "detail": _label(task.status),
                "at": task.created_at,
            }
        )

    for comm in db.scalars(
        select(Communication)
        .where(
            Communication.patient_id == patient_id,
            Communication.organization_id == actor.organization_id,
        )
        .order_by(Communication.created_at.desc())
    ):
        items.append(
            {
                "id": str(comm.id),
                "kind": "communication",
                "title": "Communication",
                "detail": comm.content,
                "at": comm.created_at,
            }
        )

    items.sort(key=lambda item: item["at"], reverse=True)
    return items


def audit_history(db: Session, actor: User, limit: int = 50) -> list[AuditActionOut]:
    from app.models import AuditLog

    stmt = (
        select(AuditLog)
        .where(AuditLog.organization_id == actor.organization_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))
