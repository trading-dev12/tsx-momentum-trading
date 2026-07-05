from core.startup import startup
from core.config_loader import load_settings
from core.watchlist_loader import load_watchlist


def main():

    settings = load_settings()

    print("====================================")
    print(settings["project_name"])
    print("Version", settings["version"])
    print("====================================")

    startup()

    print()
    print("Market:", settings["market"])
    print("Currency:", settings["currency"])
    print("Refresh:", settings["scanner_refresh_seconds"], "seconds")

    watchlist = load_watchlist(settings["watchlist_file"])

    print()
    print("Watchlist")
    print("---------")

    for symbol in watchlist:
        print(symbol)

    print()
    print(len(watchlist), "symbols loaded")


if __name__ == "__main__":
    main()