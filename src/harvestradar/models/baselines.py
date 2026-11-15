"""Baselines reported next to the model, without selection: trend only (zero anomaly), persistence
(latest published anomaly) and a 3-variable linear regression."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

LINEAR_VARS = ["hdd_z", "precip_z", "sm_root_z"]


def zero(df: pd.DataFrame) -> np.ndarray:
    return np.zeros(len(df))


def persistence(df: pd.DataFrame) -> np.ndarray:
    return df["anom_last"].fillna(0.0).to_numpy()


def fit_linear(train: pd.DataFrame) -> LinearRegression:
    X = train[LINEAR_VARS].fillna(0.0)
    return LinearRegression().fit(X, train["yield_anom"])


def linear(model: LinearRegression, df: pd.DataFrame) -> np.ndarray:
    return model.predict(df[LINEAR_VARS].fillna(0.0))
