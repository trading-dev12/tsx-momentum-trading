def display_market_data(quotes):
    print("=" * 60)
    print("TSX MOMENTUM SCANNER")
    print("=" * 60)

    for rank, quote in enumerate(quotes, start=1):
        print()
        print(f"{rank}. {quote['symbol']}")
        print("-" * 60)
        print(f"Price:           ${quote['price']:.2f}")
        print(f"TMQS:            {quote['tmqs']}/100")
        print(f"Momentum Score:  {quote['score']:.1f}")
        print(f"Gap:             {quote['gap_percent']:+.2f}%")
        print(f"Previous High:   ${quote['previous_high']:.2f}")
        print(f"Previous Close:  ${quote['previous_close']:.2f}")
        print(f"Breakout Status: {quote['breakout_status']}")
        print(f"Momentum Grade:  {quote['grades']['Momentum']}")
        print(f"Liquidity Grade: {quote['grades']['Liquidity']}")
        print(f"Decision:        {quote['decision']}")

    print()
    print("=" * 60)