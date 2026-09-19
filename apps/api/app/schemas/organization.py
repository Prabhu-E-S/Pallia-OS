from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.schemas.common import ORMModel


class OrganizationOut(ORMModel):
    id: str
    name: str
    type: str
    status: str
    created_at: datetime
    updated_at: datetime


class OrganizationList(BaseModel):
    items: list[OrganizationOut]
    total: int


class UserOut(ORMModel):
    id: str
    email: EmailStr
    full_name: str
    phone: str | None = None
    role: str
    status: str
    organization_id: str
    created_at: datetime
    updated_at: datetime


class UserList(BaseModel):
    items: list[UserOut]
    total: int
