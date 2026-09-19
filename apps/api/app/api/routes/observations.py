from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_observation_create
from app.core.database import get_db
from app.core.permissions import PERMISSION_OBSERVATION_READ
from app.core.security import require_permission
from app.models import Observation, User
from app.schemas.observation import ObservationCreate, ObservationList, ObservationOut
from app.services import observations as obs_service
from app.services.authorization import scoped_patient_ids, where_patient_scope

router = APIRouter(prefix="/observations", tags=["observations"])


@router.post("", response_model=ObservationOut, status_code=201)
def create_observation(
    payload: ObservationCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_observation_create),
):
    observation = obs_service.create_observation(db, actor, payload)
    return obs_service.to_schema(observation)


@router.get("", response_model=ObservationList)
def list_observations(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERMISSION_OBSERVATION_READ)),
):
    stmt = (
        select(Observation)
        .where(Observation.organization_id == actor.organization_id)
        .order_by(Observation.observed_at.desc())
        .limit(200)
    )
    stmt = where_patient_scope(stmt, Observation.patient_id, scoped_patient_ids(db, actor))
    observations = list(db.scalars(stmt))
    items = [obs_service.to_schema(o) for o in observations]
    return ObservationList(items=items, total=len(items))
