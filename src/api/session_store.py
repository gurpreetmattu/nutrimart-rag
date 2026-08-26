"""
api/session_store.py — process-local conversation-state store, keyed by a
client-generated session_id. Same in-memory-dict shape as api/security.py's
rate-limit log — no external store needed for a single-process demo app;
would need a shared store (Redis, etc.) if this ever ran behind multiple
worker processes, same caveat security.py's rate limiter already documents.

Deliberately not persisted to disk — conversation memory resetting on a
server restart is an acceptable, honest limitation for a portfolio demo,
not a real product's session store.
"""
from conversation.state import default_state

_sessions: dict[str, dict] = {}


def get_session(session_id: str) -> dict:
    if session_id not in _sessions:
        _sessions[session_id] = default_state()
    return _sessions[session_id]


def save_session(session_id: str, state: dict) -> None:
    _sessions[session_id] = state
