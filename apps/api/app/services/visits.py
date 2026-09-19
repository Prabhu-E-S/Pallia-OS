from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models import Patient, User, Visit
from app.schemas.visit import VisitCreate, VisitOut, VisitUpdate
from app.services import audit
from app.services import users as user_services
from app.services.patients import get_patient


def _visit_out(db: Session, visit: Visit) -> VisitOut:
    patient_name = None
    assigned_name = None
    if visit.patient_id:
        patient_name = db.scalar(select(Patient.full_name).where(Patient.id == visit.patient_id))
    if visit.assigned_to:
        assigned_name = db.scalar(select(User.full_name).where(User.id == visit.assigned_to))
    out = VisitOut.model_validate(visit)
    out.patient_name = patient_name
    out.assigned_to_name = assigned_name
    return out


def create_visit(db: Session, actor: User, payload: VisitCreate) -> Visit:
    patient = get_patient(db, actor, payload.patient_id)
    if payload.assigned_to:
        user_services.require_user_in_org(db, actor.organization_id, payload.assigned_to)

    visit = Visit(
        organization_id=actor.organization_id,
        patient_id=patient.id,
        assigned_to=payload.assigned_to,
        scheduled_at=payload.scheduled_at,
        notes=payload.notes,
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)
    audit.record(
        db,
        organization_id=visit.organization_id,
        actor_id=actor.id,
        action="visit.created",
        entity_type="visit",
        entity_id=visit.id,
        metadata={"patient_id": str(visit.patient_id)},
    )
    return visit


def update_visit(db: Session, actor: User, visit: Visit, payload: VisitUpdate) -> Visit:
    if payload.assigned_to:
        user_services.require_user_in_org(db, actor.organization_id, payload.assigned_to)
    data = payload.model_dump(exclude_unset=True)
    for field in ("scheduled_at", "assigned_to", "status", "notes", "started_at", "completed_at"):
        if field in data:
            setattr(visit, field, data[field])
    db.add(visit)
    db.commit()
    db.refresh(visit)
    audit.record(
        db,
        organization_id=visit.organization_id,
        actor_id=actor.id,
        action="visit.updated",
        entity_type="visit",
        entity_id=visit.id,
        metadata={"fields": sorted(data.keys())},
    )
    return visit


def list_for_patient(db: Session, actor: User, patient: Patient) -> list[VisitOut]:
    stmt = (
        select(Visit)
        .where(
            Visit.patient_id == patient.id,
            Visit.organization_id == actor.organization_id,
        )
        .order_by(Visit.scheduled_at.desc())
        .limit(100)
    )
    return [_visit_out(db, v) for v in db.scalars(stmt)]


def list_organization(db: Session, actor: User) -> list[VisitOut]:
    stmt = (
        select(Visit)
        .where(Visit.organization_id == actor.organization_id)
        .order_by(Visit.scheduled_at.desc())
        .limit(200)
    )
    return [_visit_out(db, v) for v in db.scalars(stmt)]


def get_visit_in_org(db: Session, actor: User, visit_id: str) -> Visit:
    from uuid import UUID

    try:
        uid = UUID(visit_id)
    except (ValueError, TypeError) as exc:
        raise NotFoundError("Visit not found") from exc
    visit = db.scalar(
        select(Visit).where(Visit.id == uid, Visit.organization_id == actor.organization_id)
    )
    if visit is None:
        raise NotFoundError("Visit not found")
    return visit
