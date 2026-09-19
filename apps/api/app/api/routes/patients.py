from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import (
    require_care_goal_create,
    require_care_goal_update,
    require_care_plan_update,
    require_patient_create,
    require_patient_read,
    require_patient_update,
)
from app.core.database import get_db
from app.models import User
from app.schemas.observation import ObservationList
from app.schemas.patient import (
    CareGoalCreate,
    CareGoalOut,
    CareGoalUpdate,
    CarePlanOut,
    CarePlanUpdate,
    PatientCreate,
    PatientDetail,
    PatientList,
    PatientSummary,
    PatientUpdate,
)
from app.schemas.task import CareTaskList
from app.schemas.visit import VisitList
from app.services import patients as patients_service
from app.services import timeline as timeline_service

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=PatientList)
def list_patients(
    db: Session = Depends(get_db),
    actor: User = Depends(require_patient_read),
):
    patients = patients_service.list_patients(db, actor)
    items = [patients_service.build_summary(p) for p in patients]
    return PatientList(items=items, total=len(items))


@router.post("", response_model=PatientSummary, status_code=201)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_patient_create),
):
    patient = patients_service.create_patient(db, actor, payload)
    return patients_service.build_summary(patient)


@router.get("/{patient_id}", response_model=PatientDetail)
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_patient_read),
):
    patient = patients_service.get_patient(db, actor, patient_id)
    return patients_service.build_detail(db, actor, patient)


@router.patch("/{patient_id}", response_model=PatientSummary)
def update_patient(
    patient_id: str,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_patient_update),
):
    patient = patients_service.get_patient(db, actor, patient_id)
    patient = patients_service.update_patient(db, actor, patient, payload)
    return patients_service.build_summary(patient)


@router.get("/{patient_id}/care-team")
def get_care_team(
    patient_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_patient_read),
):
    patient = patients_service.get_patient(db, actor, patient_id)
    detail = patients_service.build_detail(db, actor, patient)
    return {"items": detail.care_team, "total": len(detail.care_team)}


@router.get("/{patient_id}/care-plan")
def get_care_plan(
    patient_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_patient_read),
):
    patient = patients_service.get_patient(db, actor, patient_id)
    detail = patients_service.build_detail(db, actor, patient)
    return {
        "care_plan": detail.care_plan,
        "care_goals": detail.care_goals,
    }


@router.put("/{patient_id}/care-plan", response_model=CarePlanOut)
def update_care_plan(
    payload: CarePlanUpdate,
    patient_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_care_plan_update),
):
    patient = patients_service.get_patient(db, actor, patient_id)
    plan = patients_service.update_care_plan(db, actor, patient, payload)
    return CarePlanOut.model_validate(plan)


@router.post("/{patient_id}/care-plan/goals", response_model=CareGoalOut, status_code=201)
def create_care_goal(
    payload: CareGoalCreate,
    patient_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_care_goal_create),
):
    patient = patients_service.get_patient(db, actor, patient_id)
    goal = patients_service.create_care_goal(db, actor, patient, payload)
    return CareGoalOut.model_validate(goal)


@router.patch("/{patient_id}/care-plan/goals/{goal_id}", response_model=CareGoalOut)
def update_care_goal(
    payload: CareGoalUpdate,
    patient_id: str,
    goal_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_care_goal_update),
):
    patient = patients_service.get_patient(db, actor, patient_id)
    goal = patients_service.update_care_goal(db, actor, patient, goal_id, payload)
    return CareGoalOut.model_validate(goal)


@router.get("/{patient_id}/observations", response_model=ObservationList)
def list_patient_observations(
    patient_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_patient_read),
):
    from app.services import observations as obs_service

    patient = patients_service.get_patient(db, actor, patient_id)
    observations = obs_service.list_for_patient(db, actor, patient)
    items = [obs_service.to_schema(o) for o in observations]
    return ObservationList(items=items, total=len(items))


@router.get("/{patient_id}/visits", response_model=VisitList)
def list_patient_visits(
    patient_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_patient_read),
):
    from app.services import visits as visits_service

    patient = patients_service.get_patient(db, actor, patient_id)
    items = visits_service.list_for_patient(db, actor, patient)
    return VisitList(items=items, total=len(items))


@router.get("/{patient_id}/tasks", response_model=CareTaskList)
def list_patient_tasks(
    patient_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_patient_read),
):
    from app.services import tasks as tasks_service

    patient = patients_service.get_patient(db, actor, patient_id)
    items = tasks_service.list_for_patient(db, actor, patient)
    return CareTaskList(items=items, total=len(items))


@router.get("/{patient_id}/timeline")
def get_patient_timeline(
    patient_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_patient_read),
    kind: str = Query(default="all"),
):
    patient = patients_service.get_patient(db, actor, patient_id)
    return {"items": timeline_service.patient_timeline(db, actor, patient.id, kind=kind)}
