from core.config_loader import load_settings
from core.watchlist_loader import load_watchlist
from core.market_data import get_quotes
from scanner.market_scanner import display_market_data
from core.market_context import score_market_context


def display_market_summary(market):
    print()
    print("=" * 90)
    print("TSX MOMENTUM TRADING WORKSTATION")
    print("=" * 90)

    print()
    print("MARKET HEALTH")
    print("-" * 90)

    print(f"TSX:        {market['tsx_change']}%")
    print(f"Oil:        {market['oil_change']}%")
    print(f"Bitcoin:    {market['bitcoin_change']}%")
    print(f"VIX:        {market['vix_change']}%")

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

    print()
    print("Loaded Watchlist:")
    print("-" * 90)

    for symbol in watchlist:
        print(symbol)

    print()
    print(len(watchlist), "symbols loaded")

    market = score_market_context()

    quotes = get_quotes(watchlist)

    display_market_summary(market)

    display_market_data(quotes)


if __name__ == "__main__":
    main()