from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_patient_read
from app.core.database import get_db
from app.models import User
from app.schemas.dashboard import DashboardSummary
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db),
    actor: User = Depends(require_patient_read),
):
    return dashboard_service.build_summary(db, actor)
