import uuid

from sqlalchemy.orm import Session

from app.core.errors import PermissionDeniedError, UnauthorizedError
from app.models import User, UserStatus


def require_user_in_org(db: Session, organization_id: uuid.UUID, user_id: str) -> User:
    """Resolve a user and guarantee they belong to the given organization."""
    user = db.get(User, user_id)
    if user is None:
        raise UnauthorizedError("User not found")
    if user.organization_id != organization_id:
        raise PermissionDeniedError("User does not belong to this organization")
    return user


def user_active(user: User) -> bool:
    return user.status == UserStatus.ACTIVE
