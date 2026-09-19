"""Security foundation.

Phase 1 uses a lightweight development authentication mechanism so the product
can be built and tested. It is intentionally replaced later by proper OAuth2 /
OIDC authentication. The placement of these functions is deliberately stable so
that replacement happens in this module and nowhere else.

What exists here:
  * PBKDF2 password hashing helpers.
  * A signed, expiring bearer token scheme built on the standard library.
  * FastAPI dependencies that resolve the current user and enforce permissions.

What does NOT exist yet:
  * OAuth2 / OIDC flows.
  * Refresh tokens.
  * Session management.
  * Two-factor authentication.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from typing import Any

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import permissions
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import PermissionDeniedError, UnauthorizedError
from app.models import User, UserStatus

_ALGORITHM = "sha256"
_TOKEN_TTL_SECONDS = 12 * 60 * 60  # 12 hours for the development session.


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256 and a per-user salt."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return (
        f"pbkdf2_sha256$200000${base64.b64encode(salt).decode()}$"
        f"{base64.b64encode(digest).decode()}"
    )


def verify_password(password: str, encoded: str) -> bool:
    """Verify a password against a PBKDF2 hash produced by ``hash_password``."""
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


def _sign(secret: bytes, body: str) -> str:
    return hmac.new(secret, body.encode("utf-8"), hashlib.sha256).hexdigest()


def create_access_token(subject: str, ttl_seconds: int = _TOKEN_TTL_SECONDS) -> str:
    """Create a signed bearer token for the given subject (user id)."""
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": int(time.time()) + ttl_seconds,
        "iat": int(time.time()),
    }
    body = (
        base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        .rstrip(b"=")
        .decode("ascii")
    )
    secret = get_settings().secret_key.encode("utf-8")
    return f"{body}.{_sign(secret, body)}"


def decode_access_token(token: str) -> str | None:
    """Validate a token and return its subject (user id), or ``None``."""
    try:
        body, signature = token.split(".")
        secret = get_settings().secret_key.encode("utf-8")
        if not hmac.compare_digest(_sign(secret, body), signature):
            return None
        payload = json.loads(base64.urlsafe_b64decode(body + "==".ljust(len(body) % 4, "=")))
        if payload.get("exp", 0) < int(time.time()):
            return None
        return str(payload.get("sub") or "")
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


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

    subject = decode_access_token(token)
    if not subject:
        raise UnauthorizedError("Invalid or expired token")

    try:
        user_id = uuid.UUID(subject)
    except ValueError as exc:
        raise UnauthorizedError("Invalid token subject") from exc

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise UnauthorizedError("User no longer exists")
    if user.status != UserStatus.ACTIVE:
        raise PermissionDeniedError("User account is not active")

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
