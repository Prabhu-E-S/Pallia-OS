from typing import Any

from pydantic import BaseModel, EmailStr


class DevLoginRequest(BaseModel):
    email: EmailStr


class CurrentUserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    organization_id: str
    organization_name: str
    permissions: list[str] = []


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]
