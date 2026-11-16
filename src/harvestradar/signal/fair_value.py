"""Climate fair value: the futures price that today's expected world supply gap justifies, on its own.

For each crop and each trading day t:
  anchor  A_t = average close over the last 12 months (252 trading days): "no new weather news"
  gap     G_t = expected world supply vs normal from the index (in %), latest value known on day t
  slope   b   = price flexibility from price_impact.py (% price change per 1 % of world supply gap)
  fair    F_t = A_t x exp(b x G_t / 100)
  band    80 %: A_t x exp((b +/- 1.28 se_b) x G_t / 100), the same range as the implied move on the price card.
          It covers the uncertainty of the price reaction, not of the harvest forecast itself (the index's own
          80 % range of world supply sums country ranges, so it is a worst case and far too wide to price on).
  gap to fair value = close / F_t - 1

What it is: the climate component of fair value. What it is not: a full valuation. Demand, stocks, the dollar,
fund positioning and other origins move prices too; the distance between the price and F_t is what they
explain. The index is weekly before `dates.daily_start` and daily after.

Also here: how closely the index and the price moved together (weekly changes, critical windows, the next
13 weeks), so the app can say plainly why the two lines need not move together.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

Z80 = 1.2816
ANCHOR_DAYS = 252


def index_path(weekly: pd.DataFrame, daily: pd.DataFrame, key: str, daily_start: str) -> pd.DataFrame:
    """Weekly index before daily_start, daily index from it: one series of (date, gap, gap_lo, gap_hi, z)."""
    cols = ["date", "delta_prod_pct", "delta_prod_lo_pct", "delta_prod_hi_pct", "risk_z"]
    w = weekly[(weekly.commodity == key) & (weekly.date < pd.Timestamp(daily_start))][cols]
    d = daily[(daily.commodity == key) & (daily.date >= pd.Timestamp(daily_start))][cols]
    out = pd.concat([w, d], ignore_index=True).dropna(subset=["delta_prod_pct"]).sort_values("date")
    out["date"] = out["date"].astype("datetime64[ns]")
    return out.reset_index(drop=True)


def fair_value_series(prices: pd.DataFrame, path: pd.DataFrame, flex: dict) -> pd.DataFrame:
    b, se = float(flex["slope_pct_per_pct"]), float(flex["se"])
    p = prices[["date", "close"]].dropna().sort_values("date").copy()
    p["date"] = p["date"].astype("datetime64[ns]")
    p["anchor"] = p["close"].rolling(ANCHOR_DAYS, min_periods=200).mean()
    path = path.assign(date=path["date"].astype("datetime64[ns]")).sort_values("date")
    p = pd.merge_asof(p, path, on="date", direction="backward").dropna(subset=["anchor", "delta_prod_pct"])
    g = p["delta_prod_pct"]
    mid, s = b * g, (Z80 * se * g).abs()
    out = pd.DataFrame({
        "date": p["date"], "close": p["close"], "anchor": p["anchor"], "supply_gap_pct": g, "risk_z": p["risk_z"],
        "premium_pct": 100 * (np.exp(mid / 100) - 1),
        "fair": p["anchor"] * np.exp(mid / 100),
        "fair_lo": p["anchor"] * np.exp((mid - s) / 100),
        "fair_hi": p["anchor"] * np.exp((mid + s) / 100),
    })
    out["gap_to_fair_pct"] = 100 * (out["close"] / out["fair"] - 1)
    return out.reset_index(drop=True)


def build_fair_value(cfg, flex: dict, weekly: pd.DataFrame, daily: pd.DataFrame,
                     prices: dict[str, pd.DataFrame]) -> pd.DataFrame:
    parts = []
    for key, fx in flex.items():
        path = index_path(weekly, daily, key, str(cfg.dates["daily_start"]))
        parts.append(fair_value_series(prices[key], path, fx).assign(commodity=key))
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)


def summary(fv: pd.DataFrame, flex: dict) -> dict:
    """Latest reading per crop, for the app and the notes."""
    out = {}
    for key, g in fv.groupby("commodity"):
        last = g.iloc[-1]
        fx = flex[key]
        out[key] = {"date": last.date.strftime("%Y-%m-%d"), "close": round(float(last.close), 2),
                    "anchor": round(float(last.anchor), 2), "supply_gap_pct": round(float(last.supply_gap_pct), 2),
                    "premium_pct": round(float(last.premium_pct), 2), "fair": round(float(last.fair), 2),
                    "fair_lo": round(float(last.fair_lo), 2), "fair_hi": round(float(last.fair_hi), 2),
                    "gap_to_fair_pct": round(float(last.gap_to_fair_pct), 2),
                    "slope_pct_per_pct": fx["slope_pct_per_pct"], "se": fx["se"], "reliable": fx["p_value"] < 0.10,
                    "anchor_days": ANCHOR_DAYS}
    return out


def comovement(weekly: pd.DataFrame, prices: dict[str, pd.DataFrame], start: str = "2006-01-01") -> dict:
    """Correlations between the weekly index and the futures price since `start`."""
    out = {}
    for key, pr in prices.items():
        r = weekly[(weekly.commodity == key) & (weekly.date >= pd.Timestamp(start))].dropna(subset=["risk_z"])
        if len(r) < 100:
            continue
        r = r.set_index("date").sort_index()
        p = pr.assign(date=pr.date.astype("datetime64[ns]")).set_index("date")["close"].sort_index()
        lp = np.log(p).resample("W-FRI").last().reindex(r.index, method="ffill")
        dz, ret = r.risk_z.diff(), 100 * lp.diff()
        win = r.major_window_open.astype(bool)
        fwd = 100 * (lp.shift(-13) - lp)

        def c(a, b):
            v = a.corr(b)
            return None if v is None or math.isnan(v) else round(float(v), 2)

        out[key] = {"from": start, "weeks": int(len(r)), "weeks_in_windows": int(win.sum()),
                    "weekly_changes": c(dz, ret), "weekly_changes_in_windows": c(dz[win], ret[win]),
                    "index_vs_next_13_weeks": c(r.risk_z, fwd)}
    return out
