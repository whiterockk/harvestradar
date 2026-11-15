"""Write the offline snapshot read by the app (data/demo, versioned, < 50 MB)."""

from __future__ import annotations

import json
import shutil

import geopandas as gpd
import pandas as pd

from harvestradar.config import Settings
from harvestradar.ingest.manifest import download, record
from harvestradar.paths import DEMO, PROCESSED, RAW
from harvestradar.signal.risk_index import country_name

NE_URL = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"


def _world_110m() -> None:
    dest = DEMO / "world_110m.geojson"
    if dest.exists():
        return
    z = RAW / "naturalearth" / "ne_110m_admin_0_countries.zip"
    if not z.exists():
        download(NE_URL, z)
        record(z, "Natural Earth 1:110m admin 0 countries", NE_URL, "Public domain")
    g = gpd.read_file(f"zip://{z}")
    g = g[["ISO_A3", "NAME", "geometry"]].rename(columns={"ISO_A3": "iso3", "NAME": "name"})
    g.to_file(dest, driver="GeoJSON", COORDINATE_PRECISION=3)


def export_demo(cfg: Settings) -> None:
    DEMO.mkdir(parents=True, exist_ok=True)
    start = pd.Timestamp(cfg.index_start)
    risk = pd.read_parquet(PROCESSED / "risk_index.parquet")
    risk.to_parquet(DEMO / "risk_index.parquet", index=False)
    preds = pd.read_parquet(PROCESSED / "predictions_weekly.parquet")
    preds = preds[preds.as_of >= start].rename(columns={"as_of": "date"})
    preds[["commodity", "country_iso3", "season", "date", "pred_anom", "pred_lo", "pred_hi", "window_open",
           "progress", "vintage"]].to_parquet(DEMO / "predictions.parquet", index=False)
    shutil.copy(PROCESSED / "shap_latest.parquet", DEMO / "shap_latest.parquet")
    shutil.copy(PROCESSED / "oni.parquet", DEMO / "oni.parquet")
    if (PROCESSED / "notes.parquet").exists():
        shutil.copy(PROCESSED / "notes.parquet", DEMO / "notes.parquet")
    for name in ["events.json", "model_eval.json", "backtest.json"]:
        shutil.copy(PROCESSED / name, DEMO / name)
    summary = json.loads((PROCESSED / "regions_summary.json").read_text())
    meta = {"as_of": cfg.as_of_end.isoformat(), "index_start": cfg.index_start.isoformat(),
            "climatology_base": cfg.climatology["base"], "weather": "NASA POWER daily (MERRA-2), since 1981",
            "cells": summary.get("cells"), "llm": {"model_id": cfg.llm["model_id"],
                                                   "display_name": cfg.llm["display_name"]},
            "commodities": {}}
    for key, c in cfg.commodities.items():
        st = pd.read_parquet(PROCESSED / f"stress_{key}.parquet")
        st = st[st.dekad_end >= start]
        st[["region_id", "dekad_end", "stress", "hdd_z", "precip_z", "sm_root_z", "tmax_z", "tmax"]].to_parquet(
            DEMO / f"stress_{key}.parquet", index=False)
        g = gpd.read_file(PROCESSED / f"regions_{key}.gpkg")
        g["geometry"] = g.geometry.simplify(0.02, preserve_topology=True)
        g["country_name"] = g["country_iso3"].map(country_name)
        g[["region_id", "country_iso3", "country_name", "adm1_name", "weight", "world_share", "lat", "lon",
           "geometry"]].to_file(DEMO / f"regions_{key}.geojson", driver="GeoJSON", COORDINATE_PRECISION=3)
        pr = pd.read_parquet(PROCESSED / f"prices_{key}.parquet")
        pr[["date", "close"]].to_parquet(DEMO / f"prices_{key}.parquet", index=False)
        r = risk[(risk.commodity == key) & (risk.date >= start)].dropna(subset=["risk_z"])
        meta["commodities"][key] = {
            "label": c.label, "display": c.display, "glyph": c.glyph, "ticker": c.ticker,
            "price_label": c.price_label, "price_name": c.price_name, "price_unit": c.price_unit,
            "main_country": c.main_country, "main_country_name": country_name(c.main_country),
            "target": c.target, "share_source": c.share_source,
            "windows": {k: [w.model_dump() for w in v] for k, v in c.windows.items()},
            "country_names": {k: country_name(k) for k in c.windows},
            "regions": summary.get(key, {}).get("regions"), "coverage": summary.get(key, {}).get("coverage"),
            "weeks": int(len(r)), "weeks_above_2_pct": round(100 * float((r.risk_z >= 2).mean()), 1),
            "latest_dekad_end": pd.Timestamp(st.dekad_end.max()).strftime("%Y-%m-%d"),
        }
    (DEMO / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    _world_110m()
    size = sum(p.stat().st_size for p in DEMO.glob("*")) / 1e6
    print(f"[demo] snapshot written to {DEMO} ({size:.1f} MB)")
