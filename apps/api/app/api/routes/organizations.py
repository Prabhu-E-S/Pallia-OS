from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import permissions
from app.core.database import get_db
from app.core.security import require_permission
from app.models import Organization, User
from app.schemas.organization import OrganizationList, OrganizationOut

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=OrganizationList)
def list_organizations(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(permissions.PERMISSION_ORGANIZATIONS_READ)),
):
    orgs = list(db.scalars(select(Organization).order_by(Organization.name)))
    return OrganizationList(
        items=[OrganizationOut.model_validate(o) for o in orgs], total=len(orgs)
    )
