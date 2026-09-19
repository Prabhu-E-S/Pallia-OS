"""Authentication and session lifecycle service.

Sessions are server-side ``AuthSession`` rows whose only stored secret is a
SHA-256 hash of the opaque refresh token. Refreshing rotates the session:
the old row is revoked and a fresh one is created.
"""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import PermissionDeniedError, UnauthorizedError
from app.core.permissions import ROLE_PERMISSIONS
from app.core.security import (
    ACCESS_TOKEN_TTL_SECONDS,
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.models import AuthSession, Organization, User, UserStatus
from app.schemas.auth import CurrentUserOut, TokenResponse
from app.services import audit

REFRESH_SESSION_LIFETIME = timedelta(days=7)
REFRESH_COOKIE_NAME = "pallia_refresh"
REFRESH_COOKIE_PATH = "/"

ACTIONS = {
    "login_success": "LOGIN_SUCCESS",
    "login_failure": "LOGIN_FAILURE",
    "logout": "LOGOUT",
    "token_refresh": "TOKEN_REFRESH",
    "session_revoked": "SESSION_REVOKED",
    "user_created": "USER_CREATED",
    "user_updated": "USER_UPDATED",
    "permission_denied": "PERMISSION_DENIED",
}


def _client_info(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip, (user_agent[:255] if user_agent else None)


def build_user_out(user: User, organization: Organization | None) -> CurrentUserOut:
    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    status = user.status.value if hasattr(user.status, "value") else str(user.status)
    return CurrentUserOut(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=role,
        status=status,
        organization_id=str(user.organization_id),
        organization_name=organization.name if organization else "",
        permissions=list(ROLE_PERMISSIONS.get(user.role, set())),
    )


def create_session(db: Session, user: User, request: Request) -> tuple[str, AuthSession]:
    """Create a new refresh session and return (raw token, session row)."""
    refresh_token = generate_refresh_token()
    ip, user_agent = _client_info(request)
    session = AuthSession(
        user_id=user.id,
        organization_id=user.organization_id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=datetime.now(UTC) + REFRESH_SESSION_LIFETIME,
        ip_address=ip,
        user_agent=user_agent,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return refresh_token, session


def build_token_response(
    db: Session, user: User, request: Request, organization: Organization | None
) -> TokenResponse:
    """Create a session and the matching access token + response envelope."""
    refresh_token, session = create_session(db, user, request)
    access_token = create_access_token(str(user.id), sid=str(session.id))
    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_TTL_SECONDS,
        refresh_token=refresh_token,
        user=build_user_out(user, organization).model_dump(),
    )


def resolve_refresh_session(
    db: Session, refresh_token: str
) -> tuple[User, Organization | None, AuthSession]:
    """Validate a refresh token and return its user. Raises 401 on any issue.

    The matched session is revoked (single-use rotation); the caller creates a
    new session for the returned user and is given the revoked session so it can
    be audited.
    """
    digest = hash_refresh_token(refresh_token)
    session = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == digest, AuthSession.revoked_at.is_(None)
        )
    )
    if session is None or not session.is_active:
        raise UnauthorizedError("Invalid or expired refresh session")

    session.revoked_at = datetime.now(UTC)
    db.commit()

    user = db.get(User, session.user_id)
    if user is None:
        raise UnauthorizedError("User no longer exists")
    if user.status != UserStatus.ACTIVE:
        raise PermissionDeniedError("User account is not active")
    if user.organization_id != session.organization_id:
        raise UnauthorizedError("Session is no longer valid")

    organization = db.get(Organization, user.organization_id)
    return user, organization, session


def revoke_session(db: Session, session_id: uuid.UUID) -> None:
    """Revoke a session by its id (used on explicit logout)."""
    session = db.scalar(select(AuthSession).where(AuthSession.id == session_id))
    if session is not None and session.revoked_at is None:
        session.revoked_at = datetime.now(UTC)
        db.commit()


def record_login_success(db: Session, user: User) -> None:
    user.last_login_at = datetime.now(UTC)
    db.commit()
    audit.record(
        db,
        organization_id=user.organization_id,
        actor_id=user.id,
        action=ACTIONS["login_success"],
        entity_type="user",
        entity_id=user.id,
    )


def record_login_failure(db: Session, email: str) -> None:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        return
    audit.record(
        db,
        organization_id=user.organization_id,
        action=ACTIONS["login_failure"],
        entity_type="user",
        entity_id=user.id,
        metadata={"email": email},
    )


def record_logout(db: Session, user: User) -> None:
    audit.record(
        db,
        organization_id=user.organization_id,
        actor_id=user.id,
        action=ACTIONS["logout"],
        entity_type="user",
        entity_id=user.id,
    )


def record_token_refresh(db: Session, user: User) -> None:
    audit.record(
        db,
        organization_id=user.organization_id,
        actor_id=user.id,
        action=ACTIONS["token_refresh"],
        entity_type="auth_session",
    )


def record_session_revoked(db: Session, session: AuthSession) -> None:
    audit.record(
        db,
        organization_id=session.organization_id,
        action=ACTIONS["session_revoked"],
        entity_type="auth_session",
        entity_id=session.id,
    )
