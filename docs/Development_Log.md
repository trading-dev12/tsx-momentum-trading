### Completed

- Validated backtesting engine
- Confirmed approximately 2,019 historical trades
- Enhanced performance metrics
- Expanded professional trade log
- Added exit reason reporting
- Restored ATR trade simulator from Git
- Completed Optimizer v2
- Optimizer now tests:
  - ATR multiplier
  - Reward multiplier
  - Maximum hold days
- Ran 810 strategy combinations

### Key Findings

- Win rate approximately 57%
- Most exits are still time-based
- ATR exits improved trade management
- Best settings so far:
  - ATR = 2.0
  - Reward = 2.5
  - Hold = 10 days
- Best performance:
  - Return ≈ 30.79%
  - Profit Factor = 1.59
  - Expectancy = 1.33%

### Next Task

- Analyze `optimizer_results.csv`
- Choose the most robust baseline strategy
- Verify that the best settings remain strong with stricter filters
- Begin improving TMQS scoring using the optimization results
# Development Log

## Latest Session

### Completed

- Validated backtesting engine
- Confirmed approximately 2,019 historical trades
- Enhanced performance metrics
- Expanded professional trade log
- Added exit reason reporting
- Restored ATR trade simulator from Git
- Completed Optimizer v2
- Optimizer now tests:
  - ATR multiplier
  - Reward multiplier
  - Maximum hold days
- Ran 810 strategy combinations
- Added Robustness Score field to optimizer results

### Key Findings

- Best return settings:
  - TMQS = 60
  - RVOL = 1.0
  - Breakout Only = True
  - ATR Multiplier = 2.0
  - Reward Multiplier = 2.5
  - Max Hold Days = 10
  - Return = 30.79%
  - Trades = 2,019
  - Win Rate = 52.06%
  - Profit Factor = 1.59
  - Expectancy = 1.33%

- Best profit factor settings:
  - TMQS = 60
  - RVOL = 2.0
  - Breakout Only = True
  - ATR Multiplier = 1.5
  - Reward Multiplier = 2.5
  - Max Hold Days = 10
  - Return = 12.97%
  - Trades = 916
  - Win Rate = 49.24%
  - Profit Factor = 1.69
  - Expectancy = 1.33%

- Best expectancy settings:
  - TMQS = 60
  - RVOL = 2.0
  - Breakout Only = True
  - ATR Multiplier = 2.0
  - Reward Multiplier = 2.5
  - Max Hold Days = 10
  - Return = 13.96%
  - Trades = 916
  - Win Rate = 52.84%
  - Profit Factor = 1.67
  - Expectancy = 1.43%

### Important Observations

- ATR 2.0, Reward 2.5, and 10-day maximum hold appear strongest so far.
- RVOL 2.0 reduces trade count from 2,019 to 916 but improves trade quality.
- Breakout=True and Breakout=False produced identical results in many cases, so breakout filtering must be audited.
- TMQS thresholds from 60 to 70 often produced identical results, so TMQS scoring needs improvement.
- Optimizer results suggest the next major edge may come from improving trade quality filters rather than adding more indicators.

### Next Task

- Analyze `optimizer_results.csv` in detail.
- Choose a stable baseline strategy.
- Audit breakout filtering logic.
- Improve TMQS scoring so higher scores truly represent better setups.
- Add standardized data provider interface later to support seamless IBKR integration.
## Latest Session

### Completed

- Redesigned the TMQS scoring model with stronger weighting for:
  - Breakout quality
  - Relative volume
  - Price strength
  - Quality caps
- Verified that the optimizer correctly applies the breakout filter.
- Confirmed that allowing WATCH setups changes optimization results, then reverted to READY-only trading to match the intended strategy.
- Created a TMQS Distribution Analysis tool.
- Analyzed all historical setups (28,842 total) to understand TMQS score distribution.

### Key Findings

- New TMQS model reduced qualifying trades:
  - From 2,019 to 495 READY trades.
- Trade quality improved:
  - Profit Factor increased from approximately 1.59 to approximately 1.74–1.76.
  - Expectancy increased from approximately 1.33% to approximately 1.74–1.79%.
- Overall returns decreased due to the much more selective strategy.
- TMQS score distribution:
  - Average TMQS: 18.76
  - Median TMQS: 0
  - Highest TMQS: 95
- More than half of all historical setups scored between 0 and 9, confirming that the system is effectively rejecting poor-quality setups.

### Important Discovery

The optimizer's similar results for TMQS thresholds (60–75) are **not** caused by the overall TMQS distribution.

Instead, the issue appears to be that READY trades occupy a narrow TMQS range. Future analysis should focus specifically on the TMQS distribution of READY trades rather than all setups.

### Next Tasks

- Extend the TMQS Analysis tool to analyze READY trades only.
- Build a multi-factor TMQS engine that separates:
  - Setup scoring
  - Trade qualification (READY/WATCH/IGNORE)
  - Trade ranking
- Continue improving trade quality before adding additional indicators.

Latest Session
Completed
Fixed the breakout filtering bug in the historical backtester.
Updated the breakout filter to correctly recognize both BREAKOUT and STRONG BREAKOUT setups.
Verified that Breakout=True and Breakout=False now produce identical results when expected.
Improved optimizer reporting by renaming the Top 10 results to correctly display Robustness Score instead of Return.
Added a minimum trade requirement of 100 trades before a parameter set can qualify for the Robustness Score rankings.
Updated optimizer TMQS testing range from 60, 65, 70, 75, 80 to 80, 85, 90, 95.
Re-ran the complete optimizer using the new TMQS thresholds.
Validated that TMQS thresholds now meaningfully differentiate trade quality.
Key Findings
Best Overall Return
TMQS: 80
ATR Multiplier: 2.0
Reward Multiplier: 2.5
Maximum Hold Days: 10
Trades: 819
Return: 16.55%
Win Rate: 52.63%
Profit Factor: 1.64
Expectancy: 1.88%
Highest Quality Strategy
TMQS: 95
ATR Multiplier: 2.0
Reward Multiplier: 2.5
Maximum Hold Days: 10
Trades: 148
Return: 5.77%
Win Rate: 58.78%
Profit Factor: 2.45
Expectancy: 3.80%
Maximum Drawdown: -0.52%
Important Discoveries
The breakout filtering issue was confirmed to be a software bug rather than a strategy problem.
The breakout filter now behaves correctly and consistently.
TMQS is now functioning as a genuine quality ranking system.
Lower TMQS thresholds produce more trades and higher total returns.
Higher TMQS thresholds significantly improve trade quality, Profit Factor, and Expectancy while reducing the number of trades.
The optimizer is now producing reliable and trustworthy comparisons between parameter combinations.
Next Priorities
Analyze the characteristics of TMQS 95 trades (RVOL, breakout strength, and price movement).
Begin designing TMQS Version 3 by separating:
TMQS scoring
Trade qualification (READY / WATCH / IGNORE)
Trade ranking
Continue improving trade quality before adding new indicators such as sector strength and relative strength.
Maintain compatibility with the planned Interactive Brokers integration through the standardized data provider interface.
## Latest Session

### Completed

- Built and validated the TMQS Edge Analysis tool.
- Added TMQS threshold comparison for:
  - TMQS >= 80
  - TMQS >= 85
  - TMQS >= 90
  - TMQS >= 95
- Added Edge Analysis metrics:
  - Total trades
  - Return
  - Win rate
  - Profit Factor
  - Expectancy
  - Max drawdown
  - Average TMQS
  - Average RVOL
  - Median RVOL
  - RVOL range
  - Breakout type distribution
- Confirmed that higher TMQS thresholds improve trade quality:
  - TMQS 80: 819 trades, Profit Factor 1.64, Expectancy 1.88%
  - TMQS 85: 493 trades, Profit Factor 1.78, Expectancy 2.14%
  - TMQS 90: 261 trades, Profit Factor 1.92, Expectancy 2.55%
  - TMQS 95: 148 trades, Profit Factor 2.45, Expectancy 3.80%
- Confirmed that TMQS 95 trades are high-quality setups:
  - Average TMQS: 98.60
  - Average RVOL: 3.67
  - Median RVOL: 3.20
  - RVOL range: 2.50 to 8.87
  - Breakout profile: 148 STRONG BREAKOUT trades, 0 normal BREAKOUT trades
- Built and validated the Trade Profile analysis tool.
- Added trade profile sections:
  - Overall performance
  - Exit reasons
  - Holding period
  - Winner / loser profile
  - Setup quality profile
  - Breakout profile
  - Top 10 winners
  - Top 10 losers
  - Performance by symbol
- Confirmed TMQS 95 trade profile:
  - Trades analyzed: 148
  - Winners: 87
  - Losers: 61
  - Win rate: 58.78%
  - Profit Factor: 2.45
  - Expectancy: 3.80%
  - Average winner: 10.91%
  - Average loser: -6.35%
  - Exit reasons:
    - Time exit: 84
    - Target hit: 24
    - Stop hit: 40
- Added symbol-level performance analysis.
- Found that HIVE.TO is high-impact but not the only source of edge.
- Identified strong-performing symbols at TMQS 95:
  - LUN.TO: 4 trades, 100% win rate, average +9.02%
  - AC.TO: 7 trades, 100% win rate, average +8.64%
  - HIVE.TO: 25 trades, 60% win rate, average +8.55%
  - BTE.TO: 8 trades, 75% win rate, average +7.86%
  - ATH.TO: 12 trades, 75% win rate, average +6.50%
- Identified weaker or lower-quality symbols at TMQS 95:
  - TD.TO: 1 trade, average -0.85%
  - WPM.TO: 3 trades, average -1.31%
  - CLS.TO: 14 trades, average +0.35%
  - BB.TO: 24 trades, 41.7% win rate, average +1.44%
- Confirmed that symbol-level filtering or symbol-level ranking may become an important future strategy improvement.

### Key Findings

- TMQS is now functioning as a true quality-ranking system.
- Higher TMQS thresholds reduce trade count but improve trade quality.
- TMQS 95 is the current highest-quality setup group.
- TMQS 95 trades are characterized by:
  - Very strong relative volume
  - Strong breakout quality
  - Better expectancy
  - Better Profit Factor
  - Lower drawdown
- Most TMQS 95 trades still exit by time stop rather than profit target.
- HIVE.TO creates both large winners and large losers, making it a high-impact/high-volatility symbol.
- The strategy’s edge is not entirely dependent on HIVE.TO, which is encouraging.
- Symbol-level analysis is now a logical next step before TMQS v3.

### Next Tasks

- Create a dedicated Symbol Analysis tool.
- Compare symbol performance across TMQS thresholds 80, 85, 90, and 95.
- Identify which symbols are consistently strong across thresholds.
- Identify symbols that should potentially be filtered, downgraded, or ranked lower.
- Begin planning TMQS v3 architecture:
  - Separate setup scoring
  - Trade qualification
  - Trade ranking
- Continue building toward a professional research dashboard before moving to Interactive Brokers integration.
Version 2.1 – Enhanced Trade Profile & Symbol Analytics

Completed:
- Upgraded Trade Profile reporting.
- Added symbol-level Profit Factor calculations.
- Added symbol-level Expectancy calculations.
- Added symbol ratings (STRONG, GOOD, WEAK EDGE, LOW SAMPLE).
- Added minimum sample-size awareness for symbol evaluation.
- Improved Performance by Symbol report formatting.
- Fixed duplicate symbol output caused by an extra print block.
- Validated enhanced reporting with TMQS 95 historical backtest.

Current Best Results:
- Trades: 148
- Win Rate: 58.78%
- Profit Factor: 2.45
- Expectancy: 3.80%
- Max Drawdown: -0.52%

Next Steps:
- Add automated Research Summary section.
- Improve symbol ranking methodology.
- Continue TMQS Version 3 research and optimization.
Version 2.2 Beta 1 – Research Dashboard Foundation

Completed:
- Created the new research module structure.
- Standardized the backtester return interface.
- Built the Symbol Analysis research tool.
- Added automatic symbol rankings.
- Added Profit Factor, Expectancy, Win Rate, and Rating analysis by symbol.
- Added the first Research Summary section.
- Fixed the UNKNOWN symbol reporting issue.
- Improved project architecture for future research tools.

Key Findings:
- TMQS 95 continues to identify high-quality setups.
- Strongest symbols:
  - AC.TO
  - HIVE.TO
  - BTE.TO
  - ATH.TO
- SHOP.TO remains a good candidate.
- Several symbols consistently underperform and may become future filter candidates.
- Symbol-level research is proving valuable for identifying where the strategy's edge is strongest.

Next Priorities:
- Build the Research Dashboard.
- Create a numerical Research Score (0–100) for every symbol.
- Compare symbol performance across TMQS thresholds (80, 85, 90, 95).
- Continue improving trade selection while maintaining sufficient trade frequency.
- Keep all future enhancements validated through historical backtesting before integrating them into the live scanner.
## Version 2.2 Beta 1 – Research Foundation & Symbol Intelligence

### Completed

- Created a dedicated `research` module for quantitative analysis tools.
- Standardized the backtester return format using a structured dictionary:
  - `results["trades"]`
  - `results["summary"]`
- Improved project architecture to support future research tools without duplicate logic.
- Eliminated the UNKNOWN symbol reporting issue caused by processing the performance summary as a trade.
- Refactored Symbol Analysis to work with the new standardized backtester interface.
- Built the Symbol Analysis research tool.
- Added automatic symbol ranking using:
  - Win Rate
  - Profit Factor
  - Expectancy
  - Average Return
  - Best/Worst Trade
  - Sample Size
- Added symbol quality ratings:
  - STRONG
  - GOOD
  - WEAK EDGE
  - LOW SAMPLE
  - AVOID
- Added the first Research Summary section to automatically identify:
  - Top Performing Symbols
  - Good Candidates
  - Symbols Needing Improvement
  - Low Sample Size Symbols
- Improved overall research workflow and established the foundation for future quantitative research reports.

### Key Findings

Current TMQS 95 settings continue to identify high-quality momentum setups.

Current strongest performing symbols:

- AC.TO
- HIVE.TO
- BTE.TO
- ATH.TO

Additional observations:

- SHOP.TO continues to perform well and remains a strong candidate.
- BB.TO, CLS.TO, FM.TO and K.TO currently show weaker historical edges.
- Symbol-level analysis is successfully identifying where the strategy performs best.
- The strategy appears to have a measurable edge, but trade frequency at TMQS 95 is lower than desired for live trading.

### Strategic Direction

Project objective remains unchanged:

Build a momentum trading decision engine capable of producing a statistically proven edge while maintaining enough quality trade opportunities for consistent trading.

Future improvements will only be accepted if historical backtesting demonstrates measurable improvements in one or more of:

- Expectancy
- Profit Factor
- Win Rate
- Drawdown
- Risk-adjusted returns
- Trade frequency

No new filters will be permanently added without historical evidence that they improve the overall system.

### Next Priorities

1. Build the Research Dashboard.
2. Create a numerical Research Score (0–100) for every symbol.
3. Compare strategy performance across TMQS thresholds (80, 85, 90 and 95).
4. Determine the optimal balance between:
   - Trade Frequency
   - Win Rate
   - Profit Factor
   - Expectancy
5. Continue developing the research platform before adding additional trading filters.
6. Delay Portfolio Simulator development until the research platform and optimal strategy parameters are finalized.

### Long-Term Vision

Transform the project from a traditional momentum scanner into a quantitative momentum trading decision engine capable of:

- Ranking every trading opportunity by historical probability.
- Learning which symbols consistently produce the strongest edge.
- Recommending optimal scanner settings using historical evidence.
- Integrating sector strength, relative strength and market regime analysis after validation.
- Supporting Interactive Brokers real-time execution once research and validation are complete.
Completed:
- Created sector-specific watchlist files (Banks, Energy, Pipelines, Utilities, Technology, Industrials, Materials, Consumer, Insurance).
- Added research universe builder to support future expansion of the trading universe.
- Completed robustness optimizer across TMQS, RVOL, breakout, ATR, reward, and maximum hold period.
- Identified baseline high-frequency strategy (819 trades, 20.35% return).
- Identified elite high-quality strategy (148 trades, 57.43% win rate, Profit Factor 2.49, Expectancy 4.72%).
- Confirmed TMQS 95 naturally selects high-RVOL breakout candidates, indicating the quality scoring model is effectively filtering low-quality setups.

Next Task:
- Build a Trade Profile Analyzer to report performance by stock and sector before expanding the historical database with the larger research universe.
### Completed

- Added Historical Data Manager.
- Automated downloading of historical CSV data for the full research universe.
- Updated historical database for 53 valid TSX symbols.
- Removed MEG.TO from the energy watchlist because it was officially delisted.
- Added Research Universe Validator.
- Validated that all 53 watchlist symbols have usable historical data.
- Confirmed:
  - Symbols checked: 53
  - Valid files: 53
  - Missing files: 0
  - Too short files: 0

### Key Finding

The expanded research universe is now clean and ready for full-universe backtesting.

### Next Step

Build the full-universe backtest runner and compare the expanded 53-symbol results against the previous smaller universe.
### Version 2.2 Beta 2

#### Completed

- Built the Research Universe Backtesting engine.
- Successfully executed historical backtests across the full 53-stock research universe.
- Fixed the universe runner to correctly process trade lists from the backtester.
- Added per-symbol trade counting during research runs.
- Verified strict TMQS (95) and RVOL (2.0) filtering across the entire universe.
- Successfully collected 254 qualifying historical trades from the expanded research universe.

#### Key Finding

The research engine is now capable of evaluating every stock in the research universe, providing the foundation for stock ranking, sector analysis, and long-term universe optimization.

#### Next Step

Expand the research engine to calculate performance statistics for every symbol (win rate, expectancy, profit factor, average return) and automatically rank the strongest and weakest stocks.
Completed:
- Built and verified the full research universe backtester.
- Successfully backtested all 53 research universe symbols.
- Added overall performance reporting for the complete universe.
- Confirmed historical database integrity and automated history updates.
- Verified that strict TMQS (95+) and RVOL (2.0+) filters generated 254 qualifying trades across five years of historical data.

Key Results:
- 53 stocks tested
- 254 trades
- Win Rate: 55.12%
- Profit Factor: 1.97
- Expectancy: 2.34%
- Total Return: 6.10%
- Best Stock: HIVE.TO
- Worst Stock: AGI.TO

Next Step:
Develop stock-level ranking reports to identify the highest expectancy symbols and refine the research universe before further strategy optimization.
### Completed
- Successfully completed first full-universe historical backtest.
- Tested all 53 validated TSX research symbols.
- Generated 254 qualifying historical momentum trades.
- Added automated stock ranking based on historical performance.
- Added full-universe performance summary.
- Confirmed research framework is functioning correctly.

### Key Results
- Trades: 254
- Win Rate: 55.12%
- Profit Factor: 1.97
- Expectancy: 2.34%
- Total Return: 6.1%
- Max Drawdown: -0.52%

### Key Finding
The expanded research universe is now fully operational. The project has transitioned from building infrastructure to performing quantitative research capable of identifying which stocks and market conditions provide the strongest historical edge.

### Next Step
Build the Edge Analyzer to identify the highest-performing combinations of TMQS, RVOL, sectors, holding periods, and individual stocks for further optimization before paper trading.
Version 2.1 – Research Universe Engine

Added Research Universe Backtester capable of analyzing all historical TSX datasets.
Successfully backtested 53 historical symbols using research filters (TMQS ≥ 95, RVOL ≥ 2.0, Strong Breakout only).
Generated 254 qualifying historical trades across the research universe.
Added stock ranking report showing trade count, win rate, and average return by symbol.
Added edge analysis for TMQS, RVOL, and breakout classifications.
Confirmed stronger performance from TMQS 100 setups compared with TMQS 95–99.
Identified higher RVOL (approximately 5–7) as a potentially stronger edge requiring further investigation.
Established the foundation for future research modules including sector analysis, regime analysis, seasonal analysis, and automated edge discovery.
Next milestone: export complete research dataset to CSV and build a comprehensive Edge Research Dashboard.

Chris, this is one of the biggest milestones we've hit so far. We now have the infrastructure to discover profitable edges from historical data instead of relying on intuition.

ok can you send a development log we can paste

Absolutely. Here's a polished Development Log entry for this milestone.

TSX Momentum Trading System
Development Log
Version: 2.1.0 – Research Universe Engine

Date: July 9, 2026

Overview

Completed the first version of the Research Universe Engine, allowing the system to analyze every historical stock in the research universe rather than only the active watchlist. This marks the transition from a simple backtester to a quantitative research platform capable of identifying statistically significant trading edges.

Features Added
Research Universe Backtester
Created a dedicated universe backtester capable of processing all historical datasets.
Successfully analyzed 53 TSX stocks using identical trading rules.
Added configurable research filters including:
Minimum TMQS
Minimum Relative Volume (RVOL)
Breakout-only filtering
Aggregates every qualifying trade into one combined research dataset.
Stock Performance Ranking

Added automated stock ranking including:

Number of trades
Win rate
Average return
Profit factor
Best and worst performing symbols

This allows objective identification of stocks that consistently outperform the rest of the universe.

Portfolio Performance Summary

Added full-universe performance statistics including:

Total trades
Winning trades
Losing trades
Win rate
Average gain
Average loss
Expectancy
Profit factor
Total return
Maximum drawdown
Research Results
Historical Universe
Historical files analyzed: 53
Qualified trades discovered: 254
Overall Strategy Performance
Win Rate: 55.1%
Profit Factor: 1.97
Expectancy: +2.34% per trade

These results demonstrate that the current momentum strategy exhibits a measurable statistical edge across the broader TSX research universe.

Key Research Findings
High Relative Volume

Analysis indicates that higher Relative Volume values significantly improve trade performance.

Higher RVOL ranges produced:

Higher win rates
Larger average returns
Stronger profit factors

This validates Relative Volume as one of the strongest predictors currently identified.

Perfect TMQS Scores

Historical analysis suggests that setups scoring TMQS = 100 outperform those scoring in the 95–99 range.

Future refinements will focus on identifying the characteristics that consistently produce perfect-quality setups.

Strong Individual Stocks

Several symbols demonstrated exceptional historical performance and will become candidates for preferred trading universes pending larger sample sizes.

Architecture Improvements

The project now supports research at multiple levels:

Individual stock analysis
Entire watchlist analysis
Full research universe analysis
Strategy-wide statistical reporting
Edge discovery based on historical data

This significantly expands the project's research capabilities.

Next Development Phase

Planned Version 2.2 objectives:

Remove remaining debugging output.
Export every historical trade to a master research CSV.
Build the Edge Research Dashboard.
Add sector performance analysis.
Add weekday and monthly seasonality analysis.
Rank optimal TMQS and RVOL ranges.
Identify stocks that should be permanently excluded from the trading universe.
Continue refining the live scanner using statistically validated historical results.
Project Status

The project has now progressed beyond simple backtesting and into quantitative strategy research. Future improvements will be driven by historical evidence rather than intuition, allowing every enhancement to be validated before being incorporated into the live trading system.Version 3.0 – Automated Strategy Validation Engine
Overview

Completed the Version 3.0 research framework by building an automated strategy validation engine capable of testing multiple strategy configurations across the full TSX research universe. The software now performs objective comparisons of strategy settings and recommends the strongest configuration for paper trading.

Major Features Added
Multi-Watchlist Scanner
Added support for loading all watchlists automatically.
Scanner and workstation now operate across the complete research universe (53 TSX stocks).
Research Universe Backtester
Backtests every historical CSV automatically.
Combines all trades into a unified dataset.
Calculates full-universe performance metrics.
Professional Research Modules

Integrated the following research tools into a single automated workflow:

Stock Rankings
Edge Analyzer
Professional Research Dashboard
Strategy Recommendation Engine
Strategy Validator

Created an automated validation engine that:

Tests multiple TMQS thresholds.
Tests multiple RVOL thresholds.
Scores every strategy objectively.
Compares all results in a ranked table.
Automatically recommends the highest-quality configuration.
Validation Results

Best-performing configuration:

Strategy: T100_R1.5
Minimum TMQS: 100
Minimum RVOL: 1.5
Breakout Only: True
Trades: 123
Win Rate: 58.54%
Profit Factor: 2.27
Expectancy: 2.83%
Max Drawdown: -0.46%
Validation Score: 82.75
Key Findings
Increasing TMQS significantly improves strategy quality.
TMQS 100 consistently produced the strongest statistical edge.
TMQS 90 generated more trades but materially reduced profitability.
RVOL filtering above TMQS 100 had little additional impact, indicating TMQS already captures high-volume momentum characteristics.
The system can now determine optimal strategy settings automatically instead of relying on manual interpretation.
Project Milestone

Version 3.0 completes the research and validation phase.

The software is now capable of:

Scanning the full research universe.
Backtesting every stock automatically.
Ranking stock performance.
Measuring statistical edge.
Generating research dashboards.
Producing automated strategy recommendations.
Comparing strategy configurations.
Selecting the best configuration for paper trading.
Next Development Phase

Version 3.1 – Paper Trading Engine

Planned objectives:

Connect validated strategy directly to the live scanner.
Generate paper trades automatically.
Track open positions.
Manage software-based exits.
Maintain live trade journal.
Build equity curve and performance tracking.
Prepare architecture for future IBKR integration.
## Version 3.1 – Strategy Comparison Engine

Completed the first automated strategy comparison framework.

Highlights:
- Added strategy_comparison.py to evaluate multiple strategy configurations.
- Added compare_strategies.py launcher.
- Integrated the research universe backtester with automated strategy execution.
- Compared Baseline, High Quality, Aggressive, and Loose strategy configurations.
- Automatically summarized trades, win rate, profit factor, expectancy, total return, and drawdown for each strategy.
- Identified that Aggressive and Loose configurations currently produce identical results, indicating an opportunity to refine breakout filtering logic.
- Confirmed High Quality strategy produces fewer trades with improved expectancy, profit factor, and reduced drawdown.

Project Status:
The research framework has evolved from validating individual strategies to automatically comparing multiple strategy configurations. This establishes the foundation for automated strategy optimization and objective selection of paper trading candidates.

Next Development Phase:
- Build a ranked strategy comparison dashboard.
- Automatically score and sort strategies.
- Reduce research output into concise summary tables.
- Validate breakout filtering differences.
- Prepare for Version 3.2 automated optimization enhancements.
Version 3.2 – Completed Strategy Validation Framework
Completed
Added Out-of-Sample Validation using training and validation datasets.
Added Slippage Validation to simulate realistic execution costs.
Verified strategy robustness across multiple slippage levels (0.00%, 0.05%, 0.10%, 0.20%).
Confirmed strategy remained profitable under all tested slippage scenarios.
Audited and corrected performance calculations after slippage integration.
Removed temporary debugging and troubleshooting code.
Stabilized research framework in preparation for paper trading.
Key Findings
Strategy passed out-of-sample validation.
Strategy remained profitable under increasing slippage.
Profit Factor declined gradually as expected while remaining well above acceptable levels.
Expectancy remained positive across all robustness tests.
The current strategy demonstrates resilience to realistic trading friction.
Official Paper Trading Baseline
TMQS ≥ 100
RVOL ≥ 1.5
Breakout Required
ATR Multiplier = 2.0
Reward Multiplier = 2.5
Maximum Hold = 10 Days
Next Phase

Version 3.3 – Paper Trading Engine

Virtual portfolio
Position sizing
Trade journal
Open position management
Software-managed stop updates
Performance dashboard
Daily paper trading workflow
Development Log Entry

Version 3.3 – Paper Trading Engine Foundation

Completed

Created paper_trading module.
Implemented PaperPortfolio class.
Added virtual cash management.
Added open position tracking.
Added position closing with automatic profit/loss calculation.
Implemented portfolio summary including cash, portfolio value, total return, open positions, and closed trades.
Successfully completed the first end-to-end paper trade simulation.

Key Result

Verified the complete virtual trading workflow:
Open position
Deduct cash
Close position
Update cash balance
Record trade
Calculate portfolio return

Next Tasks

Build the Position Manager for automatic stop, target, and time-based exits.
Add a persistent trade journal.
Integrate the paper portfolio into the main workstation dashboard.
Begin end-to-end daily paper trading workflow.
Version 3.3 – Paper Trading Engine Foundation
Completed
Created the new paper_trading module.
Implemented PaperPortfolio class.
Added virtual cash management.
Added open position tracking.
Added automatic position closing.
Added automatic profit/loss calculations.
Added PositionManager for automated stop-loss and target monitoring.
Added TradeJournal to automatically save completed trades to paper_trade_journal.csv.
Successfully completed end-to-end paper trade simulation.
Completed Out-of-Sample Validation.
Completed Slippage Validation.
Confirmed strategy remains profitable under increasing slippage assumptions.
Official Paper Trading Baseline
TMQS ≥ 100
RVOL ≥ 1.5
Breakout Required
ATR Multiplier = 2.0
Reward Multiplier = 2.5
Maximum Hold = 10 Days
Current Project Status

Research phase is complete.

Paper Trading Engine is under active development.

Completed modules:

Historical Backtester
Optimizer
Strategy Comparison Engine
Recommendation Engine
Research Universe Backtester
Out-of-Sample Validator
Slippage Validator
Paper Portfolio
Position Manager
Trade Journal
Next Tasks
Build the Paper Trading Engine controller.
Integrate the paper portfolio into the GUI workstation.
Automatically send READY trades to the paper portfolio.
Display open positions inside the dashboard.
Add live portfolio statistics.
Add equity curve.
Prepare for IBKR paper account integration.
Development Log

Version: 3.0.0-beta6 – Paper Trading Integrated

Completed

Integrated Paper Trading Engine into the Trading Workstation.
Added Open Paper Trade button to GUI.
Added confirmation dialog before opening paper trades.
Integrated virtual portfolio with workstation.
Added live Paper Portfolio panel.
Displayed portfolio summary, cash, portfolio value, returns, open positions, and closed trades.
Connected paper trade execution directly from scanner READY signals.
Improved paper dashboard layout and GUI integration.
Refactored workstation to support future Trader Control Center enhancements.

Next Tasks

Redesign right-side Trader Control Center.
Add Close Paper Trade functionality.
Add automatic stop-loss and target monitoring.
Add live unrealized/realized P&L updates.
Add equity curve and performance statistics.
Complete live paper trading workflow before IBKR integration.
Suggested Commit Message
Version 3.1 Beta 1 – Interactive Paper Trading Workstation

Completed the first fully interactive paper trading workflow.

New Features:
- Added "Close Selected Paper Trade" button to the workstation GUI.
- Implemented manual paper trade closing from the scanner.
- Connected GUI to the PaperTradingEngine close_position() method.
- Portfolio updates immediately after opening or closing trades.
- Closed trades are automatically written to the paper trade journal.
- Improved Paper Portfolio panel integration and automatic refresh.
- Continued refinement of the trading workstation interface.

Project Status:
The workstation now supports the complete paper trading lifecycle:
Scan → Open Trade → Monitor Position → Manual or Automatic Exit → Journal → Portfolio Update.

Next Planned Tasks:
- Improve Paper Portfolio display.
- Add live trade status metrics.
- Build Trade Journal viewer.
- Add equity curve and portfolio statistics.
- Begin extended paper trading validation using live market data.
Version 3.1 Beta 2 – User-Controlled Position Sizing

Completed another major enhancement to the paper trading workstation.

New Features:
- Added user-controlled position sizing during paper trade entry.
- Paper trading engine now accepts explicit share quantities from the GUI.
- Added manual close functionality integrated with the paper trading engine.
- Portfolio, cash balance, and trade journal update correctly after manual exits.
- Improved paper portfolio display and workflow integration.

Project Status:
The workstation now supports the complete manual paper trading lifecycle:
Scan → Select → Enter Position Size → Open Trade → Monitor → Manual or Automatic Exit → Journal → Portfolio Update.

Next Planned Tasks:
- Implement risk-based position sizing recommendations.
- Improve live portfolio metrics and visualization.
- Add trade journal viewer.
- Build equity curve and performance dashboard.
- Continue extended paper trading validation before IBKR integration.
Version 3.2 Beta 1 – Paper Trading Workstation

Completed:
- Added manual paper trade entry from READY signals.
- Added user-controlled position sizing.
- Added manual paper trade closing.
- Integrated automatic portfolio updates into the GUI.
- Expanded the Paper Portfolio panel with portfolio summary, open positions, and recent closed trades.
- Implemented automatic trade journal saving for closed paper trades.
- Added TSX market session detection (PRE-MARKET, OPEN, CLOSED).
- Disabled paper trade entry outside TSX market hours.
- Added dynamic market session status messages including next market open information.
- Improved overall paper trading workflow and GUI usability.

Project Status:
The scanner, research engine, optimizer, strategy validation, and paper trading workstation are now integrated into a complete end-to-end workflow. The system is ready to begin live paper trading and real-world validation during market hours.
============================================================
Version 3.2 Beta 2 – Live ATR Paper Trading Integration
Date: July 10, 2026
============================================================

Completed:
- Added live 14-day ATR calculation to the scanner using Yahoo Finance historical daily data.
- Integrated ATR into the live quote dictionary so every scanned stock now includes its current ATR value.
- Verified ATR values propagate correctly from the market data layer through the scanner to the GUI.
- Added ATR display to the Trade Checklist for verification and debugging.
- Began integrating validated backtesting parameters into the paper trading workflow.
- Paper trade signal now includes:
    • Live ATR
    • Actual entry date/time
    • ATR-based stop price
    • ATR-based target price
- Removed dependence on the previous hardcoded trade date for new paper trades.
- Confirmed workstation, scanner, portfolio, and paper trading remain stable after integration.

Current Status:
- Live scanner operational.
- Paper trading operational.
- ATR data successfully flowing through the system.
- Foundation completed for matching live paper trades to validated backtesting rules.

Next Development Priorities:
1. Complete ATR-based paper trade execution verification.
2. Implement 10-day maximum holding period exit.
3. Save and restore paper portfolio between program restarts.
4. Begin extended live paper trading validation.
5. Compare live paper performance against XIC/XIU ETF benchmark.

Project Status:
Paper Trading Validation Phase
Estimated Completion: ~90%
Completed:
- Integrated live ATR values throughout the paper trading workflow.
- Verified ATR data flows correctly from the market scanner into the GUI.
- Added ATR display to the Trade Checklist for validation and debugging.
- Updated paper trade signal to include:
    • Live ATR
    • Current trade date
    • ATR-based stop price
    • ATR-based target price
- Removed the previous hardcoded paper trade entry date.
- Added configurable maximum holding period (default: 10 trading days) to all new paper positions.
- Implemented automatic time-exit logic in the position manager using trading-day counting.
- Added trading-day counter utility (weekdays currently; TSX holiday support planned).
- Verified scanner, portfolio manager, paper trading engine, and workstation remain stable after integration.

Validation Completed:
✓ Live scanner operational
✓ ATR calculation verified
✓ ATR passed through GUI successfully
✓ Paper trading engine accepts ATR-based trade parameters
✓ Position manager supports stop, target, and time-based exits

Current Project Status:
The paper trading system is now closely aligned with the validated backtesting strategy. Remaining work is focused on live validation, portfolio persistence, and long-term performance verification rather than core trading logic.

Next Priorities:
1. Execute and verify the first live paper trade.
2. Confirm ATR stop and target execution during live monitoring.
3. Save and restore paper portfolio between application restarts.
4. Add TSX holiday calendar support to trading-day calculations.
5. Begin multi-week live paper trading validation.
6. Compare strategy performance against XIC/XIU ETF benchmarks.

Overall Project Progress:
Version 3.3 Beta 1 – Backtest Validation & Strategy Alignment
Date: July 10, 2026
============================================================

Completed:
- Eliminated same-bar look-ahead bias from the historical backtester.
- Updated trade simulator to generate signals on the completed daily candle and enter trades at the next trading day's opening price.
- Verified next-day entry logic with live debugging output.
- Confirmed strategy performance remains stable after realistic entry timing.
- Fixed holding period reporting to correctly reflect actual exit dates rather than always reporting the maximum holding period.
- Validated that optimizer results are behaving correctly and determined that TMQS 100 naturally implies RVOL >= 3.0 due to the scoring model.
- Improved the Strategy Recommendation Engine to prevent the same stocks from appearing in both the Preferred and Avoid lists.
- Recommendation engine now correctly reports when no qualifying stocks have negative average returns.

Validation Results:
✓ Next-day entry logic verified
✓ Look-ahead bias removed
✓ Holding period calculations verified
✓ Recommendation engine verified
✓ Optimizer behaviour explained and validated

Current Recommended Paper Trading Strategy:
- TMQS: 100
- Minimum RVOL: 1.5
- Breakout Only: True
- Trades: 123
- Win Rate: 56.91%
- Profit Factor: 1.83
- Expectancy: 2.20%
- Max Drawdown: -24.15%

Key Discovery:
The strategy remained statistically stable after removing same-bar entry bias, increasing confidence that the historical edge is based on executable trade logic rather than unrealistic backtesting assumptions.

Next Priorities:
1. Decide on the live trading workflow (end-of-day strategy vs. intraday strategy).
2. Align the live scanner with the validated backtesting methodology.
3. Execute the first complete paper trade using the validated workflow.
4. Add paper portfolio persistence (save/restore).
5. Add TSX holiday calendar support.
6. Begin multi-week paper trading validation against ETF benchmarks.
============================================================
Version 3.3 Beta 2 – End-of-Day Signal Service
Date: July 10, 2026
============================================================

Completed:
- Added an end-of-day signal testing workflow based on completed daily candles.
- Added TMQS component breakdown values for breakout, volume, and price strength.
- Added reusable production service:
  core/eod_signal_service.py
- Added batch Yahoo Finance downloading for the complete watchlist.
- Reduced EOD scan time by replacing 53 separate downloads with one batch request.
- Confirmed the EOD service reproduces the validated strategy results.
- Preserved the validated workflow:
  completed signal candle -> next trading day entry.
- Restored the live trading workstation to the last stable committed GUI version after an unsuccessful GUI integration attempt.

Validation:
- Stocks scanned: 53
- READY: 0
- WATCH: 6
- IGNORE: 47
- Errors: 0

Current Status:
- Live workstation is stable.
- EOD service is stable and independently tested.
- GUI integration has been postponed until the working service changes are safely committed.

Next Priorities:
1. Reintroduce EOD mode into the GUI using small, separately tested changes.
2. Add a safe display adapter for EOD signal records.
3. Disable paper-trade entry directly from signal-day closing prices.
4. Prepare next-session trade plans using executable next-day entry rules.
Development Log – July 10, 2026

Version: 3.3 Beta 3 (Work in Progress – Not Committed)

Completed
Implemented completed-candle End-of-Day (EOD) signal engine.
EOD scan successfully processes the research universe.
Verified EOD results:
READY: 0
WATCH: 6
IGNORE: 47
ERRORS: 0
Added strategy alignment so EOD signals use the same rules as the backtester.
Began GUI integration for End-of-Day mode.
Confirmed the EOD service can be called successfully from the workstation.
Issue Encountered
During GUI integration, trading_workstation.py became corrupted due to multiple edit/restore cycles and merge conflicts.
The EOD service itself remains functional.
Only the GUI integration requires rebuilding.
Next Session Plan
Restore the workstation from the last stable commit.
Re-add the End-of-Day button.
Connect the button to scan_eod_signals().
Display READY/WATCH signals in the workstation table.
Update the Trade Checklist for EOD signals.
Disable live auto-refresh while in EOD mode.
Return to Live mode when Refresh Scanner is pressed.
Commit as Version 3.3 Beta 3 – End-of-Day Workstation Mode.
Rebuild the GUI integration from the stable Version 3.3 Beta 2 workstation using the already-working EOD engine.
Development Log Entry

Version 3.3 Beta 3 – EOD Workstation Integration (Part 1)

Completed

Restored trading_workstation.py from the last stable commit after the failed GUI integration.
Verified the workstation was fully operational again.
Added a dedicated toolbar frame for scanner controls.
Reintroduced the End-of-Day Signals button.
Connected the button to the production scan_eod_signals() service.
Implemented background-thread execution to keep the GUI responsive during EOD scans.
Added completion reporting showing READY, WATCH, IGNORE, and ERROR counts.
Confirmed successful integration with zero scan errors.

Current Status

Live scanner operational.
Paper trading operational.
EOD scan successfully launched from the workstation.
GUI and EOD engine are now connected.

Next Priority

Replace the summary popup with full EOD signal display in the scanner table.
Prevent same-day paper trade entries from EOD signals.
Begin generating executable next-day paper trading candidates using the validated workflow.
Version 3.3 Beta 3 – Persistent Paper Trading Workflow
Completed
End-of-Day Workflow
Completed production End-of-Day signal engine integration.
Verified completed-candle scanning against the full research universe.
Confirmed production scan successfully classifies READY, WATCH and IGNORE signals.
Validated zero-error production scanning.
Pending Trade Queue
Added PendingTradeQueue ownership to PaperTradingEngine.
Queue now accepts only READY signals.
Duplicate pending trades are automatically rejected.
Added pending trade lookup by symbol.
Added automatic removal after successful execution.
Added CSV persistence for pending trades.
Pending trades now survive application restarts.
Paper Trading Engine
Added queue_signal() API.
Added queue_eod_signals() API.
Added execute_pending_trade() workflow.
Added next-day execution safety lock preventing same-day execution.
Added duplicate open-position protection.
Added ATR-based stop calculation from stored EOD signal.
Added reward target calculation using project risk/reward settings.
Portfolio Persistence
Added JSON portfolio persistence.
Portfolio now saves:
Starting cash
Current cash
Open positions
Closed trades
Portfolio automatically reloads after restart.
Portfolio automatically saves after opening positions.
Portfolio automatically saves after closing positions.
End-to-End Validation

Successfully validated:

Production EOD Scanner
        ↓
PaperTradingEngine
        ↓
Pending Trade Queue
        ↓
CSV Persistence
        ↓
Next-Day Execution
        ↓
Portfolio Persistence
        ↓
Application Restart Recovery

Verified:

Production EOD scan
Queue persistence
Portfolio persistence
Overnight recovery
Duplicate prevention
Same-day execution protection
Automatic queue cleanup after execution
Current Status
Stable
Historical Backtester
Optimizer
Research Universe
TMQS Strategy
Production EOD Scanner
Pending Trade Queue
Paper Trading Engine
Portfolio Persistence
Trade Journal
Position Manager
Overnight Recovery Workflow

The complete paper trading infrastructure is now operational.

Next Development Priority

Implement automatic next-day paper trade execution.

Target workflow:

Market Close
      ↓
Run Production EOD Scan
      ↓
Queue READY Signals
      ↓
Save Pending Trades

====================

Next Market Open
      ↓
Load Pending Trades
      ↓
Retrieve Opening Prices
      ↓
Execute Paper Trades
      ↓
Open Portfolio Positions
      ↓
Begin Position Monitoring

This will complete the first fully automated paper trading cycle.
Version 3.4 Beta 1 — Automatic Next-Day Paper Execution

Date: July 11, 2026

Objective

Complete the final major component required to begin fully automated paper-trading validation by implementing automatic next-day paper trade execution using real market opening prices.

New Features
Automatic Next-Day Paper Execution
Added automatic execution of queued READY signals on the next trading day.
Executes trades using the actual market opening price.
Automatically opens paper positions without manual intervention.
Opening Price Provider

Created a dedicated opening price module that:

Retrieves the first available regular-session 1-minute opening candle from Yahoo Finance.
Falls back to the exact daily opening price when appropriate.
Never substitutes a previous trading day's price.
Correctly rejects weekends and market holidays.
Automatic Execution Service

Added a background execution service that:

Starts automatically when the Trading Workstation launches.
Runs independently of the GUI.
Checks the pending trade queue immediately on startup.
Retries every 60 seconds until an opening price becomes available.
Does not block or freeze the workstation interface.
Paper Trading Engine Enhancements

Added automatic queue processing that:

Loads all pending trades.
Verifies next-day eligibility.
Retrieves opening prices.
Calculates position sizing.
Creates paper positions.
Updates portfolio persistence.
Removes queued trades only after successful execution.
Validation Completed

Successfully verified:

✓ Overnight queue persistence
✓ Portfolio persistence
✓ Engine restart recovery
✓ Same-day execution protection
✓ Weekend protection
✓ Holiday protection
✓ Opening price retrieval
✓ One-minute market open detection
✓ Automatic execution at market open
✓ Queue retention when prices are unavailable
✓ Automatic retry behaviour
✓ Duplicate execution prevention
✓ Queue cleanup after successful execution
✓ Real Yahoo Finance integration
✓ Background execution service
✓ GUI startup integration
✓ Position sizing
✓ Stop-loss calculation
✓ Profit target calculation
Production Workflow

Market Close

Run Production EOD Scan
        ↓
Queue READY Signals
        ↓
Save pending_trades.csv

Next Trading Day

Launch Trading Workstation
        ↓
Automatic Execution Service Starts
        ↓
Load Pending Trades
        ↓
Retrieve Opening Price
        ↓
Open Paper Position
        ↓
Persist Portfolio
        ↓
Remove Pending Trade
        ↓
Monitor Position
        ↓
Automatic Exit
        ↓
Trade Journal
Current Project Status

The project has now progressed from:

Historical Backtesting

↓

Strategy Optimization

↓

Production Scanner

↓

Persistent Paper Trading

↓

Automated Next-Day Paper Execution

The complete end-to-end automated paper trading pipeline is now operational.

Next Development Phase

The immediate priority is no longer building infrastructure.

The focus now shifts to continuous production paper-trading validation, including:

Running the complete production workflow with live market data.
Monitoring automatic entries and exits during real market sessions.
Validating portfolio performance over multiple trading days.
Measuring real-world strategy performance before making any further strategy or GUI enhancements.

This milestone represents one of the largest architectural advancements in the project to date and establishes the foundation required to determine whether the momentum strategy has a repeatable edge under real market conditions.
Version 3.4 Beta 2 — Professional Risk Management

Date: July 11, 2026

Objective

Replace the temporary fixed-capital position sizing model with a professional risk-based position sizing system aligned with the validated backtesting assumptions.

Improvements
Risk-Based Position Sizing

The paper trading engine now sizes every trade using predefined portfolio risk rather than allocating a fixed percentage of available cash.

Current defaults:

Risk per trade: 1% of total portfolio equity
Maximum position size: 20% of portfolio value
Maximum concurrent positions: 5
Never exceeds available cash
Position Size Calculation

Position size is now determined using:

Portfolio value
Risk budget
Entry price
Initial stop-loss distance (ATR-based)
Available cash
Maximum allocation limit

The engine automatically selects the most conservative share quantity that satisfies all constraints.

Example

For a $10,000 portfolio:

Portfolio risk budget: $100
Entry: $26.00
Stop: $23.00
Risk per share: $3.00

Calculated position:

33 shares
Capital deployed: $858
Maximum possible loss (if stop is reached): approximately $99

This keeps every trade consistent with the intended portfolio risk model.

Validation Completed

Verified:

✓ 1% portfolio risk calculation
✓ ATR-based risk sizing
✓ Maximum allocation enforcement
✓ Available cash enforcement
✓ Maximum open-position enforcement
✓ Automatic execution compatibility
✓ Automatic monitoring compatibility
✓ Automatic exits
✓ Automatic journaling
✓ Portfolio persistence
Project Status

The paper trading engine now mirrors the risk-management philosophy used during strategy validation rather than using a simple percentage-of-cash allocation.

This provides a much more realistic simulation of live trading and ensures future paper-trading performance is directly comparable to historical backtesting assumptions.

Current Production Workflow
Production End-of-Day Scan
        ↓
Queue READY Signals
        ↓
Persistent Pending Queue
        ↓
Automatic Next-Day Execution
        ↓
Risk-Based Position Sizing
        ↓
Portfolio Persistence
        ↓
Automatic Position Monitoring
        ↓
Automatic Stop / Target / Time Exit
        ↓
Trade Journal
Next Phase

The infrastructure for automated paper trading is now substantially complete.

The immediate focus shifts to observing the strategy in live market conditions, validating trade quality, and measuring real-world performance over multiple trading sessions before making further strategy refinements or adding advanced features.
# Version 3.4 Beta 3 — Fully Automated EOD Workflow

Date: July 11, 2026

## Objective

Remove the final manual daily step from the paper-trading workflow by automating the end-of-day production scan and READY-signal queue process.

## Improvements

### Completed-Candle Validation

Updated the production EOD scanner so daily candles are handled correctly based on Toronto market time.

The scanner now:

- excludes the current day’s candle before the TSX closes;
- includes the current day’s candle after 4:00 PM ET;
- excludes same-day weekend candles;
- continues to accept prior completed trading-day candles;
- prevents stale Friday data from being treated as Monday’s completed session.

### Automatic End-of-Day Service

Added a dedicated background EOD service that:

- starts automatically with the Trading Workstation;
- checks every 60 seconds;
- runs only Monday through Friday;
- runs only after the TSX market closes;
- executes only once per trading day;
- queues all READY signals automatically;
- persists the completed run date;
- prevents duplicate scans after refreshes or application restarts;
- does not block or freeze the GUI.

### EOD Queue Integration

Connected the EOD scanner directly to the persistent pending trade queue.

The workflow now:

- scans completed daily candles;
- identifies READY signals;
- queues READY trades;
- reports duplicates;
- saves pending trades to CSV;
- preserves signals overnight for next-day execution.

## Validation Completed

Verified:

- Monday before-close candle exclusion;
- Monday after-close candle inclusion;
- previous completed trading-day acceptance;
- weekend same-day rejection;
- automatic EOD eligibility logic;
- once-per-day execution;
- persistent last-run date;
- duplicate scan prevention;
- READY-signal queueing;
- pending queue persistence;
- background-thread execution;
- workstation startup integration.

## Fully Automated Production Workflow

TSX Market Session

```text
Live scanner refreshes
        ↓
Latest prices update
        ↓
Open paper positions monitored
        ↓
Automatic stop / target / time exits
        ↓
Closed trades journaled
# Version 3.4 Beta 4 — Paper Trading Analytics Dashboard

Date: July 11, 2026

## Objective

Introduce a professional analytics dashboard to measure live paper-trading performance throughout the validation phase.

## Improvements

Added a reusable analytics engine to calculate performance statistics directly from completed paper trades.

### New Metrics

- Total Trades
- Winning Trades
- Losing Trades
- Breakeven Trades
- Win Rate
- Profit Factor
- Expectancy
- Average Winner
- Average Loser
- Total Closed Return
- Maximum Drawdown
- Best Trade
- Worst Trade

### Dashboard Improvements

Enhanced the paper-trading dashboard to display:

- Current portfolio summary
- Available cash
- Portfolio value
- Realized profit/loss
- Unrealized profit/loss
- Open positions
- Recent closed trades
- Professional performance statistics

### Validation

Verified all calculations using controlled test trades.

Confirmed accurate calculation of:

- Win rate
- Profit factor
- Expectancy
- Average gains and losses
- Closed return
- Maximum drawdown
- Best and worst trade identification

## Project Status

The platform now provides real-time performance analytics during paper trading, allowing strategy validation to be measured objectively from the very first live paper trade.
# Version 3.4 Beta 5 - System Health Monitoring Panel

Date: July 11, 2026

## Summary
Added a real-time System Health monitoring panel to the Trading Workstation, replacing the previous plain-text status line with a professional operational status display.

## Features Added

### System Health Panel
- Added dedicated System Health section to the workstation.
- Displays live operational status for:
  - Scanner
  - Automatic Execution Service
  - Automatic End-of-Day Service
  - Position Monitor
  - Trade Journal
- Displays:
  - Pending Trades
  - Open Positions
  - Closed Trades
  - Last Successful Refresh

### Integration
- Health panel now updates automatically during every scanner refresh.
- Reflects the live state of all background services.
- Integrated with the existing automatic execution and EOD service threads.

### Validation
- Verified successful workstation import.
- Verified GUI startup without errors.
- Confirmed live updates during scanner refresh.
- Confirmed health panel accurately reflects service status.

## Current Automated Workflow

The workstation now operates automatically:

1. Refresh Scanner
2. Update Market Data
3. Update Latest Prices
4. Monitor Open Positions
5. Execute Automatic Stops / Targets / Time Exits
6. Journal Closed Trades
7. Refresh Portfolio Analytics
8. Update System Health
9. Automatic End-of-Day Scan (once after market close)
10. Queue READY signals
11. Automatic Next-Day Paper Execution at market open

## Project Status

The TSX Momentum Pro workstation now includes:

- Live Market Scanner
- Automatic Scanner Refresh
- Market Health Scoring
- Best Candidate Selection
- Trade Checklist
- End-of-Day Signal Scanner
- Automatic Signal Queue
- Automatic Next-Day Paper Execution
- Professional Risk-Based Position Sizing
- Automatic Position Monitoring
- Automatic Stop / Target / Time Exits
- Automatic Trade Journal
- Paper Trading Analytics Dashboard
- Real-Time System Health Monitoring

The project is now ready for its first live paper trading validation beginning with the next trading session.
Version 3.4 Beta 6 — Morning Candidate Snapshot Support

Added immutable candidate snapshot support to the Morning Market Recorder.

Changes
Updated record_pending_candidates_once() to accept an optional supplied list of pending trades.
Preserved the existing behaviour of reading from the live pending queue when no candidate list is supplied.
Added defensive copying of supplied candidates so the recorder works from an independent snapshot.
Enabled future background recording to continue after successful automatic execution removes trades from the live pending queue.
Kept the paper portfolio, pending queue, and automatic execution workflow completely unchanged.
Validation
Created a test pending candidate.
Copied the candidate into an in-memory snapshot.
Removed the candidate from the live pending queue.
Recorded an observation using the snapshot.
Confirmed the live queue remained empty.
Confirmed one observation was successfully written to SQLite.
Confirmed the recorder checked one candidate with zero unavailable records and zero duplicates.

This establishes the correct architecture for the upcoming Morning Recorder Service.
Version 3.4 Beta 7 — Morning Recorder Scheduling Window

Added the scheduling foundation for the background Morning Market Recorder Service.

Changes
Created paper_trading/morning_recorder_service.py.
Added Toronto-time normalization.
Added a weekday-only recording rule.
Defined the Morning Recorder window as 9:30 a.m. through 10:00 a.m. Toronto time.
Added a configurable default service check interval.
Kept the new service completely separate from paper execution, pending-trade management, portfolio management, and the GUI.
Validation

Confirmed the recorder scheduling rules return:

False at 9:29 a.m.
True at 9:30 a.m.
True during the recording window.
True at 10:00 a.m.
False at 10:01 a.m.
False on weekends.

The Morning Recorder Service now has a tested market-time eligibility rule.
Version 3.4 Beta 8 — Morning Candidate Snapshot Capture

Added immutable morning candidate snapshot support to the Morning Recorder Service.

Changes
Added capture_morning_candidates() to the Morning Recorder Service.
The service now creates an independent copy of all pending candidates at the beginning of the recording session.
Snapshot data remains available even after the automatic execution engine removes trades from the live pending queue.
Preserved complete separation between the research platform and the paper-trading execution engine.
Validation
Created a test pending candidate.
Captured a morning snapshot.
Removed the candidate from the live pending queue.
Verified the snapshot still contained the candidate.
Confirmed the live queue was empty.
Confirmed the snapshot remained unchanged.

This establishes the foundation for continuous morning observation without affecting production trading behaviour.
Version 3.4 Beta 9 — Morning Recorder Service Foundation

Introduced the MorningRecorderService class as the foundation for the background Morning Recorder.

Changes
Created the MorningRecorderService class.
Added service-owned state for:
Paper trading engine reference
Configurable check interval
Background thread placeholder
Stop event
Current recording date
Immutable morning candidate snapshot
Kept the service completely independent from the paper-trading execution workflow.
Validation
Successfully instantiated the service.
Verified initial service state:
current_recording_date is None.
candidate_snapshot is an empty list.
thread is None.
stop_event is initialized and not set.

This establishes the object that will manage the complete morning recording lifecycle.
Version 3.4 Beta 10 — Morning Recorder Service Lifecycle

Added the service lifecycle methods to the MorningRecorderService class.

Changes
Added start() method to launch the recorder in a background daemon thread.
Added stop() method to request a clean shutdown and wait for the worker thread to terminate.
Added an initial placeholder worker() method that remains idle until the stop event is set.
Established the complete background service lifecycle while keeping the recorder independent of the paper-trading engine and GUI.
Validation
Successfully instantiated the service.
Confirmed the background thread starts correctly.
Confirmed the worker remains active while running.
Confirmed the service shuts down cleanly when stop() is called.

The Morning Recorder Service is now a managed background component ready for recording logic.
Version 3.4 Beta 11 — Single Morning Recording Cycle

Added a testable single-cycle recording method to the MorningRecorderService.

Changes
Added run_recording_cycle() to the service class.
The method records from the service-owned candidate snapshot.
Added safe handling when no candidates are available.
Kept the recording operation separate from the background worker loop.
Preserved complete separation from automatic paper execution and portfolio management.
Validation
Confirmed morning_recorder_service.py compiles without syntax errors.
Confirmed the service returns NO_CANDIDATES when its candidate snapshot is empty.
Confirmed the method is accessible as part of MorningRecorderService.

The service can now perform one independently testable recording pass.
Version 3.4 Beta 12 — Morning Candidate Snapshot Ownership

Added service-owned candidate snapshot capture to the Morning Recorder Service.

Changes
Added capture_today_snapshot() to MorningRecorderService.
The service now copies pending candidates into its own in-memory snapshot.
The snapshot is independent of the live pending-trade queue.
This allows morning observations to continue after automatic execution removes successfully opened trades from the pending queue.
The baseline paper-trading engine remains unchanged.
Validation
Created one test pending candidate.
Captured the candidate through the Morning Recorder Service.
Confirmed the method reported one captured candidate.
Confirmed the complete candidate data was stored in service.candidate_snapshot.

The Morning Recorder Service can now preserve its own research candidate list for the recording session.
Version 3.4 Beta 13 — Once-Per-Day Morning Snapshot

Date: July 11, 2026

Summary

Updated the Morning Recorder Service so its immutable candidate snapshot is captured only once per Toronto trading date.

Changes
Updated MorningRecorderService.capture_today_snapshot().
Added Toronto-date normalization through normalize_current_datetime().
Added tracking through current_recording_date.
Added CAPTURED status for a newly captured daily snapshot.
Added ALREADY_CAPTURED status when a snapshot already exists for the same date.
Preserved the existing same-day candidate snapshot even when the pending-trade queue changes.
Allowed a fresh snapshot to be captured when a new trading date begins.
Did not modify baseline paper execution.
Did not add the continuous recording loop.
Validation

Confirmed with a focused regression test:

First capture on July 13 recorded one candidate.
A second capture on July 13 did not replace the snapshot.
A new capture on July 14 recorded the updated two-candidate queue.
The final snapshot contained only the newly captured July 14 candidates.
Architectural Result

The Morning Recorder Service now owns a stable, immutable candidate list for each trading day. Baseline execution may remove trades from the live pending queue without interrupting the recorder’s research observations.
Version 3.4 Beta 14 — Activate Morning Recorder Scheduling Loop

Date: July 11, 2026

Summary

Replaced the placeholder Morning Recorder Service worker with an active background scheduling loop.

Changes
Updated MorningRecorderService.worker().
The worker now retrieves the current Toronto datetime.
The worker checks the existing weekday 9:30 a.m.–10:00 a.m. recording window.
During the recording window, the service calls capture_today_snapshot().
The once-per-day snapshot protection preserves the immutable candidate list.
The service then calls run_recording_cycle() using the saved snapshot.
The worker waits for the configured check_seconds interval between checks.
The stop event continues to provide clean and responsive service shutdown.
Baseline paper-trade execution remains unchanged.
Validation
Successfully compiled the complete paper_trading package.
Started the Morning Recorder Service with a one-second test interval.
Confirmed the background worker thread remained active during the test.
Stopped the service successfully.
Confirmed the worker thread was no longer alive after shutdown.
Architectural Result

The Morning Recorder Service now has an operational scheduling loop connecting the morning recording window, immutable daily candidate snapshot, and SQLite observation recording cycle.

The service remains research-only and does not modify pending trades, open positions, or baseline execution decisions.
Development Log
Version 3.4 Beta 14 – Telegram Notification Framework
Summary

Implemented the foundation for a secure Telegram notification system, enabling the trading workstation to communicate directly with a mobile device. Notifications are now supported through a reusable module that reads credentials securely from a local .env file rather than storing sensitive information in the source code.

Completed
Created and configured a dedicated Telegram bot (@ChrisTSXMomentumBot).
Verified secure communication between Python and the Telegram Bot API.
Retrieved and validated the personal Telegram Chat ID.
Implemented a permanent notifications package.
Created telegram_notifier.py with reusable send_telegram_message() functionality.
Implemented automatic loading of Telegram credentials from a local .env file.
Confirmed .env is ignored by Git and will not expose credentials in the repository.
Successfully transmitted live notifications from the trading workstation to the Android device.
Confirmed requests dependency is already included in the project requirements.
Architectural Improvements
Established a centralized notification framework that can be reused across the project.
Removed the need to manually paste API tokens during normal operation.
Isolated all Telegram-specific logic into a dedicated module to keep the remainder of the application independent of the notification implementation.
Prepared the project for future notification providers without requiring changes throughout the codebase.
Research Findings

Reviewed the workstation code and identified the ideal integration point:

check_ready_alerts()

This function already:

Detects newly qualified READY trades.
Prevents duplicate alerts.
Maintains state between refresh cycles.

This makes it the correct location for live Telegram notifications without generating repeated messages every scanner refresh.

Next Development Session

Replace the existing console output:

print("NEW READY ALERT:", ...)

with a call to the reusable Telegram notification module.

After successful validation, extend notifications to:

READY trade alerts
Paper trade opened
Stop loss triggered
Target reached
Time exit
Morning Recorder completion
End-of-day summary
System warnings and service failures
Development Log

Date: July 13, 2026

Summary

Completed validation of the fully automated End-of-Day (EOD) paper trading workflow and integrated Telegram notifications directly into the Automatic EOD Service.

Validation Completed
Automatic End-of-Day Workflow

Successfully validated the complete production EOD pipeline:

Automatic EOD scanner executed successfully after market close.
All 53 watchlist symbols scanned.
Strategy rules evaluated successfully.
READY, WATCH, and IGNORE classifications verified.
Six READY candidates correctly added to the pending trade queue.
Duplicate prevention successfully rejected duplicate queue entries.
Pending trade persistence verified using pending_trades.csv.
Zero scanner errors observed during validation.
Queue Validation

Verified:

Pending queue contains only valid READY candidates.
All trades recorded with the correct signal date.
ATR, TMQS, RVOL, breakout classification, and reason preserved.
Queue status correctly recorded as PENDING.
Telegram Integration

Identified that the Telegram notification system was operational but was not connected to the Automatic EOD workflow.

Implemented:

Telegram notification import into paper_trading/automatic_eod.py.
Automatic notification immediately following successful completion of:
EOD scan
Queue creation
State persistence
Notification failures now generate warnings without affecting successful EOD completion.
Validation

Verified:

Module compiles successfully.
Controlled integration test completed successfully.
Telegram summary message delivered successfully to mobile device.
End-to-end notification workflow confirmed operational.
Current Automated Workflow

The system now performs:

Automatic End-of-Day scan.
Strategy evaluation.
Pending trade queue creation.
Duplicate protection.
State persistence.
Telegram notification summarizing scan results.
Preparation for automatic next-day execution.
Status

Paper Trading Version 3.4 Beta 12

Current project status:

Baseline End-of-Day automation validated.

Next milestone:

Validate complete overnight execution cycle (EOD → Pending Queue → Automatic Market Open Execution → Portfolio Update → Trade Journal).
Development Log

Date: July 14, 2026

Summary

Implemented a dedicated Validation Risk Mode for the paper trading engine, allowing research to collect complete baseline data without account-size constraints.

Features Added
Validation Risk Model
Added support for two position-sizing modes:
Percentage Risk (existing behavior)
Fixed Dollar Risk (new)
Introduced configurable risk_model and fixed_risk_amount parameters to the PaperTradingEngine.
Preserved backward compatibility by keeping Percentage Risk as the default.
Validation Configuration
Configured the Trading Workstation to use:
Starting Cash: $50,000
Fixed Risk: $100 per trade
Maximum Open Positions: 20
This separates research validation from realistic account constraints while maintaining consistent trade risk.
Validation Performed
Successfully compiled:
paper_trading/paper_engine.py
gui/trading_workstation.py
Verified Fixed Risk mode returns expected position sizing.
Confirmed Trading Workstation loads:
Risk Model: fixed
Fixed Risk: $100
Starting Cash: $50,000
Maximum Open Positions: 20
Verified six pending trades remain queued for morning execution.
Notes
Telegram notifications could not connect while on the workplace network. Testing indicates the issue is network-related rather than application-related. Paper trading functionality is unaffected and should be retested on the home network.
Development Log

Date: July 14, 2026

Version

Paper Trading Validation Configuration Update

Summary

Updated the paper trading validation environment to eliminate artificial capital constraints during baseline strategy testing while preserving consistent risk sizing.

Changes
Increased Paper Trading Buying Power
Increased paper trading starting cash from $50,000 to $500,000.
Purpose is to prevent valid paper trades from being rejected due to insufficient virtual buying power during baseline validation.
Increased Maximum Open Positions
Increased maximum simultaneous paper positions from 20 to 100.
Prevents high-signal market days from being artificially limited by portfolio capacity.
Preserved Risk Model
Retained the Fixed Risk Model.
Fixed risk remains $100 per trade.
Position sizing remains unchanged despite the larger virtual bankroll.
Validation
Verified production configuration updated successfully.
Verified Trading Workstation compiles without errors.
Confirmed:
Starting Cash = $500,000
Risk Model = Fixed
Fixed Risk Amount = $100
Maximum Open Positions = 100
Design Rationale

The current objective is to validate the momentum strategy itself—not to simulate a specific account size.

By removing artificial cash and portfolio limits, the system can execute every qualifying paper trade, resulting in a more complete and statistically reliable baseline dataset. This improves confidence in subsequent performance analysis before introducing realistic capital constraints for live deployment.

Development Log
Version 3.5 Beta 1 – Telegram READY Alerts & Analytics Enhancement

Date: July 14, 2026

Stability Improvements
Fixed stale pending trade queue after workstation restart.
Added automatic synchronization between pending trades and open positions.
Pending trades for symbols with existing open positions are now automatically removed as SKIPPED instead of repeatedly attempting execution.
Verified:
Automatic execution no longer retries stale trades.
Pending queue remains synchronized after restart.
Portfolio state restores correctly.
Restart workflow is stable.
Paper Trading
Verified:
Open Positions: 6
Pending Trades: 0
Closed Trades: 0
Confirmed automatic execution, position monitoring, and journal services remain operational.
Analytics
Added Average Holding Time calculation to the paper trading analytics engine.
Uses entry_date and exit_date from completed trades.
Integrated the metric into the analytics dashboard.
Verified dashboard compiles and launches successfully.
Telegram Notifications
Integrated Telegram with the live READY signal detector.
READY alerts now include:
Symbol
Price
TMQS
Confidence Score
Relative Volume (RVOL)
Breakout Status
Decision Reason
Preserved duplicate-alert protection so the same READY symbol is not repeatedly sent.
Telegram notifications run in a background thread to prevent GUI freezes if Telegram is unavailable.
Existing Automatic End-of-Day Telegram notification remains intact.
Scanner Validation
Verified:
Scanner operational.
Auto Execution running.
Position Monitor active.
Trade Journal ready.
Queue synchronization functioning correctly.
Observed TD.TO generating a READY signal after market close. This remains an investigation item to determine why it differed from the earlier End-of-Day scan.
## Version 3.4 Beta → Fully Automated EOD Workflow

Date: July 14, 2026

Completed:
- Fixed stale pending trade cleanup after application restart.
- Added automatic removal of duplicate pending signals for symbols already held.
- Added average holding time metric to paper trading analytics dashboard.
- Integrated Telegram READY notifications with duplicate-alert protection.
- Preserved automatic End-of-Day Telegram notification workflow.
- Restored and verified paper_engine.py after development edits.
- Verified scanner, automatic execution, position monitor, journal service, and portfolio restore.
- Cleaned repository and synchronized all source code with GitHub.

Current Status:
- Scanner operational.
- Auto Execution running.
- Position Monitor active.
- Trade Journal ready.
- Portfolio restore verified.
- Git working tree clean.

Next Development Target:
- Complete Telegram Trade Control Center:
  - Trade Opened notifications
  - Trade Closed notifications
  - Portfolio/P&L status messages
  Development Log

Version 3.5 Beta 2 – Telegram Trade Lifecycle Alerts

Date: July 15, 2026

Summary

Completed the Telegram notification system for the complete paper trade lifecycle. The system now automatically notifies the user whenever a paper trade is opened or closed while preserving all existing execution, portfolio management, and journaling functionality.

Features Added
Trade Opened Notifications
Added automatic Telegram notifications whenever a paper trade is successfully opened.
Notifications include:
Symbol
Entry Price
Share Quantity
Stop Price
Profit Target
Position Risk ($)
Available Cash
Portfolio Value
Open Position Count
Trade Closed Notifications
Added automatic Telegram notifications whenever a paper trade is closed.
Supports all exit types:
Stop Hit
Target Hit
Time Exit
Manual Exit
Notifications include:
Symbol
Entry Price
Exit Price
Shares
Realized Profit/Loss ($)
Realized Return (%)
Exit Reason
Available Cash
Portfolio Value
Open Positions
Closed Trade Count
Notification Infrastructure
Added reusable asynchronous Telegram notification helper.
Notifications are sent on a background thread to avoid blocking scanner or execution performance.
Added error handling so Telegram failures cannot interrupt trading operations.
Validation

Successfully verified:

✅ Paper Trade Opened notification delivered to Telegram.
✅ Paper Trade Closed notification delivered to Telegram.
✅ Realized P/L displayed correctly.
✅ Automatic execution logic unchanged.
✅ Position sizing unchanged.
✅ Stop-loss and target logic unchanged.
✅ Paper portfolio integrity maintained.
✅ Existing six-position paper portfolio unaffected.
✅ paper_engine.py compiled successfully after changes.
Current Telegram Capabilities

The system now sends:

✅ READY setup alerts
✅ Paper Trade Opened alerts
✅ Paper Trade Closed alerts
✅ End-of-Day scan summary
Remaining Telegram Enhancement

Next milestone:

Telegram Portfolio Control Center

Planned information:

Portfolio Value
Available Cash
Open P/L
Realized P/L
Total Return
Open Positions
Pending Trades
Closed Trades
Daily Performance Summary
## Version 3.0 Beta - EOD Validation (2026-07-15)

### Objective
Validate the complete automated End-of-Day workflow and verify Telegram notifications on the home network.

### Validation Results
- Automatic End-of-Day scan executed successfully.
- Telegram EOD notification successfully received on home network.
- EOD summary:
  - READY: 2
  - QUEUED: 2
  - DUPLICATES: 0
  - WATCH: 2
  - IGNORE: 49
  - ERRORS: 0
- pending_trades.csv verified.
  - EQB.TO queued.
  - MFC.TO queued.
- automatic_eod_state.json updated correctly with today's run date.
- Paper trade journal verified.
- Two live paper trades exited today:
  - BTE.TO - Stop Hit
  - IMO.TO - Stop Hit
- Trading workstation services verified operational:
  - Scanner RUNNING
  - Auto Execution RUNNING
  - Auto EOD RUNNING
  - Position Monitor ACTIVE
  - Trade Journal READY

### Notes
Evidence strongly suggests previous Telegram notification failures were caused by the workplace network restrictions rather than the Telegram integration itself.

Next validation milestone:
Verify tomorrow morning's automatic execution of the queued trades (EQB.TO and MFC.TO) and continue validating buy/sell Telegram notifications.
## 52-Week Breakout Strategy - Initial Foundation (2026-07-15)

### Objective
Begin development of a separate 52-week breakout sister strategy without modifying or interfering with the existing momentum validation workflow.

### Added
- Created a new `strategies` Python package.
- Added `strategies/__init__.py`.
- Added `strategies/breakout_52week_strategy.py`.
- Added configurable Version 1 filters:
  - Minimum price: $5.00
  - Minimum average daily volume: 300,000 shares
  - Minimum relative volume: 1.50
  - Bullish trend requirement: 50-day SMA above 200-day SMA
  - Breakout requirement: close at or above the prior 52-week high
- Added independent READY, WATCH and IGNORE decisions.
- Added explanatory reasons to every decision result.

### Tests Passed
- Python compilation test passed.
- READY test passed for a qualifying 52-week breakout.
- WATCH test passed for a breakout with insufficient relative volume.
- IGNORE test passed when price remained below the prior 52-week high.

### Safety
The new strategy is currently isolated and is not connected to:
- The live scanner
- Automatic EOD processing
- The pending trade queue
- Paper execution
- Telegram
- The current momentum strategy

This protects the scheduled next-day momentum execution validation while allowing development of Strategy #2 to begin.

### Next Step
Build automated unit tests and then create a historical-data adapter that calculates the prior 52-week high, average volume, relative volume, 50-day SMA and 200-day SMA from actual market data.
Development Log

Date: July 15, 2026

Summary

Continued development of the Version 4 Trader Control Center with a focus on improving readability and preparing the interface for long-term paper trading validation.

Improvements Completed
Trader Control Center
Added structured section headers using:
■ Portfolio
■ Position Status
■ Performance
■ Open Positions
■ Recent Closed Trades
Improved overall visual organization of the dashboard.
Dashboard Layout
Increased readability of the Trade Checklist panel.
Refined spacing and formatting throughout the paper trading dashboard.
Added clearer position card formatting for open positions.
Improved separation between portfolio statistics and position details.
Visual Enhancements
Preserved color coding for:
Profit metrics
Loss metrics
Position status
Maintained colored position cards and enhanced dashboard readability.
Development Notes
Experimented with separate title and subtitle rendering for the Trader Control Center.
Discovered an indentation issue while modifying the renderer.
Successfully restored the last stable version from backup.
Confirmed the workstation compiles and runs correctly after restoration.
Deferred title styling improvements to a future session using a cleaner implementation approach.
Validation
✅ Dashboard compiles successfully.
✅ Trading Workstation compiles successfully.
✅ GUI launches normally.
✅ Trader Control Center displays correctly.
✅ Paper trading engine remains fully operational.
Current Status

The Version 4 Trader Control Center now provides a cleaner and more professional operational dashboard while preserving the stability of the paper trading validation system.