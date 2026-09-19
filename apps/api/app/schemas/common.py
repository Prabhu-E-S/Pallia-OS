"""Shared response schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class ApiError(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorEnvelope(BaseModel):
    error: ApiError


class HealthOut(BaseModel):
    status: str
    database: str
    version: str


class AuditActionOut(BaseModel):
    id: str
    action: str
    entity_type: str
    entity_id: str | None
    actor_id: str | None
    created_at: datetime


class ORMModel(BaseModel):
    """Output model with SQLAlchemy attribute reading and UUID serialization."""

    model_config = ConfigDict(from_attributes=True)

    @field_validator("*", mode="before")
    @classmethod
    def _coerce_uuid_before(cls, value: Any) -> Any:
        if isinstance(value, uuid.UUID):
            return str(value)
        return value


class UserRef(ORMModel):
    id: str
    full_name: str
    email: str
    role: str


class PatientRef(ORMModel):
    id: str
    full_name: str
    status: str
