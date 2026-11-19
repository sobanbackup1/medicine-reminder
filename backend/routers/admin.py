"""Admin dashboard data: today, calendar, statistics, logs."""

from __future__ import annotations

from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud
from ..auth import require_admin
from ..database import get_db_dep
from ..schemas import (
    CalendarDay,
    MedicationLogOut,
    MedicationLogUpdate,
    StatisticsOut,
    LogOut,
    EventOut,
)
from ..tz import today_local

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/today", response_model=MedicationLogOut)
def admin_today(db: Session = Depends(get_db_dep)):
    log = crud.get_or_create_today(db, today_local())
    return log


@router.get("/calendar", response_model=List[CalendarDay])
def calendar(months: int = 3, db: Session = Depends(get_db_dep)):
    today = today_local()
    start = today - timedelta(days=months * 31)
    logs = crud.list_logs_range(db, start, today)
    by_date = {l.log_date: l for l in logs}

    days: List[CalendarDay] = []
    cursor = start
    while cursor <= today:
        log = by_date.get(cursor)
        days.append(
            CalendarDay(
                log_date=cursor,
                status=log.status if log else None,
                action_timestamp=log.action_timestamp if log else None,
            )
        )
        cursor += timedelta(days=1)
    return days


@router.get("/statistics", response_model=StatisticsOut)
def statistics(db: Session = Depends(get_db_dep)):
    return StatisticsOut(**crud.compute_statistics(db))


@router.get("/logs/reminders", response_model=List[LogOut])
def reminder_logs(limit: int = 200, db: Session = Depends(get_db_dep)):
    rows = crud.list_reminder_logs(db, limit)
    return [
        LogOut(
            id=r.id,
            log_date=r.log_date,
            sent_at=r.sent_at,
            success=r.success,
            error_message=r.error_message
        )
        for r in rows
    ]


@router.get("/logs/emergencies", response_model=List[LogOut])
def emergency_logs(limit: int = 200, db: Session = Depends(get_db_dep)):
    rows = crud.list_emergency_logs(db, limit)
    return [
        LogOut(
            id=r.id,
            log_date=r.log_date,
            sent_at=r.sent_at,
            success=r.success,
            error_message=r.error_message
        )
        for r in rows
    ]


@router.get("/logs/events", response_model=List[EventOut])
def event_logs(limit: int = 200, db: Session = Depends(get_db_dep)):
    rows = crud.list_events(db, limit)
    return [
        EventOut(
            id=r.id,
            event_type=r.event_type,
            message=r.message,
            created_at=r.created_at
        )
        for r in rows
    ]


@router.get("/logs/{log_id}", response_model=MedicationLogOut)
def get_log(log_id: int, db: Session = Depends(get_db_dep)):
    log = crud.get_log_by_id(db, log_id) if hasattr(crud, "get_log_by_id") else None
    from ..models import MedicationLog
    log = db.get(MedicationLog, log_id)
    if log is None:
        raise HTTPException(404, "Log not found")
    return log


@router.put("/logs/{log_id}", response_model=MedicationLogOut)
def update_log(log_id: int, body: MedicationLogUpdate, db: Session = Depends(get_db_dep)):
    log = crud.update_log_by_id(db, log_id, body.status, body.action_timestamp)
    if log is None:
        raise HTTPException(404, "Log not found")
    crud.log_event(db, "admin", f"Admin edited log {log_id} -> {body.status}")
    return log