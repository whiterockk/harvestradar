"""Build the static web version of the app (one self-contained HTML file) from data/demo.

The Streamlit app needs a Python server; this page runs in any browser, for example as a claude.ai
Artifact. Same data, same map code (static/js/radar_map.js), same design tokens.
Usage: python scripts/build_web.py  ->  dist/web/index.html
"""

from __future__ import annotations

import base64
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "web"


def r(x, n=3):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), n)


def fair_block(data, key: str, today: pd.Timestamp) -> dict | None:
    """Price vs climate fair value: daily for the last 2 years, weekly (Friday) since 2006, plus the
    scenario parameters the pricing tool needs."""
    fv = data.fair_value(key)
    if fv.empty:
        return None
    pi = data.jsonfile("price_impact.json")
    fx, sm = pi["commodities"].get(key), pi.get("fair_value", {}).get(key)
    if fx is None or sm is None:
        return None
    d2 = fv[fv.date >= today - pd.Timedelta(days=740)]
    wk = fv.set_index("date").resample("W-FRI").last().dropna(subset=["fair"]).reset_index()
    cols = ("close", "anchor", "fair", "fair_lo", "fair_hi")
    ser = lambda f: {"d": f.date.dt.strftime("%Y-%m-%d").tolist(), **{c: [r(x, 2) for x in f[c]] for c in cols}}  # noqa: E731
    lr = data.risk_daily()
    lr = lr[lr.commodity == key].dropna(subset=["risk_z"]).iloc[-1]
    return {"recent": ser(d2), "long": ser(wk), "now": sm,
            "flex": {k: fx[k] for k in ("slope_pct_per_pct", "se", "p_value", "r2", "n", "years", "points",
                                         "marketing_year_start_month")},
            "mu": r(lr.mu_pct, 3), "sigma": r(lr.sigma_pct, 3),
            "comove": pi.get("comovement", {}).get(key)}


def main() -> None:
    import logging

    logging.getLogger("streamlit").setLevel(logging.ERROR)
    from harvestradar.app import components as C
    from harvestradar.app import data, maps
    from harvestradar.app.views import replay as RP
    from harvestradar.app.views import stress_map as SM
    from harvestradar.app.views.commodity import SHAP_LABELS
    from harvestradar.report.email_note import render_note_email

    meta = data.meta()
    today = data.today()
    out: dict = {"asOf": today.strftime("%Y-%m-%d"), "weekLabel": f"{today.day} {today:%b %Y}".upper(),
                 "priceImpact": data.jsonfile("price_impact.json"),
                 "meta": {"cells": meta["cells"], "climBase": meta["climatology_base"], "llm": meta["llm"]},
                 "crops": {}, "glyphs": {k: C._svg(f"glyph_{k}") for k in ("maize", "arabica", "cocoa")},
                 "marks": {"small": C.mark(30), "signal": C.mark_on_signal(40)}}
    out["map"] = {"viewBox": maps.world_viewbox(), "base": maps.base_layer()}
    for key, c in meta["commodities"].items():
        rs = data.risk_series(key)
        rs = rs[rs.date >= "2001-01-01"]
        rd = data.risk_daily()
        rd = rd[(rd.commodity == key) & (rd.date >= today - pd.Timedelta(weeks=66))].dropna(subset=["risk_z"])
        latest = data.latest_risk(key)
        px = data.prices(key)
        wk = px.set_index("date")["close"].resample("W-FRI").last().dropna()
        d_recent = px[px.date >= today - pd.Timedelta(weeks=66)]
        start = today - pd.Timedelta(weeks=64)
        spans = data.window_spans(key, c["main_country"], start, today)
        sh = data.shap_latest()
        sh = sh[sh.commodity == key]
        shap = {}
        for row in sh.itertuples():
            cols = [k for k in sh.columns if k.startswith("shap_") and k not in ("shap_base", "shap_commodity_code")]
            vals = pd.Series({k: getattr(row, k) for k in cols}).astype(float)
            top = vals.reindex(vals.abs().sort_values(ascending=False).index).head(4)
            shap[row.country_iso3] = {"season": int(row.season), "rows": [[SHAP_LABELS.get(k, k), r(v, 2)] for k, v in top.items()]}
        regs, borders, _ = SM.world_layers(key)
        frames = SM.frames_for(key, today.year)
        dk = data.stress(key).dekad_end.max()
        top5 = data.top_regions(key, dk, 5)
        best = float(top5["score"].max()) if len(top5) and top5["score"].max() > 0 else 1.0
        out["crops"][key] = {
            "label": c["label"], "display": c["display"], "glyph": c["glyph"], "priceLabel": c["price_label"],
            "priceName": c["price_name"], "priceUnit": c["price_unit"], "ticker": c["ticker"],
            "mainCountry": c["main_country_name"], "regionsN": c["regions"], "coverage": c["coverage"],
            "above2": c["weeks_above_2_pct"], "target": c["target"],
            "risk": {"d": rs.date.dt.strftime("%Y-%m-%d").tolist(), "z": [r(x) for x in rs.risk_z],
                     "dp": [r(x) for x in rs.delta_prod_pct]},
            "latest": {"z": r(latest["risk_z"]), "dp": r(latest["delta_prod_pct"], 2),
                       "lo": r(latest["delta_prod_lo_pct"], 2), "hi": r(latest["delta_prod_hi_pct"], 2),
                       "date": latest["date"].strftime("%Y-%m-%d"), "contributors": latest["contributors"]},
            "riskRecent": {"d": rd.date.dt.strftime("%Y-%m-%d").tolist(), "z": [r(x) for x in rd.risk_z]},
            "pricesWeekly": {"d": [d.strftime("%Y-%m-%d") for d in wk.index], "c": [r(x, 2) for x in wk]},
            "pricesRecent": {"d": d_recent.date.dt.strftime("%Y-%m-%d").tolist(), "c": [r(x, 2) for x in d_recent.close]},
            "lastPrice": {"date": px.date.iloc[-1].strftime("%Y-%m-%d"), "close": r(px.close.iloc[-1], 2)},
            "windows": [[s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d"), st] for s, e, st in spans],
            "shap": shap,
            "fair": fair_block(data, key, today),
            "map": {"regions": regs, "borders": borders, "frames": frames,
                    "start": len(frames) - 1, "dekad": dk.strftime("%Y-%m-%d"),
                    "top5": [{"rank": i + 1, "name": t.adm1_name, "iso": t.country_name,
                              "frac": max(0.0, float(t.score) / best), "hot": bool(i == 0 and t.stress >= 2)}
                             for i, t in enumerate(top5.itertuples())]},
        }
    o = data.oni_latest(today)
    o["strength"] = data.oni_strength(o["value"])
    o["period"] = o["label"].replace("-", " to ").title().replace(" To ", " to ")
    out["oni"] = o
    # episodes
    events = data.jsonfile("events.json")
    eps = {}
    for name, ev in events.items():
        key = ev["commodity"]
        focus = {"maize": "USA", "coffee": "BRA", "cocoa": "CIV"}[key]
        regs, vb, _, _ = RP.episode_layers(key, focus)
        frames = RP.episode_frames(key, focus, ev["start"], ev["end"])
        dates = [pd.Timestamp(f["date"]) for f in frames]
        se = pd.Timestamp(ev["show_end"])
        last_i = max(i for i, d in enumerate(dates) if d <= se)
        strip = sorted(set(int(round(x)) for x in np.linspace(max(0, last_i - 5), last_i, 6)))
        eps[name] = {**{k: v for k, v in ev.items() if k != "lag_correlation"}, "viewBox": vb, "regions": regs,
                     "frames": frames, "strip": strip,
                     "range": f"{dates[0]:%b %Y} · {dates[-1]:%b %Y}".upper()}
    out["episodes"] = eps
    # notes
    n = data.notes()
    notes = []
    order = {"maize": 0, "coffee": 1, "cocoa": 2}
    n = n.assign(o=n.commodity.map(order)).sort_values(["week", "o"], ascending=[False, True]).drop(columns="o")
    for row in n.to_dict("records"):
        p = json.loads(row["payload"])
        logo = base64.b64encode((ROOT / "src/harvestradar/app/static/brand/mark_on_signal_96.png").read_bytes()).decode()
        email = render_note_email(row, logo_src="data:image/png;base64," + logo)
        notes.append({"commodity": row["commodity"], "week": pd.Timestamp(row["week"]).strftime("%Y-%m-%d"),
                      "title": row["title"], "template": row["template"], "slots": p["slots"],
                      "readings": p.get("readings", {}), "checks": [bool(row["numbers_ok"]), bool(row["context_ok"]),
                                                                    bool(row["claims_ok"])],
                      "model": row["model"], "templateParagraphs": int(row.get("template_paragraphs", 0) or 0),
                      "seconds": r(row["seconds"], 0), "attempts": int(row["attempts"]), "email": email})
    out["notes"] = notes
    # method
    ev = data.jsonfile("model_eval.json")
    bt = data.jsonfile("backtest.json")
    st = data.stress("maize")
    top = data.regions("maize").sort_values("weight", ascending=False).iloc[0]
    x = st[(st.region_id == top.region_id) & (st.dekad_end >= "2012-05-01") & (st.dekad_end <= "2012-08-31")]
    out["method"] = {
        "eval": {"pooled": ev["pooled"].get("end", {}), "test": ev["test_seasons"],
                 "byCrop": {k: v.get("end", {}) for k, v in ev["by_commodity"].items()}},
        "events": {k: {kk: v.get(kk) for kk in ("label", "verdict", "first_above_2", "peak_risk_z", "peak_date",
                                                 "price_max_date")} for k, v in events.items()},
        "backtest": {k: bt.get(k) for k in ("best_rule_p", "best_rule_p_corrected", "best_p_overall",
                                            "best_p_overall_corrected")},
        "strip": {"name": top.adm1_name, "values": [r(v, 2) for v in x.stress]},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    tpl = (ROOT / "web" / "template.html").read_text()
    js = (ROOT / "src/harvestradar/app/static/js/radar_map.js").read_text()
    img = base64.b64encode((ROOT / "src/harvestradar/app/static/img/equal_earth_radar_night.webp").read_bytes()).decode()
    payload = json.dumps(out, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    html = (tpl.replace("/*__RADAR_JS__*/", js).replace("__BASE_IMG__", "data:image/webp;base64," + img)
            .replace("/*__APP_JS__*/", (ROOT / "web" / "app.js").read_text())
            .replace("__DATA__", payload))
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(f"written {OUT / 'index.html'} ({len(html) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
