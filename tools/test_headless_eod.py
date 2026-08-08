"""
Safe tests for Northstar headless automatic EOD.

The real automatic EOD worker is mocked, so no scans,
queues, trades, journals, backups, or Telegram messages run.
"""

from unittest.mock import MagicMock, patch

import core.headless_eod as headless_eod


def test_start_headless_eod_service():
    engines = {
        "momentum": MagicMock(
            name="momentum_engine"
        ),
        "52_week_breakout": MagicMock(
            name="breakout_engine"
        ),
        "mean_reversion": MagicMock(
            name="mean_reversion_engine"
        ),
    }

    fake_thread = MagicMock(
        name="eod_thread"
    )

    with patch.object(
        headless_eod,
        "start_automatic_eod_service",
        return_value=fake_thread,
    ) as start_service:
        result = (
            headless_eod
            .start_headless_eod_service(
                engines
            )
        )

    assert result is fake_thread

    start_service.assert_called_once_with(
        engines["momentum"],
        breakout_52week_engine=(
            engines["52_week_breakout"]
        ),
        mean_reversion_engine=(
            engines["mean_reversion"]
        ),
        live_snapshot_provider=None,
    )
