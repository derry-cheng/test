# Data Sources and Indicator Reference

## Market-Specific Data Ideas

### US Stocks
- Prices: exchange data, Yahoo Finance, Stooq, Polygon, Nasdaq, Alpha Vantage, Tiingo.
- Fund/institutional holdings: SEC 13F, fund N-PORT/N-CSR filings, ETF sponsor holdings, WhaleWisdom-style aggregators where accessible.
- Corporate events: SEC 10-K/10-Q/8-K, earnings-call transcripts, investor relations, Nasdaq earnings calendar.
- Other flow/risk: insider Form 4, short interest, options open interest, borrow cost if available.

### Hong Kong Stocks
- Prices: HKEX data, Yahoo Finance `.HK`, Stooq, broker/exported CSV.
- Fund/holder flows: HKEX disclosure of interests, Stock Connect southbound flows, CCASS shareholding data, fund factsheets.
- Corporate events: HKEXnews announcements, annual/interim reports, buyback disclosures.
- Macro/context: HKD rates, CNH, sector policy, China macro data for mainland-exposed issuers.

### China A-Shares
- Prices: AkShare, Tushare, exchange data, Yahoo Finance `.SS` / `.SZ`, broker/exported CSV.
- Fresher initial-screen sources: 1/3/5/10-day main-fund flow rankings, northbound Stock Connect flow, sector/industry fund-flow rankings, daily turnover expansion, relative-strength/new-high lists, margin financing changes, block trades, earnings-preview changes, and high-volume breakouts.
- Lagging confirmation sources: public fund quarterly holdings, top-ten tradable shareholders, annual/quarterly reports. Use these as confirmation, not as the only short-term screen, because they may be weeks or months old.
- Corporate events: exchange announcements, CNINFO, annual/quarterly reports, earnings previews.
- Macro/context: policy meetings, industry ministry data, commodity prices, RMB rates.

## Technical Indicator Groups

Use indicators from several groups rather than many variants from one group.

| Group | Indicators | Interpretation |
| --- | --- | --- |
| Trend | SMA/EMA, ADX/DMI, Ichimoku, MA slope | Direction, trend strength, regime |
| Momentum | RSI, MACD, stochastic, ROC, CCI, Williams %R | Overbought/oversold, acceleration, divergence |
| Volatility | ATR, Bollinger Bands, Keltner Channels, realized volatility | Risk, breakout compression, stop distance |
| Volume | OBV, MFI, VWAP, A/D line, turnover | Confirmation, accumulation/distribution |
| Relative strength | Stock vs benchmark/sector, percentile ranks | Leadership or lagging behavior |
| Market structure | Support/resistance, pivots, Fibonacci, gaps | Entry/exit zones and invalidation levels |

## Modeling Checklist

- Split data chronologically; never random-split time series for final evaluation.
- Engineer features with lagged or rolling values only.
- Compare against simple baselines.
- Tune hyperparameters only within training/validation windows.
- Use walk-forward validation for realistic performance.
- Convert return forecasts to price ranges with volatility-aware scenarios.
- Report model uncertainty and explain that historical relationships may break.


## Initial Candidate Count Guidance

- Aim for 20-50 first-pass candidates so the user can see enough alternatives before deep-dive filtering.
- For short/medium-term stock selection, prioritize fresh signals: current money flow, relative strength, sector momentum, volume expansion, catalyst proximity, and liquidity.
- Use quarterly fund holdings only as a lower-weight confirmation factor unless the user's horizon is long term.
- If a data source fails, document the failure and substitute another timely signal rather than falling back entirely to stale fund disclosures.
