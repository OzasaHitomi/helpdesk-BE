from datetime import datetime
from zoneinfo import ZoneInfo


def get_now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Tokyo"))
