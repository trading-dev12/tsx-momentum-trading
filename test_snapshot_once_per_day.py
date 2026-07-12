from datetime import datetime
from zoneinfo import ZoneInfo

from paper_trading.morning_recorder_service import (
    MorningRecorderService,
)


class Queue:
    pass


class Engine:
    pass


queue = Queue()
queue.trades = [
    {"symbol": "AAA.TO"},
]
queue.get_all = lambda: queue.trades

engine = Engine()
engine.pending_trades = queue

service = MorningRecorderService(engine)

toronto = ZoneInfo("America/Toronto")

first = service.capture_today_snapshot(
    datetime(2026, 7, 13, 9, 30, tzinfo=toronto)
)

queue.trades = [
    {"symbol": "BBB.TO"},
    {"symbol": "CCC.TO"},
]

second = service.capture_today_snapshot(
    datetime(2026, 7, 13, 9, 45, tzinfo=toronto)
)

third = service.capture_today_snapshot(
    datetime(2026, 7, 14, 9, 30, tzinfo=toronto)
)

print("FIRST :", first)
print("SECOND:", second)
print("THIRD :", third)
print("SNAPSHOT:", service.candidate_snapshot)