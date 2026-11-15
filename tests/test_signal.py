import numpy as np
import pandas as pd

from harvestradar.signal.backtest import permutation_p, perf, positions


def test_positions_rule():
    r = pd.DataFrame({"risk_z": [0, 0, 0, 0, 1.0, 1.2, -1.0, -1.0], "major_window_open": [True] * 4 + [True, False, True, True]})
    p = positions(r, 0.5, 4)
    assert p.tolist()[4] == 1 and p.tolist()[5] == 0 and p.tolist()[6] == -1


def test_permutation_p_bounds():
    rng = np.random.default_rng(1)
    ret = pd.Series(rng.normal(0, 0.02, 300))
    pos = pd.Series(rng.choice([-1, 0, 1], 300))
    p = permutation_p(ret, pos, 5, 200, 42)
    assert 0 < p <= 1
    assert "sharpe" in perf(ret, pos, 5)


def test_standardize_uses_past_only_and_flags_shortfalls():
    from harvestradar.signal.risk_index import standardize

    dates = pd.date_range("2000-01-07", "2012-12-28", freq="W-FRI")
    rng = np.random.default_rng(0)
    d = pd.Series(rng.normal(0, 0.5, len(dates)), index=dates)
    d.loc["2012-07-13":"2012-08-31"] = -3.0  # a large expected shortfall
    st = standardize(d, 15, 3, 4, 0.5)
    assert st.loc["2012-07-20", "risk_z"] > 3
    assert st.loc[:"2003-12-31", "risk_z"].isna().all()  # fewer than 4 years of history
    d2 = d.copy()
    d2.loc["2012-09-01":] = 50.0  # future values must not change earlier z
    st2 = standardize(d2, 15, 3, 4, 0.5)
    assert np.allclose(st.loc[:"2012-08-31", "risk_z"].dropna(), st2.loc[:"2012-08-31", "risk_z"].dropna())
