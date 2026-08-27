"""
structured/orders.py — orders/order_items tables + checkout/order-history
data access. Same db/products.sqlite the products/users tables live in.

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
    product_id TEXT NOT NULL REFERENCES products(product_id),
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


def init_orders_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def create_order(conn: sqlite3.Connection, user_id: str, items: list[dict]) -> dict:
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
        product = conn.execute(
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

    conn.execute(
        "INSERT INTO orders (order_id, user_id, status, total_amount, placed_at) VALUES (?, ?, ?, ?, ?)",
        (order_id, user_id, "placed", total_amount, placed_at),
    )
    conn.executemany(
        "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
        [(order_id, l["product_id"], l["quantity"], l["unit_price"]) for l in lines],
    )
    conn.commit()

    return {
        "order_id": order_id,
        "status": "placed",
        "total_amount": total_amount,
        "placed_at": placed_at,
        "items": lines,
    }


def _row_to_item(row: sqlite3.Row) -> dict:
    return {
        "product_id": row["product_id"],
        "quantity": row["quantity"],
        "unit_price": row["unit_price"],
        "name": row["name"],
        "brand": row["brand"],
        "category": row["category"],
    }


def get_orders_for_user(conn: sqlite3.Connection, user_id: str) -> list[dict]:
    orders = conn.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY placed_at DESC", (user_id,)
    ).fetchall()
    result = []
    for order in orders:
        items = conn.execute(
            """
            SELECT oi.product_id, oi.quantity, oi.unit_price, p.name, p.brand, p.category
            FROM order_items oi JOIN products p ON p.product_id = oi.product_id
            WHERE oi.order_id = ?
            """,
            (order["order_id"],),
        ).fetchall()
        result.append({
            "order_id": order["order_id"],
            "status": order["status"],
            "total_amount": order["total_amount"],
            "placed_at": order["placed_at"],
            "items": [_row_to_item(i) for i in items],
        })
    return result


def get_order_for_user(conn: sqlite3.Connection, user_id: str, order_id: str) -> dict | None:
    order = conn.execute(
        "SELECT * FROM orders WHERE order_id = ? AND user_id = ?", (order_id, user_id)
    ).fetchone()
    if order is None:
        return None
    items = conn.execute(
        """
        SELECT oi.product_id, oi.quantity, oi.unit_price, p.name, p.brand, p.category
        FROM order_items oi JOIN products p ON p.product_id = oi.product_id
        WHERE oi.order_id = ?
        """,
        (order_id,),
    ).fetchall()
    return {
        "order_id": order["order_id"],
        "status": order["status"],
        "total_amount": order["total_amount"],
        "placed_at": order["placed_at"],
        "items": [_row_to_item(i) for i in items],
    }
