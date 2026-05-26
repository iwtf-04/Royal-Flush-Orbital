from __future__ import annotations

from dataclasses import dataclass
from secrets import token_urlsafe
from typing import Dict, Optional

from pydantic import BaseModel


@dataclass
class UserRecord:
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None


# Simple in-memory user store for demo login.
# Replace with a database or identity provider for production.
_users: Dict[str, UserRecord] = {
    "dealer": UserRecord(username="dealer", password="password123"),
    "admin": UserRecord(username="admin", password="adminpass"),
}

# Session token store for demonstration only.
_sessions: Dict[str, str] = {}


def verify_user_credentials(username: str, password: str) -> bool:
    record = _users.get(username)
    return bool(record and record.password == password)


def create_session_token(username: str) -> str:
    token = token_urlsafe(32)
    _sessions[token] = username
    return token


def get_username_from_token(token: str) -> Optional[str]:
    return _sessions.get(token)
