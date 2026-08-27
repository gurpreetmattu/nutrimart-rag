"""
structured/users.py — the users table: signup/login data access, same
plain-SQLite-in-db/products.sqlite pattern ingestion/load_products.py
already uses for the products table (see config.py::get_sqlite_conn()).

Password hashing lives here too (bcrypt, via the `bcrypt` package directly
rather than passlib — passlib's bcrypt backend has had real compatibility
breaks against newer bcrypt releases, and this project only needs hash/
verify, not passlib's broader multi-scheme abstraction).
"""
import sqlite3
import uuid
from datetime import datetime, timezone

import bcrypt

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    created_at TEXT NOT NULL
);
"""


def init_users_table(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Malformed/legacy hash — never let a lookup error surface as a 500.
        return False


def create_user(conn: sqlite3.Connection, email: str, password: str, name: str | None) -> dict:
    user_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO users (user_id, email, password_hash, name, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, email.lower().strip(), hash_password(password), name, created_at),
    )
    conn.commit()
    return {"user_id": user_id, "email": email.lower().strip(), "name": name, "created_at": created_at}


def get_user_by_email(conn: sqlite3.Connection, email: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
    ).fetchone()


def get_user_by_id(conn: sqlite3.Connection, user_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()


def update_profile(conn: sqlite3.Connection, user_id: str, name: str | None, email: str) -> None:
    conn.execute(
        "UPDATE users SET name = ?, email = ? WHERE user_id = ?",
        (name, email.lower().strip(), user_id),
    )
    conn.commit()


def update_password(conn: sqlite3.Connection, user_id: str, new_password: str) -> None:
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE user_id = ?",
        (hash_password(new_password), user_id),
    )
    conn.commit()
