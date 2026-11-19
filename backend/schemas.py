"""Pydantic schemas for API request/response validation."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["taken", "forgot", "missed", "pending"]


class SettingsOut(BaseModel):
    medicine_name: str
    medication_time: str
    reminder_start_time: str
    reminder_interval_minutes: int
    emergency_time: str
    # Secrets are intentionally omitted from normal settings responses.
    patient_bark_key: str | None = None
    emergency_bark_key: str | None = None
    notification_title: str
    notification_body: str
    website_url: str
    admin_password: str | None = None
    retention_days: int

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    medicine_name: str | None = None
    medication_time: str | None = None
    reminder_start_time: str | None = None
    reminder_interval_minutes: int | None = Field(default=None, ge=1, le=1440)
    emergency_time: str | None = None
    patient_bark_key: str | None = None
    emergency_bark_key: str | None = None
    notification_title: str | None = None
    notification_body: str | None = None
    website_url: str | None = None
    admin_password: str | None = Field(default=None, min_length=16, max_length=255)
    retention_days: int | None = Field(default=None, ge=1, le=3650)


class MedicationLogOut(BaseModel):
    id: int
    log_date: date
    status: Status
    action_timestamp: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MedicationLogUpdate(BaseModel):
    status: Status
    action_timestamp: datetime | None = None


class ActionRequest(BaseModel):
    action: Literal["taken", "forgot"]


class TodayStatusOut(BaseModel):
    log_date: date
    status: Status
    action_timestamp: datetime | None
    medicine_name: str
    medication_time: str
    already_acted: bool


class LoginRequest(BaseModel):
    password: str = Field(max_length=255)


class TokenOut(BaseModel):
    token: str


class CalendarDay(BaseModel):
    log_date: date
    status: Status | None
    action_timestamp: datetime | None


class StatisticsOut(BaseModel):
    current_streak: int
    longest_streak: int
    adherence_percentage: float
    total_taken: int
    total_missed: int
    total_forgot: int
    average_confirmation_minutes: float | None


class LogOut(BaseModel):
    id: int
    log_date: date | None
    sent_at: datetime
    success: bool
    error_message: str | None


class EventOut(BaseModel):
    id: int
    event_type: str
    message: str
    created_at: datetime


class BackupOut(BaseModel):
    id: int
    created_at: datetime
    filename: str
    file_size: int | None
    success: bool
    error_message: str | None
