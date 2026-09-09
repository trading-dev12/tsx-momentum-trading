import gui.trading_workstation as workstation_module


class FakeTree:
    def __init__(self):
        self.rows = []

    def get_children(self):
        return []

    def delete(self, row):
        pass

    def insert(
        self,
        parent,
        index,
        iid=None,
        values=None,
        tags=None,
    ):
        self.rows.append(values)


class FakeLabel:
    def config(self, **kwargs):
        pass


def test_saved_eod_missing_live_metrics_show_dashes():
    workstation = (
        workstation_module
        .TradingWorkstation
        .__new__(
            workstation_module.TradingWorkstation
        )
    )

    workstation.tree = FakeTree()
    workstation.market_label = FakeLabel()
    workstation.summary_label = FakeLabel()
    workstation.best_trade_label = FakeLabel()

    workstation.load_scanner_snapshot = lambda: {
        "generated_at": "2026-09-08T16:26:26",
        "view": "EOD",
        "quotes": [
            {
                "symbol": "CLS.TO",
                "strategy": "MOMENTUM",
                "close": 45.60,
                "tmqs": 90.8,
                "rvol": 2.15,
                "breakout": "STRONG BREAKOUT",
                "decision": "READY",
                "reason": "Strong breakout with quality volume",
            }
        ],
    }

    workstation.build_strategy_queue_summary = (
        lambda ready_quotes: (
            "Momentum Queued: 1",
            "Existing READY Positions: None",
        )
    )

    workstation.update_paper_portfolio_panel = lambda: None

    result = workstation.display_saved_scanner_snapshot()

    assert result is True

    row = workstation.tree.rows[0]

    assert row[5] == "--"
    assert row[7] == "--"
    assert row[9] == "--"
    assert row[10] == "--"

    assert row[1] == "CLS.TO"
    assert row[4] == 90.8
    assert row[6] == "2.15x"
    assert row[8] == "STRONG BREAKOUT"
    assert row[11] == "READY"
