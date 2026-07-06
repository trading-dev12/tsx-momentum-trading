# TSX Momentum Pro

## Project Status

**Current Version:** 1.6

---

# Objective

Build a professional TSX momentum trading workstation that automatically scans the market, identifies only the highest probability momentum trades, alerts the user, and eventually performs historical backtesting before live deployment.

---

# Completed Features

## Scanner
- Live TSX scanner
- 23-stock watchlist
- Live pricing
- Previous day data
- Breakout detection
- Near Breakout detection
- Inside Range detection
- Weak / Below Close detection

## Scoring
- Momentum Score
- TMQS Score
- Momentum Grade
- Liquidity Grade
- Relative Volume (RVOL)

## Decision Engine
- READY
- WATCH
- IGNORE

## Market Context
- TSX Market Health
- Bitcoin
- Oil
- VIX
- Market Health Score

## GUI
- Desktop Trading Workstation
- Color-coded rows
- Refresh button
- Auto Refresh
- Countdown timer
- Last Update timestamp
- Scanner Summary
- Best Candidate display

---

# Current Known Issues

### High Priority

TMQS can still score weak setups too highly.

Example:

K

TMQS = 100

RVOL = 0.30x

Decision = WATCH

The scoring engine and decision engine should agree much more closely.

---

# Current Development Priority

Version 1.7

Improve TMQS scoring by:

- stronger RVOL penalties
- smarter breakout scoring
- reduce false positives
- align TMQS with Decision Engine

---

# Future Versions

Version 1.8
- Improved workstation layout
- Better statistics
- Trade logging

Version 2.0
- Historical backtesting
- Win rate
- Profit factor
- Drawdown analysis

---

Last Updated

July 6, 2026
Version 1.7

Completed
- Fixed VIX market data
- Improved TMQS scoring
- Added RVOL quality filter to Decision Engine
- Prevented weak-volume stocks from becoming WATCH
- Improved overall scanner reliability

Next Version (1.8)
- Configurable trading thresholds
- Quality Filter display panel
- Better workstation layout
- Trade logging
- Begin backtesting framework
Version 1.8 – Quality Filter System

Completed
- Fixed VIX market data
- Improved TMQS scoring
- Added RVOL A–F grading
- Added RVOL quality filtering in the Decision Engine
- Reduced false WATCH signals
- Added RVOL Grade column to the workstation

Next Objectives (Version 1.9)
- Confidence Score
- Trade Checklist
- Configurable trading thresholds
- Enhanced market dashboard
- Begin backtesting framework