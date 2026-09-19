"""Shared model mixins.

Both mixins derive from the declarative `Base` and are marked `__abstract__`,
which is the supported SQLAlchemy pattern for reusing columns while keeping a
single table per concrete model.
"""

import uuid
from datetime import datetime
from typing import Annotated

from sqlalchemy import DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# PK / FK columns typed once so model definitions stay readable.
UUID_PK = Annotated[uuid.UUID, mapped_column(Uuid, primary_key=True, default=uuid.uuid4)]
UUID_FK = Annotated[uuid.UUID, mapped_column(Uuid, nullable=True)]


class TimestampMixin(Base):
    """Adds ``created_at`` and ``updated_at`` UTC timestamp columns."""

    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class OrganizationScopedMixin(Base):
    """Adds an indexed ``organization_id`` column for tenant isolation.

    Every organization-owned entity must be queried with an organization
    filter; services enforce this on every read and write.
    """

    __abstract__ = True

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
