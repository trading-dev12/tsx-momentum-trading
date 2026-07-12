import time

from paper_trading.morning_recorder_service import (
    MorningRecorderService,
)


class DummyPendingTrades:
    def get_all(self):
        return []


class DummyPaperEngine:
    def __init__(self):
        self.pending_trades = DummyPendingTrades()


engine = DummyPaperEngine()

service = MorningRecorderService(
    paper_engine=engine,
    check_seconds=1,
)

print("Starting service...")
service.start()

time.sleep(3)

print("Stopping service...")
service.stop()

print("Thread alive:", service.thread.is_alive())

print("Runtime test complete.")