"""
api/orders.py — checkout + order history. Both endpoints require auth
(api/auth.py::get_current_user) — there's no guest checkout, same as most
real quick-commerce apps.

Touches two databases: orders/order_items live in Postgres (get_pg_conn,
see structured/orders.py's docstring for why), products still live in
SQLite (get_sqlite_conn) — structured/orders.py's functions take both.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.auth import get_current_user
from config import get_pg_conn, get_sqlite_conn
from structured.orders import (
    EmptyCartError,
    InvalidProductError,
    create_order,
    get_order_for_user,
    get_orders_for_user,
    init_orders_tables,
)

router = APIRouter(prefix="/api", tags=["orders"])


class CheckoutItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)


class CheckoutRequest(BaseModel):
    items: list[CheckoutItem] = Field(min_length=1)


@router.post("/checkout", status_code=201)
def checkout(req: CheckoutRequest, user: dict = Depends(get_current_user)):
    pg_conn = get_pg_conn()
    sqlite_conn = get_sqlite_conn()
    try:
        init_orders_tables(pg_conn)
        try:
            return create_order(pg_conn, sqlite_conn, user["user_id"], [item.model_dump() for item in req.items])
        except EmptyCartError:
            raise HTTPException(status_code=400, detail="Cart is empty")
        except InvalidProductError as e:
            raise HTTPException(status_code=400, detail=str(e))
    finally:
        pg_conn.close()
        sqlite_conn.close()


@router.get("/orders")
def list_orders(user: dict = Depends(get_current_user)):
    pg_conn = get_pg_conn()
    sqlite_conn = get_sqlite_conn()
    try:
        init_orders_tables(pg_conn)
        return get_orders_for_user(pg_conn, sqlite_conn, user["user_id"])
    finally:
        pg_conn.close()
        sqlite_conn.close()


@router.get("/orders/{order_id}")
def get_order(order_id: str, user: dict = Depends(get_current_user)):
    pg_conn = get_pg_conn()
    sqlite_conn = get_sqlite_conn()
    try:
        init_orders_tables(pg_conn)
        order = get_order_for_user(pg_conn, sqlite_conn, user["user_id"], order_id)
    finally:
        pg_conn.close()
        sqlite_conn.close()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
