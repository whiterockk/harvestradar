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
    r = data.risk_series(key, None, end)
    r = r[r.date > end - pd.Timedelta(weeks=weeks)]
    p = data.prices(key)
    p = p[(p.date >= r.date.min()) & (p.date <= end)]
    fig = go.Figure()
    lo = float(min(-1.0, r.risk_z.min() - 0.3))
    hi = float(max(2.6, r.risk_z.max() + 0.4))
    for s, e, stage in data.window_spans(key, m["main_country"], r.date.min(), end):
        fig.add_vrect(x0=s, x1=e, fillcolor="rgba(255,181,71,.07)", line_width=0, layer="below")
        fig.add_annotation(x=s + (e - s) / 2, y=1.0, yref="paper", yanchor="bottom",
                           text=f"{m['main_country_name'].upper()} {stage.upper()} WINDOW", showarrow=False,
                           font=dict(family="JetBrains Mono", size=13, color=T["muted"]))
    fig.add_hline(y=2, line=dict(color="#F5A93A", dash="dash", width=1.2))
    fig.add_annotation(x=0, xref="paper", y=2, text="+2", showarrow=False, xanchor="left", yanchor="bottom",
                       xshift=6, font=dict(family="JetBrains Mono", size=13, color="#F5A93A"))
    fig.add_trace(go.Scatter(x=p.date, y=p.close, name=m["price_label"], yaxis="y2", mode="lines",
                             line=dict(color=T["frost"], width=1.5), opacity=0.7,
                             hovertemplate="%{x|%d %b %Y}  %{y:,.2f}<extra>" + m["price_label"] + "</extra>"))
    # glow: wide translucent line under the index line
    fig.add_trace(go.Scatter(x=r.date, y=r.risk_z, mode="lines", line=dict(color="rgba(255,181,71,.18)", width=10,
                             shape="spline", smoothing=0.6), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=r.date, y=r.risk_z, name="HARVEST-RISK INDEX", mode="lines",
                             line=dict(color=T["signal"], width=3, shape="spline", smoothing=0.6),
                             fill="tozeroy", fillcolor="rgba(255,181,71,.08)",
                             hovertemplate="%{x|%d %b %Y}  %{y:+.2f}<extra>risk_z</extra>"))
    last = r.iloc[-1]
    fig.add_trace(go.Scatter(x=[last.date], y=[last.risk_z], mode="markers", showlegend=False, hoverinfo="skip",
                             marker=dict(size=18, color="rgba(255,181,71,.25)")))
    fig.add_trace(go.Scatter(x=[last.date], y=[last.risk_z], mode="markers", showlegend=False, hoverinfo="skip",
                             marker=dict(size=9, color=T["signal"])))
    fig.update_layout(
        height=540, margin=dict(l=48, r=70, t=44, b=36), showlegend=True,
        legend=dict(orientation="h", x=0, y=1.13, font=dict(family="JetBrains Mono", size=13, color=T["muted"]),
                    bgcolor="rgba(0,0,0,0)"),
        yaxis=dict(title=None, range=[lo, hi], zeroline=True, zerolinecolor=T["line_strong"], gridcolor=T["line"]),
        yaxis2=dict(overlaying="y", side="right", showgrid=False, tickfont=dict(family="JetBrains Mono", size=13,
                    color=T["muted"])),
        xaxis=dict(showgrid=False), hovermode="x unified")
    return fig


def render() -> None:
    key = st.session_state.crop
    m = data.meta()["commodities"][key]
    asof = st.session_state.asof
    ticker()
    r = data.latest_risk(key, asof)
    p = data.prices(key)
    p = p[p.date <= asof]
    last_px = p.iloc[-1]
    left, right = st.columns([0.655, 0.345])
    with left:
        c1, c2, c3 = st.columns([1.35, 1, 1])
        with c1:
            st.markdown(C.hero_card(m["display"], m["glyph"], data.fmt_signed(r["risk_z"]),
                                    f"week of {r['date']:%d %b %Y} &middot; risk_index.parquet"), unsafe_allow_html=True)
        with c2:
            st.markdown(C.stat_card("SUPPLY VS TREND", f"{r['delta_prod_pct']:+.1f}%",
                                    f"p10/p90 {r['delta_prod_lo_pct']:+.1f}% to {r['delta_prod_hi_pct']:+.1f}% "
                                    f"&middot; predictions"), unsafe_allow_html=True)
        with c3:
            st.markdown(C.stat_card(m["price_label"], fmt_price(key, float(last_px.close)),
                                    f"{m['ticker']} close {last_px.date:%d %b %Y} &middot; {m['price_unit']}"),
                        unsafe_allow_html=True)
        with st.container(key="glass_chart"):
            st.plotly_chart(index_chart(key, asof), use_container_width=True, config={"displayModeBar": False},
                            key=f"chart_{key}", theme=None)
            st.markdown(f'<div class="hr-source" style="margin-top:-8px">risk_index.parquet, prices_{key}.parquet '
                        f'({m["price_name"]}, {m["price_unit"]}) &middot; windows from config/commodities.yaml '
                        f'({m["main_country_name"]})</div>', unsafe_allow_html=True)
    with right:
        contribs = r["contributors"]
        rows = [{"label": c["name"], "value": c["contrib_pct"], "raises_risk": c["contrib_pct"] < 0,
                 "note": f"{c['pred_anom_pct']:+.1f}% vs trend, crop {c['season']}"
                 + (", window open" if c["window_open"] else "")} for c in contribs]
        st.markdown(C.panel("WHO DRIVES THIS WEEK &middot; PP OF WORLD SUPPLY", C.bar_rows(rows, "pp", label_w=210),
                            "contributors of the latest risk_index row &middot; share &times; predicted anomaly",
                            height=400), unsafe_allow_html=True)
        names = {c["country"]: c["name"] for c in contribs}
        default = st.session_state.get("q_country") or (contribs[0]["country"] if contribs else None)
        sh = data.shap_latest()
        sh = sh[sh.commodity == key]
        options = [c for c in names if c in set(sh.country_iso3)]
        if default not in options and options:
            default = options[0]
        if options:
            sel = st.segmented_control("Country for SHAP", options=options, format_func=lambda x: names.get(x, x),
                                       default=default, key=f"shap_country_{key}", label_visibility="collapsed")
            sel = sel or default
            st.session_state.q_country = sel
            row = sh[sh.country_iso3 == sel].iloc[0]
            cols = [c for c in sh.columns if c.startswith("shap_") and c not in ("shap_base", "shap_commodity_code")]
            vals = row[cols].astype(float)
            top = vals.reindex(vals.abs().sort_values(ascending=False).index).head(4)
            srows = [{"label": SHAP_LABELS.get(k, k), "value": float(v), "raises_risk": v < 0} for k, v in top.items()]
            title = (f"SHAP &middot; WHICH WEATHER <span style='float:right;color:{T['signal']}'>"
                     f"{names.get(sel, sel).upper()}</span>")
            body = C.bar_rows(srows, "pp", label_w=210)
            st.markdown(C.panel(title, body, f"shap_latest.parquet &middot; crop {int(row.season)} &middot; "
                                f"pp of {m['target']} anomaly, model as of {pd.Timestamp(row.as_of):%d %b %Y}",
                                height=300), unsafe_allow_html=True)
        else:
            st.markdown(C.panel("SHAP &middot; WHICH WEATHER", "<span>No SHAP values in shap_latest.parquet.</span>"),
                        unsafe_allow_html=True)

