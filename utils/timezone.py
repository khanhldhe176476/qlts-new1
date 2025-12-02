from datetime import datetime, timedelta

_VN_OFFSET = timedelta(hours=7)


def now_vn() -> datetime:
    """Return current datetime in Vietnam timezone (UTC+7)."""
    return datetime.utcnow() + _VN_OFFSET


def today_vn():
    """Return today's date in Vietnam timezone."""
    return now_vn().date()

