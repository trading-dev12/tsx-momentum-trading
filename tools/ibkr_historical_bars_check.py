from core.ibkr_data_provider import IBKRDataProvider


def main() -> None:
    provider = IBKRDataProvider(client_id=15)

    try:
        bars = provider.get_historical_bars(
            symbol="PAAS.TO",
            duration="2 D",
            bar_size="1 min",
            use_rth=True,
        )

        print("=" * 70)
        print("IBKR HISTORICAL BAR TEST")
        print("=" * 70)
        print(f"Bars received: {len(bars)}")

        for bar in bars[:5]:
            print(
                bar.date,
                bar.open,
                bar.high,
                bar.low,
                bar.close,
                bar.volume,
            )

        if bars:
            print("-" * 70)
            print("Last bar:")
            last_bar = bars[-1]
            print(
                last_bar.date,
                last_bar.open,
                last_bar.high,
                last_bar.low,
                last_bar.close,
                last_bar.volume,
            )

    finally:
        provider.disconnect()


if __name__ == "__main__":
    main()