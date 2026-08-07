"""
Northstar IBKR/TWS health monitoring.

Checks whether the local TWS API port is accepting connections.
This module does not request market data or place orders.
"""

import socket


IBKR_TWS_HOST = "127.0.0.1"
IBKR_TWS_PORT = 7496


def check_ibkr_tws_available(
    host=IBKR_TWS_HOST,
    port=IBKR_TWS_PORT,
    timeout_seconds=1.0,
):
    """
    Check whether the local TWS API socket is reachable.
    """

    try:
        with socket.create_connection(
            (host, port),
            timeout=timeout_seconds,
        ):
            return {
                "available": True,
                "host": host,
                "port": port,
                "error": None,
            }

    except OSError as error:
        return {
            "available": False,
            "host": host,
            "port": port,
            "error": str(error),
        }