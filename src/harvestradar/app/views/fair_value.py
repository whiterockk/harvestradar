"""Fair value page: futures price against the climate fair value (12-month average moved by the price reaction
the expected world supply implies), a pricing tool for scenarios, how the reaction is measured, and why the
index and the price need not move together. Everything comes from data/demo, refreshed by
`harvestradar index price` on every data run."""

from __future__ import annotations

import html as H
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from harvestradar.app import components as C
from harvestradar.app import data
from harvestradar.app.theme import T
from harvestradar.app.views.common import ticker

Z80 = 1.2816


def fmt(key: str, x: float) -> str:
    return f"{x:,.0f}" if key == "cocoa" else f"{x:,.2f}"


def gap_words(g: float) -> str:
    if g is None or not math.isfinite(g):
        return "not comparable"
    if abs(g) < 1:
        return "in line with it"
    return f"{abs(g):.1f}% {'below' if g < 0 else 'above'} it"


def corr_word(r: float | None) -> str:
    if r is None:
        return "n/a"
    a = abs(r)
    return "no link" if a < 0.1 else "weak link" if a < 0.3 else "moderate link" if a < 0.5 else "strong link"


def comove_panel(key: str) -> str:
    cm = data.jsonfile("price_impact.json").get("comovement", {}).get(key)
    if not cm:
        return ""
    m = data.meta()["commodities"][key]

    def tile(v, lab):
        val = "n/a" if v is None else f"{v:+.2f}"
        return (f'<div style="padding:14px 16px;border:1px solid {T["line"]};border-radius:12px;background:rgba(11,15,20,.35)">'
                f'<div class="hr-mono" style="font-size:28px;color:{T["frost"]}">{val}</div>'
                f'<div style="font-size:14px;color:{T["frost_2"]};margin-top:4px;line-height:1.45">{lab} '
                f'<span style="color:{T["muted"]}">({corr_word(v)})</span></div></div>')

    tiles = (f'<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px">'
             f'{tile(cm["weekly_changes"], "Week-to-week changes of the index and of the price")}'
             f'{tile(cm["weekly_changes_in_windows"], "Same, only in critical weather windows (" + str(cm["weeks_in_windows"]) + " weeks)")}'
             f'{tile(cm["index_vs_next_13_weeks"], "Index level vs the price change over the next 13 weeks")}</div>')
    text = (f'<div style="font-size:15px;color:{T["frost_2"]};line-height:1.65;margin-top:12px">The index measures how '
            f'much {m["label"].lower()} the world should harvest compared with normal for the time of year. It is not a '
            f'price model. Prices also move with demand, stocks, the dollar, fund positions, other origins and the '
            f'official crop reports, and traders often price a weather scare before it shows up in harvest forecasts. '
            f'So the two lines can diverge for weeks. Read the index for the supply side, then use the climate fair '
            f'value to turn it into a price.</div>')
    return C.panel("WHY THE INDEX AND THE PRICE DO NOT MOVE TOGETHER", tiles + text,
                   f'Correlations, weekly data since {cm["from"][:4]} ({cm["weeks"]} weeks). 0 means no link, 1 means '
                   f'the two move as one.')


def fair_chart(key: str, fv: pd.DataFrame, long: bool) -> go.Figure:
    m = data.meta()["commodities"][key]
    if long:
        f = fv.set_index("date").resample("W-FRI").last().dropna(subset=["fair"]).reset_index()
    else:
        f = fv[fv.date >= fv.date.max() - pd.Timedelta(days=740)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=f.date, y=f.fair_hi, mode="lines", line=dict(width=0), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=f.date, y=f.fair_lo, mode="lines", line=dict(width=0), fill="tonexty",
                             fillcolor="rgba(255,181,71,.16)", name="80% range", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=f.date, y=f.anchor, mode="lines", name="12-month average (anchor)",
                             line=dict(color=T["muted"], width=1.3, dash="dash"),
                             hovertemplate="%{y:,.2f}<extra>12-month average</extra>"))
    fig.add_trace(go.Scatter(x=f.date, y=f.close, mode="lines", name=m["price_name"],
                             line=dict(color=T["frost"], width=1.6), opacity=0.85,
                             hovertemplate="%{y:,.2f}<extra>price</extra>"))
    fig.add_trace(go.Scatter(x=f.date, y=f.fair, mode="lines", name="Climate fair value",
                             line=dict(color=T["signal"], width=2.6),
                             hovertemplate="%{y:,.2f}<extra>fair value</extra>"))
    fig.update_layout(height=460, margin=dict(l=60, r=20, t=40, b=36), hovermode="x unified",
                      legend=dict(orientation="h", x=0, y=1.12, font=dict(family="Inter", size=14, color=T["frost_2"]),
                                  bgcolor="rgba(0,0,0,0)"),
                      yaxis=dict(gridcolor=T["line"], title=dict(text=m["price_unit"].upper(),
                                 font=dict(family="JetBrains Mono", size=13, color=T["frost_2"]))),
                      xaxis=dict(showgrid=False))
    return fig


def flex_chart(fx: dict, gap_now: float) -> go.Figure:
    pts = pd.DataFrame(fx["points"], columns=["year", "gap", "dprice"])
    b = fx["slope_pct_per_pct"]
    a = pts.dprice.mean() - b * pts.gap.mean()
    xr = max(2.0, pts.gap.abs().max(), abs(gap_now)) * 1.12
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[-xr, xr], y=[a - b * xr, a + b * xr], mode="lines", line=dict(color=T["signal"], width=2.4),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=pts.gap, y=pts.dprice, mode="markers", text=pts.year, showlegend=False,
                             marker=dict(size=9, color=T["frost_2"], opacity=0.75),
                             hovertemplate="%{text}: supply %{x:+.1f}%, price %{y:+.1f}%<extra></extra>"))
    fig.add_vline(x=gap_now, line=dict(color=T["signal"], dash="dash", width=1))
    fig.add_annotation(x=gap_now, y=0, yref="paper", text="TODAY", showarrow=False, yanchor="bottom", xanchor="left",
                       xshift=4, font=dict(family="JetBrains Mono", size=13, color=T["signal"]))
    fig.update_layout(height=360, margin=dict(l=60, r=16, t=16, b=52),
                      xaxis=dict(range=[-xr, xr], gridcolor=T["line"], zerolinecolor=T["line_strong"],
                                 title=dict(text="WORLD SUPPLY VS NORMAL (%)", font=dict(family="JetBrains Mono", size=13))),
                      yaxis=dict(gridcolor=T["line"], zerolinecolor=T["line_strong"],
                                 title=dict(text="PRICE CHANGE IN THE YEAR (%)", font=dict(family="JetBrains Mono", size=13))))
    return fig


def scenario_value(anchor: float, reaction: float, gap: float, se: float) -> tuple[float, float, float]:
    e = lambda r: float(np.exp(-r * gap / 100))  # noqa: E731
    lo, hi = sorted([anchor * e(reaction - Z80 * se), anchor * e(reaction + Z80 * se)])
    return anchor * e(reaction), lo, hi


def _reset(key: str) -> None:
    """Back to today's values: scenario, supply gap, price reaction and anchor."""
    for k in [k for k in st.session_state if k.startswith((f"fv_gap_{key}_", f"fv_r_{key}", f"fv_a_{key}"))]:
        del st.session_state[k]
    st.session_state[f"fv_scen_{key}"] = "Today"


def render() -> None:
    key = st.session_state.crop
    m = data.meta()["commodities"][key]
    ticker()
    pi = data.jsonfile("price_impact.json")
    fx, nw = pi.get("commodities", {}).get(key), pi.get("fair_value", {}).get(key)
    fv = data.fair_value(key)
    fv = fv[fv.date <= st.session_state.asof]
    if fx is None or nw is None or fv.empty:
        st.info("No fair value in data/demo: run `harvestradar index price` then `harvestradar demo export`.")
        return
    last = fv.iloc[-1]
    if not nw["reliable"]:
        st.markdown(f'<div style="padding:12px 14px;border-radius:12px;border:1px solid rgba(255,90,54,.45);'
                    f'background:rgba(255,90,54,.08);color:{T["frost_2"]};font-size:15px;line-height:1.55;margin:4px 0 8px">'
                    f'No reliable link between world supply gaps and the {m["label"].lower()} price was found over '
                    f'{fx["years"][0]}-{fx["years"][1]} ({100 * fx["p_value"]:.0f}% chance that the measured slope is '
                    f'pure luck). The fair value therefore stays close to the 12-month average whatever the weather. '
                    f'Use it with care.</div>', unsafe_allow_html=True)
    left, right = st.columns([0.655, 0.345])
    with left:
        c1, c2, c3 = st.columns([1.35, 1, 1])
        with c1:
            st.markdown(C.stat_card("CLIMATE FAIR VALUE", fmt(key, last.fair),
                                    f"Likely between {fmt(key, last.fair_lo)} and {fmt(key, last.fair_hi)}. The price "
                                    f"that today's expected supply justifies on its own.", color=T["signal"], height=200, size=44),
                        unsafe_allow_html=True)
        with c2:
            g = float(last.gap_to_fair_pct)
            label = "In line with fair value" if abs(g) < 1 else f"{abs(g):.1f}% {'below' if g < 0 else 'above'} fair value"
            st.markdown(C.stat_card(m["price_label"], fmt(key, last.close),
                                    f"Close on {last.date.day} {last.date:%B %Y}. {label}.", height=200), unsafe_allow_html=True)
        with c3:
            st.markdown(C.stat_card("CLIMATE PREMIUM", f"{last.premium_pct:+.1f}%",
                                    f"On the 12-month average of {fmt(key, last.anchor)}, for an expected world supply "
                                    f"of {last.supply_gap_pct:+.2f}% vs normal.", height=200), unsafe_allow_html=True)
        with st.container(key="glass_fair"):
            h1, h2 = st.columns([0.7, 0.3], vertical_alignment="center")
            with h1:
                st.markdown('<div style="font-family:Space Grotesk,sans-serif;font-weight:700;font-size:20px">'
                            'Futures price and climate fair value</div>', unsafe_allow_html=True)
            with h2:
                span = st.segmented_control("Period", ["2 years", "Since 2006"], default="2 years", key="fv_span",
                                            label_visibility="collapsed")
            st.plotly_chart(fair_chart(key, fv, span == "Since 2006"), use_container_width=True,
                            config={"displayModeBar": False}, key=f"fv_{key}", theme=None)
            st.markdown(f'<div style="font-size:15px;color:{T["frost_2"]};line-height:1.6">How to read it: the orange '
                        f'line is the 12-month average price moved up or down by what the expected world supply implies. '
                        f'When the white price line is below it, the market prices less weather risk than the supply '
                        f'forecast suggests; above it, more. The gap is what other drivers explain (demand, stocks, the '
                        f'dollar, funds).</div><div class="hr-source">Updated with every data run. The price reaction is '
                        f'measured on {fx["years"][0]}-{fx["years"][1]}, so values before {fx["years"][1] + 1} are '
                        f'in-sample.</div>', unsafe_allow_html=True)
        st.markdown(comove_panel(key), unsafe_allow_html=True)
    with right:
        risk = data.risk_daily()
        lr = risk[(risk.commodity == key) & (risk.date <= st.session_state.asof)].dropna(subset=["risk_z"]).iloc[-1]
        mu, sigma = float(lr.mu_pct), float(lr.sigma_pct)
        with st.container(key="glass_calc"):
            t1, t2 = st.columns([0.62, 0.38], vertical_alignment="center")
            with t1:
                st.markdown(f'<div class="hr-caps">PRICING TOOL &middot; {H.escape(m["display"])}</div>',
                            unsafe_allow_html=True)
            with t2:
                st.button("Back to today", key=f"fv_reset_{key}", on_click=_reset, args=(key,), use_container_width=True)
            st.markdown(f'<div style="font-size:15px;color:{T["frost_2"]};margin:0 0 12px">Pick a scenario or move the '
                        f'expected world supply to see the fair value it would justify.</div>', unsafe_allow_html=True)
            scen = st.segmented_control("Scenario", ["Today", "Index 0", "Index +2", "Index +3", "Index -2"],
                                        default="Today", key=f"fv_scen_{key}", label_visibility="collapsed")
            z = {"Index 0": 0.0, "Index +2": 2.0, "Index +3": 3.0, "Index -2": -2.0}.get(scen)
            default_gap = float(last.supply_gap_pct) if z is None else round(mu - z * sigma, 2)
            gmin, gmax = math.floor(min(-6, mu - 4 * sigma)), math.ceil(max(6, mu + 4 * sigma))
            gap = st.slider("Expected world supply vs normal (%)", float(gmin), float(gmax), default_gap, 0.05,
                            key=f"fv_gap_{key}_{scen}")
            st.markdown(f'<div class="hr-source" style="margin:-8px 0 12px">Same as a risk index of '
                        f'{(mu - gap) / sigma:+.2f} today</div>', unsafe_allow_html=True)
            reaction = st.slider("Price reaction to 1% of world supply missing (%)", 0.0, 8.0,
                                 float(-fx["slope_pct_per_pct"]), 0.05, key=f"fv_r_{key}")
            anchor = st.number_input(f"Anchor price, {m['price_unit']}", min_value=0.01, value=float(round(last.anchor, 2)),
                                     key=f"fv_a_{key}")
            fair, lo, hi = scenario_value(anchor, reaction, gap, fx["se"])
            st.markdown(f'<div style="margin-top:12px;padding:16px 18px;border-radius:14px;border:1px solid rgba(255,181,71,.45);'
                        f'background:rgba(255,181,71,.06)"><div class="hr-caps">FAIR VALUE IN THIS SCENARIO</div>'
                        f'<div class="hr-mono hr-glow" style="font-size:44px;color:{T["signal"]}">{fmt(key, fair)}</div>'
                        f'<div style="font-size:15px;color:{T["frost_2"]};line-height:1.6">Likely between {fmt(key, lo)} '
                        f'and {fmt(key, hi)} (8 chances in 10). Last close {fmt(key, last.close)} is '
                        f'{gap_words(100 * (last.close / fair - 1))}.</div></div>'
                        f'<div class="hr-source">Fair value = anchor &times; exp(reaction &times; supply missing / 100). '
                        f'Research tool, not investment advice.</div>', unsafe_allow_html=True)
        with st.container(key="glass_flex"):
            st.markdown('<div class="hr-caps">HOW THE PRICE REACTION IS MEASURED</div>', unsafe_allow_html=True)
            st.plotly_chart(flex_chart(fx, float(last.supply_gap_pct)), use_container_width=True,
                            config={"displayModeBar": False}, key=f"flex_{key}", theme=None)
            st.markdown(f'<div class="hr-source">One dot per marketing year, {fx["years"][0]}-{fx["years"][1]} ({fx["n"]} '
                    f'years): realised world supply vs normal (FAOSTAT) and the change of the average futures price. '
                    f'Orange line: {-fx["slope_pct_per_pct"]:.2f}% on the price per 1% of world supply missing. '
                    f'Share of yearly price changes explained: {100 * fx["r2"]:.0f}%.</div>',
                        unsafe_allow_html=True)
