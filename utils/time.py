# utils/time.py
"""
Time utility functions for GodEye.
Handles standardized timestamp generation, normalization, and conversion.
"""

from datetime import datetime, timezone
import re

def to_iso(dt=None) -> str:
    """
    Convert a datetime object (or current time) to an ISO-8601 UTC string.

    Args:
        dt (datetime, optional): A datetime object. Defaults to current UTC time.

    Returns:
        str: ISO 8601 formatted UTC timestamp.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

def from_iso(iso_str: str) -> datetime:
    """
    Convert an ISO-8601 timestamp string back to a datetime object.

    Args:
        iso_str (str): ISO timestamp (e.g., '2025-10-11T10:45:23.123456+00:00')

    Returns:
        datetime: Parsed datetime object in UTC.
    """
    try:
        return datetime.fromisoformat(iso_str)
    except Exception:
        # handle malformed ISO strings
        cleaned = re.sub(r'Z$', '+00:00', iso_str)
        return datetime.fromisoformat(cleaned)

def utc_now() -> datetime:
    """
    Return the current UTC datetime object.
    """
    return datetime.now(timezone.utc)

def human_readable(dt=None) -> str:
    """
    Return human-friendly timestamp like '2025-10-11 10:45 UTC'.

    Args:
        dt (datetime, optional): datetime to format. Defaults to now.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M UTC")
