"""Repository paths. Everything is resolved from the repository root."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
# HARVESTRADAR_DATA_DIR relocates the whole data tree (used by tests and development fixtures)
DATA = Path(os.environ.get("HARVESTRADAR_DATA_DIR", ROOT / "data"))
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
DEMO = DATA / "demo"
REPORTS = ROOT / "reports"
MODELS_STORE = ROOT / "models_store"


def ensure_dirs() -> None:
    for p in (RAW, INTERIM, PROCESSED, DEMO, REPORTS, MODELS_STORE):
        p.mkdir(parents=True, exist_ok=True)
