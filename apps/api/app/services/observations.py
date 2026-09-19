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


def _as_number(value: str | None):
    if value is None:
        return None
    try:
        return float(value.strip())
    except (ValueError, TypeError):
        return None


def recent_changes(db: Session, actor: User, patient: Patient) -> list[dict]:
    """Latest two observations per type with a neutral, descriptive comparison.

    Numeric observations (pain scale, sleep hours) are compared numerically;
    everything else reports whether the value changed. Missing data is never
    interpreted - it simply refers to what was recorded, in order.
    """
    stmt = (
        select(Observation)
        .where(
            Observation.patient_id == patient.id,
            Observation.organization_id == actor.organization_id,
        )
        .order_by(Observation.observed_at.desc())
        .limit(200)
    )
    grouped: dict[str, list[Observation]] = {}
    for observation in db.scalars(stmt):
        key = (
            observation.type.value if hasattr(observation.type, "value") else str(observation.type)
        )
        if len(grouped.setdefault(key, [])) < 2:
            grouped[key].append(observation)

    items: list[dict] = []
    for obs_type in sorted(grouped):
        pair = grouped[obs_type]
        current = pair[0]
        previous = pair[1] if len(pair) > 1 else None
        items.append(
            {
                "type": obs_type,
                "current_value": current.value,
                "current_unit": current.unit,
                "current_observed_at": current.observed_at,
                "previous_value": previous.value if previous else None,
                "previous_unit": previous.unit if previous else None,
                "previous_observed_at": previous.observed_at if previous else None,
                "comparison": _comparison(current, previous),
            }
        )
    return items


def _comparison(current: Observation, previous: Observation | None) -> str:
    if previous is None:
        return "first"
    now = _as_number(current.value)
    before = _as_number(previous.value)
    if now is not None and before is not None:
        if now > before:
            return "increased"
        if now < before:
            return "decreased"
        return "unchanged"
    if (current.value or "").strip() == (previous.value or "").strip():
        return "unchanged"
    return "changed"
