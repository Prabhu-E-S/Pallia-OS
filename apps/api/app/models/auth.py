"""Authentication session entities.

Refresh sessions are opaque, single-use tokens. Only their SHA-256 hashes are
stored so a leaked table never exposes a usable credential.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.mixins import OrganizationScopedMixin, TimestampMixin


def _utc_or_naive(value: datetime) -> datetime:
    """SQLite returns tz-naive datetimes; treat them as UTC."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


class AuthSession(OrganizationScopedMixin, TimestampMixin):
    """A revocable server-side session bound to a refresh token."""

    __tablename__ = "auth_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(back_populates="auth_sessions")

    @property
    def is_active(self) -> bool:
        if self.revoked_at is not None:
            return False
        return _utc_or_naive(self.expires_at) > datetime.now(UTC)
