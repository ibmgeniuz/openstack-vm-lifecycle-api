from datetime import datetime, timezone


def get_datetime_now() -> datetime:
    """Return the current date and time in UTC timezone"""
    return datetime.now(tz=timezone.utc)