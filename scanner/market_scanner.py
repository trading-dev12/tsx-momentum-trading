from scanner.momentum_score import calculate_score
from scanner.stock_grader import grade_stock
from scanner.tmqs_score import calculate_tmqs
from rules.trade_decision import get_trade_decision


def display_market_data(quotes):

    print()
    print("Top Momentum")
    print("------------")

    for quote in quotes:
        quote["score"] = calculate_score(quote)
        quote["grades"] = grade_stock(quote)
        quote["tmqs"] = calculate_tmqs(quote)
        quote["decision"] = get_trade_decision(quote)

    quotes.sort(key=lambda q: q["tmqs"], reverse=True)

    for rank, quote in enumerate(quotes, start=1):
        print(
            f"{rank}. {quote['symbol']}: "
            f"${quote['price']:.2f} | "
            f"TMQS: {quote['tmqs']} | "
            f"Score: {quote['score']:.1f} | "
            f"Gap: {quote['gap_percent']:+.2f}% | "
            f"Momentum: {quote['grades']['Momentum']} | "
            f"Liquidity: {quote['grades']['Liquidity']} | "
            f"Decision: {quote['decision']}"
        )