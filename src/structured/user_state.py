"""
structured/user_state.py — per-account cart/recently-viewed/compare data
access. Lives in Postgres (config.py::get_pg_conn()), same database and
same reason as structured/users.py/orders.py: a Cloud Run container's
local disk doesn't survive scale-to-zero, so this can't live in a local
file either.

Distinct from api/session_store.py, which is unrelated: that holds
in-memory, per-process chat conversation state (deliberately not durable,
see its own docstring) — this module is the opposite, durable state tied
to an account, not a browser or a process.

No FK to products (they live in a separate SQLite database, same reason
order_items lost its FK to products in the orders migration) — product
details are never duplicated here; the frontend already has the full
catalog client-side and matches by product_id, exactly how
RecentlyViewedRail.jsx already worked before this module existed.
"""
from datetime import datetime, timezone

import psycopg

MAX_RECENTLY_VIEWED = 12
MAX_COMPARE = 4

SCHEMA = """
CREATE TABLE IF NOT EXISTS cart_items (
    user_id TEXT NOT NULL REFERENCES users(user_id),
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (user_id, product_id)
);

CREATE TABLE IF NOT EXISTS recently_viewed (
    user_id TEXT NOT NULL REFERENCES users(user_id),
    product_id TEXT NOT NULL,
    viewed_at TEXT NOT NULL,
    PRIMARY KEY (user_id, product_id)
);

CREATE TABLE IF NOT EXISTS compare_items (
    user_id TEXT NOT NULL REFERENCES users(user_id),
    product_id TEXT NOT NULL,
    added_at TEXT NOT NULL,
    PRIMARY KEY (user_id, product_id)
);
"""


def init_user_state_tables(conn: psycopg.Connection) -> None:
    conn.execute(SCHEMA)
    conn.commit()


# ---------- cart ----------

def get_cart(conn: psycopg.Connection, user_id: str) -> dict[str, int]:
    rows = conn.execute(
        "SELECT product_id, quantity FROM cart_items WHERE user_id = %s", (user_id,)
    ).fetchall()
    return {r["product_id"]: r["quantity"] for r in rows}


def set_cart_item(conn: psycopg.Connection, user_id: str, product_id: str, quantity: int) -> dict[str, int]:
    if quantity <= 0:
        conn.execute(
            "DELETE FROM cart_items WHERE user_id = %s AND product_id = %s", (user_id, product_id)
        )
    else:
        conn.execute(
            """
            INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, %s)
            ON CONFLICT (user_id, product_id) DO UPDATE SET quantity = EXCLUDED.quantity
            """,
            (user_id, product_id, quantity),
        )
    conn.commit()
    return get_cart(conn, user_id)


def merge_cart(conn: psycopg.Connection, user_id: str, items: dict[str, int]) -> dict[str, int]:
    """Sums the given quantities onto whatever's already there — used once,
    right after login, to fold a guest's localStorage cart into the
    account's server-side one without silently discarding either side."""
    current = get_cart(conn, user_id)
    for product_id, qty in items.items():
        if qty <= 0:
            continue
        new_qty = current.get(product_id, 0) + qty
        conn.execute(
            """
            INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, %s)
            ON CONFLICT (user_id, product_id) DO UPDATE SET quantity = EXCLUDED.quantity
            """,
            (user_id, product_id, new_qty),
        )
    conn.commit()
    return get_cart(conn, user_id)


def clear_cart(conn: psycopg.Connection, user_id: str) -> None:
    conn.execute("DELETE FROM cart_items WHERE user_id = %s", (user_id,))
    conn.commit()


# ---------- recently viewed ----------

def get_recently_viewed(conn: psycopg.Connection, user_id: str) -> list[str]:
    rows = conn.execute(
        "SELECT product_id FROM recently_viewed WHERE user_id = %s ORDER BY viewed_at DESC LIMIT %s",
        (user_id, MAX_RECENTLY_VIEWED),
    ).fetchall()
    return [r["product_id"] for r in rows]


def record_view(conn: psycopg.Connection, user_id: str, product_id: str) -> list[str]:
    viewed_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO recently_viewed (user_id, product_id, viewed_at) VALUES (%s, %s, %s)
        ON CONFLICT (user_id, product_id) DO UPDATE SET viewed_at = EXCLUDED.viewed_at
        """,
        (user_id, product_id, viewed_at),
    )
    # Trim to the cap so this table never grows unbounded per user — same
    # MAX_RECENTLY_VIEWED cap RecentlyViewedContext.jsx already enforces
    # client-side for a guest.
    conn.execute(
        """
        DELETE FROM recently_viewed
        WHERE user_id = %s AND product_id NOT IN (
            SELECT product_id FROM recently_viewed WHERE user_id = %s
            ORDER BY viewed_at DESC LIMIT %s
        )
        """,
        (user_id, user_id, MAX_RECENTLY_VIEWED),
    )
    conn.commit()
    return get_recently_viewed(conn, user_id)


def merge_recently_viewed(conn: psycopg.Connection, user_id: str, product_ids: list[str]) -> list[str]:
    """Replays local ids (oldest first) through record_view() so they
    interleave with any server-side history by real recency rather than
    overwriting it — same one-call-per-id approach as merge_compare()."""
    for product_id in reversed(product_ids):
        record_view(conn, user_id, product_id)
    return get_recently_viewed(conn, user_id)


# ---------- compare ----------

def get_compare(conn: psycopg.Connection, user_id: str) -> list[str]:
    rows = conn.execute(
        "SELECT product_id FROM compare_items WHERE user_id = %s ORDER BY added_at", (user_id,)
    ).fetchall()
    return [r["product_id"] for r in rows]


def toggle_compare(conn: psycopg.Connection, user_id: str, product_id: str) -> list[str]:
    # DELETE ... RETURNING + INSERT ... ON CONFLICT DO NOTHING instead of a
    # SELECT-then-branch: the old version's SELECT and its follow-up
    # INSERT/DELETE weren't atomic, so two near-simultaneous toggle calls
    # for the same product (confirmed real: React 18 StrictMode
    # double-invokes CompareContext.jsx's setState updater in dev, and nothing
    # stops a genuine double-click in prod either) could both see "not
    # present" and both try to INSERT, the second hitting the
    # (user_id, product_id) primary key and 500ing. ON CONFLICT DO NOTHING
    # makes a duplicate INSERT a harmless no-op instead.
    deleted = conn.execute(
        "DELETE FROM compare_items WHERE user_id = %s AND product_id = %s RETURNING 1",
        (user_id, product_id),
    ).fetchone()
    if deleted:
        conn.commit()
        return get_compare(conn, user_id)

    current = get_compare(conn, user_id)
    if len(current) >= MAX_COMPARE:
        # Silently no-op past the cap — the frontend already gates this
        # with a toast before ever calling here; this is a defensive
        # backstop, not the primary UX.
        return current

    conn.execute(
        """
        INSERT INTO compare_items (user_id, product_id, added_at) VALUES (%s, %s, %s)
        ON CONFLICT (user_id, product_id) DO NOTHING
        """,
        (user_id, product_id, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    return get_compare(conn, user_id)


def remove_from_compare(conn: psycopg.Connection, user_id: str, product_id: str) -> list[str]:
    conn.execute(
        "DELETE FROM compare_items WHERE user_id = %s AND product_id = %s", (user_id, product_id)
    )
    conn.commit()
    return get_compare(conn, user_id)


def clear_compare(conn: psycopg.Connection, user_id: str) -> None:
    conn.execute("DELETE FROM compare_items WHERE user_id = %s", (user_id,))
    conn.commit()


def merge_compare(conn: psycopg.Connection, user_id: str, product_ids: list[str]) -> list[str]:
    current = get_compare(conn, user_id)
    for product_id in product_ids:
        if product_id in current:
            continue
        if len(current) >= MAX_COMPARE:
            break
        toggle_compare(conn, user_id, product_id)
        current = get_compare(conn, user_id)
    return current
