"""Stress map page: live ticker, satellite map with dekad scrubber, ranking, climate context, note status."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from harvestradar.app import components as C
from harvestradar.app import data, maps
from harvestradar.app.views.common import go, ticker

MAP_H = 720


@st.cache_data(show_spinner=False)
def world_layers(key: str) -> tuple[list[dict], str, dict]:
    g = maps.project(data.regions(key))
    regs = [{"i": i, "id": r.region_id, "name": r.adm1_name, "country": r.country_name, "d": maps.geom_to_path(r.geometry)}
            for i, r in enumerate(g.itertuples())]
    w = maps.project(data.world(), tol_m=8000)
    borders = "".join(maps.geom_to_path(x) for x in w.geometry)
    pts = g.geometry.representative_point()
    centroids = {r.region_id: (round(p.x / 1000, 1), round(-p.y / 1000, 1)) for r, p in zip(g.itertuples(), pts)}
    return regs, borders, centroids


@st.cache_data(show_spinner=False)
def frames_for(key: str, year: int) -> list[dict]:
    s = data.stress(key)
    s = s[s.dekad_end.dt.year == year]
    g = data.regions(key)[["region_id", "weight"]]
    order = g["region_id"].tolist()
    _, _, cent = world_layers(key)
    out = []
    for d, f in s.groupby("dekad_end"):
        v = f.set_index("region_id")["stress"].reindex(order)
        sc = (v.clip(lower=0) * g.set_index("region_id")["weight"]).sort_values(ascending=False)
        hot = [cent[r] for r in sc.index[:3] if sc[r] > 0]
        tick = float((v.clip(lower=0) * g.set_index("region_id")["weight"]).sum() / 1.5)
        out.append({"date": d.strftime("%Y-%m-%d"), "label": maps.dekad_label(d), "short": maps.short_label(d),
                    "values": [None if not np.isfinite(x) else round(float(x), 2) for x in v.to_numpy()],
                    "hotspots": hot, "tick": min(1.0, tick)})
    return out


def _dekad_choice(key: str) -> pd.Timestamp:
    s = data.stress(key)
    avail = s.dekad_end.drop_duplicates().sort_values()
    avail = avail[avail <= st.session_state.asof + pd.Timedelta(days=0)]
    q = st.session_state.get("q_dekad")
    if q:
        try:
            t = pd.Timestamp(q)
            cand = avail[avail <= t]
            if len(cand):
                return cand.iloc[-1]
        except ValueError:
            pass
    return avail.iloc[-1]


def render() -> None:
    key = st.session_state.crop
    m = data.meta()["commodities"][key]
    ticker()
    left, right = st.columns([0.70, 0.30])
    dekad = _dekad_choice(key)
    frames = frames_for(key, dekad.year)
    start = next(i for i, f in enumerate(frames) if f["date"] == dekad.strftime("%Y-%m-%d"))
    regs, borders, _ = world_layers(key)
    months = maps.MONTHS
    rng = f"{months[pd.Timestamp(frames[0]['date']).month - 1]} · {months[pd.Timestamp(frames[-1]['date']).month - 1]} {dekad.year}"
    cfg = {"viewBox": maps.world_viewbox(), "base": maps.base_layer(), "countries": borders, "regions": regs,
           "frames": frames, "start": start, "ringRadius": 230, "labelPrefix": "STRESS VS OWN HISTORY",
           "rangeLabel": rng, "capture": st.session_state.capture,
           "autoplay": st.session_state.get("q_play") == "1",
           "ariaLabel": f"{m['label']} stress map, dekad {frames[start]['label']} {dekad.year}"}
    with left:
        st.iframe(maps.map_html(cfg, MAP_H, "world"), height=MAP_H)
        st.markdown(f'<div class="hr-source">{m["label"]}: {m["regions"]} regions covering '
                    f'{100 * m["coverage"]:.0f}% of world output (MapSPAM 2020) &middot; stress = heat, rain and '
                    f'root-zone soil moisture vs {data.meta()["climatology_base"][0]}-{data.meta()["climatology_base"][1]}'
                    f' &middot; NASA POWER, stress_{key}.parquet</div>', unsafe_allow_html=True)
    with right:
        top = data.top_regions(key, dekad, 5)
        best = float(top["score"].max()) if len(top) and top["score"].max() > 0 else 1.0
        rows = [{"rank": i + 1, "name": r.adm1_name, "iso": r.country_iso3,
                 "frac": max(0.0, float(r.score) / best), "hot": i == 0 and r.stress >= 2}
                for i, r in enumerate(top.itertuples())]
        st.markdown(C.panel("STRESS &times; SHARE OF WORLD SUPPLY", C.ranking_rows(rows, m["glyph"]),
                            f"dekad {maps.dekad_label(dekad).lower()} {dekad.year} &middot; stress_{key}.parquet "
                            f"&times; regions_{key}.geojson weights", height=356), unsafe_allow_html=True)
        o = data.oni_latest(st.session_state.asof)
        if o:
            st.markdown(C.climate_card(f"{o['value']:+.2f}", o["label"], o["series"],
                                       f"NOAA CPC ONI, published {o['available_at']} &middot; oni.parquet"),
                        unsafe_allow_html=True)
        n = data.notes()
        if len(n):
            wk = n[n.week <= st.session_state.asof]
            last = wk[wk.week == wk.week.max()] if len(wk) else n.iloc[0:0]
            row = last[last.commodity == key]
            if len(row):
                r = row.iloc[0]
                passed = int(r.numbers_ok) + int(r.get("context_ok", False)) + int(r.get("claims_ok", False))
                st.markdown(C.note_ready(passed, 3, "Friday note ready"), unsafe_allow_html=True)
                st.button("Open the weekly note", key="pick_note", on_click=go, args=("note",),
                          use_container_width=True)
