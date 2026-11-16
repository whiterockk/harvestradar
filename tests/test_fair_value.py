import math

import numpy as np
import pandas as pd
import pytest

from harvestradar.paths import DEMO
from harvestradar.signal.fair_value import comovement, fair_value_series, index_path

FLEX = {"slope_pct_per_pct": -3.0, "se": 1.0, "p_value": 0.01}


def _prices(n=400, level=100.0):
    return pd.DataFrame({"date": pd.bdate_range("2024-01-01", periods=n), "close": np.full(n, level)})


def _path(gap):
    return pd.DataFrame({"date": pd.to_datetime(["2023-12-01"]), "delta_prod_pct": [gap], "delta_prod_lo_pct": [gap - 5],
                         "delta_prod_hi_pct": [gap + 5], "risk_z": [1.0]})


def test_fair_value_moves_with_supply_gap_and_band_brackets_it():
    fv = fair_value_series(_prices(), _path(-1.0), FLEX)
    last = fv.iloc[-1]
    assert last.anchor == pytest.approx(100.0)
    assert last.fair == pytest.approx(100 * math.exp(0.03))  # 1 % missing, 3 % per 1 % -> about +3 %
    assert last.fair_lo < last.fair < last.fair_hi
    assert last.fair_lo == pytest.approx(100 * math.exp((3 - 1.2816) / 100))
    assert last.gap_to_fair_pct == pytest.approx(100 * (100 / last.fair - 1))


def test_no_gap_means_fair_value_is_the_anchor():
    last = fair_value_series(_prices(), _path(0.0), FLEX).iloc[-1]
    assert last.fair == pytest.approx(last.anchor) and last.fair_lo == pytest.approx(last.fair_hi)


def test_anchor_needs_200_days_and_uses_no_future_index():
    p = _prices()
    path = pd.DataFrame({"date": pd.to_datetime(["2024-12-01"]), "delta_prod_pct": [-2.0], "delta_prod_lo_pct": [-3.0],
                         "delta_prod_hi_pct": [-1.0], "risk_z": [2.0]})
    fv = fair_value_series(p, path, FLEX)
    assert fv.date.min() >= pd.Timestamp("2024-12-01")  # no index value known before its date
    assert len(fair_value_series(p.head(150), _path(-1.0), FLEX)) == 0


def test_index_path_switches_from_weekly_to_daily():
    cols = {"delta_prod_lo_pct": 0.0, "delta_prod_hi_pct": 0.0, "risk_z": 0.0}
    w = pd.DataFrame({"commodity": "maize", "date": pd.to_datetime(["2025-07-25", "2025-08-01", "2025-08-08"]),
                      "delta_prod_pct": [1.0, 2.0, 3.0], **cols})
    d = pd.DataFrame({"commodity": "maize", "date": pd.to_datetime(["2025-08-01", "2025-08-04"]),
                      "delta_prod_pct": [20.0, 30.0], **cols})
    p = index_path(w, d, "maize", "2025-08-01")
    assert p.delta_prod_pct.tolist() == [1.0, 20.0, 30.0]


def test_comovement_reports_correlations():
    dates = pd.date_range("2006-01-06", periods=300, freq="W-FRI")
    rng = np.random.default_rng(0)
    z = rng.normal(size=300).cumsum() / 10
    w = pd.DataFrame({"commodity": "maize", "date": dates, "risk_z": z, "major_window_open": np.arange(300) % 4 == 0})
    px = pd.DataFrame({"date": pd.bdate_range("2005-12-01", "2012-01-01")})
    px["close"] = 100 * np.exp(rng.normal(scale=0.01, size=len(px)).cumsum())
    out = comovement(w, {"maize": px})["maize"]
    assert out["weeks"] == 300 and -1 <= out["weekly_changes"] <= 1 and out["weeks_in_windows"] == 75


@pytest.mark.skipif(not (DEMO / "fair_value_daily.parquet").exists(), reason="no demo snapshot")
def test_demo_fair_value_contract():
    df = pd.read_parquet(DEMO / "fair_value_daily.parquet")
    assert {"commodity", "date", "close", "anchor", "fair", "fair_lo", "fair_hi", "gap_to_fair_pct"} <= set(df.columns)
    assert (df.fair_lo <= df.fair + 1e-9).all() and (df.fair <= df.fair_hi + 1e-9).all()
