from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.common import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health(db: Session = Depends(get_db)):
    database = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover - depends on runtime environment
        database = "unavailable"
    settings = get_settings()
    return HealthOut(
        status="ok" if database == "ok" else "degraded",
        database=database,
        version=settings.app_version,
    )
