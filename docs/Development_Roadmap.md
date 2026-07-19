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
Northstar Quant – Next Major Milestone
Historical Trade Enrichment Engine
Objective

Transform Northstar Quant from a trading platform into a quantitative research platform by recording rich contextual data for every completed trade.

Important Principle

Do not change the trading strategy during the 200-trade validation.

The momentum strategy must continue making decisions exactly as it does today so the validation remains statistically clean.

Instead, we will collect additional research data in the background.

Philosophy

Northstar Quant will follow one core principle:

Never trust assumptions when you can collect evidence.

Rather than guessing which factors matter, the platform will measure everything and let the data determine which factors have predictive value.

What Will Be Recorded

Every completed trade will be enriched with additional market context.

Market Context
Market regime
TSX trend
Volatility regime
Market breadth
VIX (or Canadian equivalent if applicable)
Relative Strength
Relative Strength vs XIC
Relative Strength vs XIU
Relative Strength ranking
Sector Analysis
Sector
Sector Relative Strength
Sector trend
Sector momentum
Trend Structure
Distance above/below:
20 SMA
50 SMA
200 SMA
Trend age
Consecutive higher highs
Consecutive higher lows
Volume Analysis
Relative Volume
Average Volume
Dollar Volume
20-day volume trend
Accumulation days (20)
Distribution days (20)
Institutional Footprint Metrics

Instead of creating an Institutional Footprint Score immediately, Northstar Quant will record the raw measurements:

Relative Volume
Relative Strength
Sector Strength
Accumulation
Trend quality
Liquidity
Distance from 52-week high
Close location within daily range

The platform will not assign weights during validation.

Why No Institutional Footprint Score?

A score requires assumptions.

Example:

RVOL = 25%
Relative Strength = 20%
Sector Strength = 15%

Those weights are opinions.

Northstar Quant will instead collect the raw data first.

Later, the research engine will determine statistically which variables deserve the most weight.

Evidence determines the score—not us.

Research Questions the Platform Will Answer

After hundreds of completed trades, Northstar Quant will answer questions such as:

Do trades with stronger institutional footprints outperform?
Does sector strength increase expectancy?
Is Relative Strength more important than RVOL?
Does distance from the 200-day moving average matter?
Which market regime produces the highest expectancy?
Which combination of variables creates the highest Profit Factor?
Long-Term Vision

Eventually the platform will be able to discover findings like:

Momentum trades with:

Institutional Footprint > 85
Strong sector momentum
Bull market regime

Produced the highest expectancy and Profit Factor.

Those conclusions will come from real trading evidence rather than intuition.

Development Priority
Phase 1 (Current)
Continue paper trading
Complete 200-trade validation
Keep trading rules frozen
Phase 2 (Next Major Project)

Historical Trade Enrichment Engine

Record all contextual variables for every completed trade.

Phase 3

Research Dashboard

Visualize and filter enriched trade data.

Phase 4

Edge Discovery Engine

Automatically rank variables by:

Expectancy
Profit Factor
Win Rate
Drawdown
Trade Count
Statistical significance