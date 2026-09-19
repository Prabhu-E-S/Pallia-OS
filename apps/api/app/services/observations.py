from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Observation, Patient, User
from app.models.enums import ObservationSource
from app.schemas.observation import ObservationCreate, ObservationOut
from app.services import audit
from app.services.patients import get_patient


def create_observation(db: Session, actor: User, payload: ObservationCreate) -> Observation:
    patient = get_patient(db, actor, payload.patient_id)
    observed_at = payload.observed_at or datetime.now(UTC)

    observation = Observation(
        organization_id=actor.organization_id,
        patient_id=patient.id,
        recorded_by=actor.id,
        type=payload.type,
        value=payload.value,
        unit=payload.unit,
        notes=payload.notes,
        observed_at=observed_at,
        source=payload.source or ObservationSource.MANUAL,
    )
    db.add(observation)
    db.commit()
    db.refresh(observation)
    audit.record(
        db,
        organization_id=observation.organization_id,
        actor_id=actor.id,
        action="observation.created",
        entity_type="observation",
        entity_id=observation.id,
        metadata={"patient_id": str(observation.patient_id), "type": str(observation.type)},
    )
    return observation


def list_for_patient(db: Session, actor: User, patient: Patient) -> list[Observation]:
    stmt = (
        select(Observation)
        .where(
            Observation.patient_id == patient.id,
            Observation.organization_id == actor.organization_id,
        )
        .order_by(Observation.observed_at.desc())
        .limit(100)
    )
    return list(db.scalars(stmt))


def to_schema(observation: Observation) -> ObservationOut:
    return ObservationOut.model_validate(observation)
