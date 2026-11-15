"""Commodity page: hero index, supply vs trend, futures price, index vs price with critical windows,
who drives this week (contributors) and SHAP (which weather)."""

from __future__ import annotations


import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from harvestradar.app import components as C
from harvestradar.app import data
from harvestradar.app.theme import T
from harvestradar.app.views.common import ticker

SHAP_LABELS = {
    "shap_hdd_z": "Heat (degree days)", "shap_tmax_z": "Daytime heat", "shap_sm_pre_z": "Soil moisture before window",
    "shap_sm_root_z": "Root-zone soil moisture", "shap_precip_z": "Rainfall", "shap_et_z": "Evapotranspiration",
    "shap_frost_z": "Frost", "shap_anom_last": "Last season's anomaly", "shap_oni": "El Niño (ONI)",
    "shap_progress": "Season progress", "shap_commodity_code": "Crop baseline",
}


def fmt_price(key: str, x: float) -> str:
    return f"{x:,.0f}" if key == "cocoa" else f"{x:,.2f}"


def index_chart(key: str, end: pd.Timestamp, weeks: int = 64) -> go.Figure:
    m = data.meta()["commodities"][key]
    r = data.risk_daily()
    r = r[(r.commodity == key) & (r.date <= end) & (r.date > end - pd.Timedelta(weeks=weeks))].dropna(subset=["risk_z"])
    p = data.prices(key)
    p = p[(p.date >= r.date.min()) & (p.date <= end)]
    fig = go.Figure()
    lo = float(min(-0.5, r.risk_z.min() - 0.3)) - 0.35
    hi = float(max(2.6, r.risk_z.max() + 0.4))
    for s, e, stage in data.window_spans(key, m["main_country"], r.date.min(), end):
        fig.add_vrect(x0=s, x1=e, fillcolor="rgba(255,181,71,.07)", line_width=0, layer="below")
        fig.add_annotation(x=s + (e - s) / 2, y=1.0, yref="paper", yanchor="bottom",
                           text=f"{m['main_country_name'].upper()} {stage.upper()} WINDOW", showarrow=False,
                           font=dict(family="JetBrains Mono", size=13, color=T["muted"]))
    fig.add_hline(y=2, line=dict(color="#F5A93A", dash="dash", width=1.2))
    fig.add_annotation(x=0, xref="paper", y=2, text="+2: RARE", showarrow=False, xanchor="left", yanchor="bottom",
                       xshift=6, font=dict(family="JetBrains Mono", size=13, color="#F5A93A"))
    fig.add_trace(go.Scatter(x=p.date, y=p.close, name=f"{m['price_name']}, right scale", yaxis="y2", mode="lines",
                             line=dict(color=T["frost"], width=1.5), opacity=0.7,
                             hovertemplate="%{x|%d %b %Y}  %{y:,.2f}<extra>price</extra>"))
    fig.add_trace(go.Scatter(x=r.date, y=r.risk_z, mode="lines", line=dict(color="rgba(255,181,71,.18)", width=10),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=r.date, y=r.risk_z, name="Risk index, left scale", mode="lines",
                             line=dict(color=T["signal"], width=3), fill="tozeroy", fillcolor="rgba(255,181,71,.08)",
                             hovertemplate="%{x|%d %b %Y}  %{y:+.2f}<extra>risk index</extra>"))
    last = r.iloc[-1]
    fig.add_trace(go.Scatter(x=[last.date], y=[last.risk_z], mode="markers", showlegend=False, hoverinfo="skip",
                             marker=dict(size=18, color="rgba(255,181,71,.25)")))
    fig.add_trace(go.Scatter(x=[last.date], y=[last.risk_z], mode="markers", showlegend=False, hoverinfo="skip",
                             marker=dict(size=9, color=T["signal"])))
    fig.update_layout(
        height=520, margin=dict(l=70, r=90, t=44, b=36), showlegend=True,
        legend=dict(orientation="h", x=0, y=1.14, font=dict(family="Inter", size=14, color=T["frost_2"]),
                    bgcolor="rgba(0,0,0,0)"),
        yaxis=dict(title=dict(text="RISK INDEX (0 = NORMAL)", font=dict(family="JetBrains Mono", size=13, color=T["signal"])),
                   range=[lo, hi], zeroline=True, zerolinecolor=T["line_strong"], gridcolor=T["line"]),
        yaxis2=dict(overlaying="y", side="right", showgrid=False,
                    title=dict(text=m["price_unit"].upper(), font=dict(family="JetBrains Mono", size=13, color=T["frost_2"])),
                    tickfont=dict(family="JetBrains Mono", size=13, color=T["muted"])),
        xaxis=dict(showgrid=False), hovermode="x unified")
    return fig


def price_panel(key: str) -> str:
    m = data.meta()["commodities"][key]
    pi = data.jsonfile("price_impact.json").get("commodities", {}).get(key)
    if not pi:
        return ""
    y0, y1 = pi["years"]
    if not pi["reliable"]:
        return C.panel("WHAT IT MEANS FOR THE PRICE",
                       f'<div style="font-size:17px;color:{T["frost_2"]};line-height:1.6">No reliable link between world '
                       f'supply gaps and the {m["label"].lower()} price since {y0} ({pi["n"]} years). No price estimate '
                       f'is shown.</div>', f"Marketing-year average futures price against the realised world supply gap, {y0}-{y1}.")
    body = (f'<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap"><span class="hr-mono" '
            f'style="font-size:40px;color:{T["signal"]}">{pi["implied_pct"]:+.1f}%</span><span style="color:{T["frost_2"]}">'
            f'expected move of the futures price over the marketing year</span></div>'
            f'<div style="font-size:16px;color:{T["frost_2"]};margin-top:8px;line-height:1.6">Likely between '
            f'<span class="hr-mono">{pi["low_pct"]:+.1f}%</span> and <span class="hr-mono">{pi["high_pct"]:+.1f}%</span> '
            f'(8 chances in 10). Since {y0}, each 1% of world supply missing came with about '
            f'<span class="hr-mono">{-pi["slope_pct_per_pct"]:+.1f}%</span> on the {m["label"].lower()} price.</div>')
    return C.panel("WHAT IT MEANS FOR THE PRICE", body,
                   f'Based on {pi["n"]} marketing years, {y0}-{y1}; the supply gap explains {100 * pi["r2"]:.0f}% of the '
                   f'yearly price changes. A rough guide, not a price forecast.')


def render() -> None:
    key = st.session_state.crop
    m = data.meta()["commodities"][key]
    asof = st.session_state.asof
    ticker()
    r = data.latest_risk(key, asof)
    p = data.prices(key)
    p = p[p.date <= asof]
    last_px = p.iloc[-1]
    unit = m["price_unit"][:1].upper() + m["price_unit"][1:]
    left, right = st.columns([0.655, 0.345])
    with left:
        c1, c2, c3 = st.columns([1.35, 1, 1])
        with c1:
            st.markdown(C.hero_card(m["display"], m["glyph"], data.fmt_signed(r["risk_z"]),
                                    f"{r['date'].day} {r['date']:%B %Y}. 0 is a normal season, above +2 is rare."),
                        unsafe_allow_html=True)
        with c2:
            st.markdown(C.stat_card("EXPECTED WORLD SUPPLY VS NORMAL", f"{r['delta_prod_pct']:+.1f}%",
                                    f"Likely between {r['delta_prod_lo_pct']:+.1f}% and {r['delta_prod_hi_pct']:+.1f}% "
                                    f"(8 chances in 10)."), unsafe_allow_html=True)
        with c3:
            st.markdown(C.stat_card(m["price_label"], fmt_price(key, float(last_px.close)),
                                    f"{unit}, nearest contract, close on {last_px.date.day} {last_px.date:%B %Y}."),
                        unsafe_allow_html=True)
        with st.container(key="glass_chart"):
            st.markdown('<div style="font-family:Space Grotesk,sans-serif;font-weight:700;font-size:20px">'
                        'Risk index and futures price, last 64 weeks</div>', unsafe_allow_html=True)
            st.plotly_chart(index_chart(key, asof), use_container_width=True, config={"displayModeBar": False},
                            key=f"chart_{key}", theme=None)
            st.markdown(f'<div style="font-size:15px;color:{T["frost_2"]};line-height:1.6">How to read it: the orange '
                        f'line rises when the model expects less {m["label"].lower()} than usual for this time of year. '
                        f'The shaded band is the {m["main_country_name"]} critical window, when weather matters most '
                        f'for the harvest. The white line is the price, for comparison.</div>', unsafe_allow_html=True)
    with right:
        st.markdown(price_panel(key), unsafe_allow_html=True)
        contribs = r["contributors"]
        rows = [{"label": c["name"], "value": c["contrib_pct"], "raises_risk": c["contrib_pct"] < 0,
                 "note": f"{c['season']} harvest: {c['pred_anom_pct']:+.1f}% vs normal"
                         + (", window open" if c["window_open"] else "")} for c in contribs]
        st.markdown(C.panel("WHICH COUNTRIES DRIVE TODAY'S READING", C.bar_rows(rows, "", label_w=210),
                            "In points of world supply: each country's share of world output times its expected harvest "
                            "gap. Amber raises the risk, blue lowers it."), unsafe_allow_html=True)
        names = {c["country"]: c["name"] for c in contribs}
        default = st.session_state.get("q_country") or (contribs[0]["country"] if contribs else None)
        sh = data.shap_latest()
        sh = sh[sh.commodity == key]
        options = [c for c in names if c in set(sh.country_iso3)]
        if default not in options and options:
            default = options[0]
        if options:
            sel = st.segmented_control("Country", options=options, format_func=lambda x: names.get(x, x),
                                       default=default, key=f"shap_country_{key}", label_visibility="collapsed")
            sel = sel or default
            st.session_state.q_country = sel
            row = sh[sh.country_iso3 == sel].iloc[0]
            cols = [c for c in sh.columns if c.startswith("shap_") and c not in ("shap_base", "shap_commodity_code")]
            vals = row[cols].astype(float)
            top = vals.reindex(vals.abs().sort_values(ascending=False).index).head(4)
            srows = [{"label": SHAP_LABELS.get(k, k), "value": float(v), "raises_risk": v < 0} for k, v in top.items()]
            title = (f"WHICH WEATHER DRIVES THE FORECAST <span style='float:right;color:{T['signal']}'>"
                     f"{names.get(sel, sel).upper()}</span>")
            st.markdown(C.panel(title, C.bar_rows(srows, "", label_w=220),
                                f"Contribution of each factor to the forecast for the {int(row.season)} harvest, in "
                                f"points of {m['target']} vs normal (SHAP values)."), unsafe_allow_html=True)
