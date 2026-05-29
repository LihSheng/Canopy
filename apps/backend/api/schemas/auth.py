from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SessionUser(BaseModel):
    id: str
    email: str
    display_name: str
    is_admin: bool = False


class TenantInfo(BaseModel):
    tenant_id: str
    name: str
    role: str


class TenantContextResponse(BaseModel):
    tenant_id: str
    role: str


class SwitchTenantRequest(BaseModel):
    tenant_id: str


class LoginResponse(BaseModel):
    user: SessionUser
    token: str
    expires_at: datetime
    tenants: list[TenantInfo] = []


class SessionResponse(BaseModel):
    authenticated: bool
    user: SessionUser | None = None
    tenant: TenantContextResponse | None = None
    tenants: list[TenantInfo] = []


class LogoutResponse(BaseModel):
    message: str
