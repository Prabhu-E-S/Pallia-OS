from datetime import datetime

from pydantic import BaseModel

from app.schemas.task import CareTaskOut
from app.schemas.visit import VisitOut


class OverviewCounts(BaseModel):
    patients: int
    active_care_plans: int
    today_visits: int
    open_tasks: int


class ActivityItem(BaseModel):
    id: str
    kind: str
    patient_id: str | None
    patient_name: str | None
    title: str
    at: datetime


class DashboardSummary(BaseModel):
    counts: OverviewCounts
    today_visits: list[VisitOut] = []
    open_tasks: list[CareTaskOut] = []
    recent_activity: list[ActivityItem] = []
