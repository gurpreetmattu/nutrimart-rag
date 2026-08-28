"""
api/user_state.py — per-account cart/recently-viewed/compare endpoints.
Every route requires auth (api/auth.py::get_current_user) — a guest never
calls any of these; the frontend contexts stay localStorage-only until
login, then switch to this API. See structured/user_state.py's docstring
for why this isn't named session_state.py.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.auth import get_current_user
from config import get_pg_conn
from structured.user_state import (
    clear_cart,
    clear_compare,
    get_cart,
    get_compare,
    get_recently_viewed,
    init_user_state_tables,
    merge_cart,
    merge_compare,
    merge_recently_viewed,
    record_view,
    remove_from_compare,
    set_cart_item,
    toggle_compare,
)

router = APIRouter(prefix="/api", tags=["user_state"])


class SetCartItemRequest(BaseModel):
    quantity: int


class MergeCartRequest(BaseModel):
    items: dict[str, int]


class MergeIdsRequest(BaseModel):
    ids: list[str] = Field(default_factory=list)


def _conn():
    conn = get_pg_conn()
    init_user_state_tables(conn)
    return conn


# ---------- cart ----------

@router.get("/cart")
def api_get_cart(user: dict = Depends(get_current_user)):
    conn = _conn()
    try:
        return get_cart(conn, user["user_id"])
    finally:
        conn.close()


@router.put("/cart/{product_id}")
def api_set_cart_item(product_id: str, req: SetCartItemRequest, user: dict = Depends(get_current_user)):
    conn = _conn()
    try:
        return set_cart_item(conn, user["user_id"], product_id, req.quantity)
    finally:
        conn.close()


@router.delete("/cart", status_code=204)
def api_clear_cart(user: dict = Depends(get_current_user)):
    conn = _conn()
    try:
        clear_cart(conn, user["user_id"])
    finally:
        conn.close()


@router.post("/cart/merge")
def api_merge_cart(req: MergeCartRequest, user: dict = Depends(get_current_user)):
    conn = _conn()
    try:
        return merge_cart(conn, user["user_id"], req.items)
    finally:
        conn.close()


# ---------- recently viewed ----------

@router.get("/recently-viewed")
def api_get_recently_viewed(user: dict = Depends(get_current_user)):
    conn = _conn()
    try:
        return get_recently_viewed(conn, user["user_id"])
    finally:
        conn.close()


@router.post("/recently-viewed/merge")
def api_merge_recently_viewed(req: MergeIdsRequest, user: dict = Depends(get_current_user)):
    conn = _conn()
    try:
        return merge_recently_viewed(conn, user["user_id"], req.ids)
    finally:
        conn.close()


# Must stay registered AFTER /recently-viewed/merge -- FastAPI/Starlette
# match routes in registration order, so a literal-path route needs to
# come before a parameterized one that would otherwise swallow it first
# (confirmed real: with this the other way around, POST /recently-viewed/
# merge was being routed here with product_id="merge" instead of ever
# reaching api_merge_recently_viewed, silently recording a fake "merge"
# product view instead of merging anything).
@router.post("/recently-viewed/{product_id}")
def api_record_view(product_id: str, user: dict = Depends(get_current_user)):
    conn = _conn()
    try:
        return record_view(conn, user["user_id"], product_id)
    finally:
        conn.close()


# ---------- compare ----------

@router.get("/compare")
def api_get_compare(user: dict = Depends(get_current_user)):
    conn = _conn()
    try:
        return get_compare(conn, user["user_id"])
    finally:
        conn.close()


@router.put("/compare/{product_id}")
def api_toggle_compare(product_id: str, user: dict = Depends(get_current_user)):
    conn = _conn()
    try:
        return toggle_compare(conn, user["user_id"], product_id)
    finally:
        conn.close()


@router.delete("/compare/{product_id}")
def api_remove_from_compare(product_id: str, user: dict = Depends(get_current_user)):
    conn = _conn()
    try:
        return remove_from_compare(conn, user["user_id"], product_id)
    finally:
        conn.close()


@router.delete("/compare", status_code=204)
def api_clear_compare(user: dict = Depends(get_current_user)):
    conn = _conn()
    try:
        clear_compare(conn, user["user_id"])
    finally:
        conn.close()


@router.post("/compare/merge")
def api_merge_compare(req: MergeIdsRequest, user: dict = Depends(get_current_user)):
    conn = _conn()
    try:
        return merge_compare(conn, user["user_id"], req.ids)
    finally:
        conn.close()
