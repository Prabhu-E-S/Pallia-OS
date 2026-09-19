"""Caregiver report workflow.

Lifecycle:
  * QUICK_STATUS / STRUCTURED / TEXT submissions are created CONFIRMED
    immediately - the caregiver is the human source, no second step needed.
  * VOICE submissions start DRAFT, gain a transcript (voice/transcribe), then a
    machine extraction (voice/extract -> REVIEW_REQUIRED) and are only written
    to the patient record after human confirmation (observations/confirm).

Only confirmed reports appear on the patient timeline; every persisted
observation carries provenance (source, ai_generated, human_verified,
confidence, model_version, source_reference).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFoundError
from app.models import (
    CaregiverReport,
    CaregiverReportMode,
    CaregiverReportStatus,
    Observation,
    ObservationSource,
    ObservationType,
    Patient,
    User,
)
from app.schemas.caregiver_report import (
    AISummaryOut,
    CaregiverReportOut,
    ExtractionOut,
    ObservationConfirmOut,
    VoiceTranscriptOut,
)
from app.schemas.observation import ObservationOut
from app.services import audit
from app.services.ai.extraction import extract_from_transcript
from app.services.speech.service import SpeechServiceError, get_speech_service

_STRUCTURED_FIELDS = (
    ("pain_level", ObservationType.PAIN, "scale 0-10"),
    ("sleep_hours", ObservationType.SLEEP, None),
    ("food_intake", ObservationType.FOOD_INTAKE, None),
    ("mobility", ObservationType.MOBILITY, None),
    ("mood", ObservationType.MOOD, None),
    ("breathing", ObservationType.BREATHING, None),
    ("energy", ObservationType.ENERGY, None),
)

_MANUAL_MODES = frozenset(
    {CaregiverReportMode.QUICK_STATUS, CaregiverReportMode.STRUCTURED, CaregiverReportMode.TEXT}
)


def _none_if_blank(value):
    if value is None or value == "":
        return None
    return value


def _structured_observations(report: "CaregiverReport") -> list[Observation]:
    """Build Observation rows from the report's structured fields."""
    observations: list[Observation] = []
    for field, obs_type, unit in _STRUCTURED_FIELDS:
        value = _none_if_blank(getattr(report, field, None))
        if value is None:
            continue
        value_text = str(value)
        observations.append(
            Observation(
                organization_id=report.organization_id,
                patient_id=report.patient_id,
                recorded_by=report.recorded_by,
                type=obs_type,
                value=value_text,
                unit=unit,
                observed_at=report.reported_at,
                source=ObservationSource.CAREGIVER_TEXT,
                source_reference=report.id,
                ai_generated=False,
                human_verified=True,
            )
        )
    return observations


def _has_content(payload) -> bool:
    structured = [getattr(payload, field, None) for field, _, _ in _STRUCTURED_FIELDS]
    return any(
        _none_if_blank(value) is not None
        for value in [*structured, payload.general_concern, payload.notes, payload.transcript]
    )


def get_report(db: Session, actor: User, patient: Patient, report_id: str) -> CaregiverReport:
    try:
        uid = uuid.UUID(report_id)
    except ValueError as exc:
        raise NotFoundError("Caregiver report not found") from exc
    report = db.scalar(
        select(CaregiverReport).where(
            CaregiverReport.id == uid,
            CaregiverReport.patient_id == patient.id,
            CaregiverReport.organization_id == actor.organization_id,
        )
    )
    if report is None:
        raise NotFoundError("Caregiver report not found")
    return report


def list_reports(db: Session, actor: User, patient: Patient) -> list[CaregiverReport]:
    stmt = (
        select(CaregiverReport)
        .where(
            CaregiverReport.patient_id == patient.id,
            CaregiverReport.organization_id == actor.organization_id,
        )
        .order_by(CaregiverReport.reported_at.desc())
        .limit(100)
    )
    return list(db.scalars(stmt))


def create_report(db: Session, actor: User, patient: Patient, payload) -> CaregiverReport:
    if payload.mode in _MANUAL_MODES and not _has_content(payload):
        raise AppError(
            "A caregiver report needs at least one observation, a concern, or a note.",
            code="VALIDATION_ERROR",
            status_code=422,
        )

    reported_at = payload.reported_at or datetime.now(UTC)
    manual = payload.mode in _MANUAL_MODES

    report = CaregiverReport(
        organization_id=actor.organization_id,
        patient_id=patient.id,
        recorded_by=actor.id,
        reported_at=reported_at,
        mode=payload.mode,
        status=(CaregiverReportStatus.CONFIRMED if manual else CaregiverReportStatus.DRAFT),
        pain_level=payload.pain_level,
        sleep_hours=_none_if_blank(payload.sleep_hours),
        food_intake=_none_if_blank(payload.food_intake),
        mobility=_none_if_blank(payload.mobility),
        mood=_none_if_blank(payload.mood),
        breathing=_none_if_blank(payload.breathing),
        energy=_none_if_blank(payload.energy),
        general_concern=_none_if_blank(payload.general_concern),
        notes=_none_if_blank(payload.notes),
        transcript=_none_if_blank(payload.transcript),
        audio_duration_seconds=payload.audio_duration_seconds,
        ai_generated=False,
        human_verified=manual,
        confirmed_at=reported_at if manual else None,
        confirmed_by=actor.id if manual else None,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    if manual:
        for observation in _structured_observations(report):
            db.add(observation)
        db.commit()

    audit.record(
        db,
        organization_id=report.organization_id,
        actor_id=actor.id,
        action="caregiver_report.created",
        entity_type="caregiver_report",
        entity_id=report.id,
        metadata={
            "patient_id": str(report.patient_id),
            "mode": str(report.mode),
            "status": str(report.status),
        },
    )
    return report


def update_report(db: Session, actor: User, report: CaregiverReport, payload) -> CaregiverReport:
    if report.status == CaregiverReportStatus.CONFIRMED:
        raise AppError("A confirmed caregiver report cannot be edited.", status_code=409)
    if report.status == CaregiverReportStatus.CANCELLED:
        raise AppError("A cancelled caregiver report cannot be edited.", status_code=409)

    for field, _, _ in _STRUCTURED_FIELDS:
        if field in payload.model_fields_set:
            setattr(report, field, getattr(payload, field))
    for field in ("general_concern", "notes", "transcript"):
        if field in payload.model_fields_set:
            setattr(report, field, _none_if_blank(getattr(payload, field)))

    db.add(report)
    db.commit()
    db.refresh(report)
    audit.record(
        db,
        organization_id=report.organization_id,
        actor_id=actor.id,
        action="caregiver_report.updated",
        entity_type="caregiver_report",
        entity_id=report.id,
        metadata={"patient_id": str(report.patient_id), "status": str(report.status)},
    )
    return report


def transcribe_voice(
    db: Session, actor: User, report: CaregiverReport, audio: bytes
) -> VoiceTranscriptOut:
    if report.mode != CaregiverReportMode.VOICE:
        raise AppError("Transcription is only available for voice reports.", status_code=422)

    audit.record(
        db,
        organization_id=report.organization_id,
        actor_id=actor.id,
        action="voice.transcription_requested",
        entity_type="caregiver_report",
        entity_id=report.id,
        metadata={"patient_id": str(report.patient_id)},
    )

    service = get_speech_service()
    try:
        transcript = service.transcribe(audio)
    except SpeechServiceError:
        audit.record(
            db,
            organization_id=report.organization_id,
            actor_id=actor.id,
            action="voice.transcription_failed",
            entity_type="caregiver_report",
            entity_id=report.id,
            metadata={"patient_id": str(report.patient_id), "service": service.name},
        )
        raise

    report.transcript = _none_if_blank(transcript.text)
    db.add(report)
    db.commit()
    db.refresh(report)

    audit.record(
        db,
        organization_id=report.organization_id,
        actor_id=actor.id,
        action="voice.transcription_completed",
        entity_type="caregiver_report",
        entity_id=report.id,
        metadata={
            "patient_id": str(report.patient_id),
            "service": service.name,
            "language": transcript.language,
        },
    )
    return VoiceTranscriptOut(
        report_id=str(report.id),
        patient_id=str(report.patient_id),
        transcript=report.transcript or "",
        language=transcript.language,
        service=service.name,
    )


def extract_voice(db: Session, actor: User, report: CaregiverReport) -> ExtractionOut:
    if report.mode != CaregiverReportMode.VOICE:
        raise AppError("Extraction is only available for voice reports.", status_code=422)
    if not report.transcript:
        raise AppError(
            "There is no transcript to extract from.", code="VALIDATION_ERROR", status_code=422
        )

    audit.record(
        db,
        organization_id=report.organization_id,
        actor_id=actor.id,
        action="ai.extraction_requested",
        entity_type="caregiver_report",
        entity_id=report.id,
        metadata={"patient_id": str(report.patient_id)},
    )

    try:
        result = extract_from_transcript(report.transcript)
    except AppError as exc:
        audit.record(
            db,
            organization_id=report.organization_id,
            actor_id=actor.id,
            action="ai.extraction_failed",
            entity_type="caregiver_report",
            entity_id=report.id,
            metadata={"patient_id": str(report.patient_id), "code": exc.code},
        )
        raise

    report.extraction = {
        "observations": [
            {
                "type": obs.type.value,
                "value": obs.value,
                "unit": obs.unit,
                "confidence": obs.confidence,
                "note": obs.note,
            }
            for obs in result.output.observations
        ],
        "not_mentioned": result.output.not_mentioned,
        "summary": result.output.summary,
    }
    report.ai_generated = True
    report.provider = result.provider
    report.model = result.model
    report.model_version = result.model_version
    report.confidence = result.confidence
    report.status = CaregiverReportStatus.REVIEW_REQUIRED
    db.add(report)
    db.commit()
    db.refresh(report)

    audit.record(
        db,
        organization_id=report.organization_id,
        actor_id=actor.id,
        action="ai.extraction_completed",
        entity_type="caregiver_report",
        entity_id=report.id,
        metadata={
            "patient_id": str(report.patient_id),
            "provider": result.provider,
            "model_version": result.model_version,
            "observation_count": len(result.output.observations),
        },
    )
    return ExtractionOut(
        report=_to_schema(db, report),
        observations=result.output.observations,
        not_mentioned=result.output.not_mentioned,
        ai=AISummaryOut(
            provider=result.provider,
            model=result.model,
            model_version=result.model_version,
            confidence=result.confidence,
        ),
    )


def confirm_observations(
    db: Session, actor: User, patient: Patient, payload
) -> ObservationConfirmOut:
    report = get_report(db, actor, patient, payload.report_id)
    if report.status == CaregiverReportStatus.CONFIRMED:
        raise AppError("This report is already confirmed.", status_code=409)
    if report.status == CaregiverReportStatus.CANCELLED:
        raise AppError("A cancelled report cannot be confirmed.", status_code=409)

    reported_at = payload.reported_at or report.reported_at or datetime.now(UTC)
    source = (
        ObservationSource.CAREGIVER_VOICE
        if report.mode == CaregiverReportMode.VOICE
        else ObservationSource.CAREGIVER_TEXT
    )

    created: list[Observation] = []
    candidate_keys = _candidate_keys(report)
    for item in payload.observations:
        observation = Observation(
            organization_id=actor.organization_id,
            patient_id=patient.id,
            recorded_by=actor.id,
            type=item.type,
            value=_none_if_blank(item.value),
            unit=_none_if_blank(item.unit),
            notes=_none_if_blank(item.notes),
            observed_at=reported_at,
            source=source,
            source_reference=report.id,
            ai_generated=report.ai_generated,
            human_verified=True,
            confidence=item.confidence if item.confidence is not None else report.confidence,
            model_version=report.model_version,
        )
        db.add(observation)
        db.flush()
        created.append(observation)

        edited = (str(item.type.value), item.value, item.unit) not in candidate_keys
        audit.record(
            db,
            organization_id=report.organization_id,
            actor_id=actor.id,
            action="observation.edited" if edited else "observation.confirmed",
            entity_type="observation",
            entity_id=observation.id,
            metadata={
                "patient_id": str(patient.id),
                "report_id": str(report.id),
                "type": str(item.type.value),
                "edited": edited,
            },
        )

    report.status = CaregiverReportStatus.CONFIRMED
    report.human_verified = True
    report.confirmed_at = reported_at
    report.confirmed_by = actor.id
    db.add(report)
    db.commit()
    db.refresh(report)

    if created:
        audit.record(
            db,
            organization_id=report.organization_id,
            actor_id=actor.id,
            action="caregiver_report.confirmed",
            entity_type="caregiver_report",
            entity_id=report.id,
            metadata={"patient_id": str(patient.id), "observation_count": len(created)},
        )

    return ObservationConfirmOut(
        report=_to_schema(db, report),
        observations=[ObservationOut.model_validate(o) for o in created],
    )


def _candidate_keys(report: CaregiverReport) -> set[tuple]:
    keys: set[tuple] = set()
    for obs in (report.extraction or {}).get("observations", []):
        keys.add((str(obs.get("type")), obs.get("value"), obs.get("unit")))
    return keys


def cancel_report(
    db: Session, actor: User, report: CaregiverReport, reason: str | None
) -> CaregiverReport:
    if report.status == CaregiverReportStatus.CONFIRMED:
        raise AppError("A confirmed report cannot be cancelled.", status_code=409)
    report.status = CaregiverReportStatus.CANCELLED
    report.cancelled_at = datetime.now(UTC)
    report.cancelled_by = actor.id
    report.cancellation_reason = _none_if_blank(reason)
    db.add(report)
    db.commit()
    db.refresh(report)
    audit.record(
        db,
        organization_id=report.organization_id,
        actor_id=actor.id,
        action="caregiver_report.cancelled",
        entity_type="caregiver_report",
        entity_id=report.id,
        metadata={"patient_id": str(report.patient_id), "reason": report.cancellation_reason},
    )
    return report


def _to_schema(db: Session, report: CaregiverReport) -> CaregiverReportOut:
    out = CaregiverReportOut.model_validate(report)
    if report.recorded_by:
        user = db.scalar(select(User.full_name).where(User.id == report.recorded_by))
        out.recorded_by_name = user if isinstance(user, str) else None
    return out
