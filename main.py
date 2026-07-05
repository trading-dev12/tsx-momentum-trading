from core.config_loader import load_settings
from core.watchlist_loader import load_watchlist
from core.market_data import get_quotes
from core.market_context import score_market_context
from scanner.market_scanner import display_market_data


def display_market_summary(market):
    print()
    print("=" * 90)
    print("TSX MOMENTUM TRADING WORKSTATION")
    print("=" * 90)

    print()
    print("MARKET HEALTH")
    print("-" * 90)

    tsx = market["tsx_change"] if market["tsx_change"] is not None else "N/A"
    oil = market["oil_change"] if market["oil_change"] is not None else "N/A"
    bitcoin = market["bitcoin_change"] if market["bitcoin_change"] is not None else "N/A"
    vix = market["vix_change"] if market["vix_change"] is not None else "N/A"

    print(f"TSX:        {tsx}%")
    print(f"Oil:        {oil}%")
    print(f"Bitcoin:    {bitcoin}%")
    print(f"VIX:        {vix}%")

    print()
    print(f"Overall Market Status: {market['status']}")
    print(f"Market Health Score:   {market['score']}/100")

    print()
    print("Market Notes:")
    for note in market["notes"]:
        print(f"- {note}")

    print("=" * 90)
    print()


def main():
    settings = load_settings()
    watchlist = load_watchlist(settings["watchlist_file"])

    quotes = get_quotes(watchlist)
    market = score_market_context()

    display_market_summary(market)
    display_market_data(quotes)


if __name__ == "__main__":
    main()