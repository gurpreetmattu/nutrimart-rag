"""
structured/users.py — the users table: signup/login data access.

Lives in Postgres (config.py::get_pg_conn()), not products.sqlite. Cloud
Run (this project's deploy target) scales to zero, and a container's local
filesystem — including a SQLite file baked into the image — does not
survive that: a signup written to one container's local disk is gone the
moment the next request cold-starts a fresh container from the image.
Confirmed as the real cause of a live "login works right after signup,
'invalid password' ~15 minutes later" report. products.sqlite itself
doesn't have this problem (read-only, deterministic, rebuilt at image
build time) — only tables an actual user writes to at runtime needed to
move off local disk. See config.py's DATABASE_URL comment for the full
writeup.

Password hashing lives here too (bcrypt, via the `bcrypt` package directly
rather than passlib — passlib's bcrypt backend has had real compatibility
breaks against newer bcrypt releases, and this project only needs hash/
verify, not passlib's broader multi-scheme abstraction).
"""
import uuid
from datetime import datetime, timezone

import bcrypt
import psycopg

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    created_at TEXT NOT NULL
);
"""


def init_users_table(conn: psycopg.Connection) -> None:
    conn.execute(SCHEMA)
    conn.commit()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Malformed/legacy hash — never let a lookup error surface as a 500.
        return False


def create_user(conn: psycopg.Connection, email: str, password: str, name: str | None) -> dict:
    user_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO users (user_id, email, password_hash, name, created_at) VALUES (%s, %s, %s, %s, %s)",
        (user_id, email.lower().strip(), hash_password(password), name, created_at),
    )
    conn.commit()
    return {"user_id": user_id, "email": email.lower().strip(), "name": name, "created_at": created_at}


def get_user_by_email(conn: psycopg.Connection, email: str) -> dict | None:
    return conn.execute(
        "SELECT * FROM users WHERE email = %s", (email.lower().strip(),)
    ).fetchone()


def get_user_by_id(conn: psycopg.Connection, user_id: str) -> dict | None:
    return conn.execute("SELECT * FROM users WHERE user_id = %s", (user_id,)).fetchone()


def update_profile(conn: psycopg.Connection, user_id: str, name: str | None, email: str) -> None:
    conn.execute(
        "UPDATE users SET name = %s, email = %s WHERE user_id = %s",
        (name, email.lower().strip(), user_id),
    )
    conn.commit()


def update_password(conn: psycopg.Connection, user_id: str, new_password: str) -> None:
    conn.execute(
        "UPDATE users SET password_hash = %s WHERE user_id = %s",
        (hash_password(new_password), user_id),
    )
    conn.commit()
