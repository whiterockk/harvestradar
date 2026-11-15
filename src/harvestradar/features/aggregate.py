"""Aggregation: grid cells -> regions -> countries, dekads, and country-season features "as of" a date.

Leak-free by construction: a feature computed for date t only uses weather up to t - publication lag,
and every anomaly is measured against the same calendar span in strictly earlier years (expanding
climatology, at least `min_years`).
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from harvestradar.config import Commodity, Settings
from harvestradar.features.stress import frost_days, hargreaves_et0, heat_degree_days
from harvestradar.features.windows import active_season, season_switch

VARS = ["tmax_c", "tmin_c", "precip_mm", "sm_root", "sm_top", "et0_mm"]
FEATURES = ["hdd_z", "tmax_z", "precip_z", "sm_root_z", "sm_pre_z", "et_z", "frost_z",
            "oni", "anom_last", "progress"]


def region_daily(cells_w: pd.DataFrame, cell_data: pd.DataFrame) -> pd.DataFrame:
    """Weighted mean of cell series per region. cells_w: region_id, cell_id, lat, cell_weight."""
    d = cell_data.copy()
    lat = d["cell_id"].str.slice(0, 7).astype(float)
    d["et0_mm"] = hargreaves_et0(d["tmax_c"].to_numpy(), d["tmin_c"].to_numpy(), lat.to_numpy(),
                                 d["date"].dt.day_of_year.to_numpy())
    m = cells_w[["region_id", "cell_id", "cell_weight"]].merge(d, on="cell_id")
    num = m[VARS].mul(m["cell_weight"], axis=0)
    num[["region_id", "date"]] = m[["region_id", "date"]]
    den = m[VARS].notna().mul(m["cell_weight"], axis=0)
    den[["region_id", "date"]] = m[["region_id", "date"]]
    s = num.groupby(["region_id", "date"])[VARS].sum(min_count=1)
    w = den.groupby(["region_id", "date"])[VARS].sum()
    out = (s / w.replace(0, np.nan)).reset_index()
    return out


def country_daily(regions: pd.DataFrame, rdaily: pd.DataFrame) -> pd.DataFrame:
    """Production-weighted mean of region series per country (weights renormalised in each country)."""
    r = regions[["region_id", "country_iso3", "weight"]].copy()
    r["w"] = r["weight"] / r.groupby("country_iso3")["weight"].transform("sum")
    m = rdaily.merge(r[["region_id", "country_iso3", "w"]], on="region_id")
    num = m[VARS].mul(m["w"], axis=0)
    num[["country_iso3", "date"]] = m[["country_iso3", "date"]]
    den = m[VARS].notna().mul(m["w"], axis=0)
    den[["country_iso3", "date"]] = m[["country_iso3", "date"]]
    s = num.groupby(["country_iso3", "date"])[VARS].sum(min_count=1)
    w = den.groupby(["country_iso3", "date"])[VARS].sum()
    return (s / w.replace(0, np.nan)).reset_index()


class SeasonCube:
    """Daily country series laid out as (season year x day offset), aligned on each season's first
    window day, so that "the same calendar span in earlier years" is a column slice."""

    def __init__(self, c: Commodity, country: str, daily: pd.DataFrame, cfg: Settings):
        self.c, self.country = c, country
        self.pre = int(cfg.features["pre_window_days"])
        self.tail = int(cfg.features["tail_days"])
        self.min_years = int(cfg.climatology["min_years_expanding"])
        heat, frost = c.thresholds.get("heat_c", 30.0), c.thresholds.get("frost_c", 0.0)
        s = daily.set_index("date").sort_index()
        s = s[~s.index.duplicated()]
        self.first_year = s.index.min().year
        self.last_date = s.index.max().date()
        years = list(range(self.first_year, self.last_date.year + 3))
        spans = {y: c.season_span(country, y) for y in years}
        lengths = [(spans[y][1] - spans[y][0]).days + 1 for y in years]
        self.lead = 400  # days before the first window kept in the cube (covers the whole season)
        self.width = self.lead + max(lengths) + self.tail + 5
        self.years = years
        self.start = {y: spans[y][0] for y in years}
        idx = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=800))
        s = s.reindex(idx)
        variables = {
            "hdd": heat_degree_days(s["tmax_c"], heat),
            "tmax": s["tmax_c"],
            "precip": s["precip_mm"],
            "sm": s["sm_root"],
            "et": s["et0_mm"],
            "frost": frost_days(s["tmin_c"], frost).where(s["tmin_c"].notna()),
        }
        ny = len(years)
        self.data = {k: np.full((ny, self.width), np.nan) for k in variables}
        self.mask = np.zeros((ny, self.width), dtype=bool)
        base = idx[0].date()
        for i, y in enumerate(years):
            o0 = (self.start[y] - dt.timedelta(days=self.lead) - base).days
            lo, hi = max(o0, 0), min(o0 + self.width, len(idx))
            if hi <= lo:
                continue
            for k, v in variables.items():
                self.data[k][i, lo - o0:hi - o0] = v.to_numpy()[lo:hi]
            days = pd.date_range(self.start[y] - dt.timedelta(days=self.lead), periods=self.width).date
            for w in c.windows[country]:
                ws, we = w.dates(y)
                self.mask[i] |= (days >= ws) & (days <= we)
        # cumulative sums (NaN treated as missing: tracked with counts)
        self.cum, self.cnt = {}, {}
        for k, a in self.data.items():
            win = np.where(self.mask & np.isfinite(a), a, 0.0)
            self.cum[k] = np.cumsum(win, axis=1)
            self.cnt[k] = np.cumsum(self.mask & np.isfinite(a), axis=1)
            allv = np.where(np.isfinite(a), a, 0.0)
            self.cum[k + "_all"] = np.cumsum(allv, axis=1)
            self.cnt[k + "_all"] = np.cumsum(np.isfinite(a), axis=1)
        self.mask_cnt = np.cumsum(self.mask, axis=1)

    def offset(self, season: int, day: dt.date) -> int:
        return (day - self.start[season]).days + self.lead

    def _z(self, vals: np.ndarray, iy: int, floor: float) -> float:
        hist = vals[:iy]
        hist = hist[np.isfinite(hist)]
        if len(hist) < self.min_years or not np.isfinite(vals[iy]):
            return np.nan
        sd = max(np.std(hist, ddof=1), floor)
        return float((vals[iy] - hist.mean()) / sd)

    def features(self, season: int, cutoff: dt.date) -> dict:
        iy = self.years.index(season)
        k = min(self.offset(season, cutoff), self.width - 1)
        total = int(self.mask[iy].sum())
        if k < 0:
            elapsed = 0
        else:
            elapsed = int(self.mask_cnt[iy, k])
        out = {"progress": elapsed / total if total else 0.0}
        if elapsed == 0:
            for f in ["hdd_z", "tmax_z", "precip_z", "sm_root_z", "et_z", "frost_z"]:
                out[f] = 0.0
        else:
            # same elapsed window span in every year: value at column k
            def agg(name: str, mean: bool) -> np.ndarray:
                s = self.cum[name][:, k]
                n = self.cnt[name][:, k].astype(float)
                full = self.mask_cnt[:, k].astype(float)
                ok = (full > 0) & (n >= 0.9 * full)
                v = s / np.maximum(n, 1) if mean else s * full / np.maximum(n, 1)
                return np.where(ok, v, np.nan)

            out["hdd_z"] = self._z(agg("hdd", False), iy, 2.0)
            out["tmax_z"] = self._z(agg("tmax", True), iy, 0.2)
            out["precip_z"] = self._z(np.sqrt(np.clip(agg("precip", False), 0, None)), iy, 0.5)
            out["sm_root_z"] = self._z(agg("sm", True), iy, 0.01)
            out["et_z"] = self._z(agg("et", False), iy, 1.0)
            out["frost_z"] = self._z(agg("frost", False), iy, 0.5)
        # soil moisture over the `pre` days ending at min(cutoff, day before first window)
        k_end = min(k, self.lead - 1)
        k_beg = k_end - self.pre
        if k_beg >= 0:
            s = self.cum["sm_all"][:, k_end] - self.cum["sm_all"][:, k_beg]
            n = self.cnt["sm_all"][:, k_end] - self.cnt["sm_all"][:, k_beg]
            v = np.where(n >= 0.9 * self.pre, s / np.maximum(n, 1), np.nan)
            out["sm_pre_z"] = self._z(v, iy, 0.01)
        else:
            out["sm_pre_z"] = np.nan
        for f in list(out):
            if f != "progress" and out[f] is not None and np.isfinite(out[f]):
                out[f] = float(np.clip(out[f], -5, 5))
        return out


def to_country_season(cfg: Settings, key: str, cdaily: pd.DataFrame, dates: list[dt.date],
                      oni: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    """Features for every (country, as_of date): the active season of each country at that date."""
    from harvestradar.ingest.enso import oni_as_of

    c = cfg.commodities[key]
    lag = cfg.lag_days
    rows = []
    for country in c.countries:
        d = cdaily[cdaily.country_iso3 == country]
        if d.empty:
            print(f"[features] {key} {country}: no weather")
            continue
        cube = SeasonCube(c, country, d, cfg)
        for t in dates:
            season = active_season(c, country, t, cube.tail)
            if season not in cube.years:
                continue
            f = cube.features(season, t - dt.timedelta(days=lag))
            ws = [w.dates(season) for w in c.windows[country]]
            f.update(commodity=key, country_iso3=country, season=season, as_of=pd.Timestamp(t),
                     window_open=any(s <= t <= e for s, e in ws),
                     switch=pd.Timestamp(season_switch(c, country, season, cube.tail)))
            rows.append(f)
    feat = pd.DataFrame(rows)
    if feat.empty:
        return feat
    feat["oni"] = oni_as_of(oni, feat["as_of"]).to_numpy()
    feat = _attach_anom_last(feat, targets)
    return feat


def _attach_anom_last(feat: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    """Most recent published yield anomaly of an earlier season (published by as_of)."""
    t = targets[["commodity", "country_iso3", "season", "yield_anom", "available_at"]].dropna()
    t = t.assign(available_at=pd.to_datetime(t["available_at"]).astype("datetime64[ns]")).sort_values("available_at")
    feat = feat.assign(as_of=pd.to_datetime(feat["as_of"]).astype("datetime64[ns]"))
    out = []
    for (k, ctry), g in feat.groupby(["commodity", "country_iso3"]):
        tt = t[(t.commodity == k) & (t.country_iso3 == ctry)]
        g = g.sort_values("as_of")
        if tt.empty:
            g["anom_last"] = np.nan
        else:
            m = pd.merge_asof(g[["as_of"]].reset_index(), tt[["available_at", "season", "yield_anom"]]
                              .rename(columns={"season": "last_season"}),
                              left_on="as_of", right_on="available_at")
            m = m.set_index("index")
            ok = m["last_season"] < g["season"]
            g["anom_last"] = m["yield_anom"].where(ok)
        out.append(g)
    return pd.concat(out).sort_index()
