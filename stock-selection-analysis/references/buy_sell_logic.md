# Buy/Sell Logic for Beginner-Friendly Reports

Use this reference when the final output should explain the investment logic to a non-professional user.

## Beginner Explanation Template

For every final stock, write the thesis in plain language:

1. **Why it appeared in the screen**: summarize the strongest data signals, such as recent main-fund inflow, relative strength, sector momentum, liquidity, valuation, earnings revision, or confirmed institutional accumulation.
2. **Why it may rise**: connect the signals into a cause-and-effect chain, e.g. "capital is flowing into the sector, this stock is leading peers, price is above key moving averages, and the upcoming catalyst could improve earnings expectations."
3. **What must happen before buying**: define a concrete trigger instead of saying "buy now" by default. Examples: pullback to support, breakout above resistance with volume, close above the 20-day moving average, or confirmation after earnings/news.
4. **Where the idea is wrong**: list invalidation signals such as breaking the stop-loss, fund flow reversal, earnings miss, sector breakdown, or abnormal volume selloff.
5. **How to sell**: provide both risk-control exits and profit-taking exits.

## Entry, Stop, and Exit Rules

Always distinguish four prices:

- **Current price**: the latest observed price, with date/time.
- **Entry zone**: a range where the reward/risk is acceptable. Prefer a range based on support, VWAP/MA pullback, ATR, or confirmed breakout retest.
- **Stop-loss / invalidation price**: a price where the original thesis is probably wrong. Common choices: below recent swing low, below 20/50-day MA, or 1.5-2.5 ATR below entry.
- **Take-profit / sell target**: a staged selling plan, not a guaranteed target. Use model base/bull forecasts, resistance, valuation upside, or 2:1 / 3:1 reward-risk.

Suggested staged exit wording:

```text
Plan: If entry is near X, stop at Y. First profit-taking zone is Z1; if volume and trend remain strong, keep a runner toward Z2. If price reaches Z1 but momentum/volume diverges, reduce rather than wait for Z2.
```

## Recommendation Labels

Use cautious labels rather than absolute commands:

- **Watchlist only**: thesis is interesting but entry trigger is missing.
- **Buy on pullback**: trend is valid but current price is extended.
- **Buy on breakout confirmation**: resistance must be broken with volume.
- **Small trial position**: signals are good but uncertainty/volatility is high.
- **Avoid / wait**: risk-reward is poor, data conflicts, liquidity is weak, or catalyst risk is high.

## Minimum Fields for Final Picks

Each final pick should include:

| Field | Meaning |
| --- | --- |
| Buy logic in one sentence | Why this stock deserves attention |
| Entry trigger | What exact market behavior would justify buying |
| Entry zone | Preferred buy range |
| Stop-loss | Where the thesis is invalidated |
| First sell target | Conservative profit-taking level |
| Second sell target | Optimistic target if trend continues |
| Forecast range | Bear/base/bull model or scenario range |
| Holding horizon | Days/weeks/months |
| Key risks | Top 2-4 things that could break the thesis |
