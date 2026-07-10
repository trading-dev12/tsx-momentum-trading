from datetime import datetime
from zoneinfo import ZoneInfo

from core.market_hours import get_tsx_market_status


toronto = ZoneInfo("America/Toronto")

test_times = [
    datetime(2026, 7, 10, 8, 30, tzinfo=toronto),
    datetime(2026, 7, 10, 9, 30, tzinfo=toronto),
    datetime(2026, 7, 10, 12, 0, tzinfo=toronto),
    datetime(2026, 7, 10, 16, 0, tzinfo=toronto),
    datetime(2026, 7, 11, 10, 0, tzinfo=toronto),
]

for test_time in test_times:
    result = get_tsx_market_status(test_time)

    print(
        test_time.strftime("%Y-%m-%d %H:%M"),
        result["status"],
        result["can_open_trade"],
        result["message"],
    )