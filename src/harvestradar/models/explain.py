"""SHAP explanations of the median model, in percentage points of yield (or production) anomaly."""

from __future__ import annotations

import numpy as np
import pandas as pd
import shap

from harvestradar.models.yield_model import MODEL_FEATURES, YieldModel, design


def shap_by_prediction(model: YieldModel, df: pd.DataFrame) -> pd.DataFrame:
    X = design(df)
    ex = shap.TreeExplainer(model.median.booster_)
    vals = ex.shap_values(X)
    out = pd.DataFrame(np.asarray(vals) * 100.0, columns=[f"shap_{c}" for c in MODEL_FEATURES], index=df.index)
    out["shap_base"] = float(np.atleast_1d(ex.expected_value)[0]) * 100.0
    return out
