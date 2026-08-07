"""
Northstar connectivity monitoring.

Provides a lightweight external-network check used by the
reliability system. This module does not contain trading logic.
"""

import socket


CONNECTIVITY_TARGETS = (
    ("1.1.1.1", 443, "Cloudflare"),
    ("8.8.8.8", 53, "Google DNS"),
)


def check_internet_connectivity(
    timeout_seconds=2.0,
):
    """
    Check whether the computer can reach the public internet.

    Multiple independent external targets are used so that one
    unavailable service does not automatically look like a full
    internet outage.
    """

    failures = []

    for host, port, label in CONNECTIVITY_TARGETS:
        try:
            with socket.create_connection(
                (host, port),
                timeout=timeout_seconds,
            ):
                return {
                    "online": True,
                    "reachable_target": label,
                    "failures": failures,
                }

        except OSError as error:
            failures.append(
                {
                    "target": label,
                    "error": str(error),
                }
            )

    return {
        "online": False,
        "reachable_target": None,
        "failures": failures,
    }