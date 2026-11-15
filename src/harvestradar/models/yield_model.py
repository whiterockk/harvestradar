"""LightGBM yield-anomaly model: one model shared by all commodities (commodity as a feature),
a median model plus 10 % / 90 % quantile models for the uncertainty band."""

from __future__ import annotations

from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd

from harvestradar.config import Settings
from harvestradar.features.aggregate import FEATURES

COMMODITY_CODES = {"maize": 0, "coffee": 1, "cocoa": 2}
MODEL_FEATURES = FEATURES + ["commodity_code"]


def design(df: pd.DataFrame) -> pd.DataFrame:
    X = df[FEATURES].astype(float).copy()
    X["commodity_code"] = df["commodity"].map(COMMODITY_CODES).astype(int)
    return X


@dataclass
class YieldModel:
    median: lgb.LGBMRegressor
    lo: lgb.LGBMRegressor
    hi: lgb.LGBMRegressor
    trained_up_to: int
    n_rows: int
    n_seasons: int

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        X = design(df)
        p = self.median.predict(X)
        lo, hi = self.lo.predict(X), self.hi.predict(X)
        lo, hi = np.minimum(lo, p), np.maximum(hi, p)
        return pd.DataFrame({"pred_anom": p, "pred_lo": lo, "pred_hi": hi}, index=df.index)


def _params(cfg: Settings) -> dict:
    m = cfg.model
    return dict(num_leaves=int(m["num_leaves"]), min_child_samples=int(m["min_data_in_leaf"]),
                learning_rate=float(m["learning_rate"]), n_estimators=int(m["n_estimators"]),
                colsample_bytree=float(m["feature_fraction"]), subsample=0.8, subsample_freq=1,
                reg_lambda=float(m.get("reg_lambda", 0.0)),
                random_state=int(cfg.seed), deterministic=True, force_row_wise=True, n_jobs=4, verbose=-1)


def train(rows: pd.DataFrame, cfg: Settings) -> YieldModel:
    """rows: training samples (features + yield_anom). Each country-season gets the same total weight."""
    X = design(rows)
    y = rows["yield_anom"].astype(float)
    key = rows["commodity"] + "|" + rows["country_iso3"] + "|" + rows["season"].astype(str)
    w = 1.0 / key.map(key.value_counts())
    mode = cfg.model.get("sample_weight", "equal")
    if mode in ("sqrt_share", "share") and "target_share" in rows:
        s = rows["target_share"].fillna(rows["target_share"].median()).clip(lower=1e-4)
        w = w * (np.sqrt(s) if mode == "sqrt_share" else s)
    base = _params(cfg)
    mono = [0] * len(MODEL_FEATURES)
    if cfg.model.get("monotone_heat", True):
        mono[MODEL_FEATURES.index("hdd_z")] = -1  # more heat in the window cannot raise the forecast
    med = lgb.LGBMRegressor(objective="regression", monotone_constraints=mono, **base)
    med.fit(X, y, sample_weight=w, categorical_feature=["commodity_code"])
    q = cfg.model.get("quantiles", [0.1, 0.9])
    lo = lgb.LGBMRegressor(objective="quantile", alpha=float(q[0]), **base)
    hi = lgb.LGBMRegressor(objective="quantile", alpha=float(q[1]), **base)
    lo.fit(X, y, sample_weight=w, categorical_feature=["commodity_code"])
    hi.fit(X, y, sample_weight=w, categorical_feature=["commodity_code"])
    return YieldModel(med, lo, hi, int(rows["season"].max()), len(rows), int(key.nunique()))
