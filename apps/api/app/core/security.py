"""Security foundation.

Authentication model (Phase 2):

  * Passwords are hashed with Argon2id (``argon2-cffi``). Legacy PBKDF2-HMAC-
    SHA256 hashes created in Phase 1 are still verified transparently.
  * Access tokens are short-lived, signed bearer tokens carrying an optional
    ``sid`` (session id reference). When ``sid`` is present the referenced
    ``AuthSession`` must still be active - this enables immediate revocation.
  * Refresh tokens are opaque random strings stored only as SHA-256 hashes in
    ``auth_sessions``. They are rotated on every refresh and can be revoked.

The placement of these functions is deliberate so auth behaviour lives in this
module and in ``app/api/routes/auth.py`` and nowhere else.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import permissions
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import PermissionDeniedError, UnauthorizedError
from app.models import AuthSession, User, UserStatus

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import InvalidHashError, VerificationError

    _argon2 = PasswordHasher()
except ImportError:  # pragma: no cover
    _argon2 = None

_ALGORITHM = "sha256"
_ACCESS_TOKEN_TTL_SECONDS = 30 * 60  # 30 minutes; short-lived by design.
# Keep the old constant name/behaviour for anything relying on a 12h token.
_TOKEN_TTL_SECONDS = _ACCESS_TOKEN_TTL_SECONDS
ACCESS_TOKEN_TTL_SECONDS = _ACCESS_TOKEN_TTL_SECONDS


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Hash a password with Argon2id and a per-user salt."""
    if _argon2 is not None:
        return _argon2.hash(password)
    # Fallback keeps the module usable if argon2-cffi is unavailable.
    return _hash_password_pbkdf2(password)


def _hash_password_pbkdf2(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return (
        f"pbkdf2_sha256$200000${base64.b64encode(salt).decode()}$"
        f"{base64.b64encode(digest).decode()}"
    )


def _verify_pbkdf2(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(expected, actual)
    except (ValueError, TypeError):
        return False


def verify_password(password: str, encoded: str) -> bool:
    """Verify a password against an Argon2id or legacy PBKDF2 hash."""
    if _argon2 is not None and encoded.startswith("$argon2"):
        try:
            return _argon2.verify(encoded, password)
        except (VerificationError, InvalidHashError):
            return False
    return _verify_pbkdf2(password, encoded)


# ---------------------------------------------------------------------------
# Refresh token helpers
# ---------------------------------------------------------------------------


def generate_refresh_token() -> str:
    """Create an opaque, high-entropy refresh token."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token so only the digest is persisted."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Access tokens
# ---------------------------------------------------------------------------


def _sign(secret: bytes, body: str) -> str:
    return hmac.new(secret, body.encode("utf-8"), hashlib.sha256).hexdigest()


def create_access_token(
    subject: str,
    ttl_seconds: int = _ACCESS_TOKEN_TTL_SECONDS,
    sid: str | None = None,
) -> str:
    """Create a signed bearer token for the given subject (user id).

    ``sid`` optionally binds the token to an ``AuthSession`` id. Tokens without
    a ``sid`` are accepted for backward compatibility (Phase 1) but do not
    participate in session revocation.
    """
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": int(time.time()) + ttl_seconds,
        "iat": int(time.time()),
    }
    if sid:
        payload["sid"] = sid
    body = (
        base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        .rstrip(b"=")
        .decode("ascii")
    )
    secret = get_settings().secret_key.encode("utf-8")
    return f"{body}.{_sign(secret, body)}"


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Validate a token and return its payload (``sub``, ``sid``, ``exp``).

    Returns ``None`` for invalid, tampered or expired tokens.
    """
    try:
        body, signature = token.split(".")
        secret = get_settings().secret_key.encode("utf-8")
        if not hmac.compare_digest(_sign(secret, body), signature):
            return None
        payload = json.loads(base64.urlsafe_b64decode(body + "==".ljust(len(body) % 4, "=")))
        if payload.get("exp", 0) < int(time.time()):
            return None
        if not payload.get("sub"):
            return None
        return payload
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


def _resolve_active_session(db: Session, sid: str, user: User) -> AuthSession | None:
    """Look up a session by its referenced id and confirm it belongs to the user."""
    try:
        session_id = uuid.UUID(sid)
    except (ValueError, TypeError):
        return None
    session = db.scalar(
        select(AuthSession).where(
            AuthSession.id == session_id,
            AuthSession.user_id == user.id,
            AuthSession.organization_id == user.organization_id,
        )
    )
    if session is None or not session.is_active:
        return None
    now = datetime.now(UTC)
    last_used = session.last_used_at
    if last_used is not None and last_used.tzinfo is None:
        last_used = last_used.replace(tzinfo=UTC)
    if session.last_used_at is None or (now - last_used).total_seconds() > 300:
        session.last_used_at = now
        db.commit()
    return session


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User:
    """Resolve the authenticated user from a bearer token."""
    if not authorization:
        raise UnauthorizedError("Authorization header is required")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedError("Bearer token is required")

    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedError("Invalid or expired token")

    subject = payload.get("sub")
    try:
        user_id = uuid.UUID(str(subject))
    except ValueError as exc:
        raise UnauthorizedError("Invalid token subject") from exc

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise UnauthorizedError("User no longer exists")
    if user.status != UserStatus.ACTIVE:
        raise PermissionDeniedError("User account is not active")

    sid = payload.get("sid")
    if sid and _resolve_active_session(db, str(sid), user) is None:
        raise UnauthorizedError("Session is no longer valid")

    return user


def require_permission(*required: str, any_of: bool = False):
    """Factory for FastAPI dependencies that enforce role-based permissions.

    Usage::

        @router.get("/patients")
        def list_patients(actor: User = Depends(require_permission("patient.read"))): ...

    With ``any_of=True`` a user needs only one of the given permissions.
    The dependency returns the resolved user so handlers can use ``actor``.
    """

    def dependency(
        user: User = Depends(get_current_user),
    ) -> User:
        allowed = permissions.permissions_for_role(user.role)
        if any_of:
            ok = bool(set(required) & allowed)
        else:
            ok = set(required).issubset(allowed)
        if not ok:
            raise PermissionDeniedError(f"Missing required permission: {', '.join(required)}")
        return user

    return dependency


# ---------------------------------------------------------------------------
# Development-time helpers (not used in production workflows).
# ---------------------------------------------------------------------------


def generate_secret_key() -> str:
    return os.urandom(48).hex()
