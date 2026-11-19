"""Short-lived access links for the patient-facing API."""

from datetime import datetime, time, timedelta
from urllib.parse import quote, urlsplit, urlunsplit

import jwt
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .auth import verify_token
from .config import env
from .tz import TZ, today_local

_admin_bearer = HTTPBearer(auto_error=False)


def create_patient_token() -> str:
    today = today_local()
    # Keep yesterday's link usable before today's notification arrives.
    expires = datetime.combine(today + timedelta(days=2), time.min, TZ)
    return jwt.encode(
        {"sub": "patient", "day": today.isoformat(), "exp": expires},
        env.secret_key,
        algorithm="HS256",
    )


def patient_link(base_url: str) -> str:
    """Put the capability in the URL fragment, not in HTTP requests or referrers."""
    parts = urlsplit(base_url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query,
                       "patient_token=" + quote(create_patient_token(), safe="")))


def require_patient_access(
    patient_token: str | None = Header(None, alias="X-Patient-Token"),
    admin: HTTPAuthorizationCredentials | None = Depends(_admin_bearer),
) -> None:
    if admin and verify_token(admin.credentials):
        return
    if patient_token:
        try:
            claims = jwt.decode(patient_token, env.secret_key, algorithms=["HS256"])
            today = today_local()
            valid_days = {today.isoformat(), (today - timedelta(days=1)).isoformat()}
            if claims.get("sub") == "patient" and claims.get("day") in valid_days:
                return
        except jwt.PyJWTError:
            pass
    raise HTTPException(status_code=401, detail="Open today's reminder link to access this page")
