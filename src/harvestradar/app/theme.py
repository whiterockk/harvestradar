"""Radar Night design system: the only colour values used by the app."""

from __future__ import annotations

TOKENS = {
    "night": "#0B0F14",
    "night_glow": "#131C27",
    "console": "#131C27",
    "line": "#1E2935",
    "line_strong": "#2A3646",
    "frost": "#EAF0F5",
    "frost_2": "#C7D1DB",
    "muted": "#8A9AAB",
    "faint": "#6F7F90",
    "signal": "#FFB547",
    "heat": "#FF5A36",
}
T = TOKENS

RAMP = [(-3, "#7EB0FF"), (-2, "#3F74D8"), (-1, "#26406A"), (0, "#1E2833"),
        (1, "#8A6424"), (2, "#F5A93A"), (3, "#FF5A36")]
RISK_BLUE = "#3F74D8"
AMBER_DARK = "#8A6424"
AMBER_MID = "#F5A93A"


def ramp(z: float) -> tuple[int, int, int]:
    z = max(-3.0, min(3.0, float(z)))
    for (z0, c0), (z1, c1) in zip(RAMP, RAMP[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0)
            a = [int(c0[i:i + 2], 16) for i in (1, 3, 5)]
            b = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
            return tuple(round(x + (y - x) * t) for x, y in zip(a, b))
    return (255, 90, 54)


def ramp_hex(z: float) -> str:
    return "#%02X%02X%02X" % ramp(z)


def ramp_opacity(z: float) -> float:
    return 0.35 + 0.65 * min(1.0, abs(float(z)) / 2)


FONT_FILES = [("Inter", 400), ("Inter", 500), ("Inter", 600), ("SpaceGrotesk", 500), ("SpaceGrotesk", 700),
              ("JetBrainsMono", 400), ("JetBrainsMono", 500)]
FAMILY = {"Inter": "Inter", "SpaceGrotesk": "Space Grotesk", "JetBrainsMono": "JetBrains Mono"}
LATIN = ("U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, "
         "U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD")
LATIN_EXT = ("U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+1D00-1DBF, U+1E00-1E9F, "
             "U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF")


def font_faces(prefix: str = "app/static/fonts") -> str:
    out = []
    for name, w in FONT_FILES:
        for sub, rng in (("latin", LATIN), ("latin-ext", LATIN_EXT)):
            out.append(f"@font-face{{font-family:'{FAMILY[name]}';font-style:normal;font-weight:{w};"
                       f"font-display:block;src:url('{prefix}/{name}-{w}-{sub}.woff2') format('woff2');"
                       f"unicode-range:{rng};}}")
    return "\n".join(out)


GLASS = ("background:linear-gradient(180deg, rgba(25,36,50,.82), rgba(13,19,27,.82));"
         "border:1px solid rgba(126,176,255,.15);border-radius:18px;"
         "box-shadow:inset 0 1px 0 rgba(255,255,255,.05), 0 20px 60px rgba(0,0,0,.35);")


def global_css(capture: bool = False) -> str:
    t = T
    anim = "" if not capture else """
    *, *::before, *::after { animation: none !important; transition: none !important; caret-color: transparent !important; }
    """
    return f"""<style>
{font_faces()}
html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select {{
  font-family: 'Inter', sans-serif; }}
h1, h2, h3, h4 {{ font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.02em; color: {t['frost']}; }}
.stApp, [data-testid="stAppViewContainer"] {{
  background: radial-gradient(1200px 700px at 30% 20%, #142030 0%, {t['night']} 70%) fixed; color: {t['frost']}; }}
[data-testid="stHeader"] {{ background: transparent; height: 0; }}
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], #MainMenu, footer,
[data-testid="stSidebarCollapsedControl"], [data-testid="stAppDeployButton"] {{ display: none !important; visibility: hidden; }}
.block-container, [data-testid="stMainBlockContainer"] {{ padding: 18px 40px 32px 40px !important; max-width: 1840px; }}
[data-testid="stMetricValue"] {{ font-family: 'JetBrains Mono', monospace; font-variant-numeric: tabular-nums; }}
[data-testid="stVerticalBlock"] {{ gap: 16px; }}
p, li {{ font-size: 16px; }}
a {{ color: {t['signal']}; }}
:focus-visible {{ outline: 2px solid {t['signal']} !important; outline-offset: 2px; }}
[data-testid="stSpinner"], [data-testid="stSkeleton"] {{ display: none !important; }}
.stPlotlyChart, [data-testid="stIFrame"] {{ border-radius: 18px; }}
iframe {{ color-scheme: dark; }}

/* top bar */
.hr-topbar {{ display:flex; align-items:center; gap:18px; height:56px; }}
.hr-brand {{ display:flex; align-items:center; gap:12px; font-family:'Space Grotesk',sans-serif; font-weight:700;
  font-size:22px; color:{t['frost']}; letter-spacing:-0.02em; white-space:nowrap; }}
.hr-brand b {{ color:{t['signal']}; font-weight:700; }}
.hr-status {{ display:flex; justify-content:flex-end; align-items:center; gap:12px; height:56px;
  font-family:'JetBrains Mono',monospace; font-size:14px; letter-spacing:.14em; color:{t['frost_2']}; white-space:nowrap; }}
.hr-dot {{ width:10px; height:10px; border-radius:50%; background:{t['signal']};
  box-shadow:0 0 0 4px rgba(255,181,71,.18), 0 0 14px {t['signal']}; display:inline-block; flex:none; }}
.hr-rule {{ height:1px; background:{t['line']}; margin:2px 0 6px 0; }}

/* navigation: st.segmented_control restyled as tabs */
.st-key-nav [data-testid="stButtonGroup"] {{ gap: 6px; }}
.st-key-nav button {{ background: transparent !important; border: 1px solid transparent !important; border-radius: 10px !important;
  color: {t['frost_2']} !important; font-family:'Inter',sans-serif; font-size:16px; padding: 6px 14px !important; min-height: 38px; }}
.st-key-nav button p {{ font-size:16px; font-weight:500; }}
.st-key-nav button:hover {{ color: {t['frost']} !important; background: rgba(255,255,255,.04) !important; }}
.st-key-nav button[kind="segmented_controlActive"], .st-key-nav button[aria-checked="true"] {{
  color: {t['signal']} !important; background: rgba(255,181,71,.12) !important;
  box-shadow: inset 0 0 0 1px rgba(255,181,71,.55) !important; }}
.st-key-nav [data-testid="stWidgetLabel"] {{ display:none; }}
.st-key-nav {{ padding-top: 8px; }}

/* glass panel and typography helpers */
.hr-glass {{ {GLASS} padding: 18px 20px; }}
.hr-caps {{ font-family:'JetBrains Mono',monospace; font-size:13px; letter-spacing:.14em; text-transform:uppercase;
  color:{t['muted']}; }}
.hr-mono {{ font-family:'JetBrains Mono',monospace; font-variant-numeric: tabular-nums; }}
.hr-source {{ font-family:'JetBrains Mono',monospace; font-size:13px; color:{t['faint']}; margin-top:10px; }}
.hr-title {{ font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:40px; letter-spacing:-0.02em;
  color:{t['frost']}; line-height:1.1; margin:0; }}
.hr-sub {{ font-family:'Inter',sans-serif; font-size:17px; color:{t['frost_2']}; }}
.hr-glow {{ text-shadow: 0 0 30px rgba(255,181,71,.45); }}
.hr-chip {{ display:inline-flex; align-items:center; gap:8px; padding:7px 14px; border-radius:10px;
  border:1px solid {t['line_strong']}; background:rgba(19,28,39,.7); font-family:'JetBrains Mono',monospace;
  font-size:13px; letter-spacing:.14em; text-transform:uppercase; color:{t['frost_2']}; }}
.hr-chip.amber {{ border-color: rgba(255,181,71,.7); color:{t['frost']}; box-shadow: 0 0 18px rgba(255,181,71,.18); }}
.hr-pill {{ font-family:'JetBrains Mono',monospace; color:{t['signal']}; background:rgba(255,181,71,.10);
  border:1px solid rgba(255,181,71,.55); border-radius:7px; padding:1px 7px; white-space:nowrap;
  font-variant-numeric: tabular-nums; }}

table.hr-plain, table.hr-plain tr, table.hr-plain th, table.hr-plain td {{ border-left: 0 !important; border-right: 0 !important;
  border-bottom: 0 !important; background: transparent !important; }}
table.hr-plain thead th {{ border-top: 0 !important; }}
[class*="st-key-glass"] {{ {GLASS} padding: 14px 18px 14px 18px; gap: 6px; }}

/* invisible click targets laid over HTML cards */
[class*="st-key-pick_"] {{ margin-top: -104px; height: 88px; margin-bottom: 10px; position: relative; z-index: 3; }}
[class*="st-key-pick_"] button {{ width:100%; height:88px; opacity:0; cursor:pointer; }}
[class*="st-key-pickn_"] {{ margin-top: -80px; height: 64px; margin-bottom: 0; position: relative; z-index: 3; }}
[class*="st-key-pickn_"] button {{ width:100%; height:64px; opacity:0; cursor:pointer; }}
.st-key-glass_note {{ gap: 14px !important; padding: 20px 24px !important; }}
[class*="st-key-pick"] button:focus-visible {{ opacity:1; background:transparent !important;
  border:2px solid {t['signal']} !important; color:transparent !important; }}

/* buttons */
.stButton button, .stDownloadButton button {{ border-radius: 12px; font-weight:600; font-size:16px; min-height:44px; }}
.st-key-open_map button {{ background:{t['signal']} !important; color:{t['night']} !important; border:none !important; }}
.st-key-download_eml button {{ background:transparent !important; color:{t['frost']} !important;
  border:1px solid {t['line_strong']} !important; }}
[data-testid="stExpander"] details {{ {GLASS} }}
[data-testid="stExpander"] summary p {{ font-size:16px; color:{t['frost_2']}; }}
[data-testid="stSelectbox"] label p, [data-testid="stRadio"] label p {{ font-size:14px; color:{t['muted']}; }}
{anim}
</style>"""


def plotly_template() -> None:
    import plotly.graph_objects as go
    import plotly.io as pio

    pio.templates["harvestradar"] = go.layout.Template(layout=dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color=T["frost_2"], size=14),
        xaxis=dict(gridcolor=T["line"], zerolinecolor=T["line_strong"], linecolor=T["line_strong"],
                   tickfont=dict(family="JetBrains Mono", size=13, color=T["muted"])),
        yaxis=dict(gridcolor=T["line"], zerolinecolor=T["line_strong"], linecolor=T["line_strong"],
                   tickfont=dict(family="JetBrains Mono", size=13, color=T["muted"])),
        colorway=[T["signal"], T["frost"], RISK_BLUE],
        hoverlabel=dict(bgcolor=T["console"], bordercolor=T["line_strong"], font_family="JetBrains Mono",
                        font_size=13),
        margin=dict(l=40, r=20, t=30, b=40),
    ))
    pio.templates.default = "harvestradar"
