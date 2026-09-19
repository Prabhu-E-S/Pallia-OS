"""Organization and User entities."""

import uuid
from typing import Annotated

from sqlalchemy import Enum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.enums import OrganizationStatus, OrganizationType, UserRole, UserStatus
from app.models.mixins import OrganizationScopedMixin, TimestampMixin

StrUUID = Annotated[uuid.UUID, mapped_column(Uuid, nullable=True)]


class Organization(TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[OrganizationType] = mapped_column(
        Enum(OrganizationType, native_enum=False, length=32),
        nullable=False,
        default=OrganizationType.OTHER,
    )
    status: Mapped[OrganizationStatus] = mapped_column(
        Enum(OrganizationStatus, native_enum=False, length=32),
        nullable=False,
        default=OrganizationStatus.ACTIVE,
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )


class User(OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=32),
        nullable=False,
        default=UserRole.CARE_COORDINATOR,
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, native_enum=False, length=32),
        nullable=False,
        default=UserStatus.ACTIVE,
    )
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    organization: Mapped[Organization] = relationship(back_populates="users")

    caregivers: Mapped[list["Caregiver"]] = relationship(back_populates="user")
