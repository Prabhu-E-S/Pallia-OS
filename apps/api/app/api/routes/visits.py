from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_visit_create, require_visit_update
from app.core.database import get_db
from app.core.permissions import PERMISSION_VISIT_READ
from app.core.security import require_permission
from app.models import User
from app.schemas.visit import VisitCreate, VisitList, VisitOut, VisitUpdate
from app.services import visits as visits_service

router = APIRouter(prefix="/visits", tags=["visits"])


@router.get("", response_model=VisitList)
def list_visits(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERMISSION_VISIT_READ)),
):
    items = visits_service.list_organization(db, actor)
    return VisitList(items=items, total=len(items))


@router.post("", response_model=VisitOut, status_code=201)
def create_visit(
    payload: VisitCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_visit_create),
):
    visit = visits_service.create_visit(db, actor, payload)
    return visits_service._visit_out(db, visit)


@router.patch("/{visit_id}", response_model=VisitOut)
def update_visit(
    visit_id: str,
    payload: VisitUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_visit_update),
):
    visit = visits_service.get_visit_in_org(db, actor, visit_id)
    visit = visits_service.update_visit(db, actor, visit, payload)
    return visits_service._visit_out(db, visit)
