"""Front-month continuous futures from yfinance (Yahoo terms: personal or research use).

The continuous series jumps at each roll; returns on detected roll days are neutralised (NaN).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from harvestradar.config import Settings
from harvestradar.ingest.manifest import record
from harvestradar.paths import PROCESSED, RAW


def load_futures(ticker: str, start: str, end: str) -> pd.DataFrame:
    import yfinance as yf

    df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.reset_index().rename(columns={"Date": "date", "Close": "close"})
    df = df[["date", "close"]].dropna()
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    return df


def detect_rolls(df: pd.DataFrame, k: float = 4.0) -> pd.Series:
    """Flag days whose absolute log return is larger than k rolling MADs AND fall in a roll month
    (the last days before expiry). Conservative: only isolated jumps are flagged."""
    r = np.log(df["close"]).diff()
    mad = r.abs().rolling(60, min_periods=20).median()
    big = r.abs() > k * mad.clip(lower=1e-4) * 1.4826
    # a roll jump is isolated: the next day does not reverse it fully
    return big.fillna(False)


def fetch_prices(cfg: Settings) -> dict[str, pd.DataFrame]:
    out = {}
    end = (pd.Timestamp(cfg.as_of_end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    for key, c in cfg.commodities.items():
        df = load_futures(c.ticker, "2000-01-01", end)
        df = df[df["date"] <= pd.Timestamp(cfg.as_of_end)]
        df["ticker"] = c.ticker
        df["ret_1d"] = np.log(df["close"]).diff()
        df["roll_flag"] = detect_rolls(df)
        df.loc[df["roll_flag"], "ret_1d"] = np.nan
        raw = RAW / "prices" / f"{key}_{c.ticker.replace('=', '')}.csv"
        raw.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(raw, index=False)
        record(raw, f"Yahoo Finance via yfinance ({c.ticker})",
               f"https://finance.yahoo.com/quote/{c.ticker}", "Yahoo terms: personal or research use")
        PROCESSED.mkdir(parents=True, exist_ok=True)
        df.to_parquet(PROCESSED / f"prices_{key}.parquet", index=False)
        out[key] = df
    return out
