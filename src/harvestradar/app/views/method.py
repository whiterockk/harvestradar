"""Method page: the pipeline in four steps, the evaluation, the honest record and the credits."""

from __future__ import annotations

import html as H

import pandas as pd
import streamlit as st

from harvestradar.app import components as C
from harvestradar.app import data
from harvestradar.app.theme import T, ramp_hex

CHIPS = ["WEATHER WEIGHTED BY WHERE CROPS GROW", "TESTING WITHOUT PEEKING AT THE FUTURE",
         "EXPLANATIONS BY WEATHER FACTOR (SHAP)", "LOCAL AI WRITER WITH FACT CHECKS", "TRADING TEST AGAINST LUCK"]


def _card(num: str, title: str, big: str, sub: str, extra: str = "", active: bool = False) -> str:
    border = "border-color:rgba(255,181,71,.75);" if active else ""
    return (f'<div class="hr-glass" style="min-height:330px;padding:20px 24px;{border}">'
            f'<div class="hr-mono" style="font-size:13px;color:{T["signal"] if active else T["muted"]}">STEP {num}</div>'
            f'<div style="font-family:Space Grotesk,sans-serif;font-weight:700;font-size:28px;margin-top:6px">{title}</div>'
            f'<div class="hr-mono" style="font-size:40px;color:{T["frost"]};margin-top:8px">{big}</div>'
            f'<div style="font-size:16px;color:{T["frost_2"]}">{sub}</div>{extra}</div>')


def _ledger_row(text: str, figure: str, verdict: str, tone: str) -> str:
    return (f'<tr><td style="padding:14px 10px;border-top:1px solid {T["line"]};font-size:17px;line-height:1.45;'
            f'color:{T["frost"]}">{H.escape(text)}</td>'
            f'<td class="hr-mono" style="padding:14px 10px;border-top:1px solid {T["line"]};font-size:15px;'
            f'color:{T["frost_2"]}">{H.escape(figure)}</td>'
            f'<td style="padding:14px 10px 6px;border-top:1px solid {T["line"]};text-align:right;white-space:nowrap">'
            f'{C.tag(verdict, tone)}</td></tr>')


def _ledger(rows: list[str]) -> str:
    th = f'font-family:JetBrains Mono,monospace;font-size:13px;letter-spacing:.12em;color:{T["muted"]};font-weight:400;padding:0 10px 10px'
    return (f'<div class="hr-glass" style="padding:18px 20px"><table class="hr-plain" style="width:100%;border-collapse:collapse">'
            f'<thead><tr><th style="{th};text-align:left">TEST</th><th style="{th};text-align:left">RESULT</th>'
            f'<th style="{th};text-align:right">VERDICT</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def render() -> None:
    meta = data.meta()
    com = meta["commodities"]
    ev = data.jsonfile("model_eval.json")
    events = data.jsonfile("events.json")
    bt = data.jsonfile("backtest.json")
    st.markdown('<h1 class="hr-title" style="margin:8px 0 18px 0">Under the hood, four steps.</h1>',
                unsafe_allow_html=True)
    n_regions = sum(c.get("regions") or 0 for c in com.values())
    glyphs = "".join(C.glyph(c["glyph"], 26, T["frost_2"]) for c in com.values())
    # weather strip: dekad stress of the top US maize region during summer 2012 (if present)
    strip = ""
    try:
        s = data.stress("maize")
        top = data.regions("maize").sort_values("weight", ascending=False).iloc[0]
        x = s[(s.region_id == top.region_id) & (s.dekad_end >= "2012-05-01") & (s.dekad_end <= "2012-08-31")]
        cells = "".join(f'<i style="flex:1;height:22px;border-radius:3px;background:{ramp_hex(v)}"></i>' for v in x.stress)
        strip = (f'<div style="display:flex;gap:3px;margin-top:26px">{cells}</div><div class="hr-source">'
                 f'{H.escape(top.adm1_name)}, summer 2012, every 10 days</div>')
    except Exception:  # noqa: BLE001
        pass
    pooled = ev.get("pooled", {}).get("end", {})
    rm = pooled.get("rmse_vs_trend_weighted_pct", pooled.get("rmse_vs_trend_pct"))
    rm_unw = pooled.get("rmse_vs_trend_pct")
    model_extra = (f'<div style="margin-top:22px">{C.chip("GRADIENT BOOSTING")} '
                   f'{C.chip("EXPLAINED FACTOR BY FACTOR", True)}</div>')
    r = data.latest_risk("maize", st.session_state.asof)
    shares = sorted(r.get("contributors", []), key=lambda c: -c["share_pct"])[:3] if r else []
    bars = "".join(
        f'<div style="display:grid;grid-template-columns:110px 1fr 52px;gap:10px;align-items:center;margin-top:8px">'
        f'<span style="font-size:15px;color:{T["frost_2"]}">{H.escape(c["name"])}</span>'
        f'<div style="height:6px;border-radius:3px;background:{T["line"]}"><div style="height:6px;border-radius:3px;'
        f'width:{min(100, 2 * c["share_pct"]):.0f}%;background:{T["frost_2"]}"></div></div>'
        f'<span class="hr-mono" style="font-size:13px;color:{T["muted"]};text-align:right">{c["share_pct"]:.0f}%</span></div>'
        for c in shares)
    cols = st.columns(4)
    cards = [
        _card("1", "Crop maps", f"{n_regions:,}", "producing regions, covering 90% of world output of each crop "
              "(MapSPAM 2020)", f'<div style="display:flex;gap:14px;margin-top:28px">{glyphs}</div>'),
        _card("2", "Weather", f"{meta.get('cells') or 0:,}", "NASA weather points, read every day since 1981", strip),
        _card("3", "Model", f"{rm:+.1f}%" if rm is not None else "n/a",
              "smaller harvest-forecast error than a simple trend, on harvests the model had never seen, weighted "
              "by world share", model_extra, active=True),
        _card("4", "World index", f"{r.get('risk_z', float('nan')):+.2f}" if r else "n/a",
              "maize today: country forecasts weighted by their share of world output", bars),
    ]
    for col, html in zip(cols, cards):
        with col:
            st.markdown(html, unsafe_allow_html=True)
    st.markdown('<div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:8px 0 6px 0">'
                '<span class="hr-caps" style="margin-right:12px">BEYOND THE COURSE</span>'
                + "".join(C.chip(c) for c in CHIPS) + "</div>", unsafe_allow_html=True)

    left, right = st.columns([0.55, 0.45])
    with left:
        st.markdown('<h2 style="font-size:30px;margin:18px 0 6px 0">Tested like sceptics.</h2>', unsafe_allow_html=True)
        rows = []
        if rm is not None:
            t0, t1 = ev.get("test_seasons", ["", ""])

            def gain(x):
                return ("Clear gain", "good") if x <= -10 else (("Small gain", "good") if x < 0 else ("No gain", "bad"))

            def err(x):
                return f"{abs(x):.1f}% {'smaller' if x < 0 else 'larger'} error than the trend"

            rows.append(_ledger_row(f"Harvest forecasts vs a simple trend, {t0} to {t1}, weighted by world share",
                                    err(rm), *gain(rm)))
            if rm_unw is not None:
                rows.append(_ledger_row("Same, every country counted equally", err(rm_unw), *gain(rm_unw)))
        for e in events.values():
            if e.get("first_above_2"):
                d = pd.Timestamp(e["first_above_2"])
                fig = f"Above +2 on {d.day} {d:%B %Y}, " + ("after the price peak" if e["verdict"] == "late"
                                                              else "before the price peak")
            else:
                fig = f"Highest {e['peak_risk_z']:+.2f}, never above +2"
            rows.append(_ledger_row(e["label"], fig, *{"caught": ("Caught", "good"), "late": ("Too late", "warn"),
                                                       "missed": ("Missed", "bad")}[e["verdict"]]))
        if bt:
            bc = bt.get("best_rule_p_corrected")
            sig = bc is not None and bc < 0.05
            rows.append(_ledger_row("Trading on the index, after costs",
                                    f"{100 * bc:.0f}% chance the gain is luck" if bc is not None else "n/a",
                                    "Significant" if sig else "Not significant", "good" if sig else "neutral"))
        st.markdown(_ledger(rows) + '<div class="hr-source">HarvestRadar is a radar, not a crystal ball. "Caught" '
                    'means the index went above +2 before the futures price peaked.</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<h2 style="font-size:30px;margin:18px 0 6px 0">Forecast errors by crop</h2>', unsafe_allow_html=True)
        trs = []
        for k, block in ev.get("by_commodity", {}).items():
            e = block.get("end", {})
            mm, tt = e.get("model", {}), e.get("trend_only", {})
            if not mm:
                continue
            trs.append(f'<tr><td style="padding:8px 6px">{H.escape(com[k]["label"])}</td>'
                       f'<td class="hr-mono" style="text-align:right">{mm.get("n", "")}</td>'
                       f'<td class="hr-mono" style="text-align:right">{100 * mm["rmse"]:.1f}</td>'
                       f'<td class="hr-mono" style="text-align:right">{100 * tt["rmse"]:.1f}</td>'
                       f'<td class="hr-mono" style="text-align:right">{(mm.get("spearman") or 0):+.2f}</td>'
                       f'<td class="hr-mono" style="text-align:right">{100 * (mm.get("sign_accuracy") or 0):.0f}%</td></tr>')
        st.markdown(f'<div class="hr-glass"><table class="hr-plain" style="width:100%;border-collapse:collapse;font-size:16px;'
                    f'color:{T["frost_2"]}"><thead><tr class="hr-caps"><th style="text-align:left;padding:6px">CROP</th>'
                    f'<th style="text-align:right">HARVESTS</th><th style="text-align:right">MODEL ERROR</th>'
                    f'<th style="text-align:right">TREND ERROR</th><th style="text-align:right">RANK MATCH</th>'
                    f'<th style="text-align:right">RIGHT DIRECTION</th></tr></thead><tbody>{"".join(trs)}</tbody></table>'
                    f'<div class="hr-source">Typical error in percentage points of yield (maize) or production (tree '
                    f'crops) vs normal. Rank match: how well the model orders good and bad harvests (1 = perfectly). '
                    f'Each year is forecast by a model trained only on harvests published before it.</div></div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="hr-glass" style="margin-top:16px"><div class="hr-caps" style="margin-bottom:8px">CREDITS</div>'
            f'<div style="font-size:15px;line-height:1.7;color:{T["frost_2"]}">'
            f'<b>Data</b>: NASA POWER (MERRA-2), MapSPAM 2020 (IFPRI, CC BY 4.0), geoBoundaries (CC BY 4.0), '
            f'FAOSTAT (CC BY 4.0), NOAA CPC ONI, futures closes via yfinance (Yahoo terms), Natural Earth.<br>'
            f'<b>Imagery</b>: NASA Blue Marble Next Generation (public domain), graded for Radar Night.<br>'
            f'<b>Model</b>: LightGBM, SHAP, scikit-learn, statsmodels; daily note by {H.escape(meta["llm"]["display_name"])} '
            f'({H.escape(meta["llm"]["model_id"])}, Hugging Face, Apache 2.0), run locally.<br>'
            f'<b>Software</b>: Streamlit, Plotly, pandas, GeoPandas. Fonts: Space Grotesk, Inter, JetBrains Mono (SIL OFL).'
            f'</div><div class="hr-source">Research output, not investment advice. Full list in docs/data_sources.md.</div></div>',
            unsafe_allow_html=True)

