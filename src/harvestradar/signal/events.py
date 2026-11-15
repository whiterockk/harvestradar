"""Event studies: 2012 US drought (maize), 2021 Brazil frost (arabica), 2023-2024 cocoa.

Nothing is assumed: for each episode we report when risk_z first crossed +2 (if it did), its peak,
the futures price path and a lagged cross-correlation between index changes and price returns.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from harvestradar.config import Settings

WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
         10: "ten", 11: "eleven", 12: "twelve"}


def price_on(prices: pd.DataFrame, day: pd.Timestamp) -> tuple[pd.Timestamp, float] | tuple[None, None]:
    p = prices[prices.date <= day]
    if p.empty:
        return None, None
    r = p.iloc[-1]
    return r.date, float(r.close)


def lag_correlation(idx: pd.DataFrame, prices: pd.DataFrame, max_lag: int = 8) -> dict[int, float]:
    """corr(change in risk_z at week t, weekly log price return at week t + lag)."""
    w = prices.set_index("date")["close"].resample("W-FRI").last().dropna()
    r = np.log(w).diff()
    z = idx.set_index("date")["risk_z"].diff()
    out = {}
    for lag in range(-max_lag, max_lag + 1):
        a = pd.concat([z, r.shift(-lag)], axis=1).dropna()
        out[lag] = round(float(a.iloc[:, 0].corr(a.iloc[:, 1])), 3) if len(a) > 10 else None
    return out


def episode(cfg: Settings, name: str, spec: dict, risk: pd.DataFrame, prices: pd.DataFrame,
            vintages: dict) -> dict:
    key = spec["commodity"]
    c = cfg.commodities[key]
    start, end = pd.Timestamp(spec["start"]), pd.Timestamp(spec["end"])
    show_end = pd.Timestamp(spec.get("show_end", spec["end"]))
    r = risk[(risk.commodity == key) & risk.date.between(start, end)].sort_values("date")
    above = r[r.risk_z >= 2.0]
    first = above.date.iloc[0] if len(above) else None
    peak = r.loc[r.risk_z.idxmax()] if len(r) else None
    pr = prices[prices.date.between(start - pd.Timedelta(days=7), end)]
    path = []
    for row in r.itertuples():
        d, close = price_on(prices, row.date)
        path.append({"date": row.date.strftime("%Y-%m-%d"), "risk_z": round(float(row.risk_z), 3),
                     "close": close})
    out = {"name": name, "label": spec["label"], "commodity": key, "start": spec["start"], "end": spec["end"],
           "show_end": show_end.strftime("%Y-%m-%d"), "price_name": c.price_name, "price_unit": c.price_unit,
           "first_above_2": first.strftime("%Y-%m-%d") if first is not None else None,
           "peak_risk_z": round(float(peak.risk_z), 3) if peak is not None else None,
           "peak_date": peak.date.strftime("%Y-%m-%d") if peak is not None else None,
           "verdict": "caught" if first is not None else "missed"}
    # price window: from the first +2 crossing (or from the episode start when the index missed it)
    from_day = first if first is not None and first <= show_end else start
    d0, p0 = price_on(prices, from_day)
    d1, p1 = price_on(prices, show_end)
    out.update(price_from=p0, price_from_date=d0.strftime("%Y-%m-%d") if d0 is not None else None,
               price_from_kind="signal" if first is not None and first <= show_end else "episode start",
               price_to=p1, price_to_date=d1.strftime("%Y-%m-%d") if d1 is not None else None,
               price_change_pct=round(100 * (p1 / p0 - 1), 1) if p0 and p1 else None)
    if len(pr):
        mx = pr.loc[pr.close.idxmax()]
        out.update(price_max=float(mx.close), price_max_date=mx.date.strftime("%Y-%m-%d"))
    # weeks between the signal and the opening of the main country's window, from config
    stage_country = spec.get("stage_country", c.main_country)
    if first is not None:
        season = first.year + 1 if first.month > 10 else first.year
        for s in (season, season + 1):
            ws = [w for w in c.windows[stage_country]]
            opens = sorted((w.dates(s)[0], w.stage) for w in ws)
            fut = [(o, st) for o, st in opens if o >= first.date()]
            if fut:
                o, stage = fut[0]
                weeks = round((o - first.date()).days / 7)
                out["weeks_before_window"] = weeks
                out["window_stage"] = stage
                out["window_open_date"] = o.isoformat()
                out["lead_text"] = (f"{WORDS.get(weeks, str(weeks))} week{'s' if weeks != 1 else ''} "
                                    f"before {stage}") if weeks > 0 else f"as {stage} began"
                break
    v = vintages.get(int(start.year)) or vintages.get(str(start.year))
    if v:
        out["model_trained_on_seasons_up_to"] = v["trained_on_seasons_up_to"]
    out["lag_correlation"] = lag_correlation(r[["date", "risk_z"]], prices)
    out["path"] = path
    return out


def build_events(cfg: Settings, risk: pd.DataFrame, prices: dict[str, pd.DataFrame], vintages: dict) -> dict:
    return {name: episode(cfg, name, spec, risk, prices[spec["commodity"]], vintages)
            for name, spec in cfg.episodes.items()}

