"""Settings CRUD (admin only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, scheduler
from ..auth import require_admin
from ..database import get_db_dep
from ..schemas import SettingsOut, SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"], dependencies=[Depends(require_admin)])


def _safe_settings(settings):
    output = SettingsOut.model_validate(settings)
    return output.model_copy(update={
        "patient_bark_key": None,
        "emergency_bark_key": None,
        "admin_password": None,
    })


@router.get("", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db_dep)):
    return _safe_settings(crud.get_settings(db))


@router.put("", response_model=SettingsOut)
def update_settings(body: SettingsUpdate, db: Session = Depends(get_db_dep)):
    updates = body.model_dump(exclude_none=True)
    s = crud.update_settings(db, updates)
    # rebuild scheduler cron jobs if times changed
    scheduler.refresh_anchor_jobs()
    crud.log_event(db, "admin", "Admin updated settings")
    return _safe_settings(s)
