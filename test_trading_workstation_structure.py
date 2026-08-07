from gui.trading_workstation import TradingWorkstation


def test_reliability_methods_remain_inside_workstation_class():
    """
    Critical workstation methods must remain members of the
    TradingWorkstation class.

    This protects against accidental indentation changes that
    leave valid Python functions outside the class.
    """

    required_methods = (
        "start_connectivity_check_if_due",
        "update_countdown",
        "format_percent",
    )

    for method_name in required_methods:
        assert hasattr(
            TradingWorkstation,
            method_name,
        ), (
            f"{method_name} is not inside "
            "TradingWorkstation."
        )

        assert callable(
            getattr(
                TradingWorkstation,
                method_name,
            )
        )