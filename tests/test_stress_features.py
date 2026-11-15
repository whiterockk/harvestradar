import datetime as dt

import numpy as np
import pandas as pd

from harvestradar.features.aggregate import SeasonCube
from harvestradar.features.stress import dekad_end, dekad_of, frost_days, hargreaves_et0, heat_degree_days, to_dekad
from harvestradar.models.targets import yield_anomaly


def synthetic_daily(start="1981-01-01", end="2026-11-10", seed=0):
    rng = np.random.default_rng(seed)
    d = pd.date_range(start, end, freq="D")
    doy = d.day_of_year.to_numpy()
    tmax = 22 + 10 * np.sin(2 * np.pi * (doy - 100) / 365) + rng.normal(0, 3, len(d))
    return pd.DataFrame({"date": d, "tmax_c": tmax, "tmin_c": tmax - 11, "precip_mm": rng.gamma(0.5, 5, len(d)),
                         "sm_root": np.clip(0.5 + rng.normal(0, 0.05, len(d)), 0, 1), "sm_top": 0.5,
                         "et0_mm": 4.0})


def test_basic_stress_functions():
    assert heat_degree_days(pd.Series([25.0, 31.0]), 29).tolist() == [0.0, 2.0]
    assert frost_days(pd.Series([1.0, 3.0]), 2.0).tolist() == [1.0, 0.0]
    et = hargreaves_et0(np.array([30.0]), np.array([18.0]), np.array([42.0]), np.array([196]))
    assert 3 < et[0] < 9
    d = pd.Series(pd.to_datetime(["2026-01-10", "2026-01-11", "2026-02-28"]))
    assert dekad_of(d).tolist() == [0, 1, 5]
    assert dekad_end(pd.Series([2026]), pd.Series([5])).iloc[0] == pd.Timestamp("2026-02-28")


def test_to_dekad_shapes():
    daily = synthetic_daily("2020-01-01", "2020-12-31").assign(region_id="X")
    dek = to_dekad(daily, 29.0)
    assert len(dek) == 36 and dek["n"].between(8, 11).all()


def test_season_features_are_leak_free(cfg):
    """Changing weather AFTER the cutoff must not change a feature computed as of the cutoff."""
    c = cfg.commodities["maize"]
    base = synthetic_daily()
    cut = dt.date(2012, 7, 20)
    a = SeasonCube(c, "USA", base, cfg).features(2012, cut)
    tampered = base.copy()
    after = tampered["date"] > pd.Timestamp(cut)
    tampered.loc[after, ["tmax_c", "precip_mm", "sm_root"]] = [45.0, 0.0, 0.01]
    b = SeasonCube(c, "USA", tampered, cfg).features(2012, cut)
    for k in a:
        assert (np.isnan(a[k]) and np.isnan(b[k])) or abs(a[k] - b[k]) < 1e-12, k
    assert 0 < a["progress"] < 1


def test_season_features_before_window_are_neutral(cfg):
    c = cfg.commodities["maize"]
    f = SeasonCube(c, "USA", synthetic_daily(), cfg).features(2012, dt.date(2012, 5, 1))
    assert f["progress"] == 0 and f["hdd_z"] == 0 and np.isfinite(f["sm_pre_z"])


def test_trend_uses_only_past_years():
    years = np.arange(1990, 2021)
    y = 5 + 0.1 * (years - 1990)
    df = pd.DataFrame({"commodity": "maize", "country_iso3": "USA", "year": years, "yield_t_ha": y})
    a = yield_anomaly(df).set_index("year")["yield_anom"]
    df2 = df.copy()
    df2.loc[df2.year == 2020, "yield_t_ha"] = 1.0  # a crash in the last year
    b = yield_anomaly(df2).set_index("year")["yield_anom"]
    assert np.allclose(a.loc[:2019].dropna(), b.loc[:2019].dropna())
    assert b.loc[2020] < -0.5 and abs(a.loc[2015]) < 1e-9
