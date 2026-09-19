from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    CarePlan,
    CarePlanStatus,
    CareTask,
    Communication,
    Observation,
    Patient,
    User,
    Visit,
    VisitStatus,
)
from app.schemas.dashboard import ActivityItem, DashboardSummary, OverviewCounts
from app.services.authorization import scoped_patient_ids, where_patient_scope
from app.services.tasks import list_open_tasks
from app.services.visits import _visit_out


def _count(db: Session, model, organization_id, *extra) -> int:
    stmt = select(func.count(model.id)).where(model.organization_id == organization_id)
    for clause in extra:
        stmt = stmt.where(clause)
    return int(db.scalar(stmt) or 0)


def build_summary(db: Session, actor: User) -> DashboardSummary:
    org_id = actor.organization_id
    allowed = scoped_patient_ids(db, actor)
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    _scope_columns = {
        Patient: Patient.id,
        CarePlan: CarePlan.patient_id,
        Visit: Visit.patient_id,
        CareTask: CareTask.patient_id,
    }

    def col(entity):
        column = _scope_columns[entity]
        return column.in_(allowed) if allowed is not None else None

    counts = OverviewCounts(
        patients=_count(db, Patient, org_id, col(Patient)),
        active_care_plans=_count(
            db, CarePlan, org_id, col(CarePlan), CarePlan.status == CarePlanStatus.ACTIVE
        ),
        today_visits=_count(
            db,
            Visit,
            org_id,
            col(Visit),
            Visit.scheduled_at >= today_start,
            Visit.scheduled_at < today_end,
            Visit.status != VisitStatus.CANCELLED,
        ),
        open_tasks=_count(
            db,
            CareTask,
            org_id,
            col(CareTask),
            CareTask.status.in_(("CREATED", "ASSIGNED", "ACCEPTED", "IN_PROGRESS")),
        ),
    )

    visits_stmt = (
        select(Visit)
        .where(
            Visit.organization_id == org_id,
            Visit.scheduled_at >= today_start,
            Visit.scheduled_at < today_end,
            Visit.status != VisitStatus.CANCELLED,
        )
        .order_by(Visit.scheduled_at.asc())
        .limit(10)
    )
    visits_stmt = where_patient_scope(visits_stmt, Visit.patient_id, allowed)
    today_visits = [_visit_out(db, v) for v in db.scalars(visits_stmt)]

    open_tasks = list_open_tasks(db, actor, limit=10)

    recent = _recent_activity(db, actor)

    return DashboardSummary(
        counts=counts,
        today_visits=today_visits,
        open_tasks=open_tasks,
        recent_activity=recent,
    )


def _recent_activity(db: Session, actor: User, limit: int = 10) -> list[ActivityItem]:
    """Merge recent observations, visits, tasks and communications."""

    def patient_name(patient_id):
        if not patient_id:
            return None
        return db.scalar(select(Patient.full_name).where(Patient.id == patient_id))

    def scoped(stmt, entity):
        return where_patient_scope(stmt, entity.patient_id, scoped_patient_ids(db, actor))

    items: list[ActivityItem] = []

    for obs in db.scalars(
        scoped(
            select(Observation)
            .where(Observation.organization_id == actor.organization_id)
            .order_by(Observation.created_at.desc())
            .limit(limit),
            Observation,
        )
    ):
        items.append(
            ActivityItem(
                id=str(obs.id),
                kind="observation",
                patient_id=str(obs.patient_id) if obs.patient_id else None,
                patient_name=patient_name(obs.patient_id),
                title=f"{obs.type.value if hasattr(obs.type, 'value') else obs.type} recorded",
                at=obs.created_at,
            )
        )

    for visit in db.scalars(
        scoped(
            select(Visit)
            .where(Visit.organization_id == actor.organization_id)
            .order_by(Visit.created_at.desc())
            .limit(limit),
            Visit,
        )
    ):
        items.append(
            ActivityItem(
                id=str(visit.id),
                kind="visit",
                patient_id=str(visit.patient_id) if visit.patient_id else None,
                patient_name=patient_name(visit.patient_id),
                title="Visit scheduled",
                at=visit.created_at,
            )
        )

    for task in db.scalars(
        scoped(
            select(CareTask)
            .where(CareTask.organization_id == actor.organization_id)
            .order_by(CareTask.created_at.desc())
            .limit(limit),
            CareTask,
        )
    ):
        items.append(
            ActivityItem(
                id=str(task.id),
                kind="task",
                patient_id=str(task.patient_id) if task.patient_id else None,
                patient_name=patient_name(task.patient_id),
                title=f"Task: {task.title}",
                at=task.created_at,
            )
        )

    for comm in db.scalars(
        scoped(
            select(Communication)
            .where(Communication.organization_id == actor.organization_id)
            .order_by(Communication.created_at.desc())
            .limit(limit),
            Communication,
        )
    ):
        items.append(
            ActivityItem(
                id=str(comm.id),
                kind="communication",
                patient_id=str(comm.patient_id) if comm.patient_id else None,
                patient_name=patient_name(comm.patient_id),
                title="Communication recorded",
                at=comm.created_at,
            )
        )

    items.sort(key=lambda item: item.at, reverse=True)
    return items[:limit]
