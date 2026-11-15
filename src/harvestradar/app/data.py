"""Offline data access for the app: everything comes from data/demo (and config/). Cached."""

from __future__ import annotations

import json
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import streamlit as st

from harvestradar.paths import DEMO

DATA = Path(os.environ.get("HARVESTRADAR_DEMO", DEMO))


@st.cache_data(show_spinner=False)
def meta() -> dict:
    return json.loads((DATA / "meta.json").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def jsonfile(name: str) -> dict:
    p = DATA / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


@st.cache_data(show_spinner=False)
def risk() -> pd.DataFrame:
    r = pd.read_parquet(DATA / "risk_index.parquet")
    r["date"] = pd.to_datetime(r["date"])
    return r


@st.cache_data(show_spinner=False)
def risk_daily() -> pd.DataFrame:
    p = DATA / "risk_index_daily.parquet"
    if not p.exists():
        return risk()
    r = pd.read_parquet(p)
    r["date"] = pd.to_datetime(r["date"])
    return r


@st.cache_data(show_spinner=False)
def today() -> pd.Timestamp:
    """The app's "today": the latest date in data/demo (never the clock)."""
    return risk_daily()["date"].max()


@st.cache_data(show_spinner=False)
def stress(key: str) -> pd.DataFrame:
    s = pd.read_parquet(DATA / f"stress_{key}.parquet")
    s["dekad_end"] = pd.to_datetime(s["dekad_end"])
    return s


@st.cache_data(show_spinner=False)
def regions(key: str) -> gpd.GeoDataFrame:
    return gpd.read_file(DATA / f"regions_{key}.geojson")


@st.cache_data(show_spinner=False)
def prices(key: str) -> pd.DataFrame:
    p = pd.read_parquet(DATA / f"prices_{key}.parquet")
    p["date"] = pd.to_datetime(p["date"])
    return p.sort_values("date")


@st.cache_data(show_spinner=False)
def predictions() -> pd.DataFrame:
    p = pd.read_parquet(DATA / "predictions.parquet")
    p["date"] = pd.to_datetime(p["date"])
    return p


@st.cache_data(show_spinner=False)
def shap_latest() -> pd.DataFrame:
    return pd.read_parquet(DATA / "shap_latest.parquet")


@st.cache_data(show_spinner=False)
def notes() -> pd.DataFrame:
    p = DATA / "notes.parquet"
    if not p.exists():
        return pd.DataFrame()
    n = pd.read_parquet(p)
    n["week"] = pd.to_datetime(n["week"])
    return n


@st.cache_data(show_spinner=False)
def oni() -> pd.DataFrame:
    p = DATA / "oni.parquet"
    if not p.exists():
        p = DATA.parent / "processed" / "oni.parquet"
    o = pd.read_parquet(p)
    o["available_at"] = pd.to_datetime(o["available_at"])
    return o


@st.cache_data(show_spinner=False)
def world() -> gpd.GeoDataFrame:
    return gpd.read_file(DATA / "world_110m.geojson")


# ---------- derived tables ----------

@st.cache_data(show_spinner=False)
def latest_risk(key: str, at: pd.Timestamp | None = None) -> dict:
    r = risk_daily()
    r = r[(r.commodity == key)].dropna(subset=["risk_z"]).sort_values("date")
    if at is not None:
        r = r[r.date <= at]
    if r.empty:
        return {}
    row = r.iloc[-1].to_dict()
    row["contributors"] = json.loads(row["contributors"])
    return row


@st.cache_data(show_spinner=False)
def risk_series(key: str, weeks: int | None = None, end: pd.Timestamp | None = None) -> pd.DataFrame:
    r = risk()
    r = r[r.commodity == key].dropna(subset=["risk_z"]).sort_values("date")
    if end is not None:
        r = r[r.date <= end]
    return r.tail(weeks) if weeks else r


@st.cache_data(show_spinner=False)
def top_regions(key: str, dekad: pd.Timestamp, n: int = 5) -> pd.DataFrame:
    s = stress(key)
    s = s[s.dekad_end == dekad]
    g = regions(key)[["region_id", "adm1_name", "country_iso3", "country_name", "weight", "lat", "lon"]]
    m = s.merge(g, on="region_id")
    m["score"] = m["stress"] * m["weight"]
    return m.sort_values("score", ascending=False).head(n).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def oni_latest(at: pd.Timestamp) -> dict:
    o = oni()
    o = o[o.available_at <= at].sort_values("available_at")
    if o.empty:
        return {}
    last = o.iloc[-1]
    hist = o.tail(36)
    return {"value": float(last.oni), "label": str(last.label), "series": hist["oni"].round(2).tolist(),
            "available_at": last.available_at.strftime("%Y-%m-%d")}


def windows_for(key: str, country: str) -> list[dict]:
    return meta()["commodities"][key]["windows"].get(country, [])


def window_spans(key: str, country: str, start: pd.Timestamp, end: pd.Timestamp) -> list[tuple]:
    """Calendar spans of a country's critical windows between two dates (from config, via meta.json)."""
    out = []
    for w in windows_for(key, country):
        for season in range(start.year - 1, end.year + 2):
            y = season + int(w.get("year_offset", 0))
            s = pd.Timestamp(f"{y}-{w['start']}")
            e = pd.Timestamp(f"{y}-{w['end']}")
            if e < s:
                e = pd.Timestamp(f"{y + 1}-{w['end']}")
            if e >= start and s <= end:
                out.append((max(s, start), min(e, end), w["stage"]))
    return sorted(set(out))


def country_names() -> dict:
    out = {}
    for c in meta()["commodities"].values():
        out.update(c.get("country_names", {}))
    return out


def oni_strength(v: float) -> str:
    """NOAA convention for the Oceanic Nino Index."""
    a = abs(v)
    kind = "El Niño" if v > 0 else "La Niña"
    if a < 0.5:
        return "neutral conditions"
    return ("weak " if a < 1 else "moderate " if a < 1.5 else "strong " if a < 2 else "very strong ") + kind


def fmt_signed(x: float, nd: int = 2) -> str:
    return f"{x:+.{nd}f}" if x is not None and np.isfinite(x) else "n/a"
