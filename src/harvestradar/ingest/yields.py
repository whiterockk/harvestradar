"""FAOSTAT QCL (crops and livestock products): production, area and yield per country and year.

Licence: CC BY 4.0 (FAO). Year Y is published around December of Y+1.
"""

from __future__ import annotations

import zipfile

import pandas as pd
import pycountry

from harvestradar.config import Settings
from harvestradar.ingest.manifest import download, record
from harvestradar.paths import PROCESSED, RAW

FAO_URL = "https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_All_Data_(Normalized).zip"
FAO_DIR = RAW / "faostat"
ELEMENTS = {"Production": "production_t", "Area harvested": "area_ha", "Yield": "yield_kg_ha"}


def fetch_faostat() -> None:
    z = FAO_DIR / "Production_Crops_Livestock_E_All_Data_Normalized.zip"
    if not z.exists():
        download(FAO_URL, z, timeout=600)
        record(z, "FAOSTAT QCL", FAO_URL, "CC BY 4.0")
    with zipfile.ZipFile(z) as zf:
        zf.extractall(FAO_DIR)


def _m49_to_iso3(code: str) -> str | None:
    code = str(code).strip("'").zfill(3)
    if code == "156":  # FAO "China, mainland" uses 156; the aggregate "China" (159) is excluded below
        return "CHN"
    c = pycountry.countries.get(numeric=code)
    return c.alpha_3 if c else None


def load_faostat(cfg: Settings) -> pd.DataFrame:
    """Tidy table: commodity, country_iso3, year, production_t, area_ha, yield_t_ha, world_production_t."""
    csv = FAO_DIR / "Production_Crops_Livestock_E_All_Data_(Normalized).csv"
    if not csv.exists():
        fetch_faostat()
    items = {c.fao_item: k for k, c in cfg.commodities.items()}
    usecols = ["Area Code", "Area Code (M49)", "Area", "Item Code", "Element", "Year", "Value"]
    chunks = []
    for ch in pd.read_csv(csv, usecols=usecols, chunksize=500_000, encoding="utf-8"):
        chunks.append(ch[ch["Item Code"].isin(items) & ch["Element"].isin(ELEMENTS)])
    df = pd.concat(chunks)
    world = df[(df["Area Code"] == 5000) & (df.Element == "Production")]
    world = world.assign(commodity=world["Item Code"].map(items))[["commodity", "Year", "Value"]]
    world = world.rename(columns={"Year": "year", "Value": "world_production_t"})
    # countries only: FAO area codes < 5000, excluding aggregates (China = 351, China incl. Taiwan etc.)
    df = df[(df["Area Code"] < 5000) & (~df["Area Code"].isin([351]))].copy()
    df["country_iso3"] = df["Area Code (M49)"].map(_m49_to_iso3)
    df = df.dropna(subset=["country_iso3"])
    df["commodity"] = df["Item Code"].map(items)
    wide = df.pivot_table(index=["commodity", "country_iso3", "Year"], columns="Element", values="Value",
                          aggfunc="sum").reset_index().rename(columns={"Year": "year", **ELEMENTS})
    wide["yield_t_ha"] = wide["production_t"] / wide["area_ha"]
    wide.loc[wide["area_ha"] <= 0, "yield_t_ha"] = float("nan")
    wide = wide.merge(world, on=["commodity", "year"], how="left")
    wide["available_at"] = pd.to_datetime((wide["year"] + 1).astype(str) + "-12-31")
    out = wide[["commodity", "country_iso3", "year", "production_t", "area_ha", "yield_t_ha",
                "world_production_t", "available_at"]].sort_values(["commodity", "country_iso3", "year"])
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out.to_parquet(PROCESSED / "fao_qcl.parquet", index=False)
    return out
