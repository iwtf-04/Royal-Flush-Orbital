from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "dealerkaki.db"


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vin TEXT NOT NULL UNIQUE,
                license_plate TEXT NOT NULL DEFAULT '',
                make TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                mileage INTEGER NOT NULL DEFAULT 0,
                purchase_price REAL NOT NULL DEFAULT 0,
                arf REAL NOT NULL,
                coe REAL NOT NULL,
                coe_at_purchase REAL NOT NULL DEFAULT 0,
                current_coe REAL NOT NULL DEFAULT 0,
                registration_date TEXT NOT NULL,
                date_acquired TEXT NOT NULL DEFAULT '',
                entry_date TEXT NOT NULL,
                estimated_value REAL NOT NULL,
                current_market_value REAL NOT NULL DEFAULT 0,
                recommended_intake_price REAL NOT NULL DEFAULT 0,
                target_selling_price REAL NOT NULL DEFAULT 0,
                depreciation_rate REAL NOT NULL,
                profit_margin REAL NOT NULL DEFAULT 0,
                risk_level TEXT NOT NULL DEFAULT '',
                recommendation TEXT NOT NULL DEFAULT '',
                recommendation_reason TEXT NOT NULL DEFAULT '',
                sold_price REAL NOT NULL DEFAULT 0,
                sold_date TEXT NOT NULL DEFAULT '',
                vehicle_type TEXT NOT NULL DEFAULT '',
                seat_count INTEGER NOT NULL DEFAULT 0,
                days_in_inventory INTEGER NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
        _ensure_vehicle_columns(conn)


def _ensure_vehicle_columns(conn) -> None:
    existing_columns = [row[1] for row in conn.execute("PRAGMA table_info(vehicles)").fetchall()]
    required_columns = {
        "license_plate": "TEXT NOT NULL DEFAULT ''",
        "mileage": "INTEGER NOT NULL DEFAULT 0",
        "purchase_price": "REAL NOT NULL DEFAULT 0",
        "coe_at_purchase": "REAL NOT NULL DEFAULT 0",
        "current_coe": "REAL NOT NULL DEFAULT 0",
        "date_acquired": "TEXT NOT NULL DEFAULT ''",
        "current_market_value": "REAL NOT NULL DEFAULT 0",
        "recommended_intake_price": "REAL NOT NULL DEFAULT 0",
        "target_selling_price": "REAL NOT NULL DEFAULT 0",
        "profit_margin": "REAL NOT NULL DEFAULT 0",
        "risk_level": "TEXT NOT NULL DEFAULT ''",
        "recommendation": "TEXT NOT NULL DEFAULT ''",
        "recommendation_reason": "TEXT NOT NULL DEFAULT ''",
        "sold_price": "REAL NOT NULL DEFAULT 0",
        "sold_date": "TEXT NOT NULL DEFAULT ''",
        "vehicle_type": "TEXT NOT NULL DEFAULT ''",
        "seat_count": "INTEGER NOT NULL DEFAULT 0",
    }

    for column_name, column_definition in required_columns.items():
        if column_name not in existing_columns:
            conn.execute(f"ALTER TABLE vehicles ADD COLUMN {column_name} {column_definition}")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
