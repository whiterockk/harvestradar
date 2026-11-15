"""Harvest-risk index (SPEC 5.9).

Expected world production gap:   dP_c(t) = sum_country share(t) x pred_anom(t)   (percent)
Risk index:                      risk_z(t) = -(dP_c(t) - mean) / sd

mean and sd are the model climatology, as in seasonal forecasting: the same vintage model re-forecasts the
same weeks of the year (within +/- `calendar_window_weeks`) over the previous `standardize_years` years
(rolling history, past years only), so the index reads "how unusual is this week's forecast for this time of
year". This removes the drift between vintages that a raw history of past forecasts would carry. The sd is
floored at `sigma_floor` x the sd of all weeks of the same hindcast, so that calm periods stay calm.
(`standardize` below, on the raw history of past forecasts, was the first version; it gave a skewed index.)
Positive risk_z = higher supply risk than usual for this time of year. Shares are those known at t
(FAOSTAT, latest published years) or MapSPAM 2020 country totals where FAOSTAT cannot split the crop
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


def standardize(delta: pd.Series, years: int, window_weeks: int, min_years: int, floor: float) -> pd.DataFrame:
    """delta: weekly dP indexed by date. Returns mean, sd (floored) and z, from past history only."""
    d = delta.sort_index()
    dates = d.index
    woy = dates.isocalendar().week.to_numpy().astype(int)
    vals = d.to_numpy()
    out = []
    for i, t in enumerate(dates):
        lo, hi = t - pd.DateOffset(years=years), t - pd.Timedelta(weeks=52)
        m = (dates >= lo) & (dates <= hi)
        if not m.any():
            out.append((np.nan, np.nan, np.nan))
            continue
        diff = np.abs(woy[m] - woy[i])
        diff = np.minimum(diff, 52 - diff)
        near = diff <= window_weeks
        hv = vals[m][near]
        yrs = pd.DatetimeIndex(dates[m][near]).year.nunique()
        if yrs < min_years or len(hv) < 3:
            out.append((np.nan, np.nan, np.nan))
            continue
        mu, sd = float(np.mean(hv)), float(np.std(hv, ddof=1))
        sd_all = float(np.std(vals[m], ddof=1))
        sd = max(sd, floor * sd_all)
        out.append((mu, sd, -(vals[i] - mu) / sd if sd > 0 else np.nan))
    return pd.DataFrame(out, index=dates, columns=["mu", "sd", "risk_z"])


def build_risk_index(cfg: Settings, preds: pd.DataFrame, targets: pd.DataFrame, fao: pd.DataFrame,
                     clim: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = []
    major = float(cfg.index["major_share"])
    for key, c in cfg.commodities.items():
        p = preds[preds.commodity == key]
        cache: dict = {}
        for t, g in p.groupby("as_of"):
            ykey = (t.year, t.month)  # shares and sigma change at most monthly
            if ykey not in cache:
                cache[ykey] = shares_at(cfg, key, fao, t)
            sh = cache[ykey]
            g = g.assign(share=g.country_iso3.map(sh).fillna(0.0))
            contrib = 100 * g.share * g.pred_anom
            delta = float(contrib.sum())
            lo = float((100 * g.share * g.pred_lo).sum())
            hi = float((100 * g.share * g.pred_hi).sum())
            cov = float(g.share.sum())
            g = g.assign(contrib=contrib).sort_values("contrib", key=np.abs, ascending=False)
            contributors = [{
                "country": r.country_iso3, "name": country_name(r.country_iso3),
                "contrib_pct": round(float(r.contrib), 3), "pred_anom_pct": round(100 * float(r.pred_anom), 2),
                "pred_lo_pct": round(100 * float(r.pred_lo), 2), "pred_hi_pct": round(100 * float(r.pred_hi), 2),
                "share_pct": round(100 * float(r.share), 2), "season": int(r.season),
                "window_open": bool(r.window_open)} for r in g.itertuples()]
            rows.append({
                "commodity": key, "date": t,
                "delta_prod_pct": round(delta, 4), "delta_prod_lo_pct": round(lo, 4),
                "delta_prod_hi_pct": round(hi, 4),
                "coverage_share": round(cov, 4),
                "major_window_open": bool((g.window_open & (g.share >= major)).any()),
                "contributors": json.dumps(contributors[:5], ensure_ascii=False),
                "contributors_all": json.dumps(contributors, ensure_ascii=False),
                "vintage": int(g.vintage.iloc[0]),
            })
    df = pd.DataFrame(rows).sort_values(["commodity", "date"]).reset_index(drop=True)
    cols = ["commodity", "date", "risk_z", "delta_prod_pct", "delta_prod_lo_pct", "delta_prod_hi_pct", "mu_pct",
            "sigma_pct", "coverage_share", "major_window_open", "contributors", "contributors_all", "vintage"]
    if clim is not None:
        return apply_climatology(df, clim)[cols].reset_index(drop=True)
    ix = cfg.index
    parts = []
    for key, g in df.groupby("commodity"):
        st = standardize(g.set_index("date")["delta_prod_pct"], int(ix["standardize_years"]),
                         int(ix["calendar_window_weeks"]), int(ix["min_years"]), float(ix["sigma_floor"]))
        g = g.assign(risk_z=st["risk_z"].round(4).to_numpy(), mu_pct=st["mu"].round(4).to_numpy(),
                     sigma_pct=st["sd"].round(4).to_numpy())
        parts.append(g)
    return pd.concat(parts)[cols].reset_index(drop=True)


def hindcast_climatology(cfg: Settings, panel: pd.DataFrame, load_model, fao: pd.DataFrame, vintages: list[int],
                         years: int, window_weeks: int, floor: float) -> pd.DataFrame:
    """Model climatology, as in seasonal forecasting: for each vintage V, the vintage-V model re-forecasts the
    same weeks of the previous `years` years; dP of those hindcasts gives the mean and sd of "what this model
    says at this time of year". Removes the drift between vintages. Returns commodity, vintage, woy, mu, sd."""
    rows = []
    for v in vintages:
        model = load_model(v)
        if model is None:
            continue
        past = panel[(panel.as_of.dt.year >= v - years) & (panel.as_of.dt.year < v)]
        if past.empty:
            continue
        p = past[["commodity", "country_iso3", "as_of"]].copy()
        p["pred"] = model.predict(past)["pred_anom"].to_numpy()
        for key in cfg.commodities:
            q = p[p.commodity == key]
            if q.empty:
                continue
            sh = shares_at(cfg, key, fao, pd.Timestamp(f"{v}-01-01"))
            q = q.assign(c=100 * q.country_iso3.map(sh).fillna(0.0) * q.pred)
            d = q.groupby("as_of").c.sum()
            woy = d.index.isocalendar().week.to_numpy().astype(int)
            sd_all = float(d.std(ddof=1))
            for w in range(1, 54):
                diff = np.abs(woy - w)
                diff = np.minimum(diff, 52 - diff)
                hv = d.to_numpy()[diff <= window_weeks]
                if len(hv) < 3:
                    continue
                rows.append({"commodity": key, "vintage": v, "woy": w, "mu": float(hv.mean()),
                             "sd": max(float(hv.std(ddof=1)), floor * sd_all)})
    return pd.DataFrame(rows)


def apply_climatology(risk: pd.DataFrame, clim: pd.DataFrame) -> pd.DataFrame:
    r = risk.copy()
    r["woy"] = r["date"].dt.isocalendar().week.astype(int).to_numpy()
    r = r.drop(columns=[c for c in ("risk_z", "mu_pct", "sigma_pct") if c in r]).merge(
        clim.rename(columns={"mu": "mu_pct", "sd": "sigma_pct"}), on=["commodity", "vintage", "woy"], how="left")
    r["risk_z"] = (-(r["delta_prod_pct"] - r["mu_pct"]) / r["sigma_pct"]).round(4)
    r["mu_pct"], r["sigma_pct"] = r["mu_pct"].round(4), r["sigma_pct"].round(4)
    return r.drop(columns="woy")
