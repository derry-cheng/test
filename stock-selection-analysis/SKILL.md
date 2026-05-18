---
name: stock-selection-analysis
description: End-to-end stock selection, technical analysis, quantitative modeling, and price forecasting for US stocks, Hong Kong stocks, and China A-shares. Use when Codex is asked to screen equities, compare stock candidates, incorporate recent fund/institutional holding changes, compute many technical indicators, build code-based forecasting models, or produce a structured investment research report with data sources and risk caveats.
---

# Stock Selection Analysis

## Core Principles

- Treat this skill as a research workflow, not financial advice. State that forecasts are probabilistic scenarios and may be wrong.
- Use current market data. If the user asks for live/latest/recent holdings, browse or query data providers before answering.
- Cover US, Hong Kong, and A-share markets, normalizing tickers before data collection:
  - US: `AAPL`, `MSFT`, `BRK-B`.
  - Hong Kong: Yahoo-style `0700.HK`, AkShare-style `00700` or exchange-qualified codes.
  - A-shares: Yahoo-style `600519.SS` / `000001.SZ`, AkShare-style `sh600519` / `sz000001`, or plain six-digit codes.
- Prefer reproducible code for screening, indicator computation, factor scoring, backtesting, and forecasting. Include commands, assumptions, and model limitations.
- Use multiple independent sources when feasible; cite sources and dates for prices, filings, fund holdings, analyst estimates, macro data, and news.
- Explain recommendations for a beginner: define why a stock is interesting, what would trigger a buy, where the idea is invalidated, and where partial/full sells would be considered.

## Workflow

### 1. Clarify Scope

Ask only if missing information blocks the analysis. Otherwise choose reasonable defaults and state them.

- Market universe: US, HK, A-share, or mixed.
- Holding horizon: short-term trading (days/weeks), swing (1-3 months), medium term (3-12 months), or long term.
- Risk preference: conservative, balanced, aggressive.
- Constraints: sectors to include/exclude, market-cap/liquidity thresholds, max number of names, currency, benchmark.
- Output depth: quick shortlist, full report, or reproducible notebook/script.

### 2. Data Collection Checklist

Collect as much as practical for the requested depth:

- Prices and volume: daily OHLCV, adjusted prices, intraday if short-term.
- Fundamentals: revenue, EPS, margins, ROE/ROIC, leverage, cash flow, valuation multiples, guidance.
- Fund/institutional flows:
  - US: 13F filings, ETF/fund holdings, insider transactions, short interest.
  - HK: exchange disclosures, Stock Connect flows, fund factsheets, CCASS concentration when relevant.
  - A-share: public fund quarterly holdings, northbound Stock Connect flows, margin financing, top shareholders.
  - Treat quarterly fund holdings as lagging confirmation, not the main short-term screen. Prefer fresher signals such as recent main-fund flows, northbound/southbound flows, unusual volume, sector rotation, breakouts, earnings revisions, and news catalysts for the first pass.
- Market context: index trend, sector rotation, rates, FX, commodity inputs, volatility, liquidity.
- Industry chain context: upstream inputs, midstream manufacturing, downstream demand, customer concentration, order backlog, inventory, utilization, announced capacity, capacity ramp schedule, capex cycle, and supply-demand balance.
- Events/news: earnings dates, regulatory changes, product cycles, buybacks, dividends, litigation.
- Analyst/consensus data if available: target prices, revisions, estimate dispersion.

See `references/data_sources_and_indicators.md` for market-specific source ideas and indicator groups. For A-share first-pass screening, use `scripts/a_share_screener.py` when network access is available to generate a reproducible 20-50 stock candidate list from current flow, liquidity, relative strength, valuation, and optional fund-holding confirmation.

### 3. Initial Screening

Create a broad candidate list before detailed stock work. Target **20-50 initial candidates** unless the user requests a different count. Do not depend only on quarterly fund disclosure; use timely market signals first, then use fund holdings as a secondary confirmation.

Use market-appropriate filters:

- Liquidity: average turnover, bid/ask practicality, suspension risk.
- Size/quality: market cap, profitability, leverage, cash conversion, audit/governance red flags.
- Momentum/trend: relative strength vs benchmark, moving-average alignment, volume confirmation.
- Valuation: absolute and sector-relative multiples; growth-adjusted valuation where useful.
- Fresh money flow: 1/3/5/10-day main-fund net inflow, northbound/southbound flows, ETF/sector inflows, block trades where available.
- Momentum and relative strength: 20/60-day relative strength, new highs, breakouts, volume expansion, sector leadership.
- Fund accumulation: recent fund/institutional additions, new entrants, increased position size, net inflows; down-weight stale quarterly disclosures.
- Catalyst proximity: earnings, policy support, product launch, sector upcycle, restructuring.
- Supply-chain and capacity inflection: upstream raw-material price changes, component shortages/surpluses, downstream order acceleration, inventory destocking/restocking, capacity utilization rising/falling, and new capacity ramping faster/slower than expected.

Score candidates with transparent weights. Example short/medium-term screen:

```text
Total = 25% fresh money flow + 20% relative strength/technical trend +
        15% liquidity/turnover + 15% quality/valuation +
        15% catalyst/sector strength + 10% fund/institutional confirmation
```

Example longer-term screen:

```text
Total = 25% business quality + 20% valuation + 20% earnings growth/revisions +
        15% fund/institutional confirmation + 10% technical trend + 10% liquidity/risk
```

Reject candidates with severe data gaps, low liquidity, accounting/governance concerns, or event risks that the user did not accept. If the screen returns fewer than 20 candidates, relax non-critical thresholds and explain why; if it returns more than 50, keep the top 20-50 by score.

### 4. Detailed Stock Analysis

For each finalist, produce a research profile:

- Business model, revenue drivers, competitive position, sector cycle, and key catalysts.
- Supply-chain map: upstream suppliers/inputs, company value-chain position, downstream customers/applications, bargaining power, and substitution risk.
- Capacity and order analysis: designed capacity, effective capacity, utilization, expansion projects, capex, delivery/ramp schedule, backlog/order visibility, inventory days, and whether demand can absorb new supply.
- Financial trend: growth, margins, working capital, FCF, leverage, dilution/buybacks, dividends.
- Valuation: historical range, peer comparison, DCF or scenario multiple where practical.
- Fund flow interpretation: who increased/decreased holdings, whether changes are meaningful versus float/volume, and whether flow confirms the thesis.
- News and event map: bullish/bearish events, expected dates, and what data would invalidate the thesis.
- Beginner buy/sell logic: why the stock may rise, what exact trigger would justify buying, preferred entry zone, stop-loss/invalidation price, first sell target, second sell target, and conditions for taking profit early.
- Risk register: macro, FX, policy, liquidity, governance, earnings, model overfit, and stop-loss/position sizing considerations.

See `references/buy_sell_logic.md` for the required plain-language buy/sell explanation template. See `references/supply_chain_capacity.md` when analyzing cyclical, manufacturing, hardware, robotics, semiconductor, EV, commodity, or ETF/industry-chain themes.

### 5. Technical Analysis Requirements

Compute and interpret more than basic moving averages. Include multiple indicator families:

- Trend: SMA/EMA 5/10/20/50/100/200, ADX/DMI, Ichimoku, moving-average slope.
- Momentum: RSI, MACD, stochastic oscillator, Williams %R, ROC, CCI.
- Volatility: ATR, Bollinger Bands, Keltner Channels, realized volatility, gap statistics.
- Volume/flow: OBV, MFI, VWAP/anchored VWAP, volume-price divergence, accumulation/distribution.
- Support/resistance: swing highs/lows, Fibonacci retracements, pivot points, volume profile if available.
- Relative strength: vs local benchmark and sector ETF/index.
- Pattern/risk: breakouts, false breakouts, drawdown, stop levels, reward/risk ratio.

Do not rely on a single indicator. Require cross-family confirmation and mention conflicts.

### 6. Code-Based Modeling and Forecasting

Use `scripts/a_share_screener.py` for A-share initial screening when the user wants current candidates rather than stale quarterly fund-disclosure-only ideas. Then use `scripts/stock_modeling.py` when the user provides CSV data or when dependencies/data access are available. The modeling script can:

- Load OHLCV CSV files or download Yahoo Finance data when `yfinance` is installed.
- Add a technical-indicator feature set.
- Train walk-forward models for forward returns.
- Emit forecast scenarios, metrics, suggested entry zones, stop-loss levels, and staged sell targets.

Recommended modeling stack, depending on available data:

1. Baseline: naïve drift, moving-average trend, benchmark-relative return.
2. Statistical: ARIMA/SARIMAX, exponential smoothing, volatility model if appropriate.
3. Machine learning: ridge/lasso, random forest, gradient boosting, XGBoost/LightGBM if installed.
4. Time-series validation: walk-forward split, no leakage, horizon-specific labels, transaction-cost assumptions.
5. Scenario forecast: bull/base/bear ranges instead of one deterministic target.

For price prediction, report:

- Forecast horizon and target variable.
- Model features and training window.
- Validation metrics: MAE/RMSE/MAPE for price or directional accuracy/ROC-AUC for direction.
- Bear/base/bull forecast prices.
- Suggested entry zone, stop-loss/invalidation price, first sell target, and second sell target derived from support/resistance, ATR, reward/risk, and forecast scenarios.
- Key drivers and what would invalidate the forecast.

Never present a sell target as guaranteed. Explain it as a level for staged profit-taking or reassessment.

### 7. Report Format

Use this structure for full reports:

```markdown
## Executive Summary
- Final ranking and recommended watchlist.
- Best fit by horizon/risk profile.

## Data and Assumptions
- Data sources, retrieval dates, ticker normalization, missing-data caveats.
- Whether fund-holding data is current enough for the horizon, and which fresher signals were used to compensate.

## Initial Screen
- Universe, filters, factor weights, rejected names.

## Finalist Deep Dives
### <Ticker / Company>
- Plain-language buy logic
- Why it appeared in the initial screen
- Fundamentals
- Supply chain, downstream demand, capacity, utilization, orders, and inventory
- Fresh money flow and fund/institutional confirmation
- Technical analysis
- Quant model and forecast
- Entry trigger and preferred entry zone
- Stop-loss / invalidation price
- Recommended staged sell targets
- Valuation and scenarios
- Risks and invalidation signals

## ETF / Thematic Fund Addendum
For ETFs and thematic funds, analyze both the tradable fund and the underlying industry basket:
- Identify the exact fund code, index tracked, expense/scale/liquidity, premium/discount if available, and top holdings.
- Map top holdings into supply-chain buckets; for robotics, use sensors/vision, controllers/servo systems, reducers/transmission, industrial robots, humanoid/embodied AI, automation integrators, and downstream customers.
- Explain whether the ETF is driven by fundamentals, policy/AI theme sentiment, industry orders, or valuation expansion.
- Use the ETF price for technical/model analysis, but use constituent fundamentals and capacity/order data for the investment thesis.
- Give ETF-specific buy logic, entry zone, stop-loss, staged sell targets, and risks such as theme crowding, high valuation, liquidity, and tracking error.

## Comparison Table
| Rank | Ticker | Market | Score | Buy label | Entry zone | Stop-loss | Sell target 1 | Sell target 2 | Forecast range | Key risk |

## Action Plan / Monitoring
- Watch levels, buy triggers, entry zones, stop-losses, staged sell targets, earnings/events, and data to refresh.
```

## Quality Gates

Before finalizing:

- Verify the latest data date and market timezone.
- Explain how fund-holding data lags; do not use stale quarterly fund disclosure as the only reason to buy.
- Check ticker suffixes and currency conversions.
- Ensure models use only information available before the prediction date.
- Include uncertainty and avoid guaranteeing returns.
- Make final recommendations understandable to a beginner: define the buy logic, trigger, entry zone, stop-loss, and sell targets in plain language.
- Cite data sources and provide code or commands used for computations.
