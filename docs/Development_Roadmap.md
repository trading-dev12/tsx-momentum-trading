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
---

## Edge Discovery Research Platform - August 8, 2026

### Status: ACTIVE - Core Research Infrastructure Complete

Northstar has now moved beyond basic trade collection into the first operational stage of systematic edge discovery.

The three production research strategies remain statistically independent:

- Momentum
- 52-Week Breakout
- Mean Reversion

Each strategy must still complete its own 200-trade validation. Results must not be pooled to accelerate validation.

### Strategy Freeze Principle

The existing strategy rules remain frozen during validation.

The Edge Research system is observational and read-only. It does not modify:

- TMQS
- READY / WATCH / IGNORE rules
- ATR stop settings
- reward target
- maximum holding period
- entry rules
- exit rules
- position-risk rules

Research findings may generate future hypotheses, but no strategy changes will be accepted until the appropriate validation review.

### Completed - Shadow Edge Analyzer

- [x] Baseline trade-performance analysis
- [x] Categorical research-factor analysis
- [x] Numeric research-factor analysis
- [x] Candidate edge tracking
- [x] Candidate overlap analysis
- [x] Candidate cohort analysis
- [x] Candidate quality gate
- [x] Combination-research readiness gate
- [x] Read-only research snapshots
- [x] Minimum-sample safeguards
- [x] Research-only candidate ratings

The analyzer can evaluate observed relationships involving:

- Market regime
- Moving-average trend alignment
- Gap characteristics
- Volatility regime
- Relative strength versus XIC
- Relative strength versus XIU
- Distance from SMA20
- Distance from SMA50
- Distance from SMA200
- Sector strength
- Gap percentage
- ATR percentage

### Combination Research Safeguard

Combination research is exploratory only and does not authorize strategy changes.

Current minimum readiness requirement:

- 60 fully enriched completed trades
- 10 distinct entry dates

Passing this gate means only that combination research may begin. It does not prove an edge.

### Completed - Research Data Quality

- [x] IBKR-primary historical research data
- [x] Yahoo fallback where appropriate
- [x] Research data-source provenance
- [x] Source-quality audit
- [x] Missing-source handling for legacy trades
- [x] Enrichment Integrity Monitor

Research source history is never invented or backfilled.

Old trades with missing enrichment remain legitimate legacy records.

### Enrichment Integrity Monitor

Monitoring begins:

2026-08-10

All newly completed trades from that date forward must satisfy the full enrichment requirement.

Current Momentum research history:

- Completed trades: 14
- Fully enriched: 9
- Legacy incomplete trades: 5
- Historical enrichment coverage: 64.3%
- New monitored trades: 0
- Current integrity status: WAITING FOR NEW TRADES

The five incomplete historical trades predate the complete enrichment pipeline and remain unchanged.

### Completed - Edge Research Dashboard

- [x] Dedicated read-only Edge Research dashboard
- [x] Validation progress
- [x] Baseline performance
- [x] Profit Factor
- [x] Expectancy
- [x] Win rate
- [x] Research depth
- [x] Combination readiness
- [x] Best current watched pattern
- [x] Research data-source quality
- [x] Enrichment Integrity status
- [x] Desktop workstation shortcut
- [x] Mobile dashboard shortcut
- [x] Phone/PWA validation

### Completed - Multi-Strategy Edge Research

Independent live Edge Research routes now exist for:

- [x] Momentum
- [x] 52-Week Breakout
- [x] Mean Reversion

Research journals remain separate:

- `paper_trade_journal.csv`
- `paper_trade_journal_52week.csv`
- `paper_trade_journal_mean_reversion.csv`

Current completed-trade counts:

- Momentum: 14
- 52-Week Breakout: 0
- Mean Reversion: 0

Testing confirmed that 52-Week Breakout and Mean Reversion do not read or include Momentum trades.

### Completed - Edge Research Strategy Selector

The Edge Research page now includes direct strategy navigation:

Momentum -> 52-Week Breakout -> Mean Reversion

The active strategy is visually highlighted.

The selector has been validated on:

- Desktop browser
- Mobile phone
- Northstar scanner/workstation environment

### Automated Test Baseline - Historical

Baseline when this section was completed:

138 passed
1 known nonfatal `eventkit` deprecation warning

The current authoritative regression baseline is recorded in the
August 14, 2026 status refresh below.

### Dashboard Recovery Validation

The dashboard recovery system was also repeatedly validated during deployment.

When the active Waitress process on port 5000 was deliberately terminated:

- the old listener stopped successfully;
- Northstar recovery automatically launched a replacement process;
- port 5000 returned automatically;
- Edge Research returned HTTP 200 after recovery.

This confirms that the mobile research dashboard can recover from an unexpected process interruption.

## COMPLETED - Candidate History and Stability Tracking

### Objective

Move Edge Research from showing only the best current candidate to measuring whether apparent edges remain stable as new trades accumulate.

### Completed Work

- [x] Store candidate research history over time
- [x] Record candidate sample size at each snapshot
- [x] Record rolling Profit Factor
- [x] Record rolling expectancy
- [x] Record rolling win rate
- [x] Measure whether candidate strength improves or deteriorates
- [x] Detect candidates that disappear as sample size increases
- [x] Distinguish persistent patterns from temporary small-sample noise
- [x] Display candidate stability on Edge Research
- [x] Keep all strategy datasets independent
- [x] Detect candidates that disappear and later reappear
- [x] Track candidate presence rate
- [x] Track current persistence streak
- [x] Track disappearance and reappearance counts
- [x] Integrate Candidate History capture into Automatic EOD
- [x] Keep Candidate History failures research-only so they cannot fail the trading EOD pipeline
- [x] Keep Edge Research dashboard reads non-mutating
- [x] Add automated Candidate History, EOD integration, dashboard-data, and dashboard-rendering tests
- [x] Validate live Candidate Stability display through the running mobile dashboard

### Completion Validation - August 14, 2026

- Functional implementation commit: `59c891b`
- Candidate History focused tests: 16 passed
- Candidate History + dashboard page focused tests: 25 passed
- Full automated regression suite excluding manual IBKR diagnostic scripts: 193 passed
- Live `/edge-research` endpoint returned HTTP 200 with Candidate Stability visible
- First stored observations created independently for Momentum, 52-Week Breakout, and Mean Reversion
- Stability states include NEW, IMPROVING, STABLE, MIXED, DETERIORATING, DISAPPEARED, REAPPEARED, and UNKNOWN
- Candidate Stability remains descriptive research only and does not alter frozen strategy rules

## NEXT PRIORITY - Combination Explorer

Only begin meaningful combination research after the readiness gate is satisfied.

Readiness gate:

- at least 60 fully enriched completed trades for the strategy;
- at least 10 distinct entry dates;
- Candidate History / Stability infrastructure operational;
- strategy rules remain frozen during validation.

The Combination Explorer should:

- analyze multiple factors together;
- enforce minimum trade-count requirements;
- penalize tiny samples;
- prevent duplicate or overlapping discoveries from appearing stronger than they are;
- rank combinations by expectancy, Profit Factor, stability, and sample size;
- remain completely separate from production strategy decisions.

### Validation Path Remains

1. Continue collecting clean trades.
2. Maintain frozen strategy rules.
3. Require 200 completed trades per strategy.
4. Build Edge Discovery tools alongside validation.
5. Use research findings to generate hypotheses.
6. Test promising hypotheses independently.
7. Require unseen forward evidence before adopting strategy changes.
8. Consider live capital only after a repeatable edge has been demonstrated.

### Longer-Term Sequence

Candidate History / Stability [COMPLETED]
-> Combination Explorer [NEXT - GATED]
-> 200-Trade Strategy Reviews
-> Evidence-Based Strategy Optimization
-> Portfolio Allocation Engine
-> Post-200-Trade US Expansion
-> Elite Opportunity Selection

The objective is not to force the current strategies to appear profitable.

The objective is to build a platform capable of discovering, rejecting, and validating market edges using evidence.

---

## August 10, 2026 - Reliability Milestone Completed

### EOD and Trading-State Reliability

- [x] Diagnosed EOD pipeline warning from August 10
- [x] Corrected Mean Reversion pending-trade reporting
- [x] Added accurate Total Pending count for Mean Reversion
- [x] Separated EOD rejection reporting into:
  - Already Open
  - Already Pending
  - Other Rejected
- [x] Identified K.TO stale pending/open-position conflict
- [x] Removed stale K.TO pending record without affecting the valid open position
- [x] Added runtime-state refresh before critical trading actions
- [x] Portfolio state now reloads before EOD signal queueing
- [x] Pending-trade state now reloads before EOD queueing and next-day execution
- [x] Added compatibility protection for in-memory test doubles
- [x] Reproduced stale-state failure condition in an isolated regression test
- [x] Confirmed stale-state protection prevents re-queuing an already-open position

### Pipeline Validation

- [x] Pipeline Validation restored to PASS
- [x] Historical pre-enrichment trades changed from WARNING to accepted legacy data
- [x] Current research rows remain strict and will continue to FAIL validation if required research data is missing

### Backup Reliability

- [x] Internal EOD backup separated from the removable external SSD
- [x] Internal EOD backups now save locally to Northstar_Backups
- [x] External SSD backup remains a separate full-project disaster-recovery layer
- [x] Automatic external SSD watcher completed
- [x] SSD is detected by volume label rather than fixed drive letter
- [x] Timestamped full-project backups are created automatically
- [x] Git repository history is included in external SSD backups
- [x] Runtime portfolios, journals, queues, configuration and research data are included

### Validation Results

- [x] Pipeline Validation: PASS
- [x] Paper-engine regression tests: 3 passed
- [x] Main automated test suite: 159 passed
- [x] No functional test failures
- [x] Known eventkit deprecation warning is non-blocking
- [x] Reliability changes committed and pushed to GitHub
- [x] Commit: a1c27e0 - Fix EOD reliability and stale trading state

### Reliability Follow-Up Backlog

- [x] Verify `tools/test_service_ownership.py` is pytest-safe in normal pytest collection
- [x] Verify GUI strategy queue counts always refresh from persisted state
- [x] Review pipeline validator handling of legitimate older pending trades when an opening price is unavailable
- [x] Future-proof recurring full-day TSX holiday generation beyond 2026
- [x] Add regression tests for future-year TSX holidays
- [x] Persist internet-outage state for recovery reporting
- [x] Add Telegram internet-restored alerts
- [ ] Add power-outage/recovery detection where practical
- [x] Add IBKR automatic reconnection protection
- [ ] Add scanner automatic reconnection after connectivity loss
- [ ] Continue reducing remaining Yahoo dependency while preserving fallback capability

### Current Reliability Position

Northstar now has multiple independent protection layers:

1. GitHub source-code history
2. Local automatic EOD backups
3. Automatic full-project external SSD snapshots
4. Pipeline validation
5. Runtime-state refresh protection
6. Automated regression testing

The next objective is to continue normal paper trading while monitoring the updated EOD and next-day execution workflow under real operating conditions.



---

## Completed Reliability / Risk Controls - August 2026

### Mean Reversion Severe-Down-Market Guard - COMPLETE

- [x] Added independent broad-market entry guard for Mean Reversion.
- [x] XIC market regime used as the broad TSX reference.
- [x] BULL regime permits new Mean Reversion entries.
- [x] SIDEWAYS regime permits new Mean Reversion entries.
- [x] BEAR regime blocks new Mean Reversion entries.
- [x] Unavailable or unknown market-regime data fails closed and blocks new entries.
- [x] Existing Mean Reversion positions are not force-closed by the guard.
- [x] Raw Mean Reversion READY signals remain preserved for research.
- [x] Momentum strategy remains unaffected.
- [x] 52-Week Breakout strategy remains unaffected.
- [x] Missed-EOD recovery evaluates the original trading date.
- [x] Headless/live scanner refresh does not perform unnecessary historical regime lookups.
- [x] EOD Telegram report shows Market Guard, Queue-Eligible READY, and Guard-Blocked READY.
- [x] Full Northstar regression suite passed: 161 tests, 0 failures.

Implementation commit:

513651d - Add Mean Reversion bear-market entry guard

---

## August 14, 2026 - Current Northstar Status

### Current Operating Position

Northstar Quant is now an operational multi-strategy paper-trading and
quantitative research platform.

The three strategies remain independent:

- Momentum
- 52-Week Breakout
- Mean Reversion

Each strategy continues toward its own 200-completed-trade validation
target. Strategy results must not be pooled to accelerate validation.

Trading rules remain frozen during this evidence-collection period.

### Production and Reliability Completed

- [x] Independent paper-trading infrastructure for all three strategies
- [x] Automatic EOD scanning and signal queueing
- [x] Automatic next-trading-day paper execution
- [x] Missed-EOD recovery safeguards
- [x] Runtime-state refresh before critical queue and execution actions
- [x] IBKR live TSX market data as the primary provider
- [x] Yahoo market-data fallback
- [x] IBKR opening-price provider with Yahoo fallbacks
- [x] Internet connectivity monitoring
- [x] IBKR/TWS connectivity monitoring
- [x] Automatic IBKR reconnection capability
- [x] Persistent internet-outage tracking with Telegram recovery notification
- [x] Pipeline validation
- [x] Automatic local EOD backup
- [x] Automatic external SSD disaster-recovery backup
- [x] Windows/Northstar recovery framework
- [x] Mean Reversion bear-market entry guard
- [x] Candidate History and Stability tracking
- [x] Candidate History capture integrated into Automatic EOD
- [x] Edge Research dashboards for all three strategies

### Recent Reliability Hardening

- [x] Manual IBKR diagnostic scripts removed from normal pytest collection
- [x] Normal pytest suite runs successfully without TWS being available
- [x] Recurring TSX full-day holiday generation supports future years
- [x] Future-year TSX holiday regression coverage added
- [x] 2026 Christmas Eve 1:00 PM TSX early close regression coverage added
- [x] Telegram EOD footer now uses the actual pending-trade total
- [x] Telegram zero, singular, and plural pending-signal wording tested

### Current Automated Test Baseline

232 passed
0 failed
1 known nonfatal `eventkit` deprecation warning

The known warning originates from `eventkit` under Python 3.13 and does
not currently represent a Northstar functional failure.

### Current Priority

1. Continue collecting clean paper-trade evidence.
2. Maintain frozen strategy rules.
3. Verify the next real Automatic EOD cycle under normal operating conditions.
4. Confirm Candidate History receives additional real observations over time.
5. Continue toward 200 completed trades independently for each strategy.
6. Continue reliability and data-quality work that does not alter strategy rules.

### Combination Explorer - Still Gated

Do not begin meaningful Combination Explorer research until the
readiness gate is satisfied for the strategy being analyzed:

- At least 60 fully enriched completed trades
- At least 10 distinct entry dates
- Candidate History / Stability operational
- Frozen production strategy rules

Passing the gate permits exploratory combination research only.
It does not prove an edge and does not authorize production rule changes.

### Remaining Operational Reliability Checks

- [x] Verify GUI strategy queue counts always refresh from persisted state
- [x] Review pipeline-validator handling of legitimate older pending trades when an opening price is unavailable
- [x] Configure BIOS/UEFI Restore on AC Power Loss if supported
- [x] Perform an actual power-loss recovery simulation
  - Verified by physical unplug/replug test: PC automatically powered back on, Northstar/TWS startup recovery ran, and Yahoo fallback kept Northstar operational while TWS awaited manual authentication.
- [ ] During an open TSX session, verify the already-running scanner automatically resumes IBKR data after TWS authentication without restarting Northstar
- [ ] Consider UPS protection for the PC, modem, and router
- [ ] Continue distinguishing local connectivity failures from upstream provider failures
- [ ] Continue reducing unnecessary Yahoo dependency while preserving it as a resilience fallback

### Next Research Sequence

Candidate History / Stability - COMPLETE

-> Continue clean data collection

-> Combination Explorer - GATED

-> 200-Trade Strategy Reviews

-> Evidence-Based Strategy Optimization

-> Portfolio Allocation Engine

-> Post-200-Trade US Expansion

-> Elite Opportunity Selection

The objective remains to discover and validate repeatable market edges
using evidence rather than changing the strategies in response to
short-term results.
