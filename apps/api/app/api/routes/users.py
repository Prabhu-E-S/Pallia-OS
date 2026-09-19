from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import permissions
from app.core.database import get_db
from app.core.security import require_permission
from app.models import User
from app.schemas.organization import UserList, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserList)
def list_users(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(permissions.PERMISSION_USERS_READ)),
):
    users = list(
        db.scalars(
            select(User)
            .where(User.organization_id == actor.organization_id)
            .order_by(User.full_name)
        )
    )
    return UserList(items=[UserOut.model_validate(u) for u in users], total=len(users))
