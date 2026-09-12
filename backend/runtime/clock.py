from datetime import datetime
from zoneinfo import ZoneInfo
import os

# Default to Asia/Kolkata or use environment variable if provided
DEFAULT_TIMEZONE = os.getenv("TZ", "Asia/Kolkata")

def get_current_datetime() -> datetime:
    return datetime.now(ZoneInfo(DEFAULT_TIMEZONE))

def get_current_date() -> str:
    return get_current_datetime().strftime("%Y-%m-%d")

def get_current_time() -> str:
    return get_current_datetime().strftime("%H:%M:%S")

def get_timezone() -> str:
    return DEFAULT_TIMEZONE

def get_day_of_week() -> str:
    return get_current_datetime().strftime("%A")
