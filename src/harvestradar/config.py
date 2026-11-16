"""Configuration: commodities.yaml and settings.yaml validated with pydantic."""

from __future__ import annotations

import datetime as dt
import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

from harvestradar.paths import CONFIG_DIR


class Window(BaseModel):
    start: str
    end: str
    stage: str
    year_offset: int = 0

    @field_validator("start", "end")
    @classmethod
    def _mmdd(cls, v: str) -> str:
        m, d = v.split("-")
        dt.date(2001, int(m), int(d))  # raises on invalid dates (29 Feb is not allowed)
        return v

    def dates(self, season: int) -> tuple[dt.date, dt.date]:
        """Calendar start and end of this window for a season (harvest) year."""
        y = season + self.year_offset
        sm, sd = (int(x) for x in self.start.split("-"))
        em, ed = (int(x) for x in self.end.split("-"))
        start = dt.date(y, sm, sd)
        end = dt.date(y, em, ed)
        if end < start:
            end = dt.date(y + 1, em, ed)
        return start, end


class Commodity(BaseModel):
    key: str = ""
    label: str
    display: str
    glyph: str
    spam_crop: str
    fao_item: int
    tickers: dict[str, str]
    price_label: str
    price_name: str
    price_unit: str
    coverage: float = Field(0.90, gt=0, le=1)
    weight_mode: str = "production"
    target: str = "yield"
    share_source: str = "fao"
    thresholds: dict[str, float]
    main_country: str
    windows: dict[str, list[Window]]

    @field_validator("weight_mode")
    @classmethod
    def _mode(cls, v: str) -> str:
        if v not in {"production", "exports"}:
            raise ValueError("weight_mode must be 'production' or 'exports'")
        return v

    @property
    def ticker(self) -> str:
        return next(iter(self.tickers.values()))

    @property
    def countries(self) -> list[str]:
        return list(self.windows)

    def season_span(self, country: str, season: int) -> tuple[dt.date, dt.date]:
        ds = [w.dates(season) for w in self.windows[country]]
        return min(d[0] for d in ds), max(d[1] for d in ds)


class Settings(BaseModel):
    paths: dict[str, str]
    seed: int
    dates: dict[str, str | int]
    climatology: dict
    regions: dict
    targets: dict
    features: dict
    model: dict
    index: dict
    backtest: dict
    llm: dict
    episodes: dict[str, dict]
    commodities: dict[str, Commodity] = {}

    @property
    def as_of_end(self) -> dt.date:
        """Last day of data. HARVESTRADAR_AS_OF_END (YYYY-MM-DD) overrides settings.yaml: the daily job sets it."""
        env = os.environ.get("HARVESTRADAR_AS_OF_END")
        return dt.date.fromisoformat(env or str(self.dates["as_of_end"]))

    @property
    def index_start(self) -> dt.date:
        return dt.date.fromisoformat(str(self.dates["index_start"]))

    @property
    def weather_start(self) -> dt.date:
        return dt.date.fromisoformat(str(self.dates["weather_start"]))

    @property
    def lag_days(self) -> int:
        return int(self.dates["publication_lag_days"])


def load_config(config_dir: str | Path | None = None) -> Settings:
    d = Path(config_dir) if config_dir else CONFIG_DIR
    with open(d / "settings.yaml", encoding="utf-8") as f:
        s = yaml.safe_load(f)
    with open(d / "commodities.yaml", encoding="utf-8") as f:
        c = yaml.safe_load(f)
    s["commodities"] = {k: Commodity(key=k, **v) for k, v in c.items()}
    return Settings(**s)


@lru_cache(maxsize=1)
def get_config() -> Settings:
    return load_config()
