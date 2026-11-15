"""Rolling-origin validation with real publication dates.

Vintage V (calendar year of the forecast date) is trained only on seasons whose FAOSTAT figures were
published before 1 January of V, then predicts every week of year V. This is the "real-time" record:
the 2012 forecasts never saw a target published in or after 2012.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from harvestradar.config import Settings
from harvestradar.models import baselines
from harvestradar.models.yield_model import YieldModel, train


def training_rows(panel: pd.DataFrame, vintage: int, cfg: Settings, stride_days: int = 14) -> pd.DataFrame:
    cut = pd.Timestamp(f"{vintage}-01-01")
    r = panel[(panel["season"] >= int(cfg.features["first_season"])) & panel["yield_anom"].notna()
              & (panel["target_available_at"] < cut)]
    # one sample every `stride_days` per country-season (weekly rows are strongly autocorrelated)
    days = (r["as_of"] - pd.Timestamp("1990-01-05")).dt.days
    return r[(days % stride_days) == 0]


def rolling_origin(panel: pd.DataFrame, cfg: Settings, first: int, last: int,
                   store=None) -> tuple[pd.DataFrame, dict]:
    """Returns weekly out-of-sample predictions for vintages first..last and vintage metadata."""
    preds, meta = [], {}
    for v in range(first, last + 1):
        tr = training_rows(panel, v, cfg)
        if tr["season"].nunique() < 5:
            continue
        model: YieldModel = train(tr, cfg)
        lin = baselines.fit_linear(tr)
        test = panel[panel["as_of"].dt.year == v]
        if test.empty:
            continue
        p = model.predict(test)
        p["pred_linear"] = baselines.linear(lin, test)
        p["vintage"] = v
        preds.append(pd.concat([test, p], axis=1))
        meta[v] = {"trained_on_seasons_up_to": int(tr["season"].max()),
                   "first_season": int(tr["season"].min()), "rows": int(len(tr)),
                   "country_seasons": int(model.n_seasons)}
        if store is not None:
            store(v, model)
        print(f"[model] vintage {v}: trained on seasons {meta[v]['first_season']}-"
              f"{meta[v]['trained_on_seasons_up_to']} ({len(tr)} rows), predicted {len(test)} weeks")
    return pd.concat(preds, ignore_index=True), meta


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    ok = np.isfinite(y) & np.isfinite(p)
    y, p = y[ok], p[ok]
    if len(y) < 3:
        return {"n": int(len(y))}
    rho = spearmanr(y, p).statistic if np.std(p) > 0 else float("nan")
    return {"n": int(len(y)), "rmse": float(np.sqrt(np.mean((y - p) ** 2))), "mae": float(np.mean(np.abs(y - p))),
            "spearman": float(rho) if np.isfinite(rho) else None,
            "sign_accuracy": float(np.mean(np.sign(y) == np.sign(p))) if np.std(p) > 0 else None}
