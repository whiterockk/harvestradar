"""HarvestRadar app (Streamlit). Offline: reads data/demo only.

URL state for filming: ?page=stress|commodity|fair|replay|note|method&crop=maize|coffee|cocoa
&date=YYYY-MM-DD&dekad=YYYY-MM-DD&episode=us_drought_2012&week=YYYY-MM-DD&country=USA&capture=1
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

HERE = Path(__file__).parent
st.set_page_config(layout="wide", page_title="HarvestRadar", page_icon=str(HERE / "static/brand/favicon_64.png"),
                   initial_sidebar_state="collapsed")

from harvestradar.app import components as C  # noqa: E402
from harvestradar.app import data, theme  # noqa: E402
from harvestradar.app.views import commodity, fair_value, method, replay, stress_map, weekly_note  # noqa: E402

PAGES = {"stress": "Stress map", "commodity": "Commodity", "fair": "Fair value", "replay": "Replay",
         "note": "Daily note", "method": "Method"}
ALIASES = {"fair-value": "fair", "pricing": "fair", "stress-map": "stress", "map": "stress", "weekly-note": "note", "notes": "note", "episode": "replay"}
CROPS = ("maize", "coffee", "cocoa")


def _init_state() -> None:
    if st.session_state.get("_init"):
        return
    qp = st.query_params
    page = ALIASES.get(qp.get("page", "stress"), qp.get("page", "stress"))
    st.session_state.nav = page if page in PAGES else "stress"
    st.session_state.page = st.session_state.nav
    crop = qp.get("crop", "maize")
    st.session_state.crop = crop if crop in CROPS else "maize"
    st.session_state.capture = qp.get("capture") == "1"
    for k in ("date", "dekad", "episode", "week", "country", "play", "data"):
        st.session_state[f"q_{k}"] = qp.get(k)
    st.session_state._init = True


def _nav_changed() -> None:
    if st.session_state.nav is None:  # clicking the active tab again keeps it
        st.session_state.nav = st.session_state.page
    st.session_state.page = st.session_state.nav


def _sync_url() -> None:
    q = {"page": st.session_state.page, "crop": st.session_state.crop}
    for k in ("date", "dekad", "episode", "week", "country"):
        v = st.session_state.get(f"q_{k}")
        if v:
            q[k] = v
    if st.session_state.capture:
        q["capture"] = "1"
    if dict(st.query_params) != q:
        st.query_params.clear()
        st.query_params.update(q)


def main() -> None:
    _init_state()
    theme.plotly_template()
    st.markdown(theme.global_css(st.session_state.capture), unsafe_allow_html=True)
    if not (data.DATA / "meta.json").exists():
        st.markdown(C.brand(), unsafe_allow_html=True)
        st.error(f"No snapshot found in {data.DATA}. Run `make all` (or `harvestradar demo export`) first. "
                 "The app never invents data.")
        return
    asof = data.today()
    if st.session_state.get("q_date"):
        try:
            asof = min(asof, pd.Timestamp(st.session_state.q_date))
        except ValueError:
            pass
    st.session_state.asof = asof
    left, mid, right = st.columns([2.1, 5.2, 3.3], vertical_alignment="center")
    with left:
        st.markdown(C.brand(), unsafe_allow_html=True)
    with mid:
        st.segmented_control("Pages", options=list(PAGES), format_func=PAGES.get, key="nav",
                             label_visibility="collapsed", selection_mode="single", on_change=_nav_changed)
    with right:
        st.markdown(C.status(f"{asof.day} {asof.strftime('%b %Y')}"), unsafe_allow_html=True)
    st.markdown('<div class="hr-rule"></div>', unsafe_allow_html=True)
    page = st.session_state.page
    {"stress": stress_map.render, "commodity": commodity.render, "fair": fair_value.render, "replay": replay.render,
     "note": weekly_note.render, "method": method.render}[page]()
    _sync_url()


main()
