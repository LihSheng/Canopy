from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: str
    email: str
    password_hash: str
    display_name: str
    created_at: datetime
    last_login_at: datetime | None
    is_active: bool


@dataclass
class TenantInfo:
    tenant_id: str
    tenant_name: str
    role: str


@dataclass
class Session:
    user_id: str
    email: str
    display_name: str
    token: str
    expires_at: datetime
    tenant_id: str | None = None
    tenants: list[TenantInfo] = field(default_factory=list)


@dataclass
class LoginInput:
    email: str
    password: str


@dataclass
class LoginOutput:
    user: "LoginOutputUser"
    token: str
    expires_at: datetime
    tenants: list[TenantInfo] = field(default_factory=list)


@dataclass
class LoginOutputUser:
    id: str
    email: str
    display_name: str


@dataclass
class SessionOutput:
    authenticated: bool
    user: Optional["LoginOutputUser"] = None
    tenant_id: str | None = None
    tenant_role: str | None = None
    tenants: list[TenantInfo] = field(default_factory=list)
