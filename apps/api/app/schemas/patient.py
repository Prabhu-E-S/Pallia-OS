from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import Gender, PatientStatus
from app.schemas.common import ORMModel


class PatientCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    date_of_birth: date | None = None
    gender: Gender | None = None
    phone: str | None = Field(default=None, max_length=32)
    address: str | None = None
    preferred_language: str | None = Field(default=None, max_length=32)
    emergency_contact_name: str | None = Field(default=None, max_length=255)
    emergency_contact_phone: str | None = Field(default=None, max_length=32)


class PatientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    date_of_birth: date | None = None
    gender: Gender | None = None
    phone: str | None = Field(default=None, max_length=32)
    address: str | None = None
    preferred_language: str | None = Field(default=None, max_length=32)
    emergency_contact_name: str | None = Field(default=None, max_length=255)
    emergency_contact_phone: str | None = Field(default=None, max_length=32)
    status: PatientStatus | None = None


class PatientSummary(ORMModel):
    id: str
    full_name: str
    date_of_birth: date | None
    gender: str | None
    phone: str | None
    preferred_language: str | None
    status: str
    organization_id: str
    created_at: datetime
    updated_at: datetime


class PatientList(BaseModel):
    items: list[PatientSummary]
    total: int


class CareTeamMemberOut(ORMModel):
    user_id: str
    full_name: str
    email: str
    role: str


class PatientCaregiverOut(ORMModel):
    caregiver_id: str
    name: str
    relationship: str | None
    is_primary: bool


class CarePlanOut(ORMModel):
    id: str
    patient_id: str
    status: str
    start_date: date | None
    review_date: date | None
    summary: str | None
    created_at: datetime
    updated_at: datetime


class CareGoalOut(ORMModel):
    id: str
    patient_id: str
    care_plan_id: str | None
    title: str
    description: str | None
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime


class PatientDetail(PatientSummary):
    address: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    care_team: list[CareTeamMemberOut] = Field(default_factory=list)
    caregivers: list[PatientCaregiverOut] = Field(default_factory=list)
    care_plan: CarePlanOut | None = None
    care_goals: list[CareGoalOut] = Field(default_factory=list)
