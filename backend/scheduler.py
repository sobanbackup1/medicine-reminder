"""APScheduler engine and medication reminder jobs.

Design
------
A single BackgroundScheduler runs inside the FastAPI process.  Three daily
cron jobs anchor the schedule:

  1. reminder_start   - fires at REMINDER_START_TIME; reconciles today's
                        state and starts the repeating reminder job.
  2. emergency_notify - fires at EMERGENCY_TIME; sends the emergency Bark
                        notification if the patient still hasn't acted.
  3. midnight_close   - fires at 00:00; stops reminders and opens the new day
                        as pending. Missed is recorded only by the patient.

The repeating reminder is a separate IntervalJob that is added/removed
dynamically so it only runs between start and confirmation.

Restart recovery
----------------
On startup, ``reconcile()`` inspects today's MedicationLog and the current
Tokyo time, then re-creates whichever jobs *should* be running right now.
This means a reboot at 9:50 PM, 10:45 PM, or 11:58 PM all recover correctly
without losing the reminder cycle.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED

from . import crud
from .database import get_db
from .tz import now_local, today_local, local_time_today, TZ
from .bark import send_bark
from .patient_access import patient_link

logger = logging.getLogger(__name__)

scheduler: Optional[BackgroundScheduler] = None
REPEAT_JOB_ID = "repeating_reminder"


# --------------------------------------------------------------------------- #
# Lifecycle
# --------------------------------------------------------------------------- #
def start_scheduler() -> None:
    global scheduler
    if scheduler is not None:
        return
    scheduler = BackgroundScheduler(timezone=str(TZ))
    scheduler.add_listener(_on_job_error, EVENT_JOB_ERROR | EVENT_JOB_MISSED)
    scheduler.start()
    _schedule_anchor_jobs()
    reconcile()
    logger.info("Scheduler started (timezone=%s)", TZ)


def shutdown_scheduler() -> None:
    global scheduler
    if scheduler:
        scheduler.shutdown(wait=False)
        scheduler = None


def _schedule_anchor_jobs() -> None:
    """(Re)create the three daily cron jobs from current settings."""
    with get_db() as db:
        s = crud.get_settings(db)

    # reminder start
    start_h, start_m = s.reminder_start_time.split(":")
    scheduler.add_job(
        on_reminder_start,
        CronTrigger(hour=int(start_h), minute=int(start_m), timezone=str(TZ)),
        id="reminder_start",
        replace_existing=True,
    )

    # emergency
    em_h, em_m = s.emergency_time.split(":")
    scheduler.add_job(
        on_emergency,
        CronTrigger(hour=int(em_h), minute=int(em_m), timezone=str(TZ)),
        id="emergency_notify",
        replace_existing=True,
    )

    # midnight close
    scheduler.add_job(
        on_midnight_close,
        CronTrigger(hour=0, minute=0, timezone=str(TZ)),
        id="midnight_close",
        replace_existing=True,
    )


def refresh_anchor_jobs() -> None:
    """Called after settings change to rebuild cron jobs with new times."""
    if scheduler:
        _schedule_anchor_jobs()


# --------------------------------------------------------------------------- #
# Reconciliation (restart recovery)
# --------------------------------------------------------------------------- #
def reconcile() -> None:
    """Rebuild today's runtime state after a restart.

    Called once at startup and safe to call repeatedly.  Decides whether the
    repeating reminder should be running right now based on today's log and
    the current Tokyo time.
    """
    if scheduler is None:
        return
    now = now_local()
    today = today_local()

    with get_db() as db:
        s = crud.get_settings(db)
        log = crud.get_or_create_today(db, today)
        log_event(db, "scheduler", f"Reconcile at {now.isoformat()}: status={log.status}")

        reminder_start = local_time_today(s.reminder_start_time)
        emergency_time = local_time_today(s.emergency_time)
        midnight = local_time_today("00:00")  # next midnight
        if midnight < now:
            midnight = midnight.replace(day=midnight.day + 1)

        acted = log.status != "pending"

        # If the patient already acted, ensure no repeating reminder runs.
        if acted:
            stop_repeating_reminder()
            return

        # If we're past reminder start but before midnight/emergency, the
        # repeating reminder should be running — start it if it isn't.
        if now >= reminder_start and now < emergency_time:
            start_repeating_reminder(s.reminder_interval_minutes)
        elif now >= emergency_time and now < midnight:
            # past emergency time — emergency should have fired; if it hasn't
            # (e.g. server was down), fire it now.
            if not _emergency_sent_today(db, today):
                on_emergency()
        else:
            stop_repeating_reminder()


def _emergency_sent_today(db, today) -> bool:
    logs = crud.emergency_for_day(db, today)
    return any(l.success for l in logs)


# --------------------------------------------------------------------------- #
# Repeating reminder
# --------------------------------------------------------------------------- #
def start_repeating_reminder(interval_minutes: int) -> None:
    if scheduler is None:
        return
    if scheduler.get_job(REPEAT_JOB_ID) is not None:
        return  # already running
    scheduler.add_job(
        send_reminder,
        IntervalTrigger(minutes=interval_minutes),
        id=REPEAT_JOB_ID,
        replace_existing=True,
        next_run_time=now_local(),  # fire immediately, then on interval
    )
    logger.info("Repeating reminder started (every %d min)", interval_minutes)


def stop_repeating_reminder() -> None:
    if scheduler and scheduler.get_job(REPEAT_JOB_ID):
        scheduler.remove_job(REPEAT_JOB_ID)
        logger.info("Repeating reminder stopped")


def send_reminder() -> None:
    """Send one Bark reminder to the patient (if they haven't acted)."""
    today = today_local()
    with get_db() as db:
        log = crud.get_or_create_today(db, today)
        if log.status != "pending":
            stop_repeating_reminder()
            return
        s = crud.get_settings(db)
        result = send_bark(
            s.patient_bark_key,
            s.notification_title,
            s.notification_body,
            url=patient_link(s.website_url),
        )
        crud.add_reminder_log(db, today, result.success, result.error)
        crud.log_event(
            db,
            "reminder",
            f"Reminder sent success={result.success} err={result.error}",
        )


# --------------------------------------------------------------------------- #
# Anchor job callbacks
# --------------------------------------------------------------------------- #
def on_reminder_start() -> None:
    today = today_local()
    with get_db() as db:
        log = crud.get_or_create_today(db, today)
        crud.log_event(db, "scheduler", f"Reminder start fired; status={log.status}")
        if log.status != "pending":
            return
        s = crud.get_settings(db)
    start_repeating_reminder(s.reminder_interval_minutes)
    send_reminder()


def on_emergency() -> None:
    today = today_local()
    with get_db() as db:
        log = crud.get_or_create_today(db, today)
        if log.status != "pending":
            return
        s = crud.get_settings(db)
        result = send_bark(
            s.emergency_bark_key,
            "Medication Not Confirmed",
            "She has not confirmed taking today's medication. Please check with her.",
            url=patient_link(s.website_url),
        )
        crud.add_emergency_log(db, today, result.success, result.error)
        crud.log_event(
            db,
            "emergency",
            f"Emergency notification sent success={result.success} err={result.error}",
        )
    stop_repeating_reminder()


def on_midnight_close() -> None:
    today = today_local()
    with get_db() as db:
        crud.get_or_create_today(db, today)
        crud.log_event(db, "scheduler", f"Midnight close: opened {today} as pending")
    stop_repeating_reminder()
    # prune old logs
    with get_db() as db:
        s = crud.get_settings(db)
        removed = crud.prune_old_logs(db, s.retention_days)
        if removed:
            crud.log_event(db, "scheduler", f"Pruned {removed} logs older than {s.retention_days}d")


# --------------------------------------------------------------------------- #
# Scheduler event listener
# --------------------------------------------------------------------------- #
def _on_job_error(event) -> None:
    with get_db() as db:
        crud.log_event(
            db,
            "error",
            f"Scheduler job error: {getattr(event, 'exception', event)}",
        )
    logger.error("Scheduler job error: %s", event)


def log_event(db, event_type: str, message: str) -> None:
    crud.log_event(db, event_type, message)
