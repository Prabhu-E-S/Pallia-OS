import uuid

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import PermissionDeniedError, UnauthorizedError
from app.core.rate_limit import login_limiter
from app.core.security import decode_access_token, get_current_user, verify_password
from app.models import Organization, User, UserStatus
from app.schemas import (
    CurrentUserOut,
    DevLoginRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.services import audit
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = auth_service.REFRESH_COOKIE_NAME
REFRESH_COOKIE_PATH = auth_service.REFRESH_COOKIE_PATH


def _set_refresh_cookie(response: Response, token: str, max_age: int) -> None:
    settings = get_settings()
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=max_age,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        samesite="lax",
        secure=not settings.is_development,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


def _organization(db: Session, org_id) -> Organization | None:
    return db.get(Organization, org_id)


def _lookup_active_user(db: Session, email: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None or user.status != UserStatus.ACTIVE:
        return None
    return user


def _refresh_token_from_request(request: Request, payload: RefreshTokenRequest | None) -> str:
    if payload is not None and payload.refresh_token:
        return payload.refresh_token
    return request.cookies.get(REFRESH_COOKIE_NAME) or ""


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Authenticate with email + password and start a refresh session."""
    ip = request.client.host if request.client else None
    login_limiter.check(payload.email, ip)

    user = _lookup_active_user(db, payload.email)
    ok_password = (
        user is not None
        and bool(user.password_hash)
        and verify_password(payload.password, user.password_hash)
    )
    if not ok_password:
        login_limiter.record(payload.email, ip)
        auth_service.record_login_failure(db, payload.email)
        # Deliberately generic so failures do not reveal which field was wrong.
        raise UnauthorizedError("Invalid email or password")

    org = _organization(db, user.organization_id)
    result = auth_service.build_token_response(db, user, request, org)
    auth_service.record_login_success(db, user)
    _set_refresh_cookie(
        response,
        result.refresh_token,
        max_age=int(auth_service.REFRESH_SESSION_LIFETIME.total_seconds()),
    )
    return result


@router.post("/dev-login", response_model=TokenResponse)
def dev_login(
    payload: DevLoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Development-only login.

    Exchanges a known user email for a signed bearer token and refresh session.
    This exists so the product can be built and demoed; it is gated to non-
    production environments and will be replaced by OAuth2/OIDC.
    """
    settings = get_settings()
    if not settings.is_development:
        raise PermissionDeniedError("Development login is unavailable")

    email = payload.email.lower()
    allowed = settings.dev_login_allowed_emails
    if allowed and email not in allowed:
        raise PermissionDeniedError("Email is not allowed for development login")

    user = _lookup_active_user(db, email)
    if user is None:
        raise UnauthorizedError("No user found for this email")

    org = _organization(db, user.organization_id)
    result = auth_service.build_token_response(db, user, request, org)
    auth_service.record_login_success(db, user)
    _set_refresh_cookie(
        response,
        result.refresh_token,
        max_age=int(auth_service.REFRESH_SESSION_LIFETIME.total_seconds()),
    )
    return result


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    response: Response,
    payload: RefreshTokenRequest | None = None,
    db: Session = Depends(get_db),
):
    """Rotate the refresh token (cookie preferred, body allowed) and mint a new
    access token. The previous session is revoked server-side."""
    refresh_token = _refresh_token_from_request(request, payload)
    if not refresh_token:
        raise UnauthorizedError("No refresh session found")

    user, org, old_session = auth_service.resolve_refresh_session(db, refresh_token)
    result = auth_service.build_token_response(db, user, request, org)
    auth_service.record_token_refresh(db, user)
    auth_service.record_session_revoked(db, old_session)
    _set_refresh_cookie(
        response,
        result.refresh_token,
        max_age=int(auth_service.REFRESH_SESSION_LIFETIME.total_seconds()),
    )
    return result


@router.post("/logout")
def logout(
    response: Response,
    request: Request,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke the current session and clear the refresh cookie."""
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    payload = decode_access_token(token) if scheme.lower() == "bearer" and token else None
    sid = payload.get("sid") if payload else None
    if sid:
        try:
            auth_service.revoke_session(db, uuid.UUID(str(sid)))
        except (ValueError, TypeError):
            pass
    audit.record(
        db,
        organization_id=actor.organization_id,
        actor_id=actor.id,
        action="LOGOUT",
        entity_type="user",
        entity_id=actor.id,
    )
    _clear_refresh_cookie(response)
    return {"ok": True}


@router.get("/me", response_model=CurrentUserOut)
def me(actor: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return the signed-in user's profile and permissions."""
    org = db.get(Organization, actor.organization_id)
    return auth_service.build_user_out(actor, org)
