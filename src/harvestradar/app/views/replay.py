"""Episode replay: an out-of-sample episode on the satellite base, dekad by dekad, with the index path
and the futures price. Everything comes from events.json, stress_<crop>.parquet and the vintage metadata."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from harvestradar.app import components as C
from harvestradar.app import data, maps
from harvestradar.app.theme import T

MAP_H = 760


@st.cache_data(show_spinner=False)
def episode_layers(key: str, focus: str) -> tuple[list[dict], list[float], dict, list[str]]:
    reg = data.regions(key)
    g = maps.project(reg, tol_m=1500)
    sub = g[g.country_iso3 == focus] if focus else g
    # frame the producing core of the focus country: its heaviest regions up to 85 % of its weight
    sub = sub.sort_values("weight", ascending=False)
    core = sub[(sub["weight"].cumsum() / sub["weight"].sum()).shift(fill_value=0) < 0.85]
    vb = maps.bbox_viewbox(core if len(core) else sub, pad=0.18, aspect=1.75)
    # every region inside the view is drawn (neighbours give context), focus first
    regs = [{"i": i, "id": r.region_id, "name": r.adm1_name, "country": r.country_name,
             "d": maps.geom_to_path(r.geometry)} for i, r in enumerate(g.itertuples())]
    pts = g.geometry.representative_point()
    cent = {r.region_id: (round(p.x / 1000, 1), round(-p.y / 1000, 1)) for r, p in zip(g.itertuples(), pts)}
    return regs, vb, cent, g["region_id"].tolist()


@st.cache_data(show_spinner=False)
def episode_frames(key: str, focus: str, start: str, end: str) -> list[dict]:
    s = data.stress(key)
    s = s[(s.dekad_end >= pd.Timestamp(start)) & (s.dekad_end <= pd.Timestamp(end))]
    _, _, cent, order = episode_layers(key, focus)
    w = data.regions(key).set_index("region_id")["weight"]
    out = []
    for d, f in s.groupby("dekad_end"):
        v = f.set_index("region_id")["stress"].reindex(order)
        sc = (v.clip(lower=0) * w.reindex(order)).sort_values(ascending=False)
        hot = [cent[r] for r in sc.index[:1] if sc[r] > 0]
        out.append({"date": d.strftime("%Y-%m-%d"), "label": f"{maps.dekad_label(d)} {d.year}",
                    "short": maps.short_label(d),
                    "values": [None if not np.isfinite(x) else round(float(x), 2) for x in v.to_numpy()],
                    "hotspots": hot, "tick": float(min(1.0, sc.clip(lower=0).sum() / 1.5))})
    return out


def path_chart(ev: dict) -> go.Figure:
    p = pd.DataFrame(ev["path"])
    p["date"] = pd.to_datetime(p["date"])
    fig = go.Figure()
    fig.add_hline(y=2, line=dict(color="#F5A93A", dash="dash", width=1.2))
    fig.add_trace(go.Scatter(x=p.date, y=p.risk_z, mode="lines", line=dict(color="rgba(255,181,71,.18)", width=9),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=p.date, y=p.risk_z, mode="lines", line=dict(color=T["signal"], width=2.6),
                             hovertemplate="%{x|%d %b %Y}  %{y:+.2f}<extra>risk_z</extra>", showlegend=False))
    mark = ev.get("first_above_2") or ev.get("peak_date")
    if mark:
        y = p.loc[p.date == pd.Timestamp(mark), "risk_z"]
        if len(y):
            fig.add_trace(go.Scatter(x=[pd.Timestamp(mark)], y=[float(y.iloc[0])], mode="markers", hoverinfo="skip",
                                     marker=dict(size=20, color="rgba(255,181,71,.28)"), showlegend=False))
            fig.add_trace(go.Scatter(x=[pd.Timestamp(mark)], y=[float(y.iloc[0])], mode="markers", hoverinfo="skip",
                                     marker=dict(size=10, color=T["signal"]), showlegend=False))
    lo, hi = float(min(-0.5, p.risk_z.min() - 0.3)), float(max(2.5, p.risk_z.max() + 0.4))
    fig.update_layout(height=200, margin=dict(l=40, r=12, t=14, b=28), yaxis=dict(range=[lo, hi]),
                      xaxis=dict(showgrid=False, tickformat="%b %Y"))
    return fig


def render() -> None:
    events = data.jsonfile("events.json")
    if not events:
        st.info("events.json is missing from data/demo.")
        return
    names = list(events)
    q = st.session_state.get("q_episode")
    if "episode_sel" not in st.session_state:
        st.session_state.episode_sel = q if q in names else names[0]
    m_all = data.meta()["commodities"]
    head_l, head_r = st.columns([0.64, 0.36], vertical_alignment="center")
    with head_l:
        st.segmented_control("Episode", options=names, format_func=lambda k: events[k]["label"],
                             key="episode_sel", label_visibility="collapsed")
    name = st.session_state.episode_sel or names[0]
    st.session_state.q_episode = name
    ev = events[name]
    key = ev["commodity"]
    m = m_all[key]
    spec_focus = {"maize": "USA", "coffee": "BRA", "cocoa": "CIV"}.get(key)
    focus = ev.get("region_focus") or spec_focus
    with head_r:
        chips = []
        if ev.get("model_trained_on_seasons_up_to"):
            chips.append(C.chip(f"MODEL TRAINED ON SEASONS UP TO {ev['model_trained_on_seasons_up_to']}", True))
        st.markdown(f'<div style="text-align:right">{"".join(chips)}</div>', unsafe_allow_html=True)
    left, right = st.columns([0.64, 0.36])
    regs, vb, _, _ = episode_layers(key, focus)
    frames = episode_frames(key, focus, ev["start"], ev["end"])
    if not frames:
        st.info("No dekad stress for this episode in data/demo.")
        return
    dates = [pd.Timestamp(f["date"]) for f in frames]
    show_end = pd.Timestamp(ev["show_end"])
    last_i = max(i for i, d in enumerate(dates) if d <= show_end) if any(d <= show_end for d in dates) else len(dates) - 1
    strip = sorted(set(int(round(x)) for x in np.linspace(max(0, last_i - 5), last_i, 6)))
    start_i = strip[0]
    if st.session_state.get("q_dekad"):
        t = pd.Timestamp(st.session_state.q_dekad)
        cand = [i for i, d in enumerate(dates) if d <= t]
        if cand:
            start_i = cand[-1]
    playing = st.session_state.get("q_play") == "1"
    cfg = {"viewBox": vb, "base": maps.base_layer(), "regions": regs, "frames": frames, "start": start_i,
           "strip": strip, "ringRadius": vb[2] / 40, "labelPrefix": f"EPISODE REPLAY · {ev['label'].upper()} "
           f"· {m['display']}", "labelWord": "DEKAD", "rangeLabel": f"{dates[0]:%b %Y} · {dates[-1]:%b %Y}".upper(),
           "capture": st.session_state.capture, "autoplay": playing,
           "ariaLabel": f"Episode replay {ev['label']}", "borderWidth": 0.8}
    with left:
        st.iframe(maps.map_html(cfg, MAP_H, "episode"), height=MAP_H)
        st.markdown(f'<div class="hr-source">dekad stress vs {data.meta()["climatology_base"][0]}-'
                    f'{data.meta()["climatology_base"][1]} &middot; NASA POWER, stress_{key}.parquet &middot; '
                    f'arrow keys step one dekad, space plays</div>', unsafe_allow_html=True)
    with right:
        if ev.get("first_above_2"):
            big, cap = ev["first_above_2"], ev.get("lead_text", "")
            title = "RISK_Z FIRST ABOVE +2"
            border = "border-color:rgba(255,181,71,.75);box-shadow:0 0 30px rgba(255,181,71,.15), 0 20px 60px rgba(0,0,0,.35);"
        else:
            big = f"{ev['peak_risk_z']:+.2f}" if ev.get("peak_risk_z") is not None else "n/a"
            cap = f"peak on {ev.get('peak_date')}: never above +2, missed"
            title = "RISK_Z PEAK IN THE EPISODE"
            border = ""
        st.markdown(f'<div class="hr-glass" style="height:190px;padding:22px 26px;{border}">'
                    f'<div class="hr-caps">{title}</div>'
                    f'<div class="hr-mono hr-glow" style="font-size:60px;line-height:1.15;color:{T["signal"]};'
                    f'margin-top:10px">{big}</div><div style="font-size:17px;color:{T["frost_2"]}">{cap}</div>'
                    f'<div class="hr-source" style="margin-top:6px">events.json &middot; risk_index.parquet</div></div>',
                    unsafe_allow_html=True)
        with st.container(key="glass_path"):
            st.markdown(f'<div class="hr-caps" style="padding-top:6px">INDEX, {pd.Timestamp(ev["start"]).year}'
                        f'{"-" + str(pd.Timestamp(ev["end"]).year) if pd.Timestamp(ev["end"]).year != pd.Timestamp(ev["start"]).year else ""}'
                        f'</div>', unsafe_allow_html=True)
            st.plotly_chart(path_chart(ev), use_container_width=True, config={"displayModeBar": False},
                            key=f"path_{name}", theme=None)
        p0, p1, ch = ev.get("price_from"), ev.get("price_to"), ev.get("price_change_pct")
        fmt = (lambda x: f"{x:,.0f}") if key == "cocoa" else (lambda x: f"{x:,.2f}".rstrip("0").rstrip("."))
        if p0 and p1:
            st.markdown(f'<div class="hr-glass" style="height:172px;padding:20px 26px">'
                        f'<div class="hr-caps">{m["price_label"]} &middot; {ev["price_from_date"]} TO {ev["price_to_date"]}</div>'
                        f'<div style="display:flex;align-items:baseline;gap:16px;margin-top:12px">'
                        f'<span class="hr-mono" style="font-size:34px;color:{T["frost_2"]}">{fmt(p0)}</span>'
                        f'<span style="color:{T["muted"]};font-size:17px">to</span>'
                        f'<span class="hr-mono" style="font-size:40px;color:{T["heat"] if ch and ch > 0 else T["frost"]}">{fmt(p1)}</span>'
                        f'<span class="hr-mono" style="font-size:22px;color:{T["heat"] if ch and ch > 0 else T["frost_2"]}">{ch:+.1f}%</span></div>'
                        f'<div class="hr-source">prices_{key}.parquet &middot; {m["price_unit"]}'
                        + (f' &middot; episode high {fmt(ev["price_max"])} on {ev["price_max_date"]}' if ev.get("price_max") else "")
                        + '</div></div>', unsafe_allow_html=True)
