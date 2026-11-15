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
