from typing import Any

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class RefreshTokenRequest(BaseModel):
    refresh_token: str | None = None


class DevLoginRequest(BaseModel):
    email: EmailStr


class CurrentUserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    status: str
    organization_id: str
    organization_name: str
    permissions: list[str] = []


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str | None = None
    user: dict[str, Any]
