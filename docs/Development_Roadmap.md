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
Phase 7
Post-200-Trade US Market Expansion and Elite Opportunity Selection

Objective

After the initial 200-trade validation milestone, expand Northstar Quant into a larger liquid US stock universe so more qualified candidates compete for a limited number of portfolio positions.

The purpose of the expansion is not simply to generate more trades. The purpose is to improve selectivity, tighten evidence-based entry requirements, and allow Northstar Quant to take only the strongest opportunities available across the TSX and US markets.

Implementation Plan

Build a US-market shadow scanner
Create a controlled universe of liquid US large-cap and mid-cap stocks
Backtest Momentum, 52-Week Breakout, and Mean Reversion independently on US data
Maintain separate US portfolios, pending queues, journals, and performance statistics
Add US exchange calendars, symbol handling, currency fields, and data-provider support
Validate realistic liquidity, spread, slippage, and execution requirements
Keep TSX and US research results separate until each market demonstrates a proven edge

Elite Opportunity Selection

Create an ELITE READY classification above the standard READY level
Require every candidate to meet minimum eligibility standards
Rank all qualified TSX and US candidates against one another
Limit entries to the highest-ranked opportunities
Apply maximum daily-entry, sector-exposure, and correlation limits
Avoid taking marginal setups merely to remain active
Allow unused capital to remain available when no elite setup exists

Potential Ranking Factors

Strategy score
TMQS
Relative volume
Relative strength
Sector strength
Market regime
Trend quality
Breakout quality
Volatility regime
Liquidity
Signal-day gap characteristics
Historical performance of comparable setups

Validation Requirements

Do not optimize for win rate alone
Prioritize expectancy, Profit Factor, drawdown, stability, and sample size
Use unseen out-of-sample data before accepting tighter rules
Continue forward paper trading after rules are frozen
Prevent overfit filters from being classified as proven improvements
Confirm that tighter requirements improve risk-adjusted results without reducing trade frequency below a useful level

Long-Term Outcome

Northstar Quant will evolve from taking every valid signal into an opportunity-ranking and capital-allocation system. A larger combined TSX and US universe will allow the platform to reject average setups and deploy capital only into the strongest evidence-supported opportunities.
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

Phase 7
Post-200-Trade US Market Expansion and Elite Opportunity Selection

Objective

After the initial 200-trade validation milestone, expand Northstar Quant into a larger liquid US stock universe so more qualified candidates compete for a limited number of portfolio positions.

The purpose of the expansion is not simply to generate more trades. The purpose is to improve selectivity, tighten evidence-based entry requirements, and allow Northstar Quant to take only the strongest opportunities available across the TSX and US markets.

Implementation Plan

Build a US-market shadow scanner
Create a controlled universe of liquid US large-cap and mid-cap stocks
Backtest Momentum, 52-Week Breakout, and Mean Reversion independently on US data
Maintain separate US portfolios, pending queues, journals, and performance statistics
Add US exchange calendars, symbol handling, currency fields, and data-provider support
Validate realistic liquidity, spread, slippage, and execution requirements
Keep TSX and US research results separate until each market demonstrates a proven edge

Elite Opportunity Selection

Create an ELITE READY classification above the standard READY level
Require every candidate to meet minimum eligibility standards
Rank all qualified TSX and US candidates against one another
Limit entries to the highest-ranked opportunities
Apply maximum daily-entry, sector-exposure, and correlation limits
Avoid taking marginal setups merely to remain active
Allow unused capital to remain available when no elite setup exists

Potential Ranking Factors

Strategy score
TMQS
Relative volume
Relative strength
Sector strength
Market regime
Trend quality
Breakout quality
Volatility regime
Liquidity
Signal-day gap characteristics
Historical performance of comparable setups

Validation Requirements

Do not optimize for win rate alone
Prioritize expectancy, Profit Factor, drawdown, stability, and sample size
Use unseen out-of-sample data before accepting tighter rules
Continue forward paper trading after rules are frozen
Prevent overfit filters from being classified as proven improvements
Confirm that tighter requirements improve risk-adjusted results without reducing trade frequency below a useful level

Long-Term Outcome

Northstar Quant will evolve from taking every valid signal into an opportunity-ranking and capital-allocation system. A larger combined TSX and US universe will allow the platform to reject average setups and deploy capital only into the strongest evidence-supported opportunities.
Long-Term Vision

Northstar Quant is evolving from a single momentum scanner into a multi-strategy quantitative research and paper-trading platform.

The objective is to operate multiple independent TSX strategies in parallel, collect statistically meaningful evidence for each, and deploy real capital only after demonstrating a sustainable edge. Each strategy will maintain separate journals, portfolios, and performance statistics, allowing evidence-based capital allocation rather than relying on subjective judgment.
NEXT PRIORITY — NORTHSTAR DIAGNOSTICS V1

Build a reusable diagnostics framework after confirming and committing the current position-sizing changes.

Scope:
- Shared diagnostics module
- Standard event structure
- Position-sizing diagnostics
- Execution diagnostics
- Scanner diagnostics
- Refresh/watchdog diagnostics
- EOD pipeline diagnostics
- Console and file logging
- Future System Health dashboard panel

Current status:
- Position-sizing diagnostic data is now captured
- Both paper execution paths return descriptive sizing errors
- Full pipeline test and clean commit required before framework work begins
✅ Phase 6 Milestone Complete – Live Market Data

Completed:

✅ Interactive Brokers API integration
✅ Live TSX quote retrieval
✅ Live batch scanning
✅ Symbol qualification
✅ Yahoo fallback layer
✅ Production validation

Northstar is now operating using professional-grade live market data.

Next Major Phase
Scanner Optimization
Replace remaining historical Yahoo requests with IBKR historical bars where appropriate.
Add connection health monitoring.
Add automatic reconnection.
Add latency measurements.
Add stale-data detection.
Continue reducing Yahoo dependency while keeping it as a resilient fallback.
Then

IBKR Paper Trading Integration

Automatic order routing
Live fills
Live positions
Account synchronization
Order status monitoring
My recommendation

I'd also update the project status.

Previously, I would have described Northstar as approximately 90–92% complete for Phase 1.

After today's work, I'd update it to:

Northstar Phase 1 Progress
Scanner Engine: 100%
Live Data Infrastructure: 100%
Reliability Framework: 98%
Paper Trading: 98%
Mobile Dashboard: 98%
Multi-Strategy Framework: 100%
IBKR Market Data Integration: 100%
Live Broker Execution: 0% (next major phase)

Overall Phase 1 completion: ~95%.

I think today's milestone deserves to be highlighted in your documentation. Months from now, you'll likely look back at August 5, 2026 as the day Northstar transitioned from a delayed-data research platform into a live market intelligence system.
## IBKR Market Data Phase 2 - Historical and Execution Pricing

### Completed

- [x] Add reusable IBKR historical-bar retrieval
- [x] Validate TSX one-minute regular-session bars
- [x] Add IBKR exact market-opening-price lookup
- [x] Validate PAAS.TO opening price against the first 09:30 IBKR bar
- [x] Preserve existing paper-execution behavior during capability testing

### Next Implementation

- [x] Make IBKR the primary opening-price provider in `paper_trading/opening_price.py`
- [x] Preserve Yahoo one-minute data as the first fallback
- [x] Preserve Yahoo exact daily data as the final fallback
- [x] Return structured IBKR failure results without stopping execution
- [x] Add automated tests for IBKR success and fallback behavior
- [x] Run end-to-end pending-trade execution validation
- [x] Record the selected price source in execution results and journals

### Later Work

- [ ] Migrate the morning observation recorder to IBKR intraday bars
- [ ] Evaluate IBKR daily bars for EOD signal generation
- [ ] Add historical-request pacing and retry controls
- [ ] Add historical-data latency and availability diagnostics
- [ ] Continue using Yahoo where it provides a measurable resilience benefit
## Scanner State Awareness (Dashboard Reliability)

### Objective

Improve the System Health dashboard so it reflects the actual operating state of Northstar rather than only the scanner heartbeat age.

### Planned Improvements

- [ ] Display **MARKET CLOSED** before the TSX opens and after it closes.
- [ ] Display **RUNNING** only during active market scanning.
- [ ] Display **STALE** only when the scanner heartbeat becomes overdue during market hours.
- [ ] Display **OFFLINE** when the scanner process is not running.
- [ ] Detect weekends and TSX market holidays and suppress false stale warnings.
- [ ] Replace generic worker states with descriptive states:
  - Waiting for Market Open
  - Refreshing
  - Idle
  - Sleeping (Market Closed)
- [ ] Display heartbeat age (for example: "Last refresh: 08:02:56 (18 seconds ago)").
- [ ] Display next scheduled refresh time during market hours.
- [ ] Continue using heartbeat monitoring to detect scanner freezes during active trading.

### Long-Term Vision

Expand the System Health panel into a complete operational dashboard showing:

- Scanner Status
- IBKR Connection
- TWS Connection
- Yahoo Backup Status
- Telegram Status
- Automatic Paper Execution Status
- Automatic EOD Status
- Pipeline Validation Status
- Last Heartbeat
- Refresh Duration
- Next Scheduled Refresh
---

## Reliability and Power-Recovery Milestone

### Status: Core Software Recovery Complete

Northstar now has a tested recovery path for Windows restarts, application interruptions, internet outages, and temporary IBKR/TWS unavailability.

### Completed

- [x] Persistent Northstar application heartbeat
- [x] Clean-shutdown detection
- [x] Unexpected restart/interruption detection
- [x] Telegram restart/recovery alert framework
- [x] Internet connectivity monitoring
- [x] Internet outage and recovery state tracking
- [x] IBKR/TWS local API health monitoring
- [x] IBKR/TWS outage and recovery alerting
- [x] Automatic IBKR reconnect capability
- [x] Yahoo market-data fallback while IBKR/TWS is unavailable
- [x] Missed EOD recovery safeguards
- [x] Automatic TWS launch after Windows logon
- [x] Automatic Northstar launch after Windows logon
- [x] Duplicate TWS process protection
- [x] Duplicate Northstar process protection
- [x] Windows Task Scheduler recovery task
- [x] 30-second post-logon startup delay
- [x] Scheduled-task retry configuration
- [x] Recovery-task installer stored in Git
- [x] Full Windows reboot recovery test completed successfully
- [x] TWS API port 7496 verified after authentication
- [x] Direct IBKR read-only quote verified after recovery
- [x] Automatic paper-execution result-handling bug corrected
- [x] Regression coverage added for empty, skipped, and multiple execution results
- [x] Full safe automated test suite: 92 passed

### Verified Recovery Sequence

Windows reboot
-> Windows logon
-> Northstar Recovery scheduled task
-> TWS launches
-> Northstar launches
-> Yahoo fallback remains available while TWS is unauthenticated
-> User authenticates TWS
-> TWS API port 7496 becomes available
-> IBKR market-data connection succeeds

No IBKR password is stored in Northstar recovery scripts.

### Remaining Power-Outage Reliability Work

- [ ] Configure BIOS/UEFI "Restore on AC Power Loss" so the PC powers itself back on when electricity returns
- [ ] Verify the Windows recovery sequence after an actual power-loss simulation
- [ ] Verify during an open TSX session that the already-running scanner automatically resumes IBKR data after TWS authentication without restarting Northstar
- [ ] Consider UPS protection for the PC, modem, and router to reduce short-outage interruptions
- [ ] Continue distinguishing local PC/connectivity failures from upstream data-provider failures

### Reliability Principle

Northstar should fail safely, preserve state, fall back where appropriate, recover automatically where possible, and clearly report when human authentication or intervention is still required.