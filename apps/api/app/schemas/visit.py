from datetime import datetime

from pydantic import BaseModel

from app.models.enums import VisitStatus
from app.schemas.common import ORMModel


class VisitCreate(BaseModel):
    patient_id: str
    assigned_to: str | None = None
    scheduled_at: datetime
    notes: str | None = None


class VisitUpdate(BaseModel):
    scheduled_at: datetime | None = None
    assigned_to: str | None = None
    status: VisitStatus | None = None
    notes: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class VisitOut(ORMModel):
    id: str
    patient_id: str
    patient_name: str | None = None
    assigned_to: str | None
    assigned_to_name: str | None = None
    scheduled_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class VisitList(BaseModel):
    items: list[VisitOut]
    total: int
