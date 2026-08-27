"""
api/orders.py — checkout + order history. Both endpoints require auth
(api/auth.py::get_current_user) — there's no guest checkout, same as most
real quick-commerce apps.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.auth import get_current_user
from config import get_sqlite_conn
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
    conn = get_sqlite_conn()
    try:
        init_orders_tables(conn)
        try:
            return create_order(conn, user["user_id"], [item.model_dump() for item in req.items])
        except EmptyCartError:
            raise HTTPException(status_code=400, detail="Cart is empty")
        except InvalidProductError as e:
            raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@router.get("/orders")
def list_orders(user: dict = Depends(get_current_user)):
    conn = get_sqlite_conn()
    try:
        init_orders_tables(conn)
        return get_orders_for_user(conn, user["user_id"])
    finally:
        conn.close()


@router.get("/orders/{order_id}")
def get_order(order_id: str, user: dict = Depends(get_current_user)):
    conn = get_sqlite_conn()
    try:
        init_orders_tables(conn)
        order = get_order_for_user(conn, user["user_id"], order_id)
    finally:
        conn.close()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
