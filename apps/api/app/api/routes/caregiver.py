"""Caregiver report, voice and observation-confirmation routes.

Every route is patient-scoped: ``get_patient`` enforces organization isolation
and object-level authorization (caregiver -> linked patients only).
"""

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import (
    require_caregiver_report_confirm,
    require_caregiver_report_create,
    require_patient_read,
)
from app.core.database import get_db
from app.core.errors import AppError
from app.models import User
from app.schemas.caregiver_report import (
    CaregiverReportCreate,
    CaregiverReportList,
    CaregiverReportOut,
    CaregiverReportUpdate,
    ExtractionOut,
    ObservationConfirm,
    ObservationConfirmOut,
    RecentChangesOut,
    VoiceTranscriptOut,
)
from app.services import caregiver_reports as reports_service
from app.services import observations as obs_service
from app.services import patients as patients_service

router = APIRouter(prefix="/patients", tags=["caregiver"])

MAX_AUDIO_BYTES = 20 * 1024 * 1024


class ReportIdPayload(BaseModel):
    report_id: str


@router.get("/{patient_id}/caregiver-reports", response_model=CaregiverReportList)
def list_reports(
    patient_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_patient_read),
):
    patient = patients_service.get_patient(db, actor, patient_id)
    reports = reports_service.list_reports(db, actor, patient)
    items = [reports_service._to_schema(db, r) for r in reports]
    return CaregiverReportList(items=items, total=len(items))


@router.post("/{patient_id}/caregiver-reports", response_model=CaregiverReportOut, status_code=201)
def create_report(
    payload: CaregiverReportCreate,
    patient_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_caregiver_report_create),
):
    patient = patients_service.get_patient(db, actor, patient_id)
    report = reports_service.create_report(db, actor, patient, payload)
    return reports_service._to_schema(db, report)


@router.patch("/{patient_id}/caregiver-reports/{report_id}", response_model=CaregiverReportOut)
def update_report(
    payload: CaregiverReportUpdate,
    patient_id: str,
    report_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_caregiver_report_create),
):
    patient = patients_service.get_patient(db, actor, patient_id)
    report = reports_service.get_report(db, actor, patient, report_id)
    report = reports_service.update_report(db, actor, report, payload)
    return reports_service._to_schema(db, report)


@router.post(
    "/{patient_id}/caregiver-reports/{report_id}/cancel", response_model=CaregiverReportOut
)
def cancel_report(
    patient_id: str,
    report_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_caregiver_report_create),
    reason: str | None = None,
):
    patient = patients_service.get_patient(db, actor, patient_id)
    report = reports_service.get_report(db, actor, patient, report_id)
    report = reports_service.cancel_report(db, actor, report, reason)
    return reports_service._to_schema(db, report)


@router.post("/{patient_id}/voice/transcribe", response_model=VoiceTranscriptOut)
def transcribe_voice(
    patient_id: str,
    report_id: str = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    actor: User = Depends(require_caregiver_report_create),
):
    patient = patients_service.get_patient(db, actor, patient_id)
    report = reports_service.get_report(db, actor, patient, report_id)
    audio_bytes = audio.file.read() if audio.file else b""
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise AppError("Audio file is too large (max 20 MB).", status_code=413)
    return reports_service.transcribe_voice(db, actor, report, audio_bytes)


@router.post("/{patient_id}/voice/extract", response_model=ExtractionOut)
def extract_voice(
    payload: ReportIdPayload,
    patient_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_caregiver_report_create),
):
    patient = patients_service.get_patient(db, actor, patient_id)
    report = reports_service.get_report(db, actor, patient, payload.report_id)
    return reports_service.extract_voice(db, actor, report)


@router.post("/{patient_id}/observations/confirm", response_model=ObservationConfirmOut)
def confirm_observations(
    payload: ObservationConfirm,
    patient_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_caregiver_report_confirm),
):
    patient = patients_service.get_patient(db, actor, patient_id)
    return reports_service.confirm_observations(db, actor, patient, payload)


@router.get("/{patient_id}/observations/recent", response_model=RecentChangesOut)
def recent_observation_changes(
    patient_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_patient_read),
):
    patient = patients_service.get_patient(db, actor, patient_id)
    changes = obs_service.recent_changes(db, actor, patient)
    return RecentChangesOut(items=changes)
