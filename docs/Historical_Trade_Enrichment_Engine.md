# Historical Trade Enrichment Engine

## Purpose

The Historical Trade Enrichment Engine transforms every completed trade into a rich research record.

Rather than simply recording entry price, exit price, and profit/loss, Northstar Quant will capture the complete market context surrounding every trade.

The objective is to discover statistically significant trading edges through evidence rather than assumptions.

Trading decisions remain unchanged during validation.

The enrichment engine operates entirely in the background.

---

# Design Philosophy

Northstar Quant follows one guiding principle:

> Never trust assumptions when you can collect evidence.

Every completed trade becomes another data point for future research.

The platform records everything that may influence trade performance and later determines which variables actually matter.

Weights and scores will not be assigned until sufficient historical evidence exists.

---

# Objectives

The Historical Trade Enrichment Engine will:

- Preserve clean 200-trade validation
- Record rich contextual market information
- Support every current and future strategy
- Build a research database over time
- Enable statistical analysis
- Enable future machine-assisted edge discovery

---

# Data Categories

## 1. Trade Information

Strategy

Symbol

Entry Date

Exit Date

Entry Price

Exit Price

Shares

Stop Loss

Target

ATR

Holding Days

Return %

Profit/Loss $

Reason for Exit

---

## 2. Market Context

TSX Trend

Market Regime

Bull / Bear / Sideways

Market Breadth

Volatility Regime

Oil Trend

Interest Rate Environment

---

## 3. Relative Strength

Relative Strength vs XIC

Relative Strength vs XIU

Relative Strength Ranking

Relative Performance over 20 days

Relative Performance over 50 days

---

## 4. Sector Analysis

Sector

Sector Relative Strength

Sector Trend

Sector Momentum

Sector Ranking

---

## 5. Trend Structure

Distance from 20 SMA

Distance from 50 SMA

Distance from 200 SMA

Distance from 52-week High

Trend Age

Higher High Count

Higher Low Count

---

## 6. Volume Analysis

Relative Volume

Average Volume

Dollar Volume

20-day Volume Trend

Accumulation Days

Distribution Days

Closing Position in Daily Range

Gap %

---

## 7. Institutional Footprint Metrics

Record raw measurements only.

No score will be calculated during validation.

Variables include:

Relative Volume

Relative Strength

Sector Strength

Accumulation

Liquidity

Trend Quality

Distance from Highs

Close Strength

---

## 8. Strategy Metrics

TMQS

RVOL

Scanner Classification

Ready / Watch / Ignore

Breakout Type

Signal Quality

---

## 9. Exit Analysis

Profit Target Hit

Stop Hit

Time Exit

Manual Exit

Maximum Favorable Excursion

Maximum Adverse Excursion

---

# Research Questions

Examples:

Does Relative Strength improve expectancy?

Does sector strength matter?

Does institutional accumulation improve results?

Which market regimes produce the best trades?

Which variables improve Profit Factor?

Which combinations create the highest expectancy?

---

# Future Research Dashboard

The dashboard will allow filtering trades by:

Market Regime

Sector

Strategy

Institutional Footprint

Trend

Relative Strength

Volume

Holding Time

Profit Factor

Expectancy

Win Rate

Drawdown

Trade Count

---

# Edge Discovery Engine

Once sufficient trades have accumulated, Northstar Quant will determine:

Which variables matter

Which variables do not matter

Optimal variable combinations

Expected performance under different market conditions

Relationships between multiple strategies

Future optimization opportunities

---

# Development Priority

Phase 1

Complete paper trading validation.

Do not modify trading logic.

Phase 2

Build Historical Trade Enrichment Engine.

Phase 3

Research Dashboard.

Phase 4

Edge Discovery Engine.

---

# Long-Term Vision

Northstar Quant is evolving from a momentum trading platform into a quantitative research laboratory.

Every completed trade becomes another experiment.

Every experiment increases the knowledge of the platform.

The long-term objective is to continuously discover statistically significant trading edges using evidence collected from real market behavior rather than intuition or prediction.
# Core Principle

The Historical Trade Enrichment Engine is shared infrastructure.

It is not designed for one strategy.

Every current and future strategy will automatically contribute to the same research database.

The value of Northstar Quant increases with every completed trade because every trade expands the evidence available for future analysis.
## Historical Trade Enrichment Engine

### Completed

✅ Relative Strength (20-day)
- XIC comparison
- XIU comparison
- Look-ahead safe
- Automatic journal integration

### Remaining

⬜ Market Regime
- Bull
- Bear
- Sideways

⬜ Sector Strength

⬜ Moving Average Context
- 20 SMA
- 50 SMA
- 200 SMA

⬜ Gap Analysis

⬜ ATR Percentile

⬜ Volatility Regime

⬜ Relative Volume Percentile

⬜ Position Sizing Metrics

⬜ Edge Discovery Dashboard
⬜ Research Filter Optimizer