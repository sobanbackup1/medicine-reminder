"""Simple admin authentication.

The admin password lives in the settings table (editable from the UI).  We
issue a signed JWT with a 12-hour expiry.  The patient never logs in.
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import env
from .database import get_db_dep
from . import crud

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"
TOKEN_TTL = timedelta(hours=12)


def create_token(password: str, db) -> Optional[str]:
    settings = crud.get_settings(db)
    if not secrets.compare_digest(password, settings.admin_password):
        return None
    payload = {
        "sub": "admin",
        "exp": datetime.now(timezone.utc) + TOKEN_TTL,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, env.secret_key, algorithm=ALGORITHM)


def verify_token(token: str) -> bool:
    try:
        claims = jwt.decode(token, env.secret_key, algorithms=[ALGORITHM])
        return claims.get("sub") == "admin"
    except jwt.PyJWTError:
        return False


def require_admin(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> None:
    if creds is None or not creds.credentials or not verify_token(creds.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin token",
        )
