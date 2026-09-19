from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import PermissionDeniedError, UnauthorizedError
from app.core.permissions import ROLE_PERMISSIONS
from app.core.security import create_access_token, get_current_user
from app.models import Organization, User
from app.schemas import CurrentUserOut, DevLoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_user_out(user: User, organization: Organization | None) -> CurrentUserOut:
    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    return CurrentUserOut(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=role,
        organization_id=str(user.organization_id),
        organization_name=organization.name if organization else "",
        permissions=list(ROLE_PERMISSIONS.get(user.role, set())),
    )


@router.post("/dev-login", response_model=TokenResponse)
def dev_login(payload: DevLoginRequest, db: Session = Depends(get_db)):
    """Development-only login.

    Exchanges a known user email for a signed bearer token. This exists so the
    product can be built and demoed; it will be replaced by OAuth2/OIDC.
    """
    settings = get_settings()
    if not settings.is_development:
        raise PermissionDeniedError("Development login is unavailable")

    email = payload.email.lower()
    allowed = settings.dev_login_allowed_emails
    if allowed and email not in allowed:
        raise PermissionDeniedError("Email is not allowed for development login")

    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        raise UnauthorizedError("No user found for this email")

    org = db.get(Organization, user.organization_id)
    token = create_access_token(str(user.id))
    out = _build_user_out(user, org)
    return TokenResponse(access_token=token, user=out.model_dump())


@router.get("/me", response_model=CurrentUserOut)
def me(actor: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return the signed-in user's profile and permissions."""
    org = db.get(Organization, actor.organization_id)
    return _build_user_out(actor, org)
