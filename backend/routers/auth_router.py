"""Admin auth endpoints."""

from __future__ import annotations

from collections import defaultdict
from threading import Lock
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .. import crud, auth
from ..database import get_db_dep
from ..schemas import LoginRequest, TokenOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

_FAILURE_WINDOW_SECONDS = 15 * 60
_BLOCK_SECONDS = 15 * 60
_MAX_FAILURES = 5
_failures: dict[str, list[float]] = defaultdict(list)
_blocked_until: dict[str, float] = {}
_rate_lock = Lock()


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _check_login_limit(key: str) -> None:
    now = monotonic()
    with _rate_lock:
        until = _blocked_until.get(key, 0)
        if until > now:
            retry_after = max(1, int(until - now))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Try again later.",
                headers={"Retry-After": str(retry_after)},
            )
        _failures[key] = [t for t in _failures[key] if now - t < _FAILURE_WINDOW_SECONDS]


def _record_login_failure(key: str) -> None:
    now = monotonic()
    with _rate_lock:
        _failures[key].append(now)
        if len(_failures[key]) >= _MAX_FAILURES:
            _blocked_until[key] = now + _BLOCK_SECONDS


def _clear_login_failures(key: str) -> None:
    with _rate_lock:
        _failures.pop(key, None)
        _blocked_until.pop(key, None)


@router.post("/login", response_model=TokenOut)
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db_dep)):
    key = _client_key(request)
    _check_login_limit(key)
    token = auth.create_token(body.password, db)
    if token is None:
        _record_login_failure(key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    _clear_login_failures(key)
    return TokenOut(token=token)


@router.get("/check")
def check( _: None = Depends(auth.require_admin)):
    return {"ok": True}
