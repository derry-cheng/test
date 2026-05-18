#!/usr/bin/env python3
"""A-share first-pass screener for 20-50 current candidates.

The screener uses fresher signals than quarterly fund-holding disclosure:
current A-share quotes, turnover/liquidity, same-day main-fund flow, and 5-day
main-fund flow from EastMoney endpoints. It can optionally merge quarterly fund
holdings as lagging confirmation, but holdings are not required for selection.

Examples:
  python scripts/a_share_screener.py --limit 30 --out out/a_share_screen
  python scripts/a_share_screener.py --limit 50 --include-fund-holdings --fund-date 20260331
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd
import requests

EASTMONEY_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://data.eastmoney.com/",
}
A_SHARE_FS = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048"
FLOW_FS = "m:0+t:6+f:!2,m:0+t:13+f:!2,m:0+t:80+f:!2,m:1+t:2+f:!2,m:1+t:23+f:!2,m:0+t:7+f:!2,m:1+t:3+f:!2"


def fetch_eastmoney_clist(fields: str, fid: str, fs: str, page_size: int = 500) -> pd.DataFrame:
    url = "https://push2delay.eastmoney.com/api/qt/clist/get"
    rows: list[dict] = []
    page = 1
    total = None
    while True:
        params = {
            "pn": page,
            "pz": page_size,
            "po": 1,
            "np": 1,
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": 2,
            "invt": 2,
            "fid": fid,
            "fs": fs,
            "fields": fields,
        }
        response = requests.get(url, params=params, headers=EASTMONEY_HEADERS, timeout=20)
        response.raise_for_status()
        payload = response.json().get("data") or {}
        diff = payload.get("diff") or []
        if total is None:
            total = int(payload.get("total") or 0)
        if not diff:
            break
        rows.extend(diff)
        if len(rows) >= total:
            break
        page += 1
    return pd.DataFrame(rows)


def fetch_fund_holdings(report_date: str) -> pd.DataFrame:
    normalized_date = f"{report_date[:4]}-{report_date[4:6]}-{report_date[6:]}"
    url = "https://data.eastmoney.com/dataapi/zlsj/list"
    first_params = {
        "date": normalized_date,
        "type": 1,
        "zjc": 0,
        "sortField": "HOULD_NUM",
        "sortDirec": 1,
        "pageNum": 1,
        "pageSize": 500,
        "p": 1,
        "pageNo": 1,
    }
    first_response = requests.get(url, params=first_params, headers=EASTMONEY_HEADERS, timeout=20)
    first_response.raise_for_status()
    first_payload = first_response.json()
    pages = int(first_payload.get("pages") or math.ceil((first_payload.get("count") or 0) / 500) or 1)
    rows = first_payload.get("data") or []
    for page in range(2, pages + 1):
        params = dict(first_params)
        params.update({"pageNum": page, "p": page, "pageNo": page})
        response = requests.get(url, params=params, headers=EASTMONEY_HEADERS, timeout=20)
        response.raise_for_status()
        rows.extend(response.json().get("data") or [])
    raw = pd.DataFrame(rows)
    if raw.empty:
        return raw
    columns = {
        "SECURITY_CODE": "code",
        "HOULD_NUM": "fund_count",
        "HOLD_VALUE": "fund_value",
        "HOLDCHA": "fund_change_type",
        "HOLDCHA_NUM": "fund_share_change",
        "HOLDCHA_RATIO": "fund_share_change_pct",
    }
    return raw.rename(columns=columns)[list(columns.values())]


def percentile_score(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if not higher_is_better:
        numeric = -numeric
    return numeric.rank(pct=True).fillna(0.5)


def build_screen(include_fund_holdings: bool, fund_date: str) -> pd.DataFrame:
    quote_fields = "f12,f14,f2,f3,f4,f5,f6,f7,f8,f9,f10,f20,f21,f23,f62,f184"
    quote = fetch_eastmoney_clist(quote_fields, fid="f62", fs=A_SHARE_FS)
    quote = quote.rename(
        columns={
            "f12": "code",
            "f14": "name",
            "f2": "price",
            "f3": "pct_chg_today",
            "f4": "price_change",
            "f5": "volume",
            "f6": "amount",
            "f7": "amplitude",
            "f8": "turnover_rate",
            "f9": "pe",
            "f10": "volume_ratio",
            "f20": "market_cap",
            "f21": "float_cap",
            "f23": "pb",
            "f62": "main_net_today",
            "f184": "main_net_pct_today",
        }
    )
    flow_fields = "f12,f14,f2,f109,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173,f257,f258,f124"
    flow = fetch_eastmoney_clist(flow_fields, fid="f164", fs=FLOW_FS)
    flow = flow.rename(
        columns={
            "f12": "code",
            "f109": "pct_chg_5d",
            "f164": "main_net_5d",
            "f165": "main_net_pct_5d",
            "f166": "super_net_5d",
            "f167": "super_net_pct_5d",
            "f168": "big_net_5d",
            "f169": "big_net_pct_5d",
        }
    )
    quote["code"] = quote["code"].astype(str).str.zfill(6)
    flow["code"] = flow["code"].astype(str).str.zfill(6)
    merged = quote.merge(
        flow[["code", "pct_chg_5d", "main_net_5d", "main_net_pct_5d", "super_net_5d", "big_net_5d"]],
        on="code",
        how="left",
    )
    if include_fund_holdings:
        fund = fetch_fund_holdings(fund_date)
        if not fund.empty:
            fund["code"] = fund["code"].astype(str).str.zfill(6)
            merged = merged.merge(fund, on="code", how="left")

    for column in merged.columns:
        if column not in {"code", "name", "fund_change_type"}:
            merged[column] = pd.to_numeric(merged[column], errors="coerce")

    filtered = merged[
        (~merged["name"].astype(str).str.contains("ST", na=False))
        & (merged["amount"] >= 100_000_000)
        & (merged["market_cap"] >= 10_000_000_000)
        & (merged["turnover_rate"].between(0.5, 25))
        & (merged["pct_chg_today"].between(-8, 8))
        & (merged["pe"].between(0, 120) | merged["pe"].isna())
    ].copy()
    filtered["money_flow_score"] = 0.6 * percentile_score(filtered["main_net_5d"]) + 0.4 * percentile_score(filtered["main_net_today"])
    filtered["relative_strength_score"] = 0.6 * percentile_score(filtered["pct_chg_5d"]) + 0.4 * percentile_score(filtered["pct_chg_today"])
    filtered["liquidity_score"] = 0.7 * percentile_score(filtered["amount"]) + 0.3 * percentile_score(filtered["turnover_rate"])
    filtered["valuation_score"] = 0.6 * percentile_score(filtered["pe"], higher_is_better=False) + 0.4 * percentile_score(filtered["pb"], higher_is_better=False)
    filtered["stability_score"] = 1 - (filtered["pct_chg_today"].abs() / 10).clip(0, 1)
    if "fund_value" in filtered:
        filtered["fund_confirmation_score"] = (
            0.5 * percentile_score(filtered["fund_value"]) + 0.3 * percentile_score(filtered["fund_count"]) + 0.2 * percentile_score(filtered["fund_share_change"].clip(lower=0))
        )
    else:
        filtered["fund_confirmation_score"] = 0.5
    filtered["score"] = (
        0.30 * filtered["money_flow_score"]
        + 0.22 * filtered["relative_strength_score"]
        + 0.16 * filtered["liquidity_score"]
        + 0.12 * filtered["valuation_score"]
        + 0.10 * filtered["stability_score"]
        + 0.10 * filtered["fund_confirmation_score"]
    )
    return filtered.sort_values("score", ascending=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Screen 20-50 A-share candidates using current flow, liquidity, valuation, and optional fund holdings.")
    parser.add_argument("--limit", type=int, default=30, help="Number of candidates to output; recommended range is 20-50")
    parser.add_argument("--out", type=Path, default=Path("a_share_screen_output"), help="Output directory")
    parser.add_argument("--include-fund-holdings", action="store_true", help="Merge quarterly fund holdings as lagging confirmation")
    parser.add_argument("--fund-date", default="20260331", help="Quarterly fund holding report date in YYYYMMDD format")
    args = parser.parse_args()
    if not 1 <= args.limit <= 200:
        raise SystemExit("--limit must be between 1 and 200")

    args.out.mkdir(parents=True, exist_ok=True)
    screen = build_screen(args.include_fund_holdings, args.fund_date)
    top = screen.head(args.limit).copy()
    columns = [
        "code",
        "name",
        "score",
        "price",
        "pct_chg_today",
        "pct_chg_5d",
        "amount",
        "turnover_rate",
        "market_cap",
        "pe",
        "pb",
        "main_net_today",
        "main_net_5d",
        "money_flow_score",
        "relative_strength_score",
        "liquidity_score",
        "valuation_score",
        "fund_confirmation_score",
    ]
    available_columns = [column for column in columns if column in top.columns]
    top[available_columns].to_csv(args.out / "candidates.csv", index=False)
    summary = {
        "rows_after_filters": int(len(screen)),
        "output_count": int(len(top)),
        "fund_holdings_included": bool(args.include_fund_holdings),
        "fund_date": args.fund_date if args.include_fund_holdings else None,
        "note": "Quarterly fund holdings are lagging confirmation only; primary ranking uses current flow, momentum, liquidity, and valuation.",
    }
    (args.out / "screen_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(top[available_columns].to_string(index=False))


if __name__ == "__main__":
    main()
