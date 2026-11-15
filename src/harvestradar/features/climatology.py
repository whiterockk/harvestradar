"""Climatologies (mean and standard deviation per region and dekad of year).

mode="fixed": one base period (used for the stress map).
mode="expanding": past years only, at least `min_years` (used for the model, to avoid look-ahead).
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd


def compute_climatology(df: pd.DataFrame, value_cols: list[str], base: tuple[int, int] = (2001, 2020),
                        mode: Literal["fixed", "expanding"] = "fixed", min_years: int = 10,
                        key: str = "region_id") -> pd.DataFrame:
    """df has columns key, year, dekad (0..35) and value_cols.
    fixed: returns key, dekad, <col>_mean, <col>_std.
    expanding: returns key, year, dekad, <col>_mean, <col>_std computed on years strictly before `year`."""
    if mode == "fixed":
        b = df[df.year.between(*base)]
        g = b.groupby([key, "dekad"])[value_cols]
        out = g.mean().add_suffix("_mean").join(g.std(ddof=1).add_suffix("_std")).reset_index()
        return out
    df = df.sort_values([key, "dekad", "year"]).reset_index(drop=True)
    out = df[[key, "year", "dekad"]].copy()
    for col in value_cols:
        g = df.groupby([key, "dekad"])[col]
        n = g.cumcount()  # number of strictly earlier years
        s1 = g.transform(lambda s: s.cumsum().shift(1))
        s2 = g.transform(lambda s: (s ** 2).cumsum().shift(1))
        mean = s1 / n.replace(0, np.nan)
        var = (s2 - n * mean ** 2) / (n - 1).replace(0, np.nan)
        out[f"{col}_mean"] = mean.where(n >= min_years)
        out[f"{col}_std"] = np.sqrt(var.clip(lower=0)).where(n >= min_years)
    return out


def zscore(x: pd.Series, mean: pd.Series, std: pd.Series, floor: float) -> pd.Series:
    return (x - mean) / std.clip(lower=floor)
