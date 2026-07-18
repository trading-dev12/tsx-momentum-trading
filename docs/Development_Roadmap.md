# TSX Momentum Trading Pro - Development Roadmap

## Phase 1 - Foundation

-   [x] Windows 11 workstation
-   [x] Python
-   [x] VS Code
-   [x] Git & GitHub

## Phase 2 - Live Scanner

-   [x] Live TSX Scanner
-   [x] Market Health Dashboard
-   [x] TMQS
-   [x] Confidence Score
-   [x] Decision Engine
-   [x] Trade Checklist
-   [x] Auto Refresh
-   [x] Best Trade Candidate

## Phase 3 - Backtesting

-   [x] Historical Loader
-   [x] Multi-stock Backtesting
-   [x] Performance Report
-   [x] Professional Trade Log
-   [x] ATR Stops & Targets
-   [x] Exit Reason Summary

### Current Priority

-   [ ] Optimizer v2 (ATR, Reward, Hold Days)
-   [ ] Equity Curve
-   [ ] Monthly Performance
-   [ ] Monte Carlo Testing
-   [ ] Walk-Forward Testing

## Phase 4 - Live Trading

-   [ ] Desktop READY Alerts
-   [ ] Windows Notifications
-   [ ] Phone Notifications
-   [ ] ATR Position Sizing
-   [ ] Trade Journal

## Phase 5 - Version 3.0

-   [ ] Interactive Brokers Integration
-   [ ] AI Trade Ranking
-   [ ] One-click Backtesting
-   [ ] Statistics Dashboard
Theme

Operational Excellence → Research Platform

The core trading engine is no longer the priority.

From this point forward, our priority is making the platform smarter, more reliable, and capable of discovering statistically valid edges.

Phase 1 — Complete Operations

Goal: Run unattended every trading day.

1. Finish Telegram notifications
Complete all remaining trade notifications.
Confirm every important event reaches your phone.
Ensure you never need to remote into the computer.
2. Mobile monitoring

Finish the mobile dashboard so you can see:

Scanner health
Market status
Open positions
Pending trades
Today's P&L
Strategy health
Last successful EOD
Last successful execution
3. PC-at-home validation

This is a major milestone.

When complete you should be able to:

Leave for work.

Come home.

Everything ran correctly.

No intervention required.

4. IBKR Market Data

Replace Yahoo with IBKR.

Benefits:

One standardized data source
More reliable prices
Easier transition to live trading
Consistent research dataset

This should be done carefully so the existing strategy logic remains unchanged. We'll verify that signals stay consistent after the data-source change.

5. Continue collecting trades

Do not optimize.

Do not tweak parameters.

Just collect clean data.

Target:

200 validated trades per strategy

Phase 2 — Historical Trade Enrichment Engine

This is the biggest software project after the execution engine.

For every completed trade we'll capture:

Trade Context
Strategy
Entry reason
Exit reason
Holding period
Risk multiple
Market Context
Market regime
XIC trend
XIU trend
Oil
CAD/USD
Volatility regime
Sector Context
Sector
Sector strength
Relative strength
Technical Context
RVOL
Gap %
ATR %
SMA20
SMA50
SMA200
Distance from each moving average
Breakout quality
Trade Quality
Setup Quality score
Historical Win Probability (future)
Confidence metadata

The result will be a master enriched dataset that every future research tool can use.

Phase 3 — Research Dashboard

Build a dedicated dashboard for analysis rather than execution.

Examples:

Equity curves by strategy
Win rate over time
Expectancy by strategy
Profit factor
Drawdown
Heat maps
Sector performance
Market-regime performance
Distribution of R-multiples
Monthly returns
Rolling statistics

This dashboard is where you'll start to see patterns emerge from the data.

Phase 4 — Edge Discovery Engine

This is where the platform begins to answer questions instead of just reporting results.

Examples:

Does RVOL > 2 outperform RVOL > 1.5?
Which sectors perform best?
Which market regimes produce the highest expectancy?
Is a gap up beneficial or harmful?
Does holding longer improve returns?
Which stop multiple performs best?
Which strategy is strongest under current conditions?

Importantly, the engine will evaluate combinations of filters, not just individual ones.

Phase 5 — Multi-Strategy Portfolio Management

Once multiple strategies are validated, the platform can decide:

How much capital to allocate to each strategy.
Which strategies should run simultaneously.
Whether two strategies are highly correlated.
When to reduce exposure because several strategies are signaling the same market risk.

This moves beyond individual trades to managing the portfolio as a whole.