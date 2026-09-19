"""Historical view of what happened across an organization.

Phase 1 simply renders available database records. Automatic summarization
is intentionally out of scope.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    CaregiverReport,
    CaregiverReportStatus,
    CareTask,
    Communication,
    Observation,
    User,
    Visit,
)
from app.schemas.common import AuditActionOut

# Filter values accepted from the client. What the spec calls "Caregiver
# updates" maps to confirmed caregiver reports; singular and plural labels are
# both accepted (the frontend uses the plural category names).
KIND_GROUPS = {
    "all": ("observation", "visit", "task", "communication", "caregiver_report"),
    "observation": ("observation",),
    "observations": ("observation",),
    "visit": ("visit",),
    "visits": ("visit",),
    "task": ("task",),
    "tasks": ("task",),
    "communication": ("communication",),
    "communications": ("communication",),
    "caregiver_report": ("caregiver_report",),
    "caregiver_update": ("caregiver_report",),
    "caregiver_updates": ("caregiver_report",),
}
KIND_FILTERS = frozenset(KIND_GROUPS)


def _label(member) -> str:
    return member.value if hasattr(member, "value") else str(member)


def _report_detail(report: CaregiverReport) -> str:
    parts = []
    if report.pain_level is not None:
        parts.append(f"Pain {report.pain_level}/10")
    for label, value in (
        ("Sleep", report.sleep_hours),
        ("Food intake", report.food_intake),
        ("Mobility", report.mobility),
        ("Mood", report.mood),
        ("Breathing", report.breathing),
        ("Energy", report.energy),
    ):
        if value:
            parts.append(f"{label}: {value}")
    detail = "; ".join(parts)
    if not detail:
        detail = report.general_concern or report.notes or report.transcript or ""
    return detail


def patient_timeline(db: Session, actor: User, patient_id: uuid.UUID, kind: str = "all"):
    """Return a merged, chronological list of a patient's records.

    ``kind`` filters to a single category (default "all"). Only confirmed
    caregiver reports are shown; in-flight DRAFT/REVIEW_REQUIRED reports are not
    part of the patient record yet.
    """
    if kind not in KIND_FILTERS:
        kind = "all"
    groups = KIND_GROUPS[kind]
    items: list[dict] = []

    if "observation" in groups:
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

    if "visit" in groups:
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

    if "task" in groups:
        for task in db.scalars(
            select(CareTask)
            .where(
                CareTask.patient_id == patient_id,
                CareTask.organization_id == actor.organization_id,
            )
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

    if "communication" in groups:
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

    if "caregiver_report" in groups:
        for report in db.scalars(
            select(CaregiverReport)
            .where(
                CaregiverReport.patient_id == patient_id,
                CaregiverReport.organization_id == actor.organization_id,
                CaregiverReport.status == CaregiverReportStatus.CONFIRMED,
            )
            .order_by(CaregiverReport.reported_at.desc())
        ):
            items.append(
                {
                    "id": str(report.id),
                    "kind": "caregiver_report",
                    "title": "Caregiver report",
                    "detail": _report_detail(report),
                    "at": report.reported_at,
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
