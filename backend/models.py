"""SQLAlchemy ORM models.

Tables:
  settings          - single-row table of editable app settings
  medication_log    - one row per patient action per day
  reminder_log      - every Bark reminder attempt
  emergency_log     - emergency contact notification attempts
  event_log         - generic application / scheduler / error events
  backup_log        - database backup history
"""

from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Boolean,
    Text,
    Index,
)
from sqlalchemy.sql import func

from .database import Base


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, default=1)
    medicine_name = Column(String(100), nullable=False, default="Medication")
    medication_time = Column(String(5), nullable=False, default="22:00")
    reminder_start_time = Column(String(5), nullable=False, default="22:30")
    reminder_interval_minutes = Column(Integer, nullable=False, default=2)
    emergency_time = Column(String(5), nullable=False, default="23:55")
    patient_bark_key = Column(String(255), nullable=False, default="")
    emergency_bark_key = Column(String(255), nullable=False, default="")
    notification_title = Column(String(200), nullable=False, default="Medication Reminder")
    notification_body = Column(Text, nullable=False, default="It is time to take your medication.")
    website_url = Column(String(255), nullable=False, default="http://localhost:8000")
    admin_password = Column(String(255), nullable=False, default="admin")
    retention_days = Column(Integer, nullable=False, default=90)


class MedicationLog(Base):
    __tablename__ = "medication_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_date = Column(Date, nullable=False, unique=True, index=True)
    status = Column(String(20), nullable=False)  # taken | forgot | missed | pending
    action_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (Index("ix_med_log_date", "log_date"),)


class ReminderLog(Base):
    __tablename__ = "reminder_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_date = Column(Date, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=False, server_default=func.now())
    success = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)


class EmergencyLog(Base):
    __tablename__ = "emergency_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_date = Column(Date, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=False, server_default=func.now())
    success = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)


class EventLog(Base):
    __tablename__ = "event_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False)  # startup, scheduler, error, button, db
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class BackupLog(Base):
    __tablename__ = "backup_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
