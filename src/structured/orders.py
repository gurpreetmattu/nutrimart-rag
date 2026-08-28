"""
structured/orders.py — orders/order_items tables + checkout/order-history
data access. Lives in Postgres (config.py::get_pg_conn()), same reason as
structured/users.py — see that module's docstring.

products.sqlite stays SQLite (read-only, deterministic, rebuilt every
image build) and is now a genuinely separate database from orders/
order_items, so every function here takes BOTH a pg_conn (orders/
order_items) and a sqlite_conn (products) — the SQL JOIN this used to do
against a single database is now a two-step lookup, merged in Python.
order_items.product_id can no longer carry a real FOREIGN KEY to
products(product_id) for the same cross-database reason; the same
integrity check happens at the application layer instead (create_order()
looks the product up in SQLite before ever inserting, same as before).

Price is never accepted from the client — `create_order()` looks up each
product's category/pack_size from the products table and computes the
charged price itself via structured/pricing.py, then snapshots that price
into order_items.unit_price. This means a price change to pricing.py's
rate table (or the deterministic jitter it derives from product_id) never
retroactively changes what a past order shows it charged.
"""
import json
import sqlite3
import uuid
from datetime import datetime, timezone

import psycopg

from structured.pricing import price_for

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    status TEXT NOT NULL,
    total_amount REAL NOT NULL,
    placed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id TEXT NOT NULL REFERENCES orders(order_id),
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL
);
"""


class EmptyCartError(Exception):
    pass


class InvalidProductError(Exception):
    def __init__(self, product_id: str):
        self.product_id = product_id
        super().__init__(f"Unknown product '{product_id}'")


def init_orders_tables(conn: psycopg.Connection) -> None:
    conn.execute(SCHEMA)
    conn.commit()


def create_order(
    pg_conn: psycopg.Connection, sqlite_conn: sqlite3.Connection, user_id: str, items: list[dict]
) -> dict:
    """
    items: [{"product_id": ..., "quantity": ...}, ...] — as submitted by
    the client. Quantities <= 0 are dropped rather than rejected (mirrors
    CartContext.jsx's own decr() behavior, which removes a line at 0).
    """
    lines = []
    for item in items:
        qty = int(item.get("quantity", 0))
        if qty <= 0:
            continue
        product = sqlite_conn.execute(
            "SELECT product_id, category, pack_size_json FROM products WHERE product_id = ?",
            (item["product_id"],),
        ).fetchone()
        if product is None:
            raise InvalidProductError(item["product_id"])
        pack_size = json.loads(product["pack_size_json"] or "{}")
        unit_price = price_for(product["product_id"], product["category"], pack_size)
        lines.append({"product_id": product["product_id"], "quantity": qty, "unit_price": unit_price})

    if not lines:
        raise EmptyCartError()

    order_id = str(uuid.uuid4())
    placed_at = datetime.now(timezone.utc).isoformat()
    total_amount = sum(l["unit_price"] * l["quantity"] for l in lines)

    pg_conn.execute(
        "INSERT INTO orders (order_id, user_id, status, total_amount, placed_at) VALUES (%s, %s, %s, %s, %s)",
        (order_id, user_id, "placed", total_amount, placed_at),
    )
    pg_conn.cursor().executemany(
        "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
        [(order_id, l["product_id"], l["quantity"], l["unit_price"]) for l in lines],
    )
    pg_conn.commit()

    return {
        "order_id": order_id,
        "status": "placed",
        "total_amount": total_amount,
        "placed_at": placed_at,
        "items": lines,
    }


def _product_lookup(sqlite_conn: sqlite3.Connection, product_ids: list[str]) -> dict[str, sqlite3.Row]:
    if not product_ids:
        return {}
    placeholders = ",".join("?" * len(product_ids))
    rows = sqlite_conn.execute(
        f"SELECT product_id, name, brand, category FROM products WHERE product_id IN ({placeholders})",
        product_ids,
    ).fetchall()
    return {r["product_id"]: r for r in rows}


def _row_to_item(item_row: dict, product_row: sqlite3.Row | None) -> dict:
    return {
        "product_id": item_row["product_id"],
        "quantity": item_row["quantity"],
        "unit_price": item_row["unit_price"],
        "name": product_row["name"] if product_row else item_row["product_id"],
        "brand": product_row["brand"] if product_row else None,
        "category": product_row["category"] if product_row else None,
    }


def get_orders_for_user(
    pg_conn: psycopg.Connection, sqlite_conn: sqlite3.Connection, user_id: str
) -> list[dict]:
    orders = pg_conn.execute(
        "SELECT * FROM orders WHERE user_id = %s ORDER BY placed_at DESC", (user_id,)
    ).fetchall()
    if not orders:
        return []

    order_ids = [o["order_id"] for o in orders]
    placeholders = ",".join(["%s"] * len(order_ids))
    all_items = pg_conn.execute(
        f"SELECT * FROM order_items WHERE order_id IN ({placeholders})", order_ids
    ).fetchall()
    products_by_id = _product_lookup(sqlite_conn, list({i["product_id"] for i in all_items}))

    items_by_order: dict[str, list[dict]] = {}
    for item in all_items:
        items_by_order.setdefault(item["order_id"], []).append(item)

    return [
        {
            "order_id": order["order_id"],
            "status": order["status"],
            "total_amount": order["total_amount"],
            "placed_at": order["placed_at"],
            "items": [
                _row_to_item(i, products_by_id.get(i["product_id"]))
                for i in items_by_order.get(order["order_id"], [])
            ],
        }
        for order in orders
    ]


def get_order_for_user(
    pg_conn: psycopg.Connection, sqlite_conn: sqlite3.Connection, user_id: str, order_id: str
) -> dict | None:
    order = pg_conn.execute(
        "SELECT * FROM orders WHERE order_id = %s AND user_id = %s", (order_id, user_id)
    ).fetchone()
    if order is None:
        return None
    items = pg_conn.execute(
        "SELECT * FROM order_items WHERE order_id = %s", (order_id,)
    ).fetchall()
    products_by_id = _product_lookup(sqlite_conn, [i["product_id"] for i in items])
    return {
        "order_id": order["order_id"],
        "status": order["status"],
        "total_amount": order["total_amount"],
        "placed_at": order["placed_at"],
        "items": [_row_to_item(i, products_by_id.get(i["product_id"])) for i in items],
    }
