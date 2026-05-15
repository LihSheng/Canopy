from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SessionUser(BaseModel):
    id: str
    email: str
    display_name: str


class LoginResponse(BaseModel):
    user: SessionUser
    token: str
    expires_at: datetime


class SessionResponse(BaseModel):
    authenticated: bool
    user: SessionUser | None = None


class LogoutResponse(BaseModel):
    message: str
