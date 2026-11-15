"""How much should the futures price move for a given supply gap? (price flexibility)

For each crop and marketing year Y (2002 to the latest published season):
  x = realised world supply gap: sum over modelled countries of share x production (or yield) anomaly, in %
  y = change of the average front-month futures price, marketing year Y vs Y-1, in % (log)
Slope b = % price change per 1 % of world supply gap (expected negative: a shortfall lifts prices).
Applied to the model's expected supply gap today: implied move = b x dP, with an 80 % band (b +/- 1.28 se).
A small-sample, descriptive estimate: reported with n, R2 and p-value, never as a forecast of the price.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

MARKETING_START = {"maize": 9, "coffee": 7, "cocoa": 10}  # first month of the marketing year


def marketing_year_prices(prices: pd.DataFrame, start_month: int) -> pd.Series:
    p = prices.set_index("date")["close"]
    my = p.index.year - (p.index.month < start_month).astype(int)
    avg = np.log(p).groupby(my).mean()
    counts = p.groupby(my).size()
    return avg[counts >= 200]  # complete marketing years only


def world_gap(targets: pd.DataFrame, key: str, countries: list[str]) -> pd.Series:
    t = targets[(targets.commodity == key) & targets.country_iso3.isin(countries)].dropna(subset=["yield_anom"])
    t = t.assign(share=t.production_t / t.world_production_t)
    return (100 * t.share * t.yield_anom).groupby(t.season).sum()


def price_flexibility(cfg, targets: pd.DataFrame, prices: dict[str, pd.DataFrame]) -> dict:
    out = {}
    for key, c in cfg.commodities.items():
        lp = marketing_year_prices(prices[key], MARKETING_START[key])
        dy = (100 * lp.diff()).dropna()
        gap = world_gap(targets, key, c.countries)
        d = pd.concat([gap.rename("gap"), dy.rename("dprice")], axis=1).dropna()
        d = d[d.index >= 2002]
        if len(d) < 8:
            continue
        m = sm.OLS(d["dprice"], sm.add_constant(d["gap"])).fit(cov_type="HC1")
        b, se = float(m.params["gap"]), float(m.bse["gap"])
        out[key] = {"slope_pct_per_pct": round(b, 2), "se": round(se, 2), "p_value": round(float(m.pvalues["gap"]), 3),
                    "r2": round(float(m.rsquared), 2), "n": int(len(d)), "years": [int(d.index.min()), int(d.index.max())],
                    "marketing_year_start_month": MARKETING_START[key],
                    "points": [[int(y), round(float(r.gap), 2), round(float(r.dprice), 1)] for y, r in d.iterrows()]}
    return out


def implied_move(flex: dict, delta_prod_pct: float) -> dict:
    b, se = flex["slope_pct_per_pct"], flex["se"]
    lo, hi = sorted([(b - 1.28 * se) * delta_prod_pct, (b + 1.28 * se) * delta_prod_pct])
    return {"implied_pct": round(b * delta_prod_pct, 1), "low_pct": round(lo, 1), "high_pct": round(hi, 1)}
