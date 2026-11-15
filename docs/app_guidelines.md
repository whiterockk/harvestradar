# HarvestRadar: app redesign guidelines

**For:** the developer redesigning the HarvestRadar Streamlit app
**From:** Paul Bogillot (ESSEC, Advanced AI Algorithms group project)
**Date:** 15 November 2026
**Visual target:** `HarvestRadar_storyboard_v3.pdf` (pages 10 to 14 show the app). Keep it open while you work.

---

## 0. In one paragraph

HarvestRadar already works: the data pipeline, the model, the risk index and the weekly note are built and tested. **Your job is the front end only.** The app must look like a product that will change how the agricultural world reads harvest risk. Today it looks like a nice student dashboard. The target is a dark "command center": satellite imagery, live readings, glass panels and one amber signal colour. You also add one feature: **exporting the weekly note as an email**. You change no model logic and no numbers, and the app must stay 100 % offline.

The app is filmed for a graded 5-minute demo video. It is shown for about 1 min 40, and "quality of the application" is worth 20 points out of 100. So every screen must hold up when filmed at 1920 x 1080 and zoomed 2x.

---

## 1. Ground rules (non-negotiable)

1. **Work on a branch:** `app-redesign` (created from `main`). Open a pull request when done. Do not push to `main`.
2. **Do not touch the pipeline.** Everything under `src/harvestradar/{ingest,geo,features,models,signal}` and `pipeline.py` stays as it is. If you think something there is wrong, write it down and tell Paul.
3. **Never invent or recompute a number.** The app only displays what is in `data/demo/` (and `config/`). If a value you need is missing, show nothing and flag it. Do not hard-code values from this document either: they are here so you can check your screens, not so you can paste them.
4. **100 % offline.** Zero external requests at runtime: no Google Fonts, no CDN, no map tiles, no analytics. Every font, image and icon is bundled in the repo. The existing offline check must still pass.
5. **Reproducible.** Python 3.11; dependencies pinned in `requirements.lock`. If you add a package (try not to), pin it and update the lock file. `make setup`, `make demo` and `make test` must still work from a fresh clone.
6. **Deterministic.** Same data gives the same screen. No random jitter, no "now" timestamps: the app's "today" is the latest date in `data/demo`.
7. **English** for everything on screen and in the code.
8. **No em dashes** in on-screen text (house style). Use colons and commas.

---

## 2. What exists today

From the README (`src/harvestradar/app/streamlit_app.py`):

- Streamlit app with **5 pages**: Stress map, Commodity, Episode replay, Weekly note, Method.
- Map: **pydeck** on a bundled Natural Earth base (`data/demo/world_110m.geojson`).
- Charts: **Plotly**.
- Data: precomputed snapshot in `data/demo/` (17 MB), loaded offline.
- Theme today: light background, rust and teal. Both go away.

Paul could not share the source with this guide, so the component names below are suggestions. Map them onto the existing code and keep its structure where it is sensible.

### 2.1 Data contracts (`data/demo/`)

| File | Columns | Used for |
|---|---|---|
| `risk_index.parquet` | `commodity, date, risk_z, delta_prod_pct, coverage_share, major_window_open, contributors` (`contributors` is a JSON string: list of `{country, contrib_pct, ...}`) | Ticker, big index number, index chart, "who drives this week" |
| `stress_{maize,coffee,cocoa}.parquet` | `region_id, dekad_end, stress, hdd_z, precip_z, sm_root_z, tmax` | Stress map, region ranking, replay |
| `regions_{crop}.geojson` | properties: `region_id, country_iso3, adm1_name, weight, lat` | Map polygons, region names, supply weights |
| `prices_{crop}.parquet` | `date, close` | Price line, price cards |
| `predictions.parquet` | `commodity, country_iso3, season, date, pred_anom, pred_lo, pred_hi, window_open` | Country forecasts, uncertainty band |
| `shap_latest.parquet` | `commodity, country_iso3, season, as_of, shap_*` (one column per feature: `shap_hdd_z`, `shap_sm_pre_z`, `shap_sm_root_z`, `shap_precip_z`, `shap_tmax_z`, `shap_et_z`, `shap_frost_z`, `shap_oni`, `shap_anom_last`, `shap_progress`, ...) | SHAP panel |
| `notes.parquet` | `commodity, week, markdown, numbers_ok, model, payload, seconds` (`model` is the LLM id or `deterministic-template`) | Weekly note page, email export |
| `events.json` | per episode (`us_drought_2012`, `brazil_frost_2021`, `cocoa_2023_2024`): summary fields + `path` (weekly `date, risk_z, close`) | Episode replay |
| `model_eval.json`, `backtest.json`, `meta.json` | evaluation, backtest, metadata (commodities, windows, tickers) | Method page, labels |
| `../processed/oni.parquet` | ONI series | El Niño card (context only, see 6.4) |

Critical windows per crop and country: `config/commodities.yaml` (`windows`). Read them from config; never hard-code them.

---

## 3. The design system: "Radar Night"

Dark, precise, calm. Calm areas stay dark and risk glows. One signal colour.

### 3.1 Three rules

1. **Colour only ever means risk.** The amber signal and the risk ramp are reserved for risk and the brand. Crops are told apart by **glyph and label**, never by colour.
2. **Every figure is set in JetBrains Mono** with tabular numbers, and every data panel says where its numbers come from.
3. **One idea per panel.** If a panel needs a paragraph to explain itself, split it or drop it.

### 3.2 Colour tokens

Put these in one module (e.g. `src/harvestradar/app/theme.py`) and use only these values.

| Token | Hex | Use |
|---|---|---|
| `night` | `#0B0F14` | App background |
| `night_glow` | `#131C27` | Centre of the background radial glow |
| `console` | `#131C27` | Raised panels, inputs |
| `line` | `#1E2935` | Hairlines, grid lines, borders |
| `line_strong` | `#2A3646` | Outlines, inactive borders |
| `frost` | `#EAF0F5` | Primary text |
| `frost_2` | `#C7D1DB` | Secondary text |
| `muted` | `#8A9AAB` | Labels, captions |
| `faint` | `#6F7F90` | Source footers only |
| `signal` | `#FFB547` | The index, active states, key numbers, primary button |
| `heat` | `#FF5A36` | Shock, price at peak, alerts |

Background of every page:

```css
background: radial-gradient(1200px 700px at 30% 20%, #142030 0%, #0B0F14 70%);
```

### 3.3 The risk ramp (maps, gauges, legends)

Diverging and **dark-centred**: on a dark map, "normal" is nearly invisible and both tails brighten.

| z | Hex |
|---|---|
| -3 and below | `#7EB0FF` |
| -2 | `#3F74D8` |
| -1 | `#26406A` |
| 0 | `#1E2833` |
| +1 | `#8A6424` |
| +2 | `#F5A93A` |
| +3 and above | `#FF5A36` |

Interpolate linearly between stops, symmetric domain [-3, +3]. On maps, set the fill opacity by intensity: `opacity = 0.35 + 0.65 * min(1, |z| / 2)`, so calm regions let the satellite ground show through and hot ones are opaque. Legends always say "lower stress / higher stress" (maps) or "lower risk / higher risk" (index), never colours alone.

```python
RAMP = [(-3, "#7EB0FF"), (-2, "#3F74D8"), (-1, "#26406A"), (0, "#1E2833"),
        (1, "#8A6424"), (2, "#F5A93A"), (3, "#FF5A36")]

def ramp(z: float) -> tuple[int, int, int]:
    z = max(-3.0, min(3.0, float(z)))
    for (z0, c0), (z1, c1) in zip(RAMP, RAMP[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0)
            a = [int(c0[i:i + 2], 16) for i in (1, 3, 5)]
            b = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
            return tuple(round(x + (y - x) * t) for x, y in zip(a, b))
    return (255, 90, 54)
```

### 3.4 Typography

All three fonts are on Google Fonts under the SIL Open Font License. **Download the font files into the repo** (`src/harvestradar/app/static/fonts/`, with their OFL licence files). Never load them from Google at runtime.

| Role | Font | Weights |
|---|---|---|
| Titles, big words, wordmark | Space Grotesk | 500, 700 |
| Body, labels, buttons | Inter | 400, 500, 600 |
| Every number, caps labels, sources, code | JetBrains Mono | 400, 500 |

Sizes in the app (CSS px; the app is filmed at 1920 x 1080):

| Style | Size | Notes |
|---|---|---|
| Page title | 38 to 40, Space Grotesk 700, letter-spacing -0.02em | |
| Hero number (the index) | 72, JetBrains Mono 500, `signal`, soft glow | |
| Card number | 28 to 36, JetBrains Mono 500 | |
| Body | 16 to 18, Inter | |
| Caps label | 13 to 15, JetBrains Mono, uppercase, letter-spacing 0.14em, `muted` | |
| Source footer | 13, JetBrains Mono, `faint` | |

**Minimum 13 px anywhere.** Below that, text is unreadable on video.

### 3.5 Shapes, spacing, effects

- Base unit 8 px; gaps 8 / 16 / 24 / 40.
- Radii: inputs and chips 10 to 12; panels 18; map frame 16.
- **Glass panel** (the house component):
  ```css
  background: linear-gradient(180deg, rgba(25,36,50,.82), rgba(13,19,27,.82));
  border: 1px solid rgba(126,176,255,.15);
  border-radius: 18px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.05), 0 20px 60px rgba(0,0,0,.35);
  ```
- **Glow** only on risk ≥ +2 and on the hero number: `text-shadow: 0 0 30px rgba(255,181,71,.45)`.
- **Live dot**: 10 px `signal` circle with `box-shadow: 0 0 0 4px rgba(255,181,71,.18), 0 0 14px #FFB547`.
- **Map frame corners**: four 22 px amber L-shaped brackets at the corners of the map (2 px, `rgba(255,181,71,.7)`), a "targeting" detail that sells the radar idea.
- Banned: emoji, gradient text, coloured left-border cards, rainbow palettes, bouncy animations, default Streamlit spinners in view.

### 3.6 Logo and glyphs

Logo files and crop glyphs are in the video brief (`HarvestRadar_video_brief_v3.md`, sections 3.6 and 3.7). Copy the SVGs as they are into `static/brand/`. Use `mark_small.svg` (30 px) + the wordmark "Harvest**Radar**" ("Radar" in `signal`, Space Grotesk 700) in the top bar, and `mark_on_signal.svg` as the favicon.

---

## 4. Streamlit implementation

### 4.1 Config

`.streamlit/config.toml`:

```toml
[theme]
base = "dark"
primaryColor = "#FFB547"
backgroundColor = "#0B0F14"
secondaryBackgroundColor = "#131C27"
textColor = "#EAF0F5"
font = "sans serif"

[server]
enableStaticServing = true   # serves src/harvestradar/app/static at /app/static

[client]
toolbarMode = "minimal"

[browser]
gatherUsageStats = false
```

`static/` must sit next to the main script for static serving. Check where Streamlit expects it for your version and adjust the path.

### 4.2 Global CSS (one function, called once at the top of every page)

```python
def inject_css():
    st.markdown(f"""<style>
    @font-face {{ font-family: 'Inter'; font-weight: 400; src: url('app/static/fonts/Inter-Regular.woff2') format('woff2'); }}
    /* ... one @font-face per file: Inter 500/600, Space Grotesk 500/700, JetBrains Mono 400/500 ... */
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    h1, h2, h3 {{ font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.02em; }}
    [data-testid="stAppViewContainer"] {{ background: radial-gradient(1200px 700px at 30% 20%, #142030 0%, #0B0F14 70%); }}
    [data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stMetricValue"] {{ font-family: 'JetBrains Mono', monospace; font-variant-numeric: tabular-nums; }}
    [data-testid="stStatusWidget"], #MainMenu, footer {{ visibility: hidden; }}
    .block-container {{ padding-top: 1rem; max-width: 1600px; }}
    </style>""", unsafe_allow_html=True)
```

- Target `data-testid` selectors, not generated class names (those change between Streamlit versions).
- Use `st.set_page_config(layout="wide", page_title="HarvestRadar", page_icon=<favicon path>)`.
- Prefer one horizontal **top bar** (logo, page tabs, live dot, "WEEK OF 13 NOV 2026 · OFFLINE") over the default sidebar. If the existing app relies on the sidebar for navigation, collapse it by default and style it with the same tokens.
- The custom cards (ticker, hero number, region ranking, El Niño card) are small HTML blocks rendered with `st.markdown(..., unsafe_allow_html=True)` from a helper module (`components.py`). Keep the HTML in Python functions with typed arguments; no data in templates.

### 4.3 Plotly template

Register once, then set it as default:

```python
import plotly.graph_objects as go, plotly.io as pio
pio.templates["harvestradar"] = go.layout.Template(layout=dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#C7D1DB", size=14),
    xaxis=dict(gridcolor="#1E2935", zerolinecolor="#2A3646", linecolor="#2A3646"),
    yaxis=dict(gridcolor="#1E2935", zerolinecolor="#2A3646", linecolor="#2A3646"),
    colorway=["#FFB547", "#EAF0F5", "#3F74D8"],
    hoverlabel=dict(bgcolor="#131C27", bordercolor="#2A3646", font_family="JetBrains Mono"),
    margin=dict(l=40, r=20, t=30, b=40),
))
pio.templates.default = "harvestradar"
```

Chart conventions:
- Index line: `#FFB547`, 3 px, with an area fill at 8 % opacity and a glowing end dot.
- Price line: `#EAF0F5`, 1.5 px, 70 % opacity, secondary axis.
- +2 threshold: dashed `#F5A93A`, labelled "+2".
- Critical windows: `rgba(255,181,71,.07)` rectangles, with the label from config (e.g. "US POLLINATION WINDOW").
- Contribution bars: risk-raising in an amber gradient (`#8A6424` → `#F5A93A`), risk-lowering in `#3F74D8`.
- Hide the Plotly mode bar (`config={"displayModeBar": False}`).

### 4.4 The map (pydeck, offline, satellite look)

The biggest single upgrade is replacing the flat vector base with **real satellite imagery**:

1. **Base image**: NASA Blue Marble (day) is public domain. Bundle one equirectangular JPG (4096 x 2048 is enough, about 2 to 4 MB) in `static/img/`. Source: NASA Visible Earth "Blue Marble Next Generation", or the `earth-blue-marble.jpg` texture shipped in the `three-globe` npm package (same NASA image). Credit "NASA Blue Marble" in the Method page and in `docs/data_sources.md`.
2. **Grade it once offline** (a small script in `scripts/`, output committed): desaturate to about 45 %, brightness about 0.5, cool tint (R ×0.86, G ×0.95, B ×1.08), compress highlights above 0.30 so ice and deserts never outshine the data. This keeps the look dark and lets the risk colours pop.
3. In pydeck: `map_style=None` (no tiles) and a `BitmapLayer` with `bounds=[-180, -85, 180, 85]` under everything.
4. `GeoJsonLayer` for the regions of the selected crop, filled with `ramp(stress)` plus the opacity rule from 3.3; thin borders in `night`.
5. **Hotspot pings**: a `ScatterplotLayer` at the centroids of the top 3 regions (stress × weight), drawn as 2 or 3 concentric unfilled rings in `signal` with decreasing opacity. Static is fine; if you animate, keep it slow (≥ 1.5 s per pulse) and make sure it can be turned off for captures.
6. Initial view: world view that crops Antarctica; pitch 0.
7. **Play / scrubber**: a dark bar under the map (glass panel) with a round amber play button and a slider of dekads. Playing steps through dekads every 0.4 s (0.16 s at "x2.5"), updating the map only, not the whole page.

Check: pydeck in Streamlit uses the deck.gl bundled with Streamlit. Confirm with the offline check that nothing is fetched from a CDN once you add the BitmapLayer.

### 4.5 Performance and stability

- `@st.cache_data` on every data load and every derived table (per commodity, per dekad).
- No visible spinner on page switch: pre-compute what each page needs at startup.
- Page switch under 1.5 s, map frame step under 300 ms on a recent laptop.
- **URL state for filming**: support query parameters `?page=commodity&crop=maize&date=2026-11-13&dekad=2012-06-10` so every screen can be opened in an exact state by a script (the video is captured with Playwright at 1920 x 1080, device scale factor 2).
- Add `?capture=1` to disable animations, hide the cursor-dependent hovers and freeze the ping rings.

---

## 5. Page by page

Match pages 10 to 14 of the storyboard. Every panel below names its data source.

### 5.1 Top bar (all pages)

Left: mark + wordmark. Centre: page tabs (active tab = amber text on `rgba(255,181,71,.12)` with a 1 px amber inner border). Right: live dot + `LIVE · WEEK OF 13 NOV 2026 · OFFLINE` (the date is the latest `risk_index.date`).

### 5.2 Live ticker (Stress map and Commodity pages)

Three glass cards in a row, one per commodity: crop glyph, `MAIZE · RISK_Z` (caps label), value in mono 28 to 34 px amber with glow, and a sparkline of the last 26 weeks of `risk_z`. Clicking a card selects that commodity.

### 5.3 Stress map

- Left (about 70 %): the satellite map (4.4) with the corner brackets, a caps label top-left `STRESS VS OWN HISTORY · DEKAD 1-10 NOV`, and the play scrubber at the bottom.
- Right column, three glass panels:
  1. **Stress × share of world supply**: top 5 regions of the selected crop for the latest dekad, ranked by `stress × weight` (from `stress_{crop}` joined with `regions_{crop}.geojson`). Each row: rank, glyph, region name (`adm1_name`), ISO3 code, and a thin bar (amber gradient, the top one ending in `heat`).
  2. **Climate driver**: "El Niño", the latest ONI value and its period (e.g. `+2.46 · ONI AUG-OCT 2026`), and a sparkline. Label it as context (see 6.4).
  3. **Friday note ready**: app icon + "Friday note ready" + "3/3 checks passed" (from `notes.numbers_ok` and the note model). Links to the Weekly note page.

### 5.4 Commodity

- Row of three cards: the **hero card** (glyph 52 px, caps label `MAIZE · HARVEST-RISK INDEX`, value 72 px amber glow), then `SUPPLY VS TREND` (`delta_prod_pct`), then `CBOT PRICE` (latest close). Use the ticker name from `meta.json`.
- Below: the **index vs price chart** (last 64 weeks; conventions in 4.3), with the critical windows of the main producer shaded and labelled from config.
- Right column:
  1. **Who drives this week**: from `contributors` of the latest `risk_index` row: country name, a bar, and the contribution in percentage points of world supply (`contrib_pct`), signed.
  2. **SHAP · which weather**: for the selected country (default: the top contributor), the 4 largest `shap_*` values from `shap_latest`, with human labels (`shap_hdd_z` → "Heat (degree days)", `shap_sm_pre_z` → "Soil moisture before window", `shap_sm_root_z` → "Root-zone soil moisture", `shap_precip_z` → "Rainfall", `shap_et_z` → "Evapotranspiration", `shap_frost_z` → "Frost", `shap_anom_last` → "Last season's anomaly", `shap_oni` → "El Niño (ONI)"). Values in percentage points.
  3. Optional: clicking a country in panel 1 updates panel 2.

### 5.5 Episode replay

- Episode selector (from `events.json`): US drought 2012 (maize), Brazil frost 2021 (coffee), Cocoa 2023-2024.
- Main area: the episode map on satellite base, regions coloured by dekad stress, with faint concentric amber rings around the hottest area.
- A **film strip** of 6 dekad thumbnails under the map (the playing one has an amber border and glow).
- Right column, glass cards:
  1. **Event card** with amber border: `RISK_Z FIRST ABOVE +2`, the date in mono 60 px (2012: `2012-06-08`), and "three weeks before pollination".
  2. **Index path** of the episode (from `events.json` `path`), +2 dashed line, glowing marker on the first crossing.
  3. **Price card**: price at the signal → price at the end of the shown window, with the % change in `heat`.
- Play / pause, plus keyboard arrows to step one dekad.
- A chip at the top: `MODEL TRAINED ON SEASONS UP TO 2011` (true: the real-time vintage model for 2012 only saw targets published before 2012).

### 5.6 Weekly note

- Left: a list of notes for the week (one per commodity) with a tag `DETERMINISTIC-TEMPLATE` when `model` is the fallback.
- Right: the selected note, rendered from `markdown`:
  - title, the three ticker cards, the note text;
  - every figure in the text shown as an **amber pill** (mono, amber text, `rgba(255,181,71,.10)` fill, 1 px amber border). The figures come from the note's own `payload`, never recomputed;
  - three badges: "Numbers checked", "Context checked", "Claims checked";
  - a line: "Written by Qwen2.5-1.5B, local · figures inserted by software";
  - a collapsible panel **Data given to the model**, showing the payload as figure + source + date cards;
  - buttons: **Open the map** (amber) and **Download as email** (outline, see section 6).

### 5.7 Method

Keep the current content, restyled: the pipeline in four steps (crop maps, weather, model, world index) as four glass cards, the evaluation figures from `model_eval.json`, the honest record (what it caught and missed, from `events.json` and `backtest.json`), and the credits (data, packages, Hugging Face model, NASA imagery).

---

## 6. New feature: weekly note as an email

The demo video shows the Friday note arriving as an email. **This must be a real feature, not a mock-up.** Keep it offline: the app produces the email; it does not send it.

### 6.1 What to build

- A function `render_note_email(note_row, risk_rows, prices) -> str` in `src/harvestradar/report/email_note.py` that returns a **self-contained HTML email**:
  - inline CSS only (email clients ignore `<style>` blocks inconsistently);
  - table-based layout, 640 px wide, dark theme with the tokens above;
  - logo as an inline SVG or embedded PNG (`cid:` attachment in the `.eml`);
  - subject line from the note title, e.g. "Maize Supply Shortfall Risk Higher Than Usual";
  - content: the three readings, the note text with figure pills, the sources block, a footer "Research output, not investment advice."
- A function `write_eml(html, subject, week) -> Path` using Python's standard `email` library (`EmailMessage`, `add_alternative(html, subtype="html")`, plain-text alternative included), writing `reports/notes/<week>_<commodity>.eml` and `.html`.
- A CLI command: `harvestradar report email --week latest` that writes the files for all three commodities.
- In the app: the **Download as email** button (`st.download_button`) on the Weekly note page.

### 6.2 What not to build

- No SMTP, no external sending service and no stored credentials. If the team later wants sending, that is a separate, opt-in step.
- No push notifications. In the video the phone notification is presented as what the export enables; if Paul wants a real one, discuss it first.

### 6.3 Tests

- The `.eml` parses back with `email.message_from_bytes` and has HTML and plain-text parts.
- Every figure in the email exists in the note's `payload` (reuse the existing number-check logic).
- The HTML has no external URLs (`http`), so it renders offline.

### 6.4 Wording rules (facts verified against the data)

- **El Niño is context, not the cause.** In the current model, `shap_oni` is 0 for the latest predictions. Label the card "Climate driver" or "Context", never "driving the index".
- **2012**: the maize price rose from 598 (8 June) to 824.5 by 20 July, but the 2012 high in the data is 831.25 on 21 August. Say "by 20 July", never "peaked on 20 July".
- **Maize +2.47 today** is driven by the expected 2026 US (−2.08 pp) and China (−2.31 pp) crops, read from `contributors`. Show it as data; do not paraphrase it differently.
- The 2021 Brazil frost does **not** show strongly in the dekad stress (Minas Gerais peaks at about +1.2). Do not caption anything "frost clearly visible".

---

## 7. Accessibility and quality bar

- Text contrast ≥ 4.5:1 on its background (3:1 at ≥ 24 px). `muted` (#8A9AAB) on `night` passes; do not go darker for text.
- Nothing is told apart by colour alone: legends carry words, crops carry glyphs, pass/fail carries icons.
- Keyboard: page tabs, play/pause, dekad stepping and the download button all reachable with Tab and Enter.
- No layout shift when data loads (fixed panel heights).
- Works at 1440 x 900 and 1920 x 1080. Mobile is not required.

---

## 8. Acceptance checklist (attach to the PR)

- [ ] Branch `app-redesign`, PR opened, no change under `ingest/`, `geo/`, `features/`, `models/`, `signal/`, `pipeline.py`.
- [ ] `make setup`, `make demo`, `make test` pass from a fresh clone.
- [ ] Offline check: zero external requests (fonts, images, map, Plotly, pydeck all local).
- [ ] Only the tokens of section 3 are used (grep for stray hex values).
- [ ] Fonts render as Space Grotesk, Inter and JetBrains Mono (no fallback font visible).
- [ ] No text under 13 px; every data panel has a source line.
- [ ] Stress map: satellite base, ramp with opacity rule, top-5 regions computed from data, hotspot rings, scrubber works.
- [ ] Commodity: hero number, index vs price with windows from config, contributors and SHAP from data.
- [ ] Episode replay: all three episodes play; 2012 shows 2012-06-08 and the right prices.
- [ ] Weekly note: figure pills, data panel, fallback tag, Download as email works.
- [ ] `harvestradar report email --week latest` writes valid `.eml` and `.html` for 3 commodities; tests pass.
- [ ] Query parameters open any page in an exact state; `?capture=1` freezes animations.
- [ ] One screenshot of each page at 1920 x 1080 attached to the PR.
- [ ] `docs/data_sources.md` credits NASA Blue Marble and the three fonts (OFL); README screenshots updated.

---

## 9. Documentation to update (part of the grade)

The assignment requires a user guide and a report of the prompts used with AI tools.

- `docs/user_guide.md`: new screenshots, and a short section on the email export.
- `docs/prompts_log.md`: if you use an AI coding assistant, add each significant prompt (tool, date, purpose, prompt or excerpt, what was kept).
- `README.md`: new logo at the top and one screenshot of the Stress map.

---

## 10. Order of work (suggested)

1. Tokens, fonts, global CSS, Plotly template, top bar (half a day). Show Paul a screenshot before going further.
2. Stress map with satellite base and right column.
3. Commodity page.
4. Episode replay.
5. Weekly note page + email export + tests.
6. Method page, query parameters, capture mode.
7. Checklist, screenshots, docs, PR.

Questions on design: Paul. Questions on data or numbers: check `data/demo` first, then ask Paul. When in doubt between "looks better" and "is exactly what the data says", the data wins.
