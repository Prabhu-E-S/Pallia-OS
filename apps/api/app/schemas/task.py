from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import CareTaskPriority, CareTaskStatus, CareTaskType
from app.schemas.common import ORMModel


class CareTaskCreate(BaseModel):
    patient_id: str
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    task_type: CareTaskType | None = None
    priority: CareTaskPriority | None = None
    assigned_to: str | None = None
    due_at: datetime | None = None


class CareTaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    task_type: CareTaskType | None = None
    priority: CareTaskPriority | None = None
    assigned_to: str | None = None
    due_at: datetime | None = None
    status: CareTaskStatus | None = None
    completed_at: datetime | None = None


class CareTaskOut(ORMModel):
    id: str
    patient_id: str
    patient_name: str | None = None
    assigned_to: str | None
    assigned_to_name: str | None = None
    created_by: str | None
    title: str
    description: str | None
    task_type: str
    priority: str
    status: str
    due_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CareTaskList(BaseModel):
    items: list[CareTaskOut]
    total: int
