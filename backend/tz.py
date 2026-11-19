"""Timezone helpers.

All scheduling logic operates in Asia/Tokyo regardless of the server's local
timezone, so the patient's 10 PM is always 10 PM Tokyo time.
"""

from __future__ import annotations

from datetime import datetime, date, time
from zoneinfo import ZoneInfo

from .config import env

TZ = ZoneInfo(env.timezone)


def now_local() -> datetime:
    return datetime.now(TZ)


def today_local() -> date:
    return now_local().date()


def local_time_today(hhmm: str) -> datetime:
    """Return the datetime for today at the given HH:MM in the app timezone."""
    h, m = hhmm.split(":")
    return datetime.combine(today_local(), time(int(h), int(m), 0), TZ)
