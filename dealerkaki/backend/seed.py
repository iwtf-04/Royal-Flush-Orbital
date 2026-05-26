from datetime import datetime

from auth import hash_password
from database import init_db, get_conn


def seed_users() -> None:
    init_db()

    users = [
        ("dealer", "password123", "staff"),
        ("admin", "adminpass", "admin"),
    ]

    with get_conn() as conn:
        for username, password, role in users:
            password_hash = hash_password(password)
            conn.execute(
                """
                INSERT OR REPLACE INTO users (username, password_hash, role, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (username, password_hash, role, datetime.utcnow().isoformat()),
            )

    print("Seed completed: dealer and admin users created.")


if __name__ == "__main__":
    seed_users()
