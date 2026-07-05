from scanner.momentum_score import calculate_score
from scanner.stock_grader import grade_stock
from rules.trade_decision import make_trade_decision


def display_market_data(quotes):

    print()
    print("Top Momentum")
    print("------------")

    scored_quotes = []

    for quote in quotes:

        score = calculate_score(quote)
        grades = grade_stock(quote)

        quote["score"] = score
        quote["grades"] = grades

        scored_quotes.append(quote)

    scored_quotes.sort(key=lambda q: q["score"], reverse=True)

    for rank, quote in enumerate(scored_quotes, start=1):

        decision = make_trade_decision(quote)

        print(
            f"{rank}. "
            f"{quote['symbol']}: "
            f"${quote['price']:.2f} | "
            f"Score: {quote['score']:.1f} | "
            f"Gap: {quote['gap_percent']:+.2f}% | "
            f"Prev High: ${quote['previous_high']:.2f} | "
            f"Prev Close: ${quote['previous_close']:.2f} | "
            f"Momentum: {quote['grades']['Momentum']} | "
            f"Liquidity: {quote['grades']['Liquidity']} | "
            f"Decision: {decision} | "
            f"{quote['status']}"
        )