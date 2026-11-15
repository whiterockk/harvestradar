"""Pre-registered trading-rule test (research only, not investment advice).

signal_t = change of risk_z over `delta_weeks` weeks.
position = +1 if signal > theta and a major critical window is open; -1 if signal < -theta; else 0.
Computed on Friday, executed at the close of the next trading day (Monday), held one week.
Returns: front-month continuous futures, roll days neutralised. Costs in bps per unit of turnover.
Reported against buy and hold, long-in-major-windows, and 1,000 random permutations of the positions.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from harvestradar.config import Settings


def weekly_returns(prices: pd.DataFrame, dates: pd.Series) -> pd.Series:
    """Log return from the first trading close after each Friday to the first close after the next Friday."""
    px = prices.set_index("date").sort_index()
    r = px["ret_1d"].fillna(0.0)
    cum = r.cumsum()
    idx = px.index
    out = []
    for d in dates:
        i0 = idx.searchsorted(d + pd.Timedelta(days=1))
        i1 = idx.searchsorted(d + pd.Timedelta(days=8))
        if i1 >= len(idx) or i0 >= len(idx):
            out.append(np.nan)
            continue
        out.append(float(cum.iloc[i1] - cum.iloc[i0]))
    return pd.Series(out, index=dates.index)


def positions(risk: pd.DataFrame, theta: float, delta_weeks: int, long_only: bool = False) -> pd.Series:
    sig = risk["risk_z"].diff(delta_weeks)
    pos = np.where((sig > theta) & risk["major_window_open"], 1, np.where(sig < -theta, -1, 0))
    if long_only:
        pos = np.maximum(pos, 0)
    return pd.Series(pos, index=risk.index).fillna(0)


def perf(ret: pd.Series, pos: pd.Series, cost_bps: float) -> dict:
    turnover = pos.diff().abs().fillna(pos.abs())
    net = pos * ret - turnover * cost_bps / 1e4
    net = net.dropna()
    if net.std() == 0 or len(net) < 20:
        return {"weeks": int(len(net)), "ann_return": 0.0, "sharpe": 0.0, "trades": int((turnover > 0).sum())}
    ann = net.mean() * 52
    vol = net.std() * np.sqrt(52)
    down = net[net < 0].std() * np.sqrt(52)
    eq = net.cumsum()
    dd = float((eq - eq.cummax()).min())
    X = np.ones((len(net), 1))
    nw = sm.OLS(net.to_numpy(), X).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
    active = net[pos.loc[net.index] != 0]
    return {"weeks": int(len(net)), "ann_return": float(ann), "ann_vol": float(vol),
            "sharpe": float(ann / vol), "sortino": float(ann / down) if down > 0 else None,
            "max_drawdown_log": dd, "hit_rate": float((active > 0).mean()) if len(active) else None,
            "trades": int((turnover > 0).sum()), "exposure": float((pos != 0).mean()),
            "nw_tstat": float(nw.tvalues[0])}


def _sharpe(ret: np.ndarray, pos: np.ndarray, cost_bps: float) -> float:
    turnover = np.abs(np.diff(pos, prepend=0))
    net = pos * ret - turnover * cost_bps / 1e4
    net = net[np.isfinite(net)]
    sd = net.std(ddof=1)
    return float(net.mean() / sd * np.sqrt(52)) if sd > 0 else 0.0


def permutation_p(ret: pd.Series, pos: pd.Series, cost_bps: float, n: int, seed: int) -> float:
    """Share of random re-orderings of the same positions with a Sharpe ratio at least as high."""
    rng = np.random.default_rng(seed)
    r, p = ret.to_numpy(dtype=float), pos.to_numpy(dtype=float)
    obs = _sharpe(r, p, cost_bps)
    count = sum(_sharpe(r, rng.permutation(p), cost_bps) >= obs for _ in range(n))
    return float((count + 1) / (n + 1))


def run_backtest(cfg: Settings, risk: pd.DataFrame, prices: dict[str, pd.DataFrame]) -> dict:
    b = cfg.backtest
    cost = float(b["cost_bps_per_trade"]) + float(b.get("slippage_bps", 0))
    out = {"rule": {"signal": f"change in risk_z over {b['delta_weeks']} weeks",
                    "long": "signal > theta and a major critical window open", "short": "signal < -theta",
                    "execution": "next trading day close after the Friday update, held one week",
                    "theta": b["theta"], "delta_weeks": b["delta_weeks"], "cost_bps_per_trade": cost,
                    "permutations": b["permutations"], "start": b["start"]},
           "disclaimer": "Research output, not investment advice.", "commodities": {}}
    for key in cfg.commodities:
        r = risk[(risk.commodity == key) & (risk.date >= pd.Timestamp(b["start"]))].dropna(subset=["risk_z"])
        r = r.reset_index(drop=True)
        ret = weekly_returns(prices[key], r["date"])
        pos = positions(r, float(b["theta"]), int(b["delta_weeks"]))
        res = perf(ret, pos, cost)
        res["permutation_p"] = permutation_p(ret, pos, cost, int(b["permutations"]), int(cfg.seed))
        bench = {"buy_and_hold": perf(ret, pd.Series(1, index=r.index), 0.0),
                 "long_in_major_windows": perf(ret, r["major_window_open"].astype(int), cost),
                 "long_only_rule": perf(ret, positions(r, float(b["theta"]), int(b["delta_weeks"]), True), cost)}
        grid = []
        for th in b["grid_theta"]:
            for dw in b["grid_delta"]:
                pp = positions(r, float(th), int(dw))
                g = perf(ret, pp, cost)
                g.update(theta=th, delta_weeks=dw,
                         permutation_p=permutation_p(ret, pp, cost, int(b["permutations"]) // 4, int(cfg.seed)))
                grid.append(g)
        out["commodities"][key] = {"rule": res, "benchmarks": bench, "grid": grid,
                                   "best_grid_p": min(g["permutation_p"] for g in grid)}
    out["best_p_overall"] = min(v["best_grid_p"] for v in out["commodities"].values())
    out["best_rule_p"] = min(v["rule"]["permutation_p"] for v in out["commodities"].values())
    return out
