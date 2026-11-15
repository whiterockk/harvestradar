"""Model target: yield anomaly vs a trend fitted ONLY on earlier years.

anom(Y) = (yield(Y) - trend(Y)) / trend(Y), trend = linear fit on the previous `trend_years` years
(at least `min_trend_years`). FAOSTAT year Y is published in December of Y+1: available_at.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from harvestradar.config import Settings


def yield_anomaly(df: pd.DataFrame, trend_years: int = 15, min_years: int = 8,
                  value: str = "yield_t_ha") -> pd.DataFrame:
    """df: commodity, country_iso3, year, <value>. Adds trend_t_ha (trend of <value>) and yield_anom."""
    out = []
    for _, g in df.sort_values("year").groupby(["commodity", "country_iso3"]):
        g = g.copy()
        yrs = g["year"].to_numpy()
        ys = g[value].to_numpy(dtype=float)
        trend = np.full(len(g), np.nan)
        for i, y in enumerate(yrs):
            m = (yrs < y) & (yrs >= y - trend_years) & np.isfinite(ys) & (ys > 0)
            if m.sum() >= min_years:
                b, a = np.polyfit(yrs[m], ys[m], 1)
                trend[i] = a + b * y
        g["trend_t_ha"] = trend
        g["yield_anom"] = (g[value] - trend) / trend
        out.append(g)
    return pd.concat(out, ignore_index=True)


def build_targets(cfg: Settings, fao: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for key, c in cfg.commodities.items():
        value = "yield_t_ha" if c.target == "yield" else "production_t"
        a = yield_anomaly(fao[fao.commodity == key], int(cfg.targets["trend_years"]),
                          int(cfg.targets["min_trend_years"]), value=value)
        a["target_kind"] = c.target
        parts.append(a)
    t = pd.concat(parts, ignore_index=True).rename(columns={"year": "season"})
    t["source"] = "FAOSTAT QCL"
    # guard against absurd anomalies from data breaks (e.g. area redefinitions)
    t.loc[t["yield_anom"].abs() > 0.8, "yield_anom"] = np.nan
    return t[["commodity", "country_iso3", "season", "yield_t_ha", "trend_t_ha", "yield_anom",
              "production_t", "world_production_t", "available_at", "source", "target_kind"]]


def country_shares(fao: pd.DataFrame, key: str, as_of: pd.Timestamp, years: int = 3) -> pd.Series:
    """Share of world production per country, mean of the latest `years` published years at as_of."""
    f = fao[(fao.commodity == key) & (fao.available_at <= as_of)]
    if f.empty:
        return pd.Series(dtype=float)
    last = f.year.max()
    f = f[f.year > last - years]
    p = f.groupby("country_iso3").production_t.mean()
    w = f.groupby("year").world_production_t.first().mean()
    return p / w
