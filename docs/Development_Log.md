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