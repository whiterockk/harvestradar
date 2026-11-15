"""NOAA CPC Oceanic Nino Index (ONI): 3-month running mean of ERSST.v5 SST anomalies in Nino 3.4.

Public domain (NOAA). Season codes DJF, JFM, ... NDJ; the value of a season is published early in the
month after its last month.
"""

from __future__ import annotations

import pandas as pd

from harvestradar.ingest.manifest import download, record
from harvestradar.paths import PROCESSED, RAW

ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
SEASONS = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]
SEASON_LABEL = {s: f"{m1}-{m3}" for s, (m1, m3) in zip(SEASONS, [
    ("DEC", "FEB"), ("JAN", "MAR"), ("FEB", "APR"), ("MAR", "MAY"), ("APR", "JUN"), ("MAY", "JUL"),
    ("JUN", "AUG"), ("JUL", "SEP"), ("AUG", "OCT"), ("SEP", "NOV"), ("OCT", "DEC"), ("NOV", "JAN")])}


def fetch_oni() -> pd.DataFrame:
    dest = RAW / "oni" / "oni.ascii.txt"
    download(ONI_URL, dest)
    record(dest, "NOAA CPC ONI", ONI_URL, "Public domain (NOAA)")
    rows = []
    for line in dest.read_text().splitlines()[1:]:
        parts = line.split()
        if len(parts) != 4:
            continue
        seas, yr, total, anom = parts
        rows.append((seas, int(yr), float(total), float(anom)))
    df = pd.DataFrame(rows, columns=["season", "year", "total", "oni"])
    idx = df["season"].map(SEASONS.index)
    # centre month of the 3-month season; DJF of year Y is centred on January Y
    df["centre"] = pd.to_datetime(dict(year=df.year, month=idx + 1, day=1))
    # last month of the season, then published around the 10th of the following month
    last = df["centre"] + pd.offsets.MonthBegin(1)
    df["available_at"] = last + pd.offsets.MonthBegin(1) + pd.Timedelta(days=9)
    df["label"] = df["season"].map(SEASON_LABEL) + " " + df["year"].astype(str)
    df = df.sort_values("centre").reset_index(drop=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED / "oni.parquet", index=False)
    return df


def oni_as_of(oni: pd.DataFrame, dates: pd.Series) -> pd.Series:
    """Latest ONI value published on or before each date."""
    o = oni.sort_values("available_at")[["available_at", "oni"]].copy()
    o["available_at"] = pd.to_datetime(o["available_at"]).astype("datetime64[ns]")
    d = pd.DataFrame({"date": pd.to_datetime(pd.Series(dates).to_numpy()).astype("datetime64[ns]")}).reset_index()
    m = pd.merge_asof(d.sort_values("date"), o, left_on="date", right_on="available_at")
    return m.set_index("index").sort_index()["oni"]
