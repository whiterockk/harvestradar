"""Map component: regions projected to Equal Earth, drawn as SVG over the graded Blue Marble base.
Rendered with st.components.v1.html; animation runs in the browser (map only, not the page)."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources

import geopandas as gpd
import numpy as np
from shapely.geometry import MultiPolygon, Polygon

from harvestradar.app.theme import T, font_faces

EQ = "+proj=eqearth +lon_0=0 +datum=WGS84 +units=m +no_defs"
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


@lru_cache(maxsize=1)
def base_meta() -> dict:
    return json.loads(resources.files("harvestradar.app").joinpath("static/img/equal_earth_radar_night.json").read_text())


@lru_cache(maxsize=1)
def js_source() -> str:
    return resources.files("harvestradar.app").joinpath("static/js/radar_map.js").read_text()


def _ring(coords) -> str:
    a = np.asarray(coords)[:, :2] / 1000.0
    pts = " ".join(f"{x:.1f} {-y:.1f}" for x, y in a)
    return f"M{pts}Z"


def geom_to_path(geom) -> str:
    if geom is None or geom.is_empty:
        return ""
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom] if isinstance(geom, Polygon) else []
    out = []
    for p in polys:
        out.append(_ring(p.exterior.coords))
        out += [_ring(i.coords) for i in p.interiors]
    return "".join(out)


def project(gdf: gpd.GeoDataFrame, tol_m: float = 4000) -> gpd.GeoDataFrame:
    g = gdf.to_crs(EQ)
    g["geometry"] = g.geometry.simplify(tol_m, preserve_topology=True)
    return g


def dekad_label(ts) -> str:
    d = ts.day
    start = 1 if d <= 10 else (11 if d <= 20 else 21)
    return f"{start}-{d} {MONTHS[ts.month - 1]}"


def short_label(ts) -> str:
    return f"{ts.day:02d} {MONTHS[ts.month - 1]}"


def world_viewbox() -> list[float]:
    m = base_meta()
    return [m["x_min_km"], -m["y_top_km"], m["x_max_km"] - m["x_min_km"], m["y_top_km"] - m["y_bottom_km"]]


def base_layer(opacity: float = 1.0) -> dict:
    m = base_meta()
    return {"href": "/app/static/img/equal_earth_radar_night.webp", "x": m["x_min_km"], "y": -m["y_top_km"],
            "w": m["x_max_km"] - m["x_min_km"], "h": m["y_top_km"] - m["y_bottom_km"], "opacity": opacity}


def bbox_viewbox(gdf_eq: gpd.GeoDataFrame, pad: float = 0.12, aspect: float = 1.6) -> list[float]:
    x0, y0, x1, y1 = (v / 1000 for v in gdf_eq.total_bounds)
    w, h = x1 - x0, y1 - y0
    x0, x1, y0, y1 = x0 - w * pad, x1 + w * pad, y0 - h * pad, y1 + h * pad
    w, h = x1 - x0, y1 - y0
    if w / h < aspect:
        cx = (x0 + x1) / 2
        w = h * aspect
        x0 = cx - w / 2
    else:
        cy = (y0 + y1) / 2
        h = w / aspect
        y0 = cy - h / 2
    return [x0, -(y0 + h), w, h]


CSS = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
html, body { margin:0; padding:0; background:transparent; font-family:'Inter',sans-serif; color:%(frost)s;
  -webkit-font-smoothing: antialiased; overflow:hidden; }
.radar { position:relative; width:100%%; height:%(h)dpx; border-radius:16px; overflow:hidden; outline:none;
  background: radial-gradient(900px 500px at 40%% 35%%, rgba(20,32,48,.65), rgba(11,15,20,.0) 70%%); }
.radar:focus-visible { box-shadow: 0 0 0 2px %(signal)s inset; }
.map-stage { position:absolute; inset:0 0 %(bar)dpx 0; }
.map-svg { width:100%%; height:100%%; display:block; }
.corner { position:absolute; width:22px; height:22px; border-color: rgba(255,181,71,.7); border-style: solid;
  border-width: 0; pointer-events:none; z-index:4; }
.c-tl { top:0; left:0; border-top-width:2px; border-left-width:2px; border-top-left-radius:6px; }
.c-tr { top:0; right:0; border-top-width:2px; border-right-width:2px; border-top-right-radius:6px; }
.c-bl { bottom:0; left:0; border-bottom-width:2px; border-left-width:2px; border-bottom-left-radius:6px; }
.c-br { bottom:0; right:0; border-bottom-width:2px; border-right-width:2px; border-bottom-right-radius:6px; }
.map-label { position:absolute; top:16px; left:22px; z-index:3; font-family:'JetBrains Mono',monospace; font-size:14px;
  letter-spacing:.14em; color:%(frost_2)s; text-transform:uppercase; text-shadow: 0 1px 8px rgba(0,0,0,.8); }
.legend { position:absolute; left:22px; bottom:%(legend_bottom)dpx; z-index:3; }
.legend .sw { display:flex; gap:4px; }
.legend .sw i { width:36px; height:8px; border-radius:3px; display:block; }
.legend .lg { display:flex; justify-content:space-between; font-family:'JetBrains Mono',monospace; font-size:13px;
  color:%(muted)s; margin-top:5px; }
.bar { position:absolute; left:16px; right:16px; bottom:12px; height:%(bar_h)dpx; display:flex; align-items:center; gap:18px;
  padding:0 18px 0 12px; z-index:5;
  background:linear-gradient(180deg, rgba(25,36,50,.82), rgba(13,19,27,.82)); border:1px solid rgba(126,176,255,.15);
  border-radius:18px; box-shadow: inset 0 1px 0 rgba(255,255,255,.05), 0 20px 60px rgba(0,0,0,.35); }
.play { width:44px; height:44px; flex:none; border-radius:50%%; border:none; cursor:pointer; background:%(signal)s;
  box-shadow: 0 0 0 5px rgba(255,181,71,.16), 0 0 18px rgba(255,181,71,.55); display:grid; place-items:center; }
.play svg { width:18px; height:18px; }
.play .i-pause { display:none; } .playing .play .i-pause { display:block; } .playing .play .i-play { display:none; }
.ticks { flex:1; height:40px; display:flex; align-items:center; justify-content:space-between; gap:2px; }
.tick { flex:1; max-width:10px; height:var(--h); border:none; padding:0; border-radius:2px; cursor:pointer;
  background:rgba(138,154,171,.28); }
.tick.on { background: rgba(255,181,71,.75); }
.tick.now { background:%(signal)s; box-shadow: 0 0 10px rgba(255,181,71,.8); }
.range { font-family:'JetBrains Mono',monospace; font-size:14px; letter-spacing:.14em; color:%(frost_2)s; white-space:nowrap; }
.speed { font-family:'JetBrains Mono',monospace; font-size:13px; color:%(muted)s; background:transparent; cursor:pointer;
  border:1px solid %(line_strong)s; border-radius:8px; padding:4px 8px; }
.speed.on { color:%(signal)s; border-color: rgba(255,181,71,.6); }
.tip { position:absolute; z-index:9; pointer-events:none; opacity:0; transition: opacity .12s; padding:8px 11px;
  background:%(console)s; border:1px solid %(line_strong)s; border-radius:10px; font-size:14px; display:flex; gap:8px;
  align-items:baseline; white-space:nowrap; }
.tip b { font-weight:600; } .tip span { color:%(muted)s; font-family:'JetBrains Mono',monospace; font-size:13px; }
.tip em { font-style:normal; color:%(signal)s; font-family:'JetBrains Mono',monospace; }
.ping { transform-box: fill-box; transform-origin: center; animation: ping 2.4s ease-out infinite; }
@keyframes ping { 0%% { opacity:.55; } 50%% { opacity:1; } 100%% { opacity:.55; } }
.capture .ping { animation:none; }
.strip { position:absolute; left:16px; right:16px; bottom:12px; height:%(strip_h)dpx; display:grid;
  grid-template-columns: repeat(6, 1fr); gap:12px; padding:10px; z-index:5;
  background:linear-gradient(180deg, rgba(25,36,50,.82), rgba(13,19,27,.82)); border:1px solid rgba(126,176,255,.15);
  border-radius:18px; }
.thumb { position:relative; border:1px solid %(line_strong)s; border-radius:10px; overflow:hidden; padding:0;
  background:%(night)s; cursor:pointer; }
.thumb svg { width:100%%; height:calc(100%% - 24px); display:block; }
.thumb-label { height:24px; line-height:24px; font-family:'JetBrains Mono',monospace; font-size:13px; color:%(muted)s;
  text-align:left; padding-left:8px; }
.thumb.active { border-color: rgba(255,181,71,.9); box-shadow: 0 0 16px rgba(255,181,71,.45); }
.thumb.active .thumb-label { color:%(signal)s; }
.episode .bar { bottom: %(ep_bar_bottom)dpx; }
"""

PLAY_ICON = ('<svg class="i-play" viewBox="0 0 24 24"><path d="M7 4.5v15l13-7.5z" fill="#0B0F14"/></svg>'
             '<svg class="i-pause" viewBox="0 0 24 24"><path d="M6 4h4.5v16H6zM13.5 4H18v16h-4.5z" fill="#0B0F14"/></svg>')


def map_html(cfg: dict, height: int, mode: str = "world") -> str:
    bar_h = 64
    strip_h = 138 if mode == "episode" else 0
    css = CSS % dict(h=height, bar=(bar_h + 24) if mode == "world" else (bar_h + strip_h + 36), bar_h=bar_h,
                     legend_bottom=(bar_h + 30) if mode == "world" else (bar_h + strip_h + 44),
                     strip_h=strip_h, ep_bar_bottom=strip_h + 22, **T)
    legend = "".join(f'<i style="background:{c}"></i>' for c in
                     ["#7EB0FF", "#3F74D8", "#26406A", "#1E2833", "#8A6424", "#F5A93A", "#FF5A36"])
    strip = '<div class="strip"></div>' if mode == "episode" else ""
    speed = '<button class="speed" aria-label="Playback speed">x1</button>'
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{font_faces('/app/static/fonts')}{css}</style></head>
<body><div class="radar {mode}" tabindex="0" aria-label="{cfg.get('ariaLabel', 'Map')}">
<div class="map-stage"></div>
<div class="corner c-tl"></div><div class="corner c-tr"></div><div class="corner c-bl"></div><div class="corner c-br"></div>
<div class="map-label"></div>
<div class="legend"><div class="sw">{legend}</div><div class="lg"><span>{cfg.get('legendLow', 'lower stress')}</span>
<span>{cfg.get('legendHigh', 'higher stress')}</span></div></div>
<div class="bar"><button class="play" aria-label="Play">{PLAY_ICON}</button><div class="ticks"></div>
<div class="range">{cfg.get('rangeLabel', '')}</div>{speed}</div>
{strip}<div class="tip"></div></div>
<script>{js_source()}</script>
<script>RadarMap(document.querySelector('.radar'), {json.dumps(cfg, separators=(',', ':'))});</script>
</body></html>"""
