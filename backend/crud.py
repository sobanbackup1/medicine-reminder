"""CRUD helpers for all database operations.

Keeping query logic here keeps routers thin and makes the scheduler's
reconciliation logic easy to reason about.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Sequence

from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from .models import (
    Setting,
    MedicationLog,
    ReminderLog,
    EmergencyLog,
    EventLog,
    BackupLog,
)
from .config import env


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #
def get_settings(db: Session) -> Setting:
    row = db.get(Setting, 1)
    if row is None:
        row = Setting(
            id=1,
            medicine_name=env.default_medicine_name,
            medication_time=env.default_medication_time,
            reminder_start_time=env.default_reminder_start,
            reminder_interval_minutes=env.default_reminder_interval,
            emergency_time=env.default_emergency_time,
            patient_bark_key=env.default_patient_bark_key,
            emergency_bark_key=env.default_emergency_bark_key,
            notification_title=env.default_notif_title,
            notification_body=env.default_notif_body,
            website_url=env.website_url,
            admin_password=env.default_admin_password,
            retention_days=90,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def update_settings(db: Session, updates: dict) -> Setting:
    row = get_settings(db)
    for key, value in updates.items():
        if value is not None and hasattr(row, key):
            setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


# --------------------------------------------------------------------------- #
# Medication log
# --------------------------------------------------------------------------- #
def get_or_create_today(db: Session, today: date | None = None) -> MedicationLog:
    if today is None:
        today = _today()
    row = db.execute(
        select(MedicationLog).where(MedicationLog.log_date == today)
    ).scalar_one_or_none()
    if row is None:
        row = MedicationLog(log_date=today, status="pending", action_timestamp=None)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def set_status(
    db: Session,
    today: date | None,
    status: str,
    action_timestamp: datetime | None = None,
) -> MedicationLog:
    if today is None:
        today = _today()
    row = get_or_create_today(db, today)
    row.status = status
    row.action_timestamp = action_timestamp or datetime.now()
    db.commit()
    db.refresh(row)
    return row


def reset_today(db: Session, today: date | None = None) -> MedicationLog:
    """Return today's medication record to pending for an explicit undo."""
    if today is None:
        today = _today()
    row = get_or_create_today(db, today)
    row.status = "pending"
    row.action_timestamp = None
    db.commit()
    db.refresh(row)
    return row


def get_log_by_date(db: Session, day: date) -> MedicationLog | None:
    return db.execute(
        select(MedicationLog).where(MedicationLog.log_date == day)
    ).scalar_one_or_none()


def update_log_by_id(
    db: Session, log_id: int, status: str, action_timestamp: datetime | None
) -> MedicationLog | None:
    row = db.get(MedicationLog, log_id)
    if row is None:
        return None
    row.status = status
    row.action_timestamp = action_timestamp
    db.commit()
    db.refresh(row)
    return row


def list_logs_range(db: Session, start: date, end: date) -> Sequence[MedicationLog]:
    return db.execute(
        select(MedicationLog)
        .where(MedicationLog.log_date >= start)
        .where(MedicationLog.log_date <= end)
        .order_by(MedicationLog.log_date)
    ).scalars().all()


def list_all_logs(db: Session) -> Sequence[MedicationLog]:
    return db.execute(
        select(MedicationLog).order_by(MedicationLog.log_date.desc())
    ).scalars().all()


def prune_old_logs(db: Session, retention_days: int = 90) -> int:
    cutoff = _today() - timedelta(days=retention_days)
    result = db.execute(
        MedicationLog.__table__.delete().where(MedicationLog.log_date < cutoff)
    )
    db.commit()
    return result.rowcount


# --------------------------------------------------------------------------- #
# Reminder / emergency logs
# --------------------------------------------------------------------------- #
def add_reminder_log(db: Session, day: date, success: bool, error: str | None) -> None:
    db.add(ReminderLog(log_date=day, success=success, error_message=error))
    db.commit()


def add_emergency_log(db: Session, day: date, success: bool, error: str | None) -> None:
    db.add(EmergencyLog(log_date=day, success=success, error_message=error))
    db.commit()


def reminders_for_day(db: Session, day: date) -> Sequence[ReminderLog]:
    return db.execute(
        select(ReminderLog).where(ReminderLog.log_date == day).order_by(ReminderLog.sent_at)
    ).scalars().all()


def emergency_for_day(db: Session, day: date) -> Sequence[EmergencyLog]:
    return db.execute(
        select(EmergencyLog).where(EmergencyLog.log_date == day).order_by(EmergencyLog.sent_at)
    ).scalars().all()


def list_reminder_logs(db: Session, limit: int = 200) -> Sequence[ReminderLog]:
    return db.execute(
        select(ReminderLog).order_by(desc(ReminderLog.sent_at)).limit(limit)
    ).scalars().all()


def list_emergency_logs(db: Session, limit: int = 200) -> Sequence[EmergencyLog]:
    return db.execute(
        select(EmergencyLog).order_by(desc(EmergencyLog.sent_at)).limit(limit)
    ).scalars().all()


# --------------------------------------------------------------------------- #
# Event log
# --------------------------------------------------------------------------- #
def log_event(db: Session, event_type: str, message: str) -> None:
    try:
        db.add(EventLog(event_type=event_type, message=message))
        db.commit()
    except Exception:
        db.rollback()


def list_events(db: Session, limit: int = 200) -> Sequence[EventLog]:
    return db.execute(
        select(EventLog).order_by(desc(EventLog.created_at)).limit(limit)
    ).scalars().all()


# --------------------------------------------------------------------------- #
# Backup log
# --------------------------------------------------------------------------- #
def add_backup_log(
    db: Session, filename: str, file_size: int | None, success: bool, error: str | None
) -> None:
    db.add(
        BackupLog(
            filename=filename,
            file_size=file_size,
            success=success,
            error_message=error,
        )
    )
    db.commit()


def list_backups(db: Session) -> Sequence[BackupLog]:
    return db.execute(
        select(BackupLog).order_by(desc(BackupLog.created_at))
    ).scalars().all()


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #
def compute_statistics(db: Session) -> dict:
    logs = db.execute(
        select(MedicationLog).order_by(MedicationLog.log_date.desc())
    ).scalars().all()

    total_taken = sum(1 for l in logs if l.status == "taken")
    total_missed = sum(1 for l in logs if l.status == "missed")
    total_forgot = sum(1 for l in logs if l.status == "forgot")
    total = total_taken + total_missed + total_forgot
    adherence = round((total_taken / total * 100), 1) if total else 0.0

    # streaks (consecutive "taken" ending today or yesterday)
    taken_dates = {l.log_date for l in logs if l.status == "taken"}
    today = _today()
    current_streak = 0
    cursor = today
    if today not in taken_dates:
        cursor = today - timedelta(days=1)
    while cursor in taken_dates:
        current_streak += 1
        cursor -= timedelta(days=1)

    # longest streak
    sorted_taken = sorted(taken_dates)
    longest = 0
    run = 0
    prev = None
    for d in sorted_taken:
        if prev is not None and (d - prev).days == 1:
            run += 1
        else:
            run = 1
        longest = max(longest, run)
        prev = d

    # average confirmation time (minutes from medication_time to action)
    settings = get_settings(db)
    med_hour, med_min = _parse_hhmm(settings.medication_time)
    deltas = []
    for l in logs:
        if l.status == "taken" and l.action_timestamp:
            med_dt = datetime(l.log_date.year, l.log_date.month, l.log_date.day, med_hour, med_min)
            delta = (l.action_timestamp - med_dt).total_seconds() / 60.0
            if delta >= 0:
                deltas.append(delta)
    avg_minutes = round(sum(deltas) / len(deltas), 1) if deltas else None

    return {
        "current_streak": current_streak,
        "longest_streak": longest,
        "adherence_percentage": adherence,
        "total_taken": total_taken,
        "total_missed": total_missed,
        "total_forgot": total_forgot,
        "average_confirmation_minutes": avg_minutes,
    }


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _today() -> date:
    from .tz import today_local
    return today_local()


def _parse_hhmm(s: str) -> tuple[int, int]:
    h, m = s.split(":")
    return int(h), int(m)
