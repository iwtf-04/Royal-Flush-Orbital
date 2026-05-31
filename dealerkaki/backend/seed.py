from datetime import datetime

from auth import hash_password
from database import init_db, get_conn


def seed_users() -> None:
    init_db()

    users = [
        ("staff1", "staff123", "frontline staff"),
        ("inventory1", "inventory123", "inventory manager"),
        ("dealer1", "dealer123", "dealer"),
        ("admin1", "admin123", "admin"),
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

    print("Seed completed: staff1, inventory1, dealer1, and admin1 users created.")


if __name__ == "__main__":
    seed_users()
