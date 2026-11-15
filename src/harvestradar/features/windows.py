"""Critical windows: membership tests and active-season logic (windows may cross the year end)."""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from harvestradar.config import Commodity, Window


def in_critical_window(dates: pd.Series | pd.DatetimeIndex, windows: list[Window], season: int) -> np.ndarray:
    """True where a date falls inside any window of the given season."""
    d = pd.to_datetime(pd.Series(dates)).dt.date.to_numpy()
    out = np.zeros(len(d), dtype=bool)
    for w in windows:
        s, e = w.dates(season)
        out |= (d >= s) & (d <= e)
    return out


def window_open_on(day: dt.date, windows: list[Window]) -> bool:
    """Is any window of any season open on this day? (checks the seasons around the date)"""
    for season in (day.year - 1, day.year, day.year + 1, day.year + 2):
        for w in windows:
            s, e = w.dates(season)
            if s <= day <= e:
                return True
    return False


def season_switch(c: Commodity, country: str, season: int, tail_days: int) -> dt.date:
    """Last day on which `season` is the active (tracked) season for a country: the earlier of
    (end of its last window + tail) and (the day before the next season's first window)."""
    _, end = c.season_span(country, season)
    nxt, _ = c.season_span(country, season + 1)
    return min(end + dt.timedelta(days=tail_days), nxt - dt.timedelta(days=1))


def active_season(c: Commodity, country: str, day: dt.date, tail_days: int) -> int:
    for season in range(day.year - 2, day.year + 3):
        if day <= season_switch(c, country, season, tail_days):
            return season
    raise ValueError("no active season found")
