"""Harvest-risk index.

Expected world production gap:   dP_c(t) = sum_country share(t) x pred_anom(t)   (percent)
Risk index:                      risk_z(t) = -dP_c(t) / sigma(t)

sigma(t) is the standard deviation of the REALISED world-weighted anomaly sum_country share x anom(y)
over the latest published seasons (default 30), so the index reads "expected shortfall in units of a
typical year-to-year supply surprise". Positive risk_z = higher supply risk. Shares are those known at
t (FAOSTAT, latest published years) or MapSPAM 2020 country totals where FAOSTAT cannot split the crop
(arabica).
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pycountry

from harvestradar.config import Settings
from harvestradar.models.targets import country_shares
from harvestradar.paths import PROCESSED


def country_name(iso3: str) -> str:
    special = {"USA": "United States", "RUS": "Russia", "IRN": "Iran", "VNM": "Vietnam", "BOL": "Bolivia",
               "TZA": "Tanzania", "VEN": "Venezuela", "LAO": "Laos", "COD": "DR Congo", "CIV": "Côte d'Ivoire",
               "KOR": "South Korea", "PRK": "North Korea", "SYR": "Syria", "MDA": "Moldova"}
    if iso3 in special:
        return special[iso3]
    c = pycountry.countries.get(alpha_3=iso3)
    return getattr(c, "common_name", None) or (c.name if c else iso3)


def shares_at(cfg: Settings, key: str, fao: pd.DataFrame, t: pd.Timestamp) -> pd.Series:
    c = cfg.commodities[key]
    if c.share_source == "mapspam":
        s = pd.read_parquet(PROCESSED / f"country_shares_{key}.parquet").set_index("country_iso3")["share"]
        return s
    return country_shares(fao, key, t)


def realised_sigma(targets: pd.DataFrame, key: str, shares: pd.Series, countries: list[str],
                   t: pd.Timestamp, years: int, min_years: int) -> float:
    tg = targets[(targets.commodity == key) & targets.country_iso3.isin(countries)
                 & (targets.available_at <= t)].dropna(subset=["yield_anom"])
    if tg.empty:
        return np.nan
    tg = tg.assign(w=tg.country_iso3.map(shares).fillna(0.0))
    a = (tg.w * tg.yield_anom).groupby(tg.season).sum()
    a = a.sort_index().tail(years)
    if len(a) < min_years:
        return np.nan
    return float(a.std(ddof=1))


def build_risk_index(cfg: Settings, preds: pd.DataFrame, targets: pd.DataFrame, fao: pd.DataFrame) -> pd.DataFrame:
    rows = []
    years, min_years = int(cfg.index["sigma_history_years"]), int(cfg.index["min_sigma_years"])
    major = float(cfg.index["major_share"])
    for key, c in cfg.commodities.items():
        p = preds[preds.commodity == key]
        cache: dict = {}
        for t, g in p.groupby("as_of"):
            ykey = (t.year, t.month)  # shares and sigma change at most monthly
            if ykey not in cache:
                sh = shares_at(cfg, key, fao, t)
                cache[ykey] = (sh, realised_sigma(targets, key, sh, c.countries, t, years, min_years))
            sh, sigma = cache[ykey]
            g = g.assign(share=g.country_iso3.map(sh).fillna(0.0))
            contrib = 100 * g.share * g.pred_anom
            delta = float(contrib.sum())
            lo = float((100 * g.share * g.pred_lo).sum())
            hi = float((100 * g.share * g.pred_hi).sum())
            cov = float(g.share.sum())
            risk_z = -delta / (100 * sigma) if sigma and np.isfinite(sigma) else np.nan
            g = g.assign(contrib=contrib).sort_values("contrib", key=np.abs, ascending=False)
            contributors = [{
                "country": r.country_iso3, "name": country_name(r.country_iso3),
                "contrib_pct": round(float(r.contrib), 3), "pred_anom_pct": round(100 * float(r.pred_anom), 2),
                "pred_lo_pct": round(100 * float(r.pred_lo), 2), "pred_hi_pct": round(100 * float(r.pred_hi), 2),
                "share_pct": round(100 * float(r.share), 2), "season": int(r.season),
                "window_open": bool(r.window_open)} for r in g.itertuples()]
            rows.append({
                "commodity": key, "date": t, "risk_z": round(risk_z, 4) if np.isfinite(risk_z) else np.nan,
                "delta_prod_pct": round(delta, 4), "delta_prod_lo_pct": round(lo, 4),
                "delta_prod_hi_pct": round(hi, 4), "sigma_pct": round(100 * sigma, 4) if sigma else np.nan,
                "coverage_share": round(cov, 4),
                "major_window_open": bool((g.window_open & (g.share >= major)).any()),
                "contributors": json.dumps(contributors[:5], ensure_ascii=False),
                "contributors_all": json.dumps(contributors, ensure_ascii=False),
                "vintage": int(g.vintage.iloc[0]),
            })
    return pd.DataFrame(rows).sort_values(["commodity", "date"]).reset_index(drop=True)
