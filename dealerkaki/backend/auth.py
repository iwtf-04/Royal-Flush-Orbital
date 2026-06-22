from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from secrets import token_urlsafe
from typing import Dict, Optional

import bcrypt
from pydantic import BaseModel

from database import get_conn


SESSION_DURATION_HOURS = 8
DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"invalid-password", bcrypt.gensalt())


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None


@dataclass
class UserRecord:
    username: str
    password_hash: str
    role: str


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_user_by_username(username: str) -> Optional[Dict[str, str]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, role, created_at FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, str]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, username, role, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def get_all_users() -> list[Dict[str, str]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, username, role, created_at FROM users ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def create_user(username: str, password: str, role: str) -> Dict[str, str]:
    password_hash = hash_password(password)
    created_at = datetime.utcnow().isoformat()
    with get_conn() as conn:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
            (username, password_hash, role, created_at),
        )
        user_id = cursor.lastrowid
    return {
        "id": user_id,
        "username": username,
        "role": role,
        "created_at": created_at,
    }


def delete_user(user_id: int) -> bool:
    with get_conn() as conn:
        cursor = conn.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,),
        )
        return cursor.rowcount > 0


def verify_user_credentials(username: str, password: str) -> bool:
    user = get_user_by_username(username)
    if user is None:
        bcrypt.checkpw(password.encode("utf-8"), DUMMY_PASSWORD_HASH)
        return False
    return verify_password(password, user["password_hash"])


def create_session_token(username: str) -> str:
    token = token_urlsafe(32)
    expires_at = (datetime.utcnow() + timedelta(hours=SESSION_DURATION_HOURS)).isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sessions (token, username, expires_at) VALUES (?, ?, ?)",
            (token, username, expires_at),
        )
    return token


def get_username_from_token(token: str) -> Optional[str]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT username, expires_at FROM sessions WHERE token = ?",
            (token,),
        ).fetchone()
        if row is None:
            return None

        expires_at = datetime.fromisoformat(row["expires_at"])
        if expires_at <= datetime.utcnow():
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            return None

        return row["username"]
