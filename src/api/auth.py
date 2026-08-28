"""
api/auth.py — signup/login/logout/me. JWT stored in an httpOnly cookie,
not returned in the response body or asked of the frontend to store in
localStorage — this is the one real security decision in this module: an
httpOnly cookie can't be read by injected/malicious JS, where localStorage
can. The frontend never sees or handles the raw token; it just sends
credentials: "include" and the browser does the rest.

No refresh-token rotation, no email verification, no OAuth providers, no
password-reset flow — deliberately out of scope for this project (see
CLAUDE.md-adjacent discussion). A password-reset-by-email flow was built
and fully verified in an earlier session (token generation/expiry/single-
use, a Resend-backed email, the works) but deliberately removed again: it
only ever delivers to the email address the project's own Resend account
is registered under, not any other real user's inbox, without paying for
and verifying a domain — a real product gap for an unpaid portfolio demo,
not worth carrying. A single short-lived (7-day) access token is the
whole mechanism; logout just clears the cookie, and there's no server-side
blocklist since the token's own expiry bounds exposure.
"""
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field

from config import get_pg_conn
from structured.users import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    init_users_table,
    update_password,
    update_profile,
    verify_password,
)

# Required in production; a fixed local-dev fallback is fine for a
# single-machine portfolio demo but must never be relied on once deployed
# (anyone who reads this source could forge tokens against that fallback).
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-only-insecure-secret-change-me")
ALGORITHM = "HS256"
TOKEN_EXPIRY = timedelta(days=7)
COOKIE_NAME = "access_token"

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    name: str | None = Field(default=None, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class UserOut(BaseModel):
    user_id: str
    email: str
    name: str | None = None


class UpdateProfileRequest(BaseModel):
    email: EmailStr
    name: str | None = Field(default=None, max_length=200)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)


def _create_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc) + TOKEN_EXPIRY}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=int(TOKEN_EXPIRY.total_seconds()),
        path="/",
    )


def get_current_user(access_token: str | None = Cookie(default=None, alias=COOKIE_NAME)) -> dict:
    """FastAPI dependency — 401s if there's no valid session. Use on every
    endpoint that requires auth (checkout, order history)."""
    if access_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    conn = get_pg_conn()
    try:
        user = get_user_by_id(conn, payload["sub"])
    finally:
        conn.close()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return {"user_id": user["user_id"], "email": user["email"], "name": user["name"]}


def get_optional_user(access_token: str | None = Cookie(default=None, alias=COOKIE_NAME)) -> dict | None:
    """Same as get_current_user but returns None instead of 401 — for
    endpoints that behave differently when logged in but don't require it."""
    if access_token is None:
        return None
    try:
        return get_current_user(access_token)
    except HTTPException:
        return None


@router.post("/signup", response_model=UserOut, status_code=201)
def signup(req: SignupRequest, response: Response):
    conn = get_pg_conn()
    try:
        init_users_table(conn)
        if get_user_by_email(conn, req.email) is not None:
            raise HTTPException(status_code=409, detail="An account with this email already exists")
        user = create_user(conn, req.email, req.password, req.name)
    finally:
        conn.close()

    _set_auth_cookie(response, _create_token(user["user_id"]))
    return UserOut(user_id=user["user_id"], email=user["email"], name=user["name"])


@router.post("/login", response_model=UserOut)
def login(req: LoginRequest, response: Response):
    conn = get_pg_conn()
    try:
        init_users_table(conn)
        user = get_user_by_email(conn, req.email)
    finally:
        conn.close()

    # Deliberately identical error for "no such email" and "wrong
    # password" — distinguishing them lets an attacker enumerate
    # registered emails, a real and cheap-to-avoid mitigation.
    if user is None or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    _set_auth_cookie(response, _create_token(user["user_id"]))
    return UserOut(user_id=user["user_id"], email=user["email"], name=user["name"])


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME, path="/")


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)):
    return UserOut(**user)


@router.patch("/me", response_model=UserOut)
def update_me(req: UpdateProfileRequest, user: dict = Depends(get_current_user)):
    conn = get_pg_conn()
    try:
        if req.email.lower().strip() != user["email"]:
            existing = get_user_by_email(conn, req.email)
            if existing is not None and existing["user_id"] != user["user_id"]:
                raise HTTPException(status_code=409, detail="An account with this email already exists")
        update_profile(conn, user["user_id"], req.name, req.email)
    finally:
        conn.close()
    return UserOut(user_id=user["user_id"], email=req.email.lower().strip(), name=req.name)


@router.post("/change-password", status_code=204)
def change_password(req: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    conn = get_pg_conn()
    try:
        row = get_user_by_id(conn, user["user_id"])
        if row is None or not verify_password(req.current_password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        update_password(conn, user["user_id"], req.new_password)
    finally:
        conn.close()
