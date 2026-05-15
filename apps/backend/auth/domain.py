from dataclasses import dataclass
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
class Session:
    user_id: str
    email: str
    display_name: str
    token: str
    expires_at: datetime


@dataclass
class LoginInput:
    email: str
    password: str


@dataclass
class LoginOutput:
    user: "LoginOutputUser"
    token: str
    expires_at: datetime


@dataclass
class LoginOutputUser:
    id: str
    email: str
    display_name: str


@dataclass
class SessionOutput:
    authenticated: bool
    user: Optional["LoginOutputUser"] = None
