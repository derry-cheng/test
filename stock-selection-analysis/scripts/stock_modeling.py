#!/usr/bin/env python3
"""Stock technical analysis and forecasting helper.

Examples:
  python scripts/stock_modeling.py --csv data.csv --horizon 20 --out out
  python scripts/stock_modeling.py --ticker AAPL --start 2020-01-01 --horizon 20 --out out

CSV input must include date, open, high, low, close, and volume columns. Column names are
case-insensitive; adjusted close is used as close when present.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def _find_col(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    mapping = {c.lower().strip().replace(" ", "_"): c for c in columns}
    for cand in candidates:
        key = cand.lower().strip().replace(" ", "_")
        if key in mapping:
            return mapping[key]
    return None


def load_prices(args: argparse.Namespace) -> pd.DataFrame:
    if args.csv:
        raw = pd.read_csv(args.csv)
    else:
        import yfinance as yf  # type: ignore

        raw = yf.download(args.ticker, start=args.start, end=args.end, auto_adjust=False, progress=False)
        raw = raw.reset_index()
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = [c[0] for c in raw.columns]

    date_col = _find_col(raw.columns, ["date", "datetime", "time"])
    open_col = _find_col(raw.columns, ["open"])
    high_col = _find_col(raw.columns, ["high"])
    low_col = _find_col(raw.columns, ["low"])
    close_col = _find_col(raw.columns, ["adj_close", "adjusted_close", "adj close", "close"])
    volume_col = _find_col(raw.columns, ["volume", "vol"])
    required = {"date": date_col, "open": open_col, "high": high_col, "low": low_col, "close": close_col, "volume": volume_col}
    missing = [name for name, col in required.items() if col is None]
    if missing:
        raise SystemExit(f"Missing required columns: {', '.join(missing)}")

    df = raw[[date_col, open_col, high_col, low_col, close_col, volume_col]].copy()
    df.columns = ["date", "open", "high", "low", "close", "volume"]
    df["date"] = pd.to_datetime(df["date"])
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna().sort_values("date").drop_duplicates("date").set_index("date")
    return df


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / window, adjust=False).mean()
    loss = -delta.clip(upper=0).ewm(alpha=1 / window, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    close = out["close"]
    high = out["high"]
    low = out["low"]
    volume = out["volume"]

    for window in [5, 10, 20, 50, 100, 200]:
        out[f"sma_{window}"] = close.rolling(window).mean()
        out[f"ema_{window}"] = close.ewm(span=window, adjust=False).mean()
        out[f"ret_{window}"] = close.pct_change(window)
        out[f"volatility_{window}"] = close.pct_change().rolling(window).std() * math.sqrt(252)

    out["rsi_14"] = rsi(close, 14)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    out["macd"] = ema12 - ema26
    out["macd_signal"] = out["macd"].ewm(span=9, adjust=False).mean()
    out["macd_hist"] = out["macd"] - out["macd_signal"]

    tr = pd.concat([(high - low), (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    out["atr_14"] = tr.rolling(14).mean()
    mid = close.rolling(20).mean()
    std = close.rolling(20).std()
    out["bb_upper"] = mid + 2 * std
    out["bb_lower"] = mid - 2 * std
    out["bb_pct"] = (close - out["bb_lower"]) / (out["bb_upper"] - out["bb_lower"])

    low14 = low.rolling(14).min()
    high14 = high.rolling(14).max()
    out["stoch_k"] = 100 * (close - low14) / (high14 - low14)
    out["stoch_d"] = out["stoch_k"].rolling(3).mean()
    typical_price = (high + low + close) / 3
    raw_money_flow = typical_price * volume
    positive_flow = raw_money_flow.where(typical_price.diff() > 0, 0).rolling(14).sum()
    negative_flow = raw_money_flow.where(typical_price.diff() < 0, 0).rolling(14).sum().abs()
    out["mfi_14"] = 100 - (100 / (1 + positive_flow / negative_flow.replace(0, np.nan)))
    out["obv"] = (np.sign(close.diff()).fillna(0) * volume).cumsum()
    out["vwap_20"] = (typical_price * volume).rolling(20).sum() / volume.rolling(20).sum()
    out["target_return"] = close.pct_change().shift(-1)
    return out


def build_trade_plan(features: pd.DataFrame, forecast: dict) -> dict:
    needed = ["close", "sma_20", "sma_50", "atr_14", "bb_upper", "bb_lower", "vwap_20"]
    latest = features[needed].replace([np.inf, -np.inf], np.nan).dropna().iloc[-1]
    close = float(latest["close"])
    atr = float(latest["atr_14"])
    sma20 = float(latest["sma_20"])
    sma50 = float(latest["sma_50"])
    vwap20 = float(latest["vwap_20"])
    support = min(sma20, sma50, vwap20)
    resistance = max(float(latest["bb_upper"]), close + 2 * atr)
    pullback_low = max(min(support, close - 0.5 * atr), 0)
    pullback_high = max(min(close, support + 0.5 * atr), pullback_low)
    stop_loss = max(min(support - 1.5 * atr, close - 2 * atr), 0)
    risk_per_share = max(close - stop_loss, atr)
    first_target = max(forecast["base_predicted_price"], close + 2 * risk_per_share, resistance)
    second_target = max(forecast["bull_price"], close + 3 * risk_per_share, first_target)
    if close > forecast["base_predicted_price"] and close > sma20:
        label = "watch_or_buy_on_pullback"
        rationale = "Current price is above the model base forecast or already extended; prefer a pullback or fresh breakout confirmation."
    elif close > sma20 and close > sma50:
        label = "buy_on_confirmation"
        rationale = "Trend is positive; require volume/price confirmation before entry."
    else:
        label = "watchlist_only"
        rationale = "Trend confirmation is incomplete; wait for price to reclaim key moving averages."
    return {
        "label": label,
        "rationale": rationale,
        "current_price": close,
        "entry_zone_low": pullback_low,
        "entry_zone_high": pullback_high,
        "stop_loss": stop_loss,
        "first_sell_target": first_target,
        "second_sell_target": second_target,
        "risk_per_share": risk_per_share,
    }


def train_forecast(features: pd.DataFrame, horizon: int) -> dict:
    from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import Ridge
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    data = features.copy()
    data[f"future_return_{horizon}"] = data["close"].shift(-horizon) / data["close"] - 1
    feature_cols = [
        c
        for c in data.columns
        if c not in {f"future_return_{horizon}", "target_return"}
        and c not in {"open", "high", "low", "close", "volume"}
    ]
    model_data = data[feature_cols + [f"future_return_{horizon}", "close"]].replace([np.inf, -np.inf], np.nan).dropna()
    minimum_rows = max(80, horizon * 4)
    if len(model_data) < minimum_rows:
        raise SystemExit(f"Need at least {minimum_rows} usable rows after indicators for modeling")

    split = int(len(model_data) * 0.8)
    train = model_data.iloc[:split]
    test = model_data.iloc[split:]
    X_train = train[feature_cols]
    y_train = train[f"future_return_{horizon}"]
    X_test = test[feature_cols]
    y_test = test[f"future_return_{horizon}"]

    models = {
        "ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "random_forest": RandomForestRegressor(n_estimators=300, min_samples_leaf=5, random_state=7, n_jobs=-1),
        "hist_gradient_boosting": HistGradientBoostingRegressor(max_iter=300, learning_rate=0.04, random_state=7),
    }
    results = {}
    best_name = None
    best_mae = float("inf")
    for name, model in models.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        mae = float(mean_absolute_error(y_test, pred))
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        directional_accuracy = float((np.sign(pred) == np.sign(y_test)).mean())
        results[name] = {"mae_return": mae, "rmse_return": rmse, "directional_accuracy": directional_accuracy}
        if mae < best_mae:
            best_name = name
            best_mae = mae

    best_model = models[best_name]
    latest_features = data[feature_cols + ["close"]].replace([np.inf, -np.inf], np.nan).dropna().iloc[[-1]]
    latest_x = latest_features[feature_cols]
    pred_return = float(best_model.predict(latest_x)[0])
    last_close = float(latest_features["close"].iloc[-1])
    realized_vol = float(features["close"].pct_change().tail(60).std() * math.sqrt(horizon))
    forecast_price = last_close * (1 + pred_return)
    forecast = {
        "rows_used": int(len(model_data)),
        "horizon_days": horizon,
        "last_date": str(latest_features.index[-1].date()),
        "last_close": last_close,
        "best_model": best_name,
        "model_metrics": results,
        "base_predicted_return": pred_return,
        "base_predicted_price": forecast_price,
        "bear_price": last_close * (1 + pred_return - realized_vol),
        "bull_price": last_close * (1 + pred_return + realized_vol),
        "realized_volatility_over_horizon": realized_vol,
        "feature_count": len(feature_cols),
    }
    forecast["trade_plan"] = build_trade_plan(features, forecast)
    return forecast


def summarize_technicals(features: pd.DataFrame) -> dict:
    needed = ["close", "sma_20", "sma_50", "sma_200", "rsi_14", "macd_hist", "stoch_k", "mfi_14", "atr_14", "bb_pct", "volatility_20", "obv", "vwap_20"]
    latest = features[needed].replace([np.inf, -np.inf], np.nan).dropna().iloc[-1]
    close = float(latest["close"])
    return {
        "date": str(latest.name.date()),
        "close": close,
        "trend": {
            "above_sma_20": bool(close > latest["sma_20"]),
            "above_sma_50": bool(close > latest["sma_50"]),
            "above_sma_200": bool(close > latest["sma_200"]),
            "sma_20": float(latest["sma_20"]),
            "sma_50": float(latest["sma_50"]),
            "sma_200": float(latest["sma_200"]),
        },
        "momentum": {
            "rsi_14": float(latest["rsi_14"]),
            "macd_hist": float(latest["macd_hist"]),
            "stoch_k": float(latest["stoch_k"]),
            "mfi_14": float(latest["mfi_14"]),
        },
        "volatility": {
            "atr_14": float(latest["atr_14"]),
            "bb_pct": float(latest["bb_pct"]),
            "volatility_20_ann": float(latest["volatility_20"]),
        },
        "volume": {
            "obv": float(latest["obv"]),
            "vwap_20": float(latest["vwap_20"]),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute technical indicators and forecast stock prices.")
    parser.add_argument("--csv", type=Path, help="CSV file with OHLCV columns")
    parser.add_argument("--ticker", help="Yahoo Finance ticker, e.g. AAPL, 0700.HK, 600519.SS")
    parser.add_argument("--start", default="2018-01-01", help="Download start date for --ticker")
    parser.add_argument("--end", default=None, help="Download end date for --ticker")
    parser.add_argument("--horizon", type=int, default=20, help="Forecast horizon in trading days")
    parser.add_argument("--out", type=Path, default=Path("stock_model_output"), help="Output directory")
    args = parser.parse_args()
    if not args.csv and not args.ticker:
        raise SystemExit("Pass either --csv or --ticker")

    args.out.mkdir(parents=True, exist_ok=True)
    prices = load_prices(args)
    features = add_indicators(prices)
    summary = summarize_technicals(features)
    forecast = train_forecast(features, args.horizon)
    output = {"technical_summary": summary, "forecast": forecast}
    features.to_csv(args.out / "features.csv")
    (args.out / "summary.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
