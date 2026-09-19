from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models import CareTask, Patient, User
from app.models.enums import CareTaskPriority, CareTaskType
from app.schemas.task import CareTaskCreate, CareTaskOut, CareTaskUpdate
from app.services import audit
from app.services import users as user_services
from app.services.patients import get_patient

OPEN_STATUSES = ("CREATED", "ASSIGNED", "ACCEPTED", "IN_PROGRESS")


def _task_out(db: Session, task: CareTask) -> CareTaskOut:
    patient_name = None
    assigned_name = None
    if task.patient_id:
        patient_name = db.scalar(select(Patient.full_name).where(Patient.id == task.patient_id))
    if task.assigned_to:
        assigned_name = db.scalar(select(User.full_name).where(User.id == task.assigned_to))
    out = CareTaskOut.model_validate(task)
    out.patient_name = patient_name
    out.assigned_to_name = assigned_name
    return out


def create_task(db: Session, actor: User, payload: CareTaskCreate) -> CareTask:
    patient = get_patient(db, actor, payload.patient_id)
    if payload.assigned_to:
        user_services.require_user_in_org(db, actor.organization_id, payload.assigned_to)

    task = CareTask(
        organization_id=actor.organization_id,
        patient_id=patient.id,
        assigned_to=payload.assigned_to,
        created_by=actor.id,
        title=payload.title,
        description=payload.description,
        task_type=payload.task_type or CareTaskType.GENERAL,
        priority=payload.priority or CareTaskPriority.NORMAL,
        due_at=payload.due_at,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    audit.record(
        db,
        organization_id=task.organization_id,
        actor_id=actor.id,
        action="care_task.created",
        entity_type="care_task",
        entity_id=task.id,
        metadata={"patient_id": str(task.patient_id), "title": task.title},
    )
    return task


def update_task(db: Session, actor: User, task: CareTask, payload: CareTaskUpdate) -> CareTask:
    if payload.assigned_to:
        user_services.require_user_in_org(db, actor.organization_id, payload.assigned_to)
    data = payload.model_dump(exclude_unset=True)
    for field in (
        "title",
        "description",
        "task_type",
        "priority",
        "assigned_to",
        "due_at",
        "status",
        "completed_at",
    ):
        if field in data:
            setattr(task, field, data[field])
    if data.get("status") in ("COMPLETED", "VERIFIED", "CANCELLED"):
        task.completed_at = data.get("completed_at") or task.completed_at
    db.add(task)
    db.commit()
    db.refresh(task)
    audit.record(
        db,
        organization_id=task.organization_id,
        actor_id=actor.id,
        action="care_task.updated",
        entity_type="care_task",
        entity_id=task.id,
        metadata={"fields": sorted(data.keys())},
    )
    return task


def list_for_patient(db: Session, actor: User, patient: Patient) -> list[CareTaskOut]:
    stmt = (
        select(CareTask)
        .where(
            CareTask.patient_id == patient.id,
            CareTask.organization_id == actor.organization_id,
        )
        .order_by(CareTask.created_at.desc())
        .limit(100)
    )
    return [_task_out(db, t) for t in db.scalars(stmt)]


def list_organization(db: Session, actor: User) -> list[CareTaskOut]:
    stmt = (
        select(CareTask)
        .where(CareTask.organization_id == actor.organization_id)
        .order_by(CareTask.created_at.desc())
        .limit(200)
    )
    return [_task_out(db, t) for t in db.scalars(stmt)]


def list_open_tasks(db: Session, actor: User, limit: int = 10) -> list[CareTaskOut]:
    stmt = (
        select(CareTask)
        .where(
            CareTask.organization_id == actor.organization_id,
            CareTask.status.in_(OPEN_STATUSES),
        )
        .order_by(CareTask.created_at.desc())
        .limit(limit)
    )
    return [_task_out(db, t) for t in db.scalars(stmt)]


def get_task_in_org(db: Session, actor: User, task_id: str) -> CareTask:
    from uuid import UUID

    try:
        uid = UUID(task_id)
    except (ValueError, TypeError) as exc:
        raise NotFoundError("Task not found") from exc
    task = db.scalar(
        select(CareTask).where(
            CareTask.id == uid, CareTask.organization_id == actor.organization_id
        )
    )
    if task is None:
        raise NotFoundError("Task not found")
    return task
