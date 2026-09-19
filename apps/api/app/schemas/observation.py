from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ObservationSource, ObservationType
from app.schemas.common import ORMModel


class ObservationCreate(BaseModel):
    patient_id: str
    type: ObservationType
    value: str | None = Field(default=None, max_length=255)
    unit: str | None = Field(default=None, max_length=32)
    notes: str | None = None
    observed_at: datetime | None = None
    source: ObservationSource | None = None


class ObservationOut(ORMModel):
    id: str
    patient_id: str
    recorded_by: str | None
    type: str
    value: str | None
    unit: str | None
    notes: str | None
    observed_at: datetime
    source: str
    source_reference: str | None
    ai_generated: bool
    human_verified: bool
    confidence: float | None
    model_version: str | None
    created_at: datetime


class ObservationList(BaseModel):
    items: list[ObservationOut]
    total: int
