from datetime import datetime, timedelta, timezone


def get_dushanbe_time() -> datetime:
    dushanbe_timezone = timezone(timedelta(hours=5))
    return datetime.now(dushanbe_timezone)
