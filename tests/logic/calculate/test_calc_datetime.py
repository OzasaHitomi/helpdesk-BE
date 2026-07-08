from datetime import datetime
from zoneinfo import ZoneInfo

from freezegun import freeze_time

from helpdesk_be.logic.calculate.calc_datetime import (
    get_now,
)


@freeze_time("2026-05-01 12:00:00+00:00")
def test_get_now() -> None:
    expected = datetime(
        year=2026, month=5, day=1, hour=21, minute=0, second=0, tzinfo=ZoneInfo("Asia/Tokyo")
    )
    result = get_now()

    assert expected == result
    assert result.tzinfo == ZoneInfo("Asia/Tokyo")
