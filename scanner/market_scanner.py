from scanner.momentum_score import calculate_score
from scanner.stock_grader import grade_stock
from scanner.tmqs_score import calculate_tmqs
from rules.trade_decision import get_trade_decision


def display_market_data(quotes):

    for quote in quotes:
        quote["score"] = calculate_score(quote)
        quote["grades"] = grade_stock(quote)
        quote["tmqs"] = calculate_tmqs(quote)
        quote["decision"] = get_trade_decision(quote)

    quotes.sort(key=lambda q: q["tmqs"], reverse=True)

    print()
    print("=" * 60)
    print("TOP TSX MOMENTUM SETUPS")
    print("=" * 60)

    for rank, quote in enumerate(quotes, start=1):
        print()
        print(f"{rank}. {quote['symbol']}")
        print("-" * 60)
        print(f"Price:          ${quote['price']:.2f}")
        print(f"TMQS:           {quote['tmqs']}/100")
        print(f"Momentum Score: {quote['score']:.1f}")
        print(f"Gap:            {quote['gap_percent']:+.2f}%")
        print(f"Previous High:  ${quote['previous_high']:.2f}")
        print(f"Previous Close: ${quote['previous_close']:.2f}")
        print(f"Momentum Grade: {quote['grades']['Momentum']}")
        print(f"Liquidity Grade:{quote['grades']['Liquidity']}")
        print(f"Decision:       {quote['decision']}")

    print()
    print("=" * 60)