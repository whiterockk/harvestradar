"""Daily and dekad stress variables.

- heat degree days above a crop threshold (Schlenker and Roberts 2009: maize 29 C)
- frost days (tmin below a threshold, coffee)
- Hargreaves reference evapotranspiration (FAO-56 eq. 52), from tmax, tmin and latitude
- dekad composite stress: mean of heat, dryness (30-day rain) and root-zone soil moisture anomalies,
  re-standardised against the fixed base period so that it reads as a z-score.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from harvestradar.features.climatology import compute_climatology, zscore


def heat_degree_days(tmax: pd.Series, threshold_c: float) -> pd.Series:
    return (tmax - threshold_c).clip(lower=0)


def frost_days(tmin: pd.Series, threshold_c: float = 2.0) -> pd.Series:
    return (tmin < threshold_c).astype(float)


def extraterrestrial_radiation(lat_deg: np.ndarray, doy: np.ndarray) -> np.ndarray:
    """Ra in MJ m-2 day-1 (FAO-56 eq. 21)."""
    phi = np.deg2rad(lat_deg)
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    delta = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1, 1))
    return (24 * 60 / np.pi) * 0.0820 * dr * (ws * np.sin(phi) * np.sin(delta)
                                              + np.cos(phi) * np.cos(delta) * np.sin(ws))


def hargreaves_et0(tmax: np.ndarray, tmin: np.ndarray, lat_deg: np.ndarray, doy: np.ndarray) -> np.ndarray:
    ra = extraterrestrial_radiation(lat_deg, doy)
    tmean = (tmax + tmin) / 2
    return 0.0023 * (ra / 2.45) * (tmean + 17.8) * np.sqrt(np.clip(tmax - tmin, 0, None))


def spi_like(precip_sum: pd.Series) -> pd.Series:
    """Square-root transform before z-scoring: closer to normal than raw rainfall sums."""
    return np.sqrt(precip_sum.clip(lower=0))


def dekad_of(dates: pd.Series) -> pd.Series:
    d = pd.to_datetime(dates)
    return (d.dt.month - 1) * 3 + np.minimum((d.dt.day - 1) // 10, 2)


def dekad_end(year: pd.Series, dekad: pd.Series) -> pd.Series:
    month = dekad // 3 + 1
    k = dekad % 3
    first = pd.to_datetime(dict(year=year, month=month, day=1))
    last = first + pd.offsets.MonthEnd(0)
    day = np.where(k == 0, 10, np.where(k == 1, 20, last.dt.day))
    return pd.to_datetime(dict(year=year, month=month, day=day))


def to_dekad(daily: pd.DataFrame, heat_c: float) -> pd.DataFrame:
    """daily: region_id, date, tmax_c, tmin_c, precip_mm, sm_root. Returns dekad table."""
    d = daily.copy()
    d["year"] = d["date"].dt.year
    d["dekad"] = dekad_of(d["date"])
    d["hdd"] = heat_degree_days(d["tmax_c"], heat_c)
    g = d.groupby(["region_id", "year", "dekad"])
    out = g.agg(tmax=("tmax_c", "mean"), precip=("precip_mm", "sum"), sm_root=("sm_root", "mean"),
                hdd=("hdd", "sum"), n=("tmax_c", "count")).reset_index()
    out = out.sort_values(["region_id", "year", "dekad"])
    out["precip30"] = out.groupby("region_id")["precip"].transform(lambda s: s.rolling(3, min_periods=3).sum())
    out["precip30_t"] = spi_like(out["precip30"])
    out["dekad_end"] = dekad_end(out["year"], out["dekad"])
    return out


def dekad_stress(dek: pd.DataFrame, base: tuple[int, int]) -> pd.DataFrame:
    """Anomalies vs a fixed base period and the composite stress index."""
    cols = ["tmax", "hdd", "precip30_t", "sm_root"]
    clim = compute_climatology(dek, cols, base=base, mode="fixed")
    m = dek.merge(clim, on=["region_id", "dekad"], how="left")
    m["tmax_z"] = zscore(m["tmax"], m["tmax_mean"], m["tmax_std"], 0.3)
    m["hdd_z"] = zscore(m["hdd"], m["hdd_mean"], m["hdd_std"], 2.0)
    m["precip_z"] = zscore(m["precip30_t"], m["precip30_t_mean"], m["precip30_t_std"], 0.5)
    m["sm_root_z"] = zscore(m["sm_root"], m["sm_root_mean"], m["sm_root_std"], 0.01)
    for c in ["tmax_z", "hdd_z", "precip_z", "sm_root_z"]:
        m[c] = m[c].clip(-4, 4)
    heat = m[["tmax_z", "hdd_z"]].mean(axis=1)
    m["raw"] = (heat - m["precip_z"] - m["sm_root_z"]) / 3
    c2 = compute_climatology(m[["region_id", "year", "dekad", "raw"]], ["raw"], base=base, mode="fixed")
    m = m.merge(c2, on=["region_id", "dekad"], how="left")
    m["stress"] = zscore(m["raw"], m["raw_mean"], m["raw_std"], 0.1).clip(-4, 4)
    out = m[["region_id", "dekad_end", "year", "dekad", "stress", "hdd_z", "precip_z", "sm_root_z",
             "tmax_z", "tmax"]].copy()
    for c in ["stress", "hdd_z", "precip_z", "sm_root_z", "tmax_z", "tmax"]:
        out[c] = out[c].astype("float32").round(3)
    return out.dropna(subset=["stress"])
