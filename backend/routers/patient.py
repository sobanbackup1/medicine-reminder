"""Patient-facing API: today's status and the TAKEN / FORGOT buttons.

The patient uses a daily access link included in Bark reminders.
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from .. import crud, scheduler
from ..database import get_db_dep
from ..schemas import ActionRequest, CalendarDay, TodayStatusOut
from ..patient_access import require_patient_access
from ..patient_access import create_patient_token
from ..tz import now_local, today_local

router = APIRouter(prefix="/api/patient", tags=["patient"], dependencies=[Depends(require_patient_access)])


@router.get("/today", response_model=TodayStatusOut)
def get_today(response: Response, db: Session = Depends(get_db_dep)):
    # A device that opened a reminder can keep its access current each day.
    response.headers["X-Patient-Token"] = create_patient_token()
    today = today_local()
    log = crud.get_or_create_today(db, today)
    s = crud.get_settings(db)
    already = log.status != "pending"
    return TodayStatusOut(
        log_date=log.log_date,
        status=log.status,
        action_timestamp=log.action_timestamp,
        medicine_name=s.medicine_name,
        medication_time=s.medication_time,
        already_acted=already,
    )


@router.get("/calendar", response_model=list[CalendarDay])
def patient_calendar(days: int = 28, start_date: date | None = None, db: Session = Depends(get_db_dep)):
    """Return the current 28-day pill sheet, starting one day before today."""
    if days < 1 or days > 90:
        raise HTTPException(400, "days must be between 1 and 90")
    today = today_local()
    start = start_date or (today - timedelta(days=1))
    end = start + timedelta(days=days - 1)
    logs = crud.list_logs_range(db, start, end)
    by_date = {log.log_date: log for log in logs}
    result = []
    cursor = start
    while cursor <= end:
        log = by_date.get(cursor)
        result.append(
            CalendarDay(
                log_date=cursor,
                status=log.status if log else None,
                action_timestamp=log.action_timestamp if log else None,
            )
        )
        cursor += timedelta(days=1)
    return result


@router.post("/action", response_model=TodayStatusOut)
def record_action(body: ActionRequest, db: Session = Depends(get_db_dep)):
    today = today_local()
    log = crud.get_or_create_today(db, today)

    if log.status != "pending":
        raise HTTPException(400, "Already recorded for today")

    crud.set_status(db, today, body.action, now_local())
    crud.log_event(db, "button", f"Patient pressed {body.action.upper()} at {now_local().isoformat()}")
    scheduler.stop_repeating_reminder()

    log = crud.get_or_create_today(db, today)
    s = crud.get_settings(db)
    return TodayStatusOut(
        log_date=log.log_date,
        status=log.status,
        action_timestamp=log.action_timestamp,
        medicine_name=s.medicine_name,
        medication_time=s.medication_time,
        already_acted=True,
    )


@router.post("/missed", response_model=TodayStatusOut)
def mark_missed(db: Session = Depends(get_db_dep)):
    """Record that today's medication was missed and stop reminders."""
    today = today_local()
    log = crud.get_or_create_today(db, today)
    if log.status != "pending":
        raise HTTPException(400, "Already recorded for today")
    crud.set_status(db, today, "missed", now_local())
    crud.log_event(db, "button", f"Patient marked today's medication missed at {now_local().isoformat()}")
    scheduler.stop_repeating_reminder()
    log = crud.get_or_create_today(db, today)
    s = crud.get_settings(db)
    return TodayStatusOut(
        log_date=log.log_date,
        status=log.status,
        action_timestamp=log.action_timestamp,
        medicine_name=s.medicine_name,
        medication_time=s.medication_time,
        already_acted=True,
    )


@router.post("/undo", response_model=TodayStatusOut)
def undo_today(db: Session = Depends(get_db_dep)):
    """Clear today's action and return it to pending."""
    today = today_local()
    crud.reset_today(db, today)
    crud.log_event(db, "button", f"Patient undid today's medication action at {now_local().isoformat()}")
    scheduler.reconcile()
    log = crud.get_or_create_today(db, today)
    s = crud.get_settings(db)
    return TodayStatusOut(
        log_date=log.log_date,
        status=log.status,
        action_timestamp=log.action_timestamp,
        medicine_name=s.medicine_name,
        medication_time=s.medication_time,
        already_acted=False,
    )
