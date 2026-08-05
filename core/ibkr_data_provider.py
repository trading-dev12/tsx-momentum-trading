"""
IBKR Market Data Provider

Provides read-only TSX quote access through Interactive Brokers
Trader Workstation.

This module does not place or manage broker orders.
"""

from __future__ import annotations

import math
from typing import Any

from ib_insync import IB, Stock


IBKR_HOST = "127.0.0.1"
IBKR_PORT = 7496
IBKR_CLIENT_ID = 11
IBKR_QUOTE_WAIT_SECONDS = 2.0

IBKR_SYMBOL_ALIASES = {
    "CCL-B.TO": "CCL.B",
    "EMP-A.TO": "EMP.A",
    "GIB-A.TO": "GIB.A",
    "TECK-B.TO": "TECK.B",
}

class IBKRDataProvider:
    """
    Read-only Interactive Brokers market-data provider.
    """

    def __init__(
        self,
        host: str = IBKR_HOST,
        port: int = IBKR_PORT,
        client_id: int = IBKR_CLIENT_ID,
    ):
        self.host = host
        self.port = int(port)
        self.client_id = int(client_id)
        self.ib = IB()

    def connect(self) -> None:
        """
        Connect to TWS when not already connected.
        """

        if self.ib.isConnected():
            return

        self.ib.connect(
            self.host,
            self.port,
            clientId=self.client_id,
            readonly=True,
            timeout=10,
        )

        if not self.ib.isConnected():
            raise ConnectionError(
                "IBKR connection could not be established."
            )

    def disconnect(self) -> None:
        """
        Disconnect cleanly from TWS.
        """

        if self.ib.isConnected():
            self.ib.disconnect()

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """
        Convert a Northstar/Yahoo TSX symbol into the
        corresponding IBKR symbol.
        """

        normalized = str(symbol).strip().upper()

        alias = IBKR_SYMBOL_ALIASES.get(normalized)

        if alias is not None:
            return alias

        if normalized.endswith(".TO"):
            normalized = normalized[:-3]

        return normalized

    @staticmethod
    def valid_number(value: Any) -> bool:
        """
        Return True when value is a usable finite number.
        """

        try:
            return math.isfinite(float(value))
        except (TypeError, ValueError):
            return False

    def build_tsx_contract(self, symbol: str) -> Stock:
        """
        Build an IBKR contract for a TSX-listed stock.
        """

        return Stock(
            self.normalize_symbol(symbol),
            "SMART",
            "CAD",
            primaryExchange="TSE",
        )

    def get_quote(self, symbol: str) -> dict[str, Any]:
        """
        Return a normalized quote for one TSX symbol.

        Price selection order:
        1. Last traded price
        2. Bid/ask midpoint
        3. Previous close
        """

        self.connect()

        contract = self.build_tsx_contract(symbol)

        qualified = self.ib.qualifyContracts(contract)

        if not qualified:
            raise ValueError(
                f"IBKR could not qualify contract for {symbol}."
            )

        ticker = self.ib.reqMktData(
            contract,
            genericTickList="",
            snapshot=False,
            regulatorySnapshot=False,
        )

        try:
            self.ib.sleep(IBKR_QUOTE_WAIT_SECONDS)

            last = (
                float(ticker.last)
                if self.valid_number(ticker.last)
                else None
            )

            bid = (
                float(ticker.bid)
                if self.valid_number(ticker.bid)
                else None
            )

            ask = (
                float(ticker.ask)
                if self.valid_number(ticker.ask)
                else None
            )

            close = (
                float(ticker.close)
                if self.valid_number(ticker.close)
                else None
            )

            volume = (
                float(ticker.volume)
                if self.valid_number(ticker.volume)
                else None
            )

            if last is not None:
                price = last
                price_source = "LAST"
            elif bid is not None and ask is not None:
                price = (bid + ask) / 2
                price_source = "MIDPOINT"
            elif close is not None:
                price = close
                price_source = "CLOSE"
            else:
                raise ValueError(
                    f"No usable IBKR price received for {symbol}."
                )

            return {
                "symbol": symbol.upper(),
                "ibkr_symbol": contract.symbol,
                "exchange": contract.primaryExchange,
                "currency": contract.currency,
                "price": price,
                "price_source": price_source,
                "last": last,
                "bid": bid,
                "ask": ask,
                "close": close,
                "volume": volume,
                "source": "IBKR",
                "connected": self.ib.isConnected(),
            }

        finally:
            self.ib.cancelMktData(contract)

    def get_quotes(
        self,
        symbols: list[str],
    ) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
        """
        Retrieve live quotes for multiple TSX symbols using
        one TWS connection and one shared data wait.

        Returns:
            quotes_by_symbol, errors_by_symbol
        """

        self.connect()

        quotes_by_symbol = {}
        errors_by_symbol = {}
        subscriptions = []

        for symbol in symbols:
            try:
                contract = self.build_tsx_contract(symbol)

                qualified = self.ib.qualifyContracts(contract)

                if not qualified:
                    raise ValueError(
                        f"IBKR could not qualify {symbol}."
                    )

                ticker = self.ib.reqMktData(
                    contract,
                    genericTickList="",
                    snapshot=False,
                    regulatorySnapshot=False,
                )

                subscriptions.append(
                    (symbol, contract, ticker)
                )

            except Exception as error:
                errors_by_symbol[symbol] = str(error)

        self.ib.sleep(IBKR_QUOTE_WAIT_SECONDS)

        for symbol, contract, ticker in subscriptions:
            try:
                last = (
                    float(ticker.last)
                    if self.valid_number(ticker.last)
                    else None
                )

                bid = (
                    float(ticker.bid)
                    if self.valid_number(ticker.bid)
                    else None
                )

                ask = (
                    float(ticker.ask)
                    if self.valid_number(ticker.ask)
                    else None
                )

                close = (
                    float(ticker.close)
                    if self.valid_number(ticker.close)
                    else None
                )

                volume = (
                    float(ticker.volume)
                    if self.valid_number(ticker.volume)
                    else None
                )

                if last is not None:
                    price = last
                    price_source = "LAST"

                elif bid is not None and ask is not None:
                    price = (bid + ask) / 2
                    price_source = "MIDPOINT"

                elif close is not None:
                    price = close
                    price_source = "CLOSE"

                else:
                    raise ValueError(
                        f"No usable IBKR price for {symbol}."
                    )

                quotes_by_symbol[symbol] = {
                    "symbol": symbol.upper(),
                    "ibkr_symbol": contract.symbol,
                    "exchange": contract.primaryExchange,
                    "currency": contract.currency,
                    "price": price,
                    "price_source": price_source,
                    "last": last,
                    "bid": bid,
                    "ask": ask,
                    "close": close,
                    "volume": volume,
                    "source": "IBKR",
                    "connected": self.ib.isConnected(),
                }

            except Exception as error:
                errors_by_symbol[symbol] = str(error)

            finally:
                self.ib.cancelMktData(contract)

        return quotes_by_symbol, errors_by_symbol




def get_ibkr_quote(symbol: str) -> dict[str, Any]:
    """
    Convenience function for retrieving one quote.
    """

    provider = IBKRDataProvider()

    try:
        return provider.get_quote(symbol)
    finally:
        provider.disconnect()
