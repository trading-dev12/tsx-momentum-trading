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
Phase 2 — Historical Trade Enrichment Engine

Status: Core enrichment modules completed

The enrichment engine records the market and stock conditions that existed on the signal date for every paper trade. These fields are research-only and do not currently alter trade-entry or trade-management decisions.

Completed modules

Relative Strength versus XIC and XIU

Market Regime

Moving Average Context

Sector Strength

Gap Analysis

Volatility Regime

Research dimensions now recorded
Stock relative strength versus broad TSX benchmarks
Broad-market trend regime
Price position versus 20-day, 50-day and 200-day moving averages
Sector performance versus the market
Signal-day opening gap characteristics
ATR as a percentage of price
20-day realized volatility
Volatility percentile and regime
Remaining Phase 2 work

Confirm all live trade-creation paths attach the complete enrichment payload

Confirm enrichment fields appear correctly in future real paper-trade journal rows

Review missing-data and unavailable-status rates after live collection begins

Build a master enriched trade dataset for analysis

Document the final enrichment schema and field definitions

Next major phase
Phase 3 — Edge Discovery and Statistical Analysis

Planned capabilities:

Calculate Profit Factor
Calculate expectancy
Calculate win rate
Calculate average gain and average loss
Calculate maximum drawdown
Track trade count and sample size
Group performance by individual research factors
Test combinations of research factors
Rank promising conditions
Separate strategy performance by market regime
Apply minimum sample-size and statistical-confidence safeguards
Prevent weak or overfit combinations from being treated as proven edges

New research ideas should remain in the backlog until the current validation and data-collection milestones are complete.
Development Roadmap
Current Milestone
Phase 1 — Production Validation

Objective

Verify the complete Momentum production workflow after the EOD reliability improvements.

Validation checklist:

Live READY signal generated
Automatic EOD reports identical READY signal
Pending queue populated correctly
Automatic next-day execution successful
Dashboard updates correctly
Telegram notifications verified
Phase 2 — Version 4.0
Multi-Strategy Paper Trading

Promote the remaining research strategies into fully independent paper-trading systems.

Momentum

Current Status

Scanner ✅
Paper Trading ✅
Journal ✅
Dashboard ✅
52-Week Breakout

To Build

Independent Paper Trading Engine
Independent Pending Queue
Independent Portfolio
Independent Journal
Dashboard Integration
Telegram Notifications
Performance Statistics
Mean Reversion

To Build

Independent Paper Trading Engine
Independent Pending Queue
Independent Portfolio
Independent Journal
Dashboard Integration
Telegram Notifications
Performance Statistics
Phase 3
Unified Multi-Strategy Dashboard

Create a portfolio overview displaying all strategies simultaneously.

Example:

Momentum
Open Trades
Closed Trades
Return
Profit Factor

52 Week Breakout
Open Trades
Closed Trades
Return
Profit Factor

Mean Reversion
Open Trades
Closed Trades
Return
Profit Factor
Phase 4
Comparative Analytics

Develop tools to compare strategy performance objectively.

Metrics include:

Win Rate
Profit Factor
Expectancy
Maximum Drawdown
Average Hold Time
Sector Performance
Market Regime Performance
Relative Strength Performance
Phase 5
Strategy Optimizer

Build a research engine capable of identifying statistically significant improvements.

Examples:

ATR optimization
Relative Strength thresholds
Volatility regime filters
Sector rotation
Position sizing
Time-based exits
Phase 6
Portfolio Allocation Engine

Allocate capital dynamically based on each strategy's proven performance.

Example:

Momentum
$4,000

Mean Reversion
$3,500

52 Week Breakout
$2,500

Allocation will be driven by objective performance metrics rather than equal weighting.

Long-Term Vision

Northstar Quant is evolving from a single momentum scanner into a multi-strategy quantitative research and paper-trading platform.

The objective is to operate multiple independent TSX strategies in parallel, collect statistically meaningful evidence for each, and deploy real capital only after demonstrating a sustainable edge. Each strategy will maintain separate journals, portfolios, and performance statistics, allowing evidence-based capital allocation rather than relying on subjective judgment.