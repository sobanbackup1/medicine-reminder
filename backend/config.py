"""Application configuration loaded from environment variables.

All configurable values live in the .env file at the project root.  The
database is the single source of truth for runtime settings (admin-editable),
but we also seed those database rows from these environment defaults on first
run so the app works out-of-the-box.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# .env lives at the project root (one level above backend/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _get(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class EnvConfig:
    # MySQL
    mysql_host: str = _get("MYSQL_HOST", "127.0.0.1")
    mysql_port: int = _get_int("MYSQL_PORT", 3306)
    mysql_user: str = _get("MYSQL_USER", "medication")
    mysql_password: str = _get("MYSQL_PASSWORD")
    mysql_database: str = _get("MYSQL_DATABASE", "medication_reminder")

    # App
    app_host: str = _get("APP_HOST", "0.0.0.0")
    app_port: int = _get_int("APP_PORT", 8000)
    website_url: str = _get("WEBSITE_URL", "http://localhost:8000")

    # Auth
    secret_key: str = _get("SECRET_KEY")
    default_admin_password: str = _get("ADMIN_PASSWORD")

    # Defaults seeded into the settings table
    default_medicine_name: str = _get("MEDICINE_NAME", "Medication")
    default_medication_time: str = _get("MEDICATION_TIME", "22:00")
    default_reminder_start: str = _get("REMINDER_START_TIME", "22:30")
    default_reminder_interval: int = _get_int("REMINDER_INTERVAL", 2)
    default_emergency_time: str = _get("EMERGENCY_TIME", "23:55")
    default_patient_bark_key: str = _get("PATIENT_BARK_KEY", "")
    default_emergency_bark_key: str = _get("EMERGENCY_BARK_KEY", "")
    default_notif_title: str = _get("NOTIFICATION_TITLE", "Medication Reminder")
    default_notif_body: str = _get(
        "NOTIFICATION_MESSAGE",
        "It is time to take your medication. Please confirm.",
    )

    # Timezone for all scheduling logic
    timezone: str = _get("TIMEZONE", "Asia/Tokyo")

    # Paths
    backup_dir: str = _get("BACKUP_DIR", str(PROJECT_ROOT / "backups"))

    def __post_init__(self) -> None:
        if not self.mysql_password or self.mysql_password == "medication":
            raise RuntimeError("Set a strong MYSQL_PASSWORD in .env")
        if len(self.secret_key) < 32 or self.secret_key == "change-me-in-production":
            raise RuntimeError("Set a strong SECRET_KEY in .env")
        if len(self.default_admin_password) < 16 or self.default_admin_password == "admin":
            raise RuntimeError("Set a strong ADMIN_PASSWORD in .env")


env = EnvConfig()
