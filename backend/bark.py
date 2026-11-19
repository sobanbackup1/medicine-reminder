"""Bark push notification client.

Bark (https://bark.day.app) delivers a single-device push via a simple HTTPS
GET/POST.  We POST JSON for richer payloads (sound, group, url).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

BARK_SERVER = "https://api.day.app"


@dataclass
class BarkResult:
    success: bool
    error: str | None = None


def send_bark(
    device_key: str,
    title: str,
    body: str,
    url: str | None = None,
    *,
    sound: str = "bell",
    timeout: float = 10.0,
) -> BarkResult:
    """Send a Bark notification.

    Returns BarkResult(success=False, error=...) on failure rather than
    raising, so the scheduler can log and continue.
    """
    if not device_key:
        return BarkResult(False, "missing device key")

    endpoint = f"{BARK_SERVER}/{device_key}"
    payload: dict[str, object] = {
        "title": title,
        "body": body,
        "sound": sound,
    }
    if url:
        payload["url"] = url

    try:
        resp = httpx.post(endpoint, json=payload, timeout=timeout)
        if 200 <= resp.status_code < 300:
            return BarkResult(True)
        return BarkResult(False, f"HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as exc:  # network / DNS / timeout
        return BarkResult(False, str(exc))
