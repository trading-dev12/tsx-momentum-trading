from paper_trading.journal import save_trade
from paper_trading.portfolio import PaperPortfolio
from paper_trading.position_manager import monitor_positions


def test_trade_journal_uses_temporary_file(tmp_path):
    journal_file = tmp_path / "paper_trade_journal.csv"

    portfolio = PaperPortfolio(starting_cash=10000)

    position = {
        "symbol": "SHOP.TO",
        "strategy": "MOMENTUM",
        "entry_date": "2026-07-09",
        "entry_price": 100.00,
        "shares": 10,
        "stop_price": 95.00,
        "target_price": 112.50,
        "tmqs": 100,
        "rvol": 2.5,
    }

    portfolio.open_position(position)

    current_prices = {
        "SHOP.TO": 113.00,
    }

    closed_trades = monitor_positions(
        portfolio=portfolio,
        current_prices=current_prices,
        current_date="2026-07-10",
    )

    assert len(closed_trades) == 1

    for trade in closed_trades:
        save_trade(
            trade,
            file_path=str(journal_file),
        )

    assert journal_file.exists()

    saved_text = journal_file.read_text(encoding="utf-8")

    assert "SHOP.TO" in saved_text
    assert "MOMENTUM" in saved_text
    assert "Target hit" in saved_text