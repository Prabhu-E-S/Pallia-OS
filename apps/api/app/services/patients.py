import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFoundError
from app.models import (
    Caregiver,
    CareGoal,
    CarePlan,
    CareTeam,
    Patient,
    PatientCaregiver,
    PatientCareTeamMember,
    User,
)
from app.schemas.patient import (
    CarePlanOut,
    CareTeamMemberOut,
    PatientCaregiverOut,
    PatientDetail,
    PatientSummary,
    PatientUpdate,
)
from app.services import audit
from app.services.authorization import ensure_patient_access, scoped_patient_ids

_scalar_fields = {
    "full_name",
    "date_of_birth",
    "gender",
    "phone",
    "address",
    "preferred_language",
    "emergency_contact_name",
    "emergency_contact_phone",
    "status",
}

_PLAN_FIELDS = {"status", "summary", "start_date", "review_date"}

_GOAL_FIELDS = {"title", "description", "status", "priority"}


def get_patient(db: Session, actor: User, patient_id: str) -> Patient:
    try:
        uid = uuid.UUID(patient_id)
    except (ValueError, AttributeError, TypeError) as exc:
        raise NotFoundError("Patient not found") from exc
    patient = db.scalar(
        select(Patient).where(
            Patient.id == uid,
            Patient.organization_id == actor.organization_id,
        )
    )
    if patient is None:
        raise NotFoundError("Patient not found")
    return ensure_patient_access(db, actor, patient)


def list_patients(db: Session, actor: User) -> list[Patient]:
    stmt = (
        select(Patient)
        .where(Patient.organization_id == actor.organization_id)
        .order_by(Patient.created_at.desc())
        .limit(200)
    )
    allowed = scoped_patient_ids(db, actor)
    if allowed is not None:
        stmt = stmt.where(Patient.id.in_(allowed))
    return list(db.scalars(stmt))


def create_patient(db: Session, actor: User, payload) -> Patient:
    patient = Patient(
        organization_id=actor.organization_id,
        full_name=payload.full_name,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        phone=payload.phone,
        address=payload.address,
        preferred_language=payload.preferred_language,
        emergency_contact_name=payload.emergency_contact_name,
        emergency_contact_phone=payload.emergency_contact_phone,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    audit.record(
        db,
        organization_id=patient.organization_id,
        actor_id=actor.id,
        action="patient.created",
        entity_type="patient",
        entity_id=patient.id,
        metadata={"full_name": patient.full_name},
    )
    return patient


def update_patient(db: Session, actor: User, patient: Patient, payload: PatientUpdate) -> Patient:
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if field in _scalar_fields:
            setattr(patient, field, value)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    audit.record(
        db,
        organization_id=patient.organization_id,
        actor_id=actor.id,
        action="patient.updated",
        entity_type="patient",
        entity_id=patient.id,
        metadata={"fields": sorted(data.keys())},
    )
    return patient


def build_summary(patient: Patient) -> PatientSummary:
    return PatientSummary.model_validate(patient)


def _care_team_members(
    db: Session, patient_id: uuid.UUID, organization_id: uuid.UUID
) -> list[CareTeamMemberOut]:
    rows = db.execute(
        select(User.id, User.full_name, User.email, PatientCareTeamMember.role)
        .join(PatientCareTeamMember, PatientCareTeamMember.user_id == User.id)
        .join(CareTeam, CareTeam.id == PatientCareTeamMember.care_team_id)
        .where(CareTeam.patient_id == patient_id, CareTeam.organization_id == organization_id)
    ).all()
    return [
        CareTeamMemberOut(
            user_id=str(row.id),
            full_name=row.full_name,
            email=row.email,
            role=row.role.value if hasattr(row.role, "value") else str(row.role),
        )
        for row in rows
    ]


def _caregivers(db: Session, patient_id: uuid.UUID) -> list[PatientCaregiverOut]:
    rows = db.execute(
        select(
            PatientCaregiver.caregiver_id,
            User.full_name,
            PatientCaregiver.relationship_type,
            PatientCaregiver.is_primary,
        )
        .join(Caregiver, Caregiver.id == PatientCaregiver.caregiver_id)
        .join(User, User.id == Caregiver.user_id)
        .where(PatientCaregiver.patient_id == patient_id)
    ).all()
    return [
        PatientCaregiverOut(
            caregiver_id=str(row.caregiver_id),
            name=row.full_name,
            relationship=(
                row.relationship_type.value if hasattr(row.relationship_type, "value") else None
            ),
            is_primary=bool(row.is_primary),
        )
        for row in rows
    ]


def _care_plan(db: Session, patient_id: uuid.UUID, organization_id: uuid.UUID) -> CarePlan | None:
    return db.scalar(
        select(CarePlan)
        .where(
            CarePlan.patient_id == patient_id,
            CarePlan.organization_id == organization_id,
        )
        .order_by(CarePlan.created_at.desc())
        .limit(1)
    )


def build_detail(
    db: Session,
    actor: User,
    patient: Patient,
) -> PatientDetail:
    base = PatientSummary.model_validate(patient)

    care_plan = _care_plan(db, patient.id, actor.organization_id)

    from app.models import CareGoal

    care_goals: list[CareGoal] = (
        list(db.scalars(select(CareGoal).where(CareGoal.care_plan_id == care_plan.id)).all())
        if care_plan
        else []
    )

    return PatientDetail(
        **base.model_dump(),
        address=patient.address,
        emergency_contact_name=patient.emergency_contact_name,
        emergency_contact_phone=patient.emergency_contact_phone,
        care_team=_care_team_members(db, patient.id, actor.organization_id),
        caregivers=_caregivers(db, patient.id),
        care_plan=CarePlanOut.model_validate(care_plan) if care_plan else None,
        care_goals=care_goals,
    )


def latest_care_plan(db: Session, actor: User, patient: Patient) -> CarePlan | None:
    return _care_plan(db, patient.id, actor.organization_id)


def update_care_plan(db: Session, actor: User, patient: Patient, payload) -> CarePlan:
    plan = latest_care_plan(db, actor, patient)
    if plan is None:
        raise AppError(
            "This patient has no care plan yet.", code="VALIDATION_ERROR", status_code=422
        )
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if field in _PLAN_FIELDS and value is not None:
            setattr(plan, field, value)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    audit.record(
        db,
        organization_id=plan.organization_id,
        actor_id=actor.id,
        action="care_plan.updated",
        entity_type="care_plan",
        entity_id=plan.id,
        metadata={"patient_id": str(patient.id), "fields": sorted(data.keys())},
    )
    return plan


def create_care_goal(db: Session, actor: User, patient: Patient, payload) -> CareGoal:
    plan: CarePlan | None = None
    if payload.care_plan_id:
        try:
            plan_uid = uuid.UUID(payload.care_plan_id)
        except (ValueError, TypeError):
            plan_uid = None
        if plan_uid:
            plan = db.scalar(
                select(CarePlan).where(
                    CarePlan.id == plan_uid,
                    CarePlan.patient_id == patient.id,
                    CarePlan.organization_id == actor.organization_id,
                )
            )
        if plan is None:
            raise NotFoundError("Care plan not found")
    else:
        plan = latest_care_plan(db, actor, patient)
    if plan is None:
        raise AppError(
            "Create a care plan before adding goals.", code="VALIDATION_ERROR", status_code=422
        )

    from app.models.enums import CareGoalPriority, CareGoalStatus

    goal_kwargs: dict = {
        "patient_id": patient.id,
        "care_plan_id": plan.id,
        "title": payload.title,
        "description": payload.description,
        "status": payload.status or CareGoalStatus.OPEN,
    }
    if payload.priority is not None:
        goal_kwargs["priority"] = payload.priority
    elif "priority" in payload.model_fields_set and payload.priority is None:
        goal_kwargs["priority"] = CareGoalPriority.NORMAL
    goal = CareGoal(**goal_kwargs)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    audit.record(
        db,
        organization_id=actor.organization_id,
        actor_id=actor.id,
        action="care_goal.created",
        entity_type="care_goal",
        entity_id=goal.id,
        metadata={"patient_id": str(patient.id), "title": goal.title},
    )
    return goal


def update_care_goal(db: Session, actor: User, patient: Patient, goal_id: str, payload) -> CareGoal:
    try:
        uid = uuid.UUID(goal_id)
    except (ValueError, TypeError) as exc:
        raise NotFoundError("Care goal not found") from exc
    goal = db.scalar(select(CareGoal).where(CareGoal.id == uid, CareGoal.patient_id == patient.id))
    if goal is None:
        raise NotFoundError("Care goal not found")
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if field in _GOAL_FIELDS and value is not None:
            setattr(goal, field, value)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    audit.record(
        db,
        organization_id=actor.organization_id,
        actor_id=actor.id,
        action="care_goal.updated",
        entity_type="care_goal",
        entity_id=goal.id,
        metadata={"patient_id": str(goal.patient_id), "fields": sorted(data.keys())},
    )
    return goal
