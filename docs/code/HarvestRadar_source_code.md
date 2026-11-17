# HarvestRadar source code

Commit cd62cee of https://github.com/whiterockk/harvestradar, 85 files, 8,742 lines, printed 17 November 2026. To rebuild the project, copy each block into the file named in its heading (or download the repository as a zip from GitHub).

## Contents

1. `pyproject.toml`
2. `Makefile`
3. `requirements.lock`
4. `requirements-llm.lock`
5. `.gitignore`
6. `.streamlit/config.toml`
7. `config/commodities.yaml`
8. `config/settings.yaml`
9. `.github/workflows/daily.yml`
10. `.github/workflows/pages.yml`
11. `src/harvestradar/__init__.py`
12. `src/harvestradar/app/__init__.py`
13. `src/harvestradar/app/assistant.py`
14. `src/harvestradar/app/components.py`
15. `src/harvestradar/app/data.py`
16. `src/harvestradar/app/maps.py`
17. `src/harvestradar/app/static/js/radar_map.js`
18. `src/harvestradar/app/streamlit_app.py`
19. `src/harvestradar/app/theme.py`
20. `src/harvestradar/app/views/__init__.py`
21. `src/harvestradar/app/views/commodity.py`
22. `src/harvestradar/app/views/common.py`
23. `src/harvestradar/app/views/fair_value.py`
24. `src/harvestradar/app/views/method.py`
25. `src/harvestradar/app/views/replay.py`
26. `src/harvestradar/app/views/stress_map.py`
27. `src/harvestradar/app/views/weekly_note.py`
28. `src/harvestradar/cli.py`
29. `src/harvestradar/config.py`
30. `src/harvestradar/demo/__init__.py`
31. `src/harvestradar/demo/export.py`
32. `src/harvestradar/features/__init__.py`
33. `src/harvestradar/features/aggregate.py`
34. `src/harvestradar/features/climatology.py`
35. `src/harvestradar/features/stress.py`
36. `src/harvestradar/features/windows.py`
37. `src/harvestradar/geo/__init__.py`
38. `src/harvestradar/geo/regions.py`
39. `src/harvestradar/ingest/__init__.py`
40. `src/harvestradar/ingest/boundaries.py`
41. `src/harvestradar/ingest/enso.py`
42. `src/harvestradar/ingest/manifest.py`
43. `src/harvestradar/ingest/power.py`
44. `src/harvestradar/ingest/prices.py`
45. `src/harvestradar/ingest/yields.py`
46. `src/harvestradar/models/__init__.py`
47. `src/harvestradar/models/baselines.py`
48. `src/harvestradar/models/explain.py`
49. `src/harvestradar/models/targets.py`
50. `src/harvestradar/models/validation.py`
51. `src/harvestradar/models/yield_model.py`
52. `src/harvestradar/paths.py`
53. `src/harvestradar/pipeline.py`
54. `src/harvestradar/report/__init__.py`
55. `src/harvestradar/report/checks.py`
56. `src/harvestradar/report/email_note.py`
57. `src/harvestradar/report/llm.py`
58. `src/harvestradar/report/prompts/weekly_note_system.md`
59. `src/harvestradar/report/weekly_note.py`
60. `src/harvestradar/signal/__init__.py`
61. `src/harvestradar/signal/backtest.py`
62. `src/harvestradar/signal/events.py`
63. `src/harvestradar/signal/fair_value.py`
64. `src/harvestradar/signal/price_impact.py`
65. `src/harvestradar/signal/risk_index.py`
66. `src/harvestradar/update.py`
67. `web/app.js`
68. `web/template.html`
69. `scripts/build_map_base.py`
70. `scripts/build_web.py`
71. `scripts/capture.py`
72. `scripts/code_listing.py`
73. `scripts/grade_blue_marble.py`
74. `scripts/offline_check.py`
75. `scripts/storyboard_facts.py`
76. `tests/conftest.py`
77. `tests/test_cli.py`
78. `tests/test_config_windows.py`
79. `tests/test_email.py`
80. `tests/test_fair_value.py`
81. `tests/test_note_checks.py`
82. `tests/test_signal.py`
83. `tests/test_stress_features.py`
84. `tests/test_theme_and_contracts.py`
85. `tests/test_update.py`

## 1. `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "harvestradar"
version = "0.1.0"
description = "Harvest-risk index for agricultural commodities: weather where crops grow, one number per commodity, every week."
readme = "README.md"
requires-python = ">=3.11,<3.12"
license = { text = "MIT" }
dependencies = [
  "pandas", "pyarrow", "numpy", "geopandas", "shapely", "pyogrio", "rasterio", "exactextract",
  "requests", "pydantic", "pyyaml", "typer", "pycountry",
  "scikit-learn", "lightgbm", "shap", "statsmodels",
  "streamlit", "pydeck", "plotly", "pillow", "yfinance",
]

[project.optional-dependencies]
llm = ["torch", "transformers", "accelerate"]
dev = ["pytest", "ruff", "playwright"]

[project.scripts]
harvestradar = "harvestradar.cli:app"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
harvestradar = ["report/prompts/*.md", "app/static/**/*", "app/.streamlit/*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"

[tool.ruff]
line-length = 110
target-version = "py311"
```

## 2. `Makefile`

```
PY ?= python3.11
VENV ?= .venv
BIN = $(VENV)/bin
PORT ?= 8501

.PHONY: setup demo data regions features train index backtest notes email export all test lint offline-check screenshots lock

setup:  ## Create the pinned environment
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.lock
	$(BIN)/pip install --no-deps -e .
	@echo "pinned environment ready"

demo:  ## Run the app on data/demo, offline
	$(BIN)/streamlit run src/harvestradar/app/streamlit_app.py --server.port $(PORT) --server.headless true

data:  ## Download all sources (network)
	$(BIN)/harvestradar data fao
	$(BIN)/harvestradar data oni
	$(BIN)/harvestradar data prices
	$(BIN)/harvestradar regions build
	$(BIN)/harvestradar data weather

regions:
	$(BIN)/harvestradar regions build

features:
	$(BIN)/harvestradar features build

train:
	$(BIN)/harvestradar model train

index backtest:
	$(BIN)/harvestradar index build
	$(BIN)/harvestradar index daily

notes:  ## Needs the optional LLM dependencies: pip install -r requirements-llm.lock
	$(BIN)/harvestradar report notes

email:
	$(BIN)/harvestradar report email --week latest

export:
	$(BIN)/harvestradar demo export

all: data features train index notes export email

test:
	$(BIN)/pytest

lint:
	$(BIN)/ruff check src tests scripts

offline-check:  ## Starts the app and fails on any request that leaves localhost
	$(BIN)/python scripts/offline_check.py

screenshots:
	$(BIN)/python scripts/capture.py

lock:
	uv pip compile pyproject.toml -o requirements.lock --python-version 3.11
```

## 3. `requirements.lock`

```
# This file was autogenerated by uv via the following command:
#    uv pip compile pyproject.toml --extra dev -o requirements.lock --python-version 3.11
affine==3.0.1
    # via rasterio
altair==6.3.0
    # via streamlit
annotated-doc==0.0.6
    # via typer
annotated-types==0.8.0
    # via pydantic
anyio==4.16.0
    # via
    #   starlette
    #   streamlit
attrs==26.1.0
    # via
    #   affine
    #   jsonschema
    #   rasterio
    #   referencing
beautifulsoup4==4.15.0
    # via yfinance
certifi==2026.10.23
    # via
    #   curl-cffi
    #   pyogrio
    #   pyproj
    #   rasterio
    #   requests
cffi==2.1.1
    # via curl-cffi
charset-normalizer==3.5.2
    # via requests
click==8.5.1
    # via
    #   click-plugins
    #   cligj
    #   rasterio
    #   streamlit
    #   uvicorn
click-plugins==1.1.1.2
    # via rasterio
cligj==0.7.2
    # via rasterio
cloudpickle==3.1.2
    # via
    #   joblib
    #   shap
curl-cffi==0.17.0
    # via yfinance
exactextract==0.3.0
    # via harvestradar (pyproject.toml)
formulaic==1.2.2
    # via statsmodels
geopandas==1.2.0
    # via harvestradar (pyproject.toml)
greenlet==3.5.6
    # via playwright
h11==0.16.0
    # via uvicorn
idna==3.20
    # via
    #   anyio
    #   requests
iniconfig==2.3.1
    # via pytest
interface-meta==2.0.1
    # via formulaic
itsdangerous==2.2.0
    # via streamlit
jinja2==3.1.6
    # via
    #   altair
    #   pydeck
joblib==1.6.0
    # via scikit-learn
jsonschema==4.26.0
    # via altair
jsonschema-specifications==2025.9.1
    # via jsonschema
lightgbm==4.7.0
    # via harvestradar (pyproject.toml)
llvmlite==0.50.0
    # via
    #   numba
    #   shap
lxml==6.1.3
    # via yfinance
markdown-it-py==4.3.0
    # via rich
markupsafe==3.0.4
    # via jinja2
mdurl==0.1.2
    # via markdown-it-py
narwhals==2.28.0
    # via
    #   altair
    #   formulaic
    #   lightgbm
    #   plotly
    #   scikit-learn
numba==0.68.1
    # via shap
numpy==2.4.6
    # via
    #   harvestradar (pyproject.toml)
    #   exactextract
    #   formulaic
    #   geopandas
    #   lightgbm
    #   numba
    #   pandas
    #   patsy
    #   pydeck
    #   pyogrio
    #   rasterio
    #   scikit-learn
    #   scipy
    #   shap
    #   shapely
    #   statsmodels
    #   streamlit
    #   yfinance
packaging==26.3
    # via
    #   altair
    #   geopandas
    #   patsy
    #   plotly
    #   pyogrio
    #   pytest
    #   shap
    #   statsmodels
    #   streamlit
pandas==3.1.1
    # via
    #   harvestradar (pyproject.toml)
    #   formulaic
    #   geopandas
    #   shap
    #   statsmodels
    #   streamlit
    #   yfinance
patsy==1.0.3
    # via statsmodels
peewee==4.5.3
    # via yfinance
pillow==13.0.0
    # via
    #   harvestradar (pyproject.toml)
    #   streamlit
platformdirs==4.14.5
    # via yfinance
playwright==1.65.2
    # via harvestradar (pyproject.toml)
plotly==7.1.0
    # via harvestradar (pyproject.toml)
pluggy==1.7.0
    # via pytest
protobuf==7.36.2
    # via
    #   streamlit
    #   yfinance
pyarrow==26.0.1
    # via
    #   harvestradar (pyproject.toml)
    #   streamlit
pycountry==26.2.16
    # via harvestradar (pyproject.toml)
pycparser==3.12
    # via cffi
pydantic==2.14.3
    # via
    #   harvestradar (pyproject.toml)
    #   typer
pydantic-core==2.50.4
    # via pydantic
pydeck==0.9.3
    # via
    #   harvestradar (pyproject.toml)
    #   streamlit
pygments==2.21.0
    # via
    #   pytest
    #   rich
pyogrio==0.13.0
    # via
    #   harvestradar (pyproject.toml)
    #   geopandas
pyparsing==3.3.3
    # via rasterio
pyproj==3.7.2
    # via geopandas
pytest==9.2.0
    # via harvestradar (pyproject.toml)
python-dateutil==4.0.0
    # via pandas
python-multipart==0.0.33
    # via streamlit
pytz==2026.6
    # via yfinance
pyyaml==6.0.3
    # via harvestradar (pyproject.toml)
rasterio==1.4.4
    # via harvestradar (pyproject.toml)
referencing==0.37.0
    # via
    #   jsonschema
    #   jsonschema-specifications
requests==2.34.2
    # via
    #   harvestradar (pyproject.toml)
    #   streamlit
    #   yfinance
rich==15.0.0
    # via typer
rpds-py==2026.9.1
    # via
    #   jsonschema
    #   referencing
ruff==0.17.5
    # via harvestradar (pyproject.toml)
scikit-learn==1.9.1
    # via
    #   harvestradar (pyproject.toml)
    #   shap
scipy==1.17.1
    # via
    #   formulaic
    #   lightgbm
    #   scikit-learn
    #   shap
    #   statsmodels
shap==0.51.0
    # via harvestradar (pyproject.toml)
shapely==2.2.0
    # via
    #   harvestradar (pyproject.toml)
    #   geopandas
shellingham==1.5.4
    # via typer
slicer==0.0.8
    # via shap
soupsieve==2.10
    # via beautifulsoup4
starlette==1.10.0
    # via streamlit
statsmodels==0.15.0
    # via harvestradar (pyproject.toml)
streamlit==1.67.0
    # via harvestradar (pyproject.toml)
threadpoolctl==3.8.0
    # via scikit-learn
tqdm==4.70.1
    # via shap
typer==0.29.1
    # via harvestradar (pyproject.toml)
typing-extensions==4.16.0
    # via
    #   altair
    #   anyio
    #   beautifulsoup4
    #   formulaic
    #   pydantic
    #   pydantic-core
    #   referencing
    #   shap
    #   starlette
    #   streamlit
    #   typing-inspection
typing-inspection==0.4.5
    # via pydantic
tzdata==2026.6
    # via python-dateutil
urllib3==2.8.0
    # via requests
uvicorn==0.54.0
    # via streamlit
watchdog==7.1.0
    # via streamlit
websockets==17.4
    # via
    #   streamlit
    #   yfinance
wrapt==2.5.2
    # via formulaic
yfinance==1.8.0
    # via harvestradar (pyproject.toml)
```

## 4. `requirements-llm.lock`

```
--extra-index-url https://download.pytorch.org/whl/cpu
accelerate==1.15.0
hf-xet==1.8.0
huggingface-hub==2.4.0
regex==2026.11.9
safetensors==0.8.0
tokenizers==0.23.3
torch==2.15.0+cpu
transformers==5.23.0
```

## 5. `.gitignore`

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
data/raw/
data/interim/
data/processed/*
!data/processed/oni.parquet
models_store/
.env
*.egg-info/
.DS_Store
captures/
dist/
```

## 6. `.streamlit/config.toml`

```toml
[theme]
base = "dark"
primaryColor = "#FFB547"
backgroundColor = "#0B0F14"
secondaryBackgroundColor = "#131C27"
textColor = "#EAF0F5"
font = "Inter, sans-serif"
headingFont = "Space Grotesk, sans-serif"
codeFont = "JetBrains Mono, monospace"
baseFontSize = 16

[[theme.fontFaces]]
family = "Inter"
url = "app/static/fonts/Inter-400-latin.woff2"
weight = 400
unicodeRange = "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD"

[[theme.fontFaces]]
family = "Inter"
url = "app/static/fonts/Inter-400-latin-ext.woff2"
weight = 400
unicodeRange = "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF"

[[theme.fontFaces]]
family = "Inter"
url = "app/static/fonts/Inter-500-latin.woff2"
weight = 500
unicodeRange = "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD"

[[theme.fontFaces]]
family = "Inter"
url = "app/static/fonts/Inter-500-latin-ext.woff2"
weight = 500
unicodeRange = "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF"

[[theme.fontFaces]]
family = "Inter"
url = "app/static/fonts/Inter-600-latin.woff2"
weight = 600
unicodeRange = "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD"

[[theme.fontFaces]]
family = "Inter"
url = "app/static/fonts/Inter-600-latin-ext.woff2"
weight = 600
unicodeRange = "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF"

[[theme.fontFaces]]
family = "Space Grotesk"
url = "app/static/fonts/SpaceGrotesk-500-latin.woff2"
weight = 500
unicodeRange = "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD"

[[theme.fontFaces]]
family = "Space Grotesk"
url = "app/static/fonts/SpaceGrotesk-500-latin-ext.woff2"
weight = 500
unicodeRange = "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF"

[[theme.fontFaces]]
family = "Space Grotesk"
url = "app/static/fonts/SpaceGrotesk-700-latin.woff2"
weight = 700
unicodeRange = "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD"

[[theme.fontFaces]]
family = "Space Grotesk"
url = "app/static/fonts/SpaceGrotesk-700-latin-ext.woff2"
weight = 700
unicodeRange = "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF"

[[theme.fontFaces]]
family = "JetBrains Mono"
url = "app/static/fonts/JetBrainsMono-400-latin.woff2"
weight = 400
unicodeRange = "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD"

[[theme.fontFaces]]
family = "JetBrains Mono"
url = "app/static/fonts/JetBrainsMono-400-latin-ext.woff2"
weight = 400
unicodeRange = "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF"

[[theme.fontFaces]]
family = "JetBrains Mono"
url = "app/static/fonts/JetBrainsMono-500-latin.woff2"
weight = 500
unicodeRange = "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD"

[[theme.fontFaces]]
family = "JetBrains Mono"
url = "app/static/fonts/JetBrainsMono-500-latin-ext.woff2"
weight = 500
unicodeRange = "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF"

[server]
enableStaticServing = true   # serves src/harvestradar/app/static at /app/static
headless = true
runOnSave = false
fileWatcherType = "none"

[client]
toolbarMode = "minimal"
showErrorDetails = true
showSidebarNavigation = false

[browser]
gatherUsageStats = false

[global]
developmentMode = false
```

## 7. `config/commodities.yaml`

```yaml
# HarvestRadar commodity configuration.
# Critical windows are DEFAULTS TO VALIDATE against GEOGLAM, SAGE (Sacks 2010) and USDA IPAD calendars.
# Window dates are MM-DD. year_offset is relative to the season year (the FAOSTAT harvest year).
# A window whose end is before its start runs into the next calendar year.
maize:
  label: "Maize"
  display: "MAIZE"
  glyph: maize
  spam_crop: MAIZ
  fao_item: 56
  tickers: {cbot: "ZC=F"}
  price_label: "CORN FUTURES, CHICAGO"
  price_name: "Corn futures (CBOT, Chicago)"
  price_unit: "US cents per bushel"
  coverage: 0.90
  weight_mode: production
  target: yield                  # annual crop: yield anomaly (area responds to planting decisions)
  thresholds: {heat_c: 29.0, frost_c: 0.0}
  main_country: USA
  windows:
    USA: [{start: "07-01", end: "08-15", stage: "pollination"}]
    CHN: [{start: "07-01", end: "08-31", stage: "silking"}]
    BRA: [{start: "03-01", end: "05-31", stage: "safrinha"}]
    ARG: [{start: "01-01", end: "02-28", stage: "flowering"}]
    UKR: [{start: "07-01", end: "08-15", stage: "pollination"}]
    IND: [{start: "08-01", end: "09-15", stage: "kharif flowering"}]
    MEX: [{start: "08-01", end: "09-30", stage: "flowering"}]
    CAN: [{start: "07-01", end: "08-15", stage: "pollination"}]
    FRA: [{start: "07-01", end: "08-15", stage: "pollination"}]
    RUS: [{start: "07-01", end: "08-15", stage: "pollination"}]
    ZAF: [{start: "01-01", end: "02-28", stage: "flowering"}]
    ROU: [{start: "07-01", end: "08-15", stage: "pollination"}]

coffee:
  label: "Arabica"
  display: "ARABICA"
  glyph: arabica
  spam_crop: COFF               # MapSPAM 2020 code for arabica (RCOF is robusta)
  fao_item: 656
  tickers: {ice_us: "KC=F"}
  price_label: "ARABICA FUTURES, NEW YORK"
  price_name: "Arabica coffee futures (ICE, New York)"
  price_unit: "US cents per pound"
  coverage: 0.90
  # The spec suggests export weights for coffee. USDA PSD exports do not split arabica from robusta,
  # so arabica uses production weights from MapSPAM 2020 (COFF = arabica). See docs/data_sources.md.
  weight_mode: production
  share_source: mapspam          # FAOSTAT does not split arabica from robusta
  # tree crop: FAOSTAT harvested area is often imputed, so the target is the production anomaly
  target: production
  thresholds: {heat_c: 30.0, frost_c: 2.0}
  main_country: BRA
  windows:
    BRA: [{start: "09-01", end: "11-30", stage: "flowering", year_offset: -1},
          {start: "06-01", end: "08-31", stage: "frost risk", year_offset: -1}]
    COL: [{start: "03-01", end: "05-31", stage: "flowering"}]
    ETH: [{start: "02-01", end: "04-30", stage: "flowering"}]
    HND: [{start: "03-01", end: "05-31", stage: "flowering"}]
    PER: [{start: "09-01", end: "11-30", stage: "flowering", year_offset: -1}]
    GTM: [{start: "03-01", end: "05-31", stage: "flowering"}]
    MEX: [{start: "03-01", end: "05-31", stage: "flowering"}]

cocoa:
  label: "Cocoa"
  display: "COCOA"
  glyph: cocoa
  spam_crop: COCO
  fao_item: 661
  tickers: {ice_us: "CC=F"}
  price_label: "COCOA FUTURES, NEW YORK"
  price_name: "Cocoa futures (ICE, New York)"
  price_unit: "US dollars per tonne"
  coverage: 0.90
  weight_mode: production
  target: production             # tree crop, see coffee
  thresholds: {heat_c: 33.0, frost_c: 0.0}
  main_country: CIV
  windows:
    CIV: [{start: "05-01", end: "09-30", stage: "main crop development"},
          {start: "12-01", end: "02-28", stage: "dry season"}]
    GHA: [{start: "05-01", end: "09-30", stage: "main crop development"},
          {start: "12-01", end: "02-28", stage: "dry season"}]
    NGA: [{start: "05-01", end: "09-30", stage: "main crop development"},
          {start: "12-01", end: "02-28", stage: "dry season"}]
    CMR: [{start: "05-01", end: "09-30", stage: "main crop development"},
          {start: "12-01", end: "02-28", stage: "dry season"}]
    IDN: [{start: "06-01", end: "09-30", stage: "dry season"}]
    ECU: [{start: "01-01", end: "04-30", stage: "flowering"}]
```

## 8. `config/settings.yaml`

```yaml
# Paths are relative to the repository root.
paths:
  raw: data/raw
  interim: data/interim
  processed: data/processed
  demo: data/demo
  reports: reports

seed: 42

dates:
  weather_start: "1981-01-01"
  # The pipeline's "today": the Friday of the latest weekly update. Fixed for reproducibility.
  as_of_end: "2026-11-13"
  index_start: "2001-01-05"
  daily_start: "2025-08-01"      # the index is also computed every working day from this date
  publication_lag_days: 5        # NASA POWER daily data are used 5 days after the fact

climatology:
  base: [2001, 2020]             # fixed base for the stress map
  min_years_expanding: 10        # expanding climatology for the model (past years only)

regions:
  max_cells_per_region: 5        # NASA POWER cells (0.5 x 0.625 deg) sampled per region
  weights_switch_year: 2016      # documented assumption: MapSPAM 2020 weights used for all years

targets:
  trend_years: 15                # linear trend on the previous 15 years
  min_trend_years: 8
  publication_month: 12          # FAOSTAT year Y is published in December of Y+1

features:
  lead_days: 120                 # a season becomes active this many days before its first window
  tail_days: 120                 # and stays active this many days after its last window
  pre_window_days: 60            # soil moisture before the window
  first_season: 1991

model:
  first_vintage: 1997           # early vintages only feed the rolling history used to standardise the index
  first_test_year: 2012
  last_test_year: 2024
  # Hyperparameters chosen on vintages 2003-2011 only (out-of-sample, end of season), then frozen.
  # Compared: 15 leaves / 10 per leaf (spec default), 7 / 40, 5 / 80; equal, sqrt-share, share weights.
  num_leaves: 5
  min_data_in_leaf: 80
  learning_rate: 0.03
  n_estimators: 200
  feature_fraction: 0.7
  reg_lambda: 10.0
  sample_weight: sqrt_share     # each country-season weighs sqrt(its share of world production)
  monotone_heat: true
  quantiles: [0.1, 0.9]

index:
  # risk_z = -(dP - mean) / sd; mean and sd: model climatology (the same vintage re-forecasts the same
  # weeks, +/- 3, of the previous 15 years); sd floored at 0.5 x sd of all weeks. Chosen for calibration
  # (sd of risk_z close to 1 over 2006-2026) among: raw forecast history (rolling or expanding) and this.
  standardize_years: 15
  calendar_window_weeks: 3
  min_years: 4
  sigma_floor: 0.5
  major_share: 0.10              # a window is "major" when the country holds >= 10 % of world supply

backtest:
  theta: 0.5
  delta_weeks: 4
  cost_bps_per_trade: 5
  slippage_bps: 0
  permutations: 1000
  grid_theta: [0.25, 0.5, 1.0]
  grid_delta: [2, 4, 8]
  start: "2006-01-01"

llm:
  provider: transformers
  model_id: "Qwen/Qwen2.5-1.5B-Instruct"
  display_name: "Qwen2.5-1.5B"
  max_new_tokens: 320
  retries: 2
  days: 5                        # daily notes generated for the latest N working days

episodes:
  us_drought_2012: {commodity: maize, label: "US drought 2012", start: "2012-05-01", end: "2012-09-28",
                    show_end: "2012-07-20", region_focus: USA, stage_country: USA}
  brazil_frost_2021: {commodity: coffee, label: "Brazil frost 2021", start: "2021-05-01", end: "2021-09-30",
                      show_end: "2021-08-31", region_focus: BRA, stage_country: BRA}
  cocoa_2023_2024: {commodity: cocoa, label: "Cocoa 2023-2024", start: "2023-07-01", end: "2024-12-31",
                    show_end: "2024-12-31", region_focus: CIV, stage_country: CIV}
```

## 9. `.github/workflows/daily.yml`

```yaml
# Daily update of HarvestRadar, every working day.
# New data only (NASA POWER weather, futures closes, El Nino), then index, climate fair value, daily notes,
# and the web edition published on GitHub Pages. The heavy data (weather since 1981, models) lives in the
# Actions cache; if the cache is empty, it is restored from the "data-state" release (created on the first
# run from the data-state branch, which is then deleted) and the missing days are fetched again.
name: Daily update

on:
  schedule:
    - cron: "17 5 * * 1-5"   # 05:17 UTC (06:17 or 07:17 in Paris), Monday to Friday
  workflow_dispatch:
    inputs:
      deterministic_notes:
        description: "Write the notes from the fixed template (skip the AI model)"
        type: boolean
        default: false

permissions:
  contents: write   # first run: turn the data-state branch into a release
  pages: write
  id-token: write

concurrency:
  group: daily-update
  cancel-in-progress: false

env:
  STATE_PATHS: data/raw/power data/processed models_store

jobs:
  update:
    runs-on: ubuntu-latest
    timeout-minutes: 150
    environment:
      name: github-pages
      url: ${{ steps.deploy.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
          cache-dependency-path: |
            requirements.lock
            requirements-llm.lock

      - name: Install
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.lock -r requirements-llm.lock
          pip install -e . --no-deps
          pip install pytest

      - name: Restore data state (cache)
        id: state
        uses: actions/cache/restore@v4
        with:
          path: |
            data/raw/power
            data/processed
            models_store
          key: state-v1-${{ github.run_id }}
          restore-keys: state-v1-

      - name: Restore data state (release, or the data-state branch the first time)
        if: steps.state.outputs.cache-matched-key == ''
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          if gh release view data-state >/dev/null 2>&1; then
            gh release download data-state --pattern 'state.tar.zst' --dir /tmp
            tar --zstd -xf /tmp/state.tar.zst && rm /tmp/state.tar.zst
          else
            git fetch --depth=1 origin data-state:refs/remotes/origin/data-state
            git checkout origin/data-state -- $STATE_PATHS
            git reset -q
            echo "STATE_FROM_BRANCH=1" >> "$GITHUB_ENV"
          fi

      - name: Restore the AI model (cache)
        uses: actions/cache@v4
        with:
          path: ~/.cache/huggingface
          key: hf-qwen2.5-1.5b-instruct-v1

      - name: Update
        run: harvestradar update ${{ inputs.deterministic_notes && '--deterministic-notes' || '' }}

      - name: Tests on the new snapshot
        run: pytest -q

      - name: Save data state (cache)
        if: success()
        uses: actions/cache/save@v4
        with:
          path: |
            data/raw/power
            data/processed
            models_store
          key: state-v1-${{ github.run_id }}

      - name: Move the data snapshot from the branch to a release (first run only)
        if: success() && env.STATE_FROM_BRANCH == '1'
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          tar --zstd -cf /tmp/state.tar.zst $STATE_PATHS
          gh release create data-state /tmp/state.tar.zst --prerelease --title "Data state for the daily update" \
            --notes "Weather since 1981 (NASA POWER), processed tables and models. Restored by the daily workflow when its cache is empty."
          git push origin --delete data-state

      - name: Build the web edition
        run: |
          python scripts/build_web.py
          mkdir -p _site
          cp dist/web/index.html _site/index.html
          touch _site/.nojekyll

      - uses: actions/upload-pages-artifact@v3
        with:
          path: _site

      - id: deploy
        uses: actions/deploy-pages@v4
```

## 10. `.github/workflows/pages.yml`

```yaml
# Publish the web edition on GitHub Pages from the snapshot in data/demo, on every push to main.
# The daily update (daily.yml) publishes it too, with fresh data.
name: Publish web edition

on:
  push:
    branches: [main]
    paths: ["web/**", "data/demo/**", "scripts/build_web.py", "src/harvestradar/**"]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  publish:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    environment:
      name: github-pages
      url: ${{ steps.deploy.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
          cache-dependency-path: requirements.lock
      - name: Install
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.lock
          pip install -e . --no-deps
      - name: Build the web edition
        run: |
          python scripts/build_web.py
          mkdir -p _site
          cp dist/web/index.html _site/index.html
          touch _site/.nojekyll
      - uses: actions/upload-pages-artifact@v3
        with:
          path: _site
      - id: deploy
        uses: actions/deploy-pages@v4
```

## 11. `src/harvestradar/__init__.py`

```python
"""HarvestRadar: see the harvest shock before the price does."""

__version__ = "0.1.0"
```

## 12. `src/harvestradar/app/__init__.py`

```python

```

## 13. `src/harvestradar/app/assistant.py`

```python
"""In-app assistant: the question is answered in the page by the local Qwen model (the one that writes the
daily notes), from the page's figures. Free, no account, nothing leaves the computer once the model is in the
Hugging Face cache. Without the optional LLM dependencies, a link to ask ChatGPT in a new tab is offered
instead. Same instructions and data as the web edition (web/app.js, contextText)."""

from __future__ import annotations

from urllib.parse import quote

from harvestradar.app import data

URL = "https://chatgpt.com/?q="
RULES = ("You are the HarvestRadar assistant, inside a research dashboard on weather risk for maize, arabica coffee and "
         "cocoa futures. Use only the HarvestRadar figures below for numbers, and say plainly when something is not in "
         "them (stocks, positioning, news). The risk index compares the expected world harvest with normal for the time "
         "of year: 0 = normal, above +2 = rare; it moves with the weather and is weakly linked to prices week to week. "
         "Less supply than normal (index above 0) tends to push prices up; more supply pushes them down. "
         "The climate fair value is the 12-month average price moved by the price reaction to the expected world supply "
         "gap. Give trade ideas as scenarios with entry logic, invalidation level and risks, never personalised advice. "
         "Answer in at most 150 words, in the language of the question.")


def _fmt(key: str, x: float) -> str:
    return f"{x:,.0f}" if key == "cocoa" else f"{x:,.2f}"


def crop_line(key: str, asof, full: bool) -> str:
    m = data.meta()["commodities"][key]
    r = data.latest_risk(key, asof)
    pi = data.jsonfile("price_impact.json")
    fv = pi.get("fair_value", {}).get(key)
    s = (f"- {m['label']} ({m['price_name']}, {m['price_unit']}): risk index {r['risk_z']:+.2f}; expected world supply "
         f"{r['delta_prod_pct']:+.2f}% vs normal")
    if fv:
        s += (f"; last close {_fmt(key, fv['close'])}; climate fair value {_fmt(key, fv['fair'])} (80% range "
              f"{_fmt(key, fv['fair_lo'])} to {_fmt(key, fv['fair_hi'])}), price {fv['gap_to_fair_pct']:+.1f}% vs fair value; "
              f"price reaction {-fv['slope_pct_per_pct']:.2f}% per 1% of world supply missing"
              + ("" if fv["reliable"] else " (not statistically reliable)"))
    s += "."
    if full:
        s += "\n  Countries behind the reading (points of world supply): " + ", ".join(
            f"{c['name']} {c['contrib_pct']:+.2f}" + (" (critical window open)" if c["window_open"] else "")
            for c in r["contributors"][:4]) + "."
    return s


def context(key: str, page: str, asof) -> str:
    lines = [crop_line(k, asof, k == key) for k in data.meta()["commodities"]]
    return (f"{RULES}\n\nHarvestRadar data of {asof.day} {asof:%B %Y}:\n" + "\n".join(lines)
            + f"\n\nThe user is looking at the {page} page, crop: {data.meta()['commodities'][key]['label']}.")


def chatgpt_url(question: str, key: str, page: str, asof) -> str:
    return URL + quote(context(key, page, asof) + f"\n\nMy question: {question}")


def local_model_available() -> bool:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError:
        return False
    return True


def answer_local(question: str, key: str, page: str, asof) -> str:
    from harvestradar.config import get_config
    from harvestradar.report.llm import generate

    model_id = get_config().llm["model_id"]
    return generate(model_id, context(key, page, asof), question, max_new_tokens=320)
```

## 14. `src/harvestradar/app/components.py`

```python
"""Small HTML blocks (rendered with st.markdown(..., unsafe_allow_html=True)). Typed arguments, no data
access here: pages pass in values read from data/demo."""

from __future__ import annotations

import html as H
import re
from functools import lru_cache
from importlib import resources

import numpy as np

from harvestradar.app.theme import GLASS, T

E = H.escape


@lru_cache(maxsize=16)
def _svg(name: str) -> str:
    s = resources.files("harvestradar.app").joinpath(f"static/brand/{name}.svg").read_text()
    return re.sub(r"\s+", " ", s).strip()


def glyph(kind: str, size: int = 22, color: str = T["frost"]) -> str:
    s = _svg(f"glyph_{kind}")
    s = re.sub(r'width="\d+" height="\d+"', f'width="{size}" height="{size}"', s, count=1)
    return f'<span style="color:{color};display:inline-flex;flex:none">{s}</span>'


def mark(size: int = 30) -> str:
    s = _svg("mark_small")
    return re.sub(r'width="\d+" height="\d+"', f'width="{size}" height="{size}"', s, count=1)


def mark_on_signal(size: int = 40) -> str:
    s = _svg("mark_on_signal")
    return re.sub(r'width="\d+" height="\d+"', f'width="{size}" height="{size}"', s, count=1)


def brand() -> str:
    return f'<div class="hr-topbar"><div class="hr-brand">{mark(30)}<span>Harvest<b>Radar</b></span></div></div>'


def status(week_label: str) -> str:
    return f'<div class="hr-status"><span class="hr-dot"></span><span>DATA AS OF {E(week_label.upper())}</span></div>'


def _smooth_path(xs: np.ndarray, ys: np.ndarray) -> str:
    pts = list(zip(xs, ys))
    if len(pts) < 2:
        return ""
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(1, len(pts)):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[i]
        cx = (x0 + x1) / 2
        d += f" C{cx:.1f},{y0:.1f} {cx:.1f},{y1:.1f} {x1:.1f},{y1:.1f}"
    return d


def sparkline(values: list[float], w: int = 120, h: int = 40, color: str = T["signal"], fill: bool = True,
              dot: bool = True, pad: int = 5, ref: float | None = None) -> str:
    v = np.asarray([x for x in values if x is not None and np.isfinite(x)], dtype=float)
    if len(v) < 2:
        return f'<svg width="{w}" height="{h}"></svg>'
    lo, hi = float(v.min()), float(v.max())
    if ref is not None:
        lo, hi = min(lo, ref), max(hi, ref)
    if hi - lo < 1e-9:
        hi = lo + 1
    xs = np.linspace(pad, w - pad, len(v))
    ys = h - pad - (v - lo) / (hi - lo) * (h - 2 * pad)
    d = _smooth_path(xs, ys)
    uid = abs(hash((tuple(np.round(v, 3)), w, h, color))) % 10**8
    area = (f'<path d="{d} L{xs[-1]:.1f},{h} L{xs[0]:.1f},{h} Z" fill="url(#sg{uid})"/>' if fill else "")
    refline = ""
    if ref is not None:
        ry = h - pad - (ref - lo) / (hi - lo) * (h - 2 * pad)
        refline = (f'<line x1="{pad}" x2="{w - pad}" y1="{ry:.1f}" y2="{ry:.1f}" stroke="{T["line_strong"]}" '
                   f'stroke-dasharray="3 4"/>')
    end = (f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="3.6" fill="{color}" '
           f'style="filter:drop-shadow(0 0 5px {color})"/>' if dot else "")
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" aria-hidden="true"><defs>'
            f'<linearGradient id="sg{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{color}" '
            f'stop-opacity=".28"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient></defs>'
            f'{refline}{area}<path d="{d}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/>'
            f'{end}</svg>')


def ticker_card(display: str, glyph_kind: str, value: str, series: list[float], selected: bool,
                glow: bool, spark_w: int = 132, suffix: str = " &middot; RISK INDEX") -> str:
    border = "border-color:rgba(255,181,71,.55);box-shadow:0 0 0 1px rgba(255,181,71,.25), 0 20px 60px rgba(0,0,0,.35);" \
        if selected else ""
    g = "hr-glow" if glow else ""
    return (f'<div class="hr-glass" style="height:88px;padding:14px 20px;display:flex;align-items:center;gap:16px;{border}">'
            f'{glyph(glyph_kind, 26, T["frost_2"])}'
            f'<div style="flex:1;min-width:0"><div class="hr-caps" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{E(display)}{suffix}</div>'
            f'<div class="hr-mono {g}" style="font-size:32px;line-height:40px;color:{T["signal"]};font-weight:500">{E(value)}</div></div>'
            f'{sparkline(series, spark_w, 46)}</div>')


def stat_card(label: str, value: str, sub: str = "", color: str = T["frost"], height: int = 164,
              size: int = 34) -> str:
    return (f'<div class="hr-glass" style="height:{height}px;padding:20px 24px">'
            f'<div class="hr-caps">{E(label)}</div>'
            f'<div class="hr-mono" style="font-size:{size}px;line-height:1.25;color:{color};margin-top:12px;font-weight:500">{E(value)}</div>'
            f'<div class="hr-source" style="margin-top:6px">{sub}</div></div>')


def hero_card(display: str, glyph_kind: str, value: str, sub: str, height: int = 164) -> str:
    return (f'<div class="hr-glass" style="height:{height}px;padding:18px 24px;display:flex;align-items:center;gap:22px">'
            f'{glyph(glyph_kind, 52, T["frost_2"])}'
            f'<div><div class="hr-caps">{E(display)} &middot; HARVEST-RISK INDEX</div>'
            f'<div class="hr-mono hr-glow" style="font-size:72px;line-height:1;color:{T["signal"]};font-weight:500;'
            f'margin-top:6px">{E(value)}</div><div class="hr-source" style="margin-top:8px">{sub}</div></div></div>')


def panel(title: str, body: str, source: str = "", height: int | None = None, extra: str = "") -> str:
    h = f"height:{height}px;" if height else ""
    src = f'<div class="hr-source">{source}</div>' if source else ""
    return (f'<div class="hr-glass" style="{h}display:flex;flex-direction:column;{extra}">'
            f'<div class="hr-caps" style="margin-bottom:12px">{title}</div><div style="flex:1">{body}</div>{src}</div>')


def ranking_rows(rows: list[dict], glyph_kind: str) -> str:
    """rows: rank, name, iso, frac (0-1 of the top score), hot (bool)."""
    out = []
    for r in rows:
        end = T["heat"] if r["hot"] else T["signal"]
        out.append(
            f'<div style="display:grid;grid-template-columns:34px 26px 1fr auto;align-items:center;gap:6px 10px;'
            f'margin-bottom:10px">'
            f'<span class="hr-mono" style="font-size:13px;color:{T["muted"]}">{r["rank"]:02d}</span>'
            f'{glyph(glyph_kind, 18, T["frost_2"])}'
            f'<span style="font-size:16px;color:{T["frost"]};white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{E(r["name"])}</span>'
            f'<span style="font-size:14px;color:{T["muted"]}">{E(r["iso"])}</span>'
            f'<span></span><span></span>'
            f'<div style="grid-column:3 / span 2;height:4px;border-radius:3px;background:{T["line"]}">'
            f'<div style="width:{max(3, 100 * r["frac"]):.0f}%;height:4px;border-radius:3px;'
            f'background:linear-gradient(90deg,#8A6424,#F5A93A 70%,{end});box-shadow:0 0 8px rgba(255,181,71,.35)"></div></div>'
            f'</div>')
    return "".join(out)


def climate_card(value: str, period: str, series: list[float], source: str, strength: str = "El Niño") -> str:
    return (f'<div class="hr-glass" style="height:196px;padding:18px 20px">'
            f'<div class="hr-caps">EL NIÑO &middot; BACKGROUND</div>'
            f'<div style="font-family:Space Grotesk,sans-serif;font-weight:700;font-size:22px;margin-top:8px;color:{T["frost"]}">{E(strength[:1].upper() + strength[1:])}</div>'
            f'<div style="display:flex;align-items:flex-end;justify-content:space-between;gap:12px">'
            f'<div><span class="hr-mono" style="font-size:30px;color:{T["signal"]}">{E(value)} &deg;C</span>'
            f'<div style="font-size:14px;color:{T["muted"]};margin-top:2px">Pacific sea temperature vs normal, {E(period)}</div></div>'
            f'{sparkline(series, 200, 48)}</div>'
            f'<div class="hr-source" style="margin-top:6px">{source}</div></div>')


def note_ready(passed: int, total: int, label: str) -> str:
    return (f'<div class="hr-glass" style="height:88px;padding:16px 20px;display:flex;align-items:center;gap:16px">'
            f'<span style="flex:none;border-radius:10px;overflow:hidden;display:inline-flex">{mark_on_signal(40)}</span>'
            f'<div><div style="font-size:17px;color:{T["frost"]};font-weight:500">{E(label)}</div>'
            f'<div style="font-size:14px;color:{T["muted"]}">{passed} of {total} checks passed</div></div>'
            f'<div style="margin-left:auto" class="hr-mono"><span style="font-size:13px;color:{T["signal"]}">OPEN</span></div></div>')


def bar_rows(rows: list[dict], unit: str = "pp", max_abs: float | None = None, label_w: int = 180) -> str:
    """Diverging bars: risk-raising (negative supply) in amber, risk-lowering in blue.
    rows: label, value (signed), raises_risk (bool), note (optional)."""
    if not rows:
        return f'<div style="color:{T["muted"]};font-size:15px">No data.</div>'
    m = max_abs or max(abs(r["value"]) for r in rows) or 1.0
    out = []
    for r in rows:
        frac = min(1.0, abs(r["value"]) / m)
        amber = r["raises_risk"]
        bg = ("linear-gradient(90deg,#8A6424,#F5A93A)" if amber else "#3F74D8")
        glow = "0 0 12px rgba(255,181,71,.45)" if amber else "0 0 10px rgba(63,116,216,.4)"
        bar = (f'<div style="height:12px;width:{max(2, 100 * frac):.1f}%;border-radius:7px;background:{bg};'
               f'box-shadow:{glow};{"margin-left:auto" if not amber else ""}"></div>')
        left = bar if not amber else ""
        right = bar if amber else ""
        note = f'<div class="hr-mono" style="font-size:13px;color:{T["muted"]}">{E(r["note"])}</div>' if r.get("note") else ""
        out.append(
            f'<div style="display:grid;grid-template-columns:{label_w}px 1fr 1fr 84px;align-items:center;gap:10px;'
            f'min-height:44px">'
            f'<div><div style="font-size:16px;color:{T["frost"]};white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{E(r["label"])}</div>{note}</div>'
            f'<div style="display:flex">{left}</div><div style="display:flex;border-left:1px solid {T["line_strong"]}">{right}</div>'
            f'<div class="hr-mono" style="text-align:right;font-size:15px;color:{T["signal"] if amber else T["frost_2"]}">'
            f'{r["value"]:+.2f}{(" " + unit) if unit else ""}</div></div>')
    return "".join(out)


def legend_risk(low: str = "lower risk", high: str = "higher risk", width: int = 36) -> str:
    sw = "".join(f'<i style="width:{width}px;height:8px;border-radius:3px;display:block;background:{c}"></i>' for c in
                 ["#7EB0FF", "#3F74D8", "#26406A", "#1E2833", "#8A6424", "#F5A93A", "#FF5A36"])
    return (f'<div><div style="display:flex;gap:4px">{sw}</div><div class="hr-mono" style="display:flex;'
            f'justify-content:space-between;font-size:13px;color:{T["muted"]};margin-top:5px"><span>{low}</span>'
            f'<span>{high}</span></div></div>')


def chip(text: str, amber: bool = False) -> str:
    return f'<span class="hr-chip{" amber" if amber else ""}">{E(text)}</span>'


TONES = {"good": ("#7EB0FF", "rgba(126,176,255,.45)", "rgba(63,116,216,.14)"),
         "warn": (T["signal"], "rgba(255,181,71,.5)", "rgba(255,181,71,.10)"),
         "bad": (T["heat"], "rgba(255,90,54,.5)", "rgba(255,90,54,.10)"),
         "neutral": (T["muted"], T["line_strong"], "rgba(19,28,39,.7)")}


def tag(text: str, tone: str = "neutral", plain: bool = False) -> str:
    """Status tag: a coloured dot and a word (verdicts, checks). No tick or cross symbols."""
    color, border, bg = TONES.get(tone, TONES["neutral"])
    font = ("font-family:Inter,sans-serif;font-size:14px;" if plain else
            "font-family:JetBrains Mono,monospace;font-size:13px;letter-spacing:.08em;text-transform:uppercase;")
    return (f'<span style="display:inline-flex;align-items:center;gap:8px;padding:5px 11px;border-radius:8px;'
            f'border:1px solid {border};background:{bg};color:{color};white-space:nowrap;{font}margin:0 8px 8px 0">'
            f'<i style="width:7px;height:7px;border-radius:50%;background:{color};display:inline-block"></i>{E(text)}</span>')


def badge(text: str, ok: bool) -> str:
    return tag(text if ok else f"{text}: failed", "good" if ok else "bad", plain=True)


def glass_open(extra: str = "") -> str:
    return f'<div style="{GLASS}{extra}">'
```

## 15. `src/harvestradar/app/data.py`

```python
"""Offline data access for the app: everything comes from data/demo (and config/). Cached."""

from __future__ import annotations

import json
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import streamlit as st

from harvestradar.paths import DEMO

DATA = Path(os.environ.get("HARVESTRADAR_DEMO", DEMO))


@st.cache_data(show_spinner=False)
def meta() -> dict:
    return json.loads((DATA / "meta.json").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def jsonfile(name: str) -> dict:
    p = DATA / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


@st.cache_data(show_spinner=False)
def risk() -> pd.DataFrame:
    r = pd.read_parquet(DATA / "risk_index.parquet")
    r["date"] = pd.to_datetime(r["date"])
    return r


@st.cache_data(show_spinner=False)
def risk_daily() -> pd.DataFrame:
    p = DATA / "risk_index_daily.parquet"
    if not p.exists():
        return risk()
    r = pd.read_parquet(p)
    r["date"] = pd.to_datetime(r["date"])
    return r


@st.cache_data(show_spinner=False)
def fair_value(key: str | None = None) -> pd.DataFrame:
    """Climate fair value every trading day (empty frame if the snapshot predates it)."""
    p = DATA / "fair_value_daily.parquet"
    if not p.exists():
        return pd.DataFrame(columns=["commodity", "date", "close", "anchor", "fair", "fair_lo", "fair_hi"])
    f = pd.read_parquet(p)
    f["date"] = pd.to_datetime(f["date"])
    return f[f.commodity == key].sort_values("date") if key else f


@st.cache_data(show_spinner=False)
def today() -> pd.Timestamp:
    """The app's "today": the latest date in data/demo (never the clock)."""
    return risk_daily()["date"].max()


@st.cache_data(show_spinner=False)
def stress(key: str) -> pd.DataFrame:
    s = pd.read_parquet(DATA / f"stress_{key}.parquet")
    s["dekad_end"] = pd.to_datetime(s["dekad_end"])
    return s


@st.cache_data(show_spinner=False)
def regions(key: str) -> gpd.GeoDataFrame:
    return gpd.read_file(DATA / f"regions_{key}.geojson")


@st.cache_data(show_spinner=False)
def prices(key: str) -> pd.DataFrame:
    p = pd.read_parquet(DATA / f"prices_{key}.parquet")
    p["date"] = pd.to_datetime(p["date"])
    return p.sort_values("date")


@st.cache_data(show_spinner=False)
def predictions() -> pd.DataFrame:
    p = pd.read_parquet(DATA / "predictions.parquet")
    p["date"] = pd.to_datetime(p["date"])
    return p


@st.cache_data(show_spinner=False)
def shap_latest() -> pd.DataFrame:
    return pd.read_parquet(DATA / "shap_latest.parquet")


@st.cache_data(show_spinner=False)
def notes() -> pd.DataFrame:
    p = DATA / "notes.parquet"
    if not p.exists():
        return pd.DataFrame()
    n = pd.read_parquet(p)
    n["week"] = pd.to_datetime(n["week"])
    return n


@st.cache_data(show_spinner=False)
def oni() -> pd.DataFrame:
    p = DATA / "oni.parquet"
    if not p.exists():
        p = DATA.parent / "processed" / "oni.parquet"
    o = pd.read_parquet(p)
    o["available_at"] = pd.to_datetime(o["available_at"])
    return o


@st.cache_data(show_spinner=False)
def world() -> gpd.GeoDataFrame:
    return gpd.read_file(DATA / "world_110m.geojson")


# ---------- derived tables ----------

@st.cache_data(show_spinner=False)
def latest_risk(key: str, at: pd.Timestamp | None = None) -> dict:
    r = risk_daily()
    r = r[(r.commodity == key)].dropna(subset=["risk_z"]).sort_values("date")
    if at is not None:
        r = r[r.date <= at]
    if r.empty:
        return {}
    row = r.iloc[-1].to_dict()
    row["contributors"] = json.loads(row["contributors"])
    return row


@st.cache_data(show_spinner=False)
def risk_series(key: str, weeks: int | None = None, end: pd.Timestamp | None = None) -> pd.DataFrame:
    r = risk()
    r = r[r.commodity == key].dropna(subset=["risk_z"]).sort_values("date")
    if end is not None:
        r = r[r.date <= end]
    return r.tail(weeks) if weeks else r


@st.cache_data(show_spinner=False)
def top_regions(key: str, dekad: pd.Timestamp, n: int = 5) -> pd.DataFrame:
    s = stress(key)
    s = s[s.dekad_end == dekad]
    g = regions(key)[["region_id", "adm1_name", "country_iso3", "country_name", "weight", "lat", "lon"]]
    m = s.merge(g, on="region_id")
    m["score"] = m["stress"] * m["weight"]
    return m.sort_values("score", ascending=False).head(n).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def oni_latest(at: pd.Timestamp) -> dict:
    o = oni()
    o = o[o.available_at <= at].sort_values("available_at")
    if o.empty:
        return {}
    last = o.iloc[-1]
    hist = o.tail(36)
    return {"value": float(last.oni), "label": str(last.label), "series": hist["oni"].round(2).tolist(),
            "available_at": last.available_at.strftime("%Y-%m-%d")}


def windows_for(key: str, country: str) -> list[dict]:
    return meta()["commodities"][key]["windows"].get(country, [])


def window_spans(key: str, country: str, start: pd.Timestamp, end: pd.Timestamp) -> list[tuple]:
    """Calendar spans of a country's critical windows between two dates (from config, via meta.json)."""
    out = []
    for w in windows_for(key, country):
        for season in range(start.year - 1, end.year + 2):
            y = season + int(w.get("year_offset", 0))
            s = pd.Timestamp(f"{y}-{w['start']}")
            e = pd.Timestamp(f"{y}-{w['end']}")
            if e < s:
                e = pd.Timestamp(f"{y + 1}-{w['end']}")
            if e >= start and s <= end:
                out.append((max(s, start), min(e, end), w["stage"]))
    return sorted(set(out))


def country_names() -> dict:
    out = {}
    for c in meta()["commodities"].values():
        out.update(c.get("country_names", {}))
    return out


def oni_strength(v: float) -> str:
    """NOAA convention for the Oceanic Nino Index."""
    a = abs(v)
    kind = "El Niño" if v > 0 else "La Niña"
    if a < 0.5:
        return "neutral conditions"
    return ("weak " if a < 1 else "moderate " if a < 1.5 else "strong " if a < 2 else "very strong ") + kind


def fmt_signed(x: float, nd: int = 2) -> str:
    return f"{x:+.{nd}f}" if x is not None and np.isfinite(x) else "n/a"
```

## 16. `src/harvestradar/app/maps.py`

```python
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
<div class="map-label"></div>
<div class="legend"><div class="sw">{legend}</div><div class="lg"><span>{cfg.get('legendLow', 'lower stress')}</span>
<span>{cfg.get('legendHigh', 'higher stress')}</span></div></div>
<div class="bar"><button class="play" aria-label="Play">{PLAY_ICON}</button><div class="ticks"></div>
<div class="range">{cfg.get('rangeLabel', '')}</div>{speed}</div>
{strip}<div class="tip"></div></div>
<script>{js_source()}</script>
<script>RadarMap(document.querySelector('.radar'), {json.dumps(cfg, separators=(',', ':'))});</script>
</body></html>"""
```

## 17. `src/harvestradar/app/static/js/radar_map.js`

```javascript
/* HarvestRadar map: SVG regions on an Equal Earth Blue Marble base, coloured with the Radar Night risk
   ramp, hotspot rings, dekad scrubber (play, pause, arrows). Offline: no external request. */
(function () {
  const RAMP = [[-3, [126, 176, 255]], [-2, [63, 116, 216]], [-1, [38, 64, 106]], [0, [30, 40, 51]],
                [1, [138, 100, 36]], [2, [245, 169, 58]], [3, [255, 90, 54]]];
  function ramp(z) {
    z = Math.max(-3, Math.min(3, z));
    for (let i = 0; i < RAMP.length - 1; i++) {
      const [z0, c0] = RAMP[i], [z1, c1] = RAMP[i + 1];
      if (z >= z0 && z <= z1) {
        const t = (z - z0) / (z1 - z0);
        return c0.map((v, k) => Math.round(v + (c1[k] - v) * t));
      }
    }
    return [255, 90, 54];
  }
  const NS = "http://www.w3.org/2000/svg";
  const el = (n, a = {}) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); return e; };

  window.RadarMap = function (root, cfg) {
    const vb = cfg.viewBox;
    const svg = el("svg", { viewBox: vb.join(" "), preserveAspectRatio: "xMidYMid meet", class: "map-svg",
                            role: "img", "aria-label": cfg.ariaLabel || "Stress map" });
    const defs = el("defs");
    defs.innerHTML = `<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="${vb[2] / 500}" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>`;
    svg.appendChild(defs);
    const b = cfg.base;
    svg.appendChild(el("image", { href: b.href, x: b.x, y: b.y, width: b.w, height: b.h, preserveAspectRatio: "none",
                                  opacity: b.opacity || 1 }));
    if (cfg.countries) svg.appendChild(el("path", { d: cfg.countries, fill: "none", stroke: "rgba(199,209,219,0.16)",
                                                     "stroke-width": cfg.borderWidth || 0.6, "vector-effect": "non-scaling-stroke" }));
    const g = el("g");
    const paths = cfg.regions.map((r) => {
      const p = el("path", { d: r.d, stroke: "#0B0F14", "stroke-width": 0.7, "vector-effect": "non-scaling-stroke",
                             "stroke-opacity": 0.9, "data-i": r.i });
      g.appendChild(p);
      return p;
    });
    svg.appendChild(g);
    const rings = el("g", { class: "rings" });
    svg.appendChild(rings);
    root.querySelector(".map-stage").appendChild(svg);

    const label = root.querySelector(".map-label");
    const ticks = root.querySelector(".ticks");
    const playBtn = root.querySelector(".play");
    const speedBtn = root.querySelector(".speed");
    const tip = root.querySelector(".tip");
    const strip = root.querySelector(".strip");
    let idx = cfg.start, timer = null, speed = 1;

    // scrubber ticks: one per frame, height from the frame's weighted positive stress
    cfg.frames.forEach((f, i) => {
      const t = document.createElement("button");
      t.className = "tick"; t.setAttribute("aria-label", "Dekad " + f.label); t.tabIndex = -1;
      t.style.setProperty("--h", (8 + 26 * Math.min(1, f.tick)).toFixed(1) + "px");
      t.addEventListener("click", () => { stop(); show(i); });
      ticks.appendChild(t);
    });

    // film strip (episode mode): small copies of the map at chosen frames
    const thumbs = [];
    if (strip && cfg.strip) {
      cfg.strip.forEach((fi) => {
        const card = document.createElement("button");
        card.className = "thumb"; card.setAttribute("aria-label", "Dekad " + cfg.frames[fi].label);
        const s = el("svg", { viewBox: vb.join(" "), preserveAspectRatio: "xMidYMid slice" });
        s.appendChild(el("image", { href: b.href, x: b.x, y: b.y, width: b.w, height: b.h, preserveAspectRatio: "none" }));
        const gg = el("g");
        cfg.regions.forEach((r) => {
          const v = cfg.frames[fi].values[r.i];
          const c = ramp(v == null ? 0 : v), o = 0.35 + 0.65 * Math.min(1, Math.abs(v || 0) / 2);
          gg.appendChild(el("path", { d: r.d, fill: `rgb(${c})`, "fill-opacity": o, stroke: "#0B0F14",
                                       "stroke-width": 0.4, "vector-effect": "non-scaling-stroke" }));
        });
        s.appendChild(gg);
        card.appendChild(s);
        const cap = document.createElement("div"); cap.className = "thumb-label"; cap.textContent = cfg.frames[fi].short;
        card.appendChild(cap);
        card.addEventListener("click", () => { stop(); show(fi); });
        strip.appendChild(card);
        thumbs.push([fi, card]);
      });
    }

    function drawRings(hs) {
      rings.innerHTML = "";
      const R = cfg.ringRadius;
      hs.forEach(([x, y], k) => {
        const grp = el("g", { class: "ping", style: `animation-delay:${k * 0.5}s` });
        [1, 1.9, 2.9].forEach((m, j) => grp.appendChild(el("circle", { cx: x, cy: y, r: R * m, fill: "none",
          stroke: "#FFB547", "stroke-opacity": [0.9, 0.5, 0.25][j], "stroke-width": 1.4, "vector-effect": "non-scaling-stroke" })));
        grp.appendChild(el("circle", { cx: x, cy: y, r: R * 0.32, fill: "#FFB547", filter: "url(#glow)" }));
        rings.appendChild(grp);
      });
    }

    function show(i) {
      idx = (i + cfg.frames.length) % cfg.frames.length;
      const f = cfg.frames[idx];
      paths.forEach((p, k) => {
        const v = f.values[k];
        if (v == null) { p.setAttribute("fill", "none"); return; }
        const c = ramp(v);
        p.setAttribute("fill", `rgb(${c[0]},${c[1]},${c[2]})`);
        p.setAttribute("fill-opacity", (0.35 + 0.65 * Math.min(1, Math.abs(v) / 2)).toFixed(3));
      });
      drawRings(f.hotspots || []);
      if (label) label.textContent = cfg.labelPrefix + " · " + (cfg.labelWord ? cfg.labelWord + " " : "") + f.label;
      ticks.querySelectorAll(".tick").forEach((t, k) => t.classList.toggle("on", k <= idx));
      ticks.querySelectorAll(".tick").forEach((t, k) => t.classList.toggle("now", k === idx));
      thumbs.forEach(([fi, card]) => card.classList.toggle("active", fi === idx));
      const out = root.querySelector(".frame-date"); if (out) out.textContent = f.date;
    }
    function stop() { if (timer) { clearInterval(timer); timer = null; } root.classList.remove("playing"); playBtn.setAttribute("aria-label", "Play"); }
    function play() {
      if (cfg.capture) return;
      stop(); root.classList.add("playing"); playBtn.setAttribute("aria-label", "Pause");
      if (idx >= cfg.frames.length - 1) show(0);
      timer = setInterval(() => { if (idx >= cfg.frames.length - 1) { stop(); return; } show(idx + 1); }, speed === 1 ? 400 : 160);
    }
    playBtn.addEventListener("click", () => (timer ? stop() : play()));
    if (speedBtn) speedBtn.addEventListener("click", () => {
      speed = speed === 1 ? 2.5 : 1; speedBtn.textContent = "x" + speed; speedBtn.classList.toggle("on", speed !== 1);
      if (timer) play();
    });
    root.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight") { stop(); show(idx + 1); e.preventDefault(); }
      else if (e.key === "ArrowLeft") { stop(); show(idx - 1); e.preventDefault(); }
      else if (e.key === " " && e.target === root) { timer ? stop() : play(); e.preventDefault(); }
    });
    if (!cfg.capture) {
      paths.forEach((p, k) => {
        p.addEventListener("mousemove", (e) => {
          const r = cfg.regions[k], v = cfg.frames[idx].values[k];
          tip.innerHTML = `<b>${r.name}</b><span>${r.country}</span><em>${v == null ? "no data" : (v >= 0 ? "+" : "") + v.toFixed(2)}</em>`;
          const box = root.getBoundingClientRect();
          tip.style.left = (e.clientX - box.left + 14) + "px"; tip.style.top = (e.clientY - box.top + 14) + "px";
          tip.style.opacity = 1;
        });
        p.addEventListener("mouseleave", () => { tip.style.opacity = 0; });
      });
    } else {
      root.classList.add("capture");
    }
    show(idx);
    if (cfg.autoplay && !cfg.capture) play();
    return { stop: stop, play: play, show: show };
  };
})();
```

## 18. `src/harvestradar/app/streamlit_app.py`

```python
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
```

## 19. `src/harvestradar/app/theme.py`

```python
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
```

## 20. `src/harvestradar/app/views/__init__.py`

```python

```

## 21. `src/harvestradar/app/views/commodity.py`

```python
"""Commodity page: hero index, supply vs trend, futures price, index vs price with critical windows,
who drives this week (contributors) and SHAP (which weather)."""

from __future__ import annotations

import html as H

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from harvestradar.app import components as C
from harvestradar.app import data
from harvestradar.app.assistant import answer_local, chatgpt_url, local_model_available
from harvestradar.app.theme import T
from harvestradar.app.views.common import ticker
from harvestradar.app.views.fair_value import chain_panel, comove_panel, gap_words

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
    fv = data.jsonfile("price_impact.json").get("fair_value", {}).get(key)
    if fv:
        body += (f'<div style="font-size:16px;color:{T["frost_2"]};margin-top:12px;padding-top:12px;line-height:1.6;'
                 f'border-top:1px solid {T["line"]}">Climate fair value today: <span class="hr-mono" style="color:'
                 f'{T["signal"]}">{fmt_price(key, fv["fair"])}</span>. The price (<span class="hr-mono">'
                 f'{fmt_price(key, fv["close"])}</span>) is {gap_words(fv["gap_to_fair_pct"])}. See the Fair value page.</div>')
    return C.panel("WHAT IT MEANS FOR THE PRICE", body,
                   f'Based on {pi["n"]} marketing years, {y0}-{y1}; the supply gap explains {100 * pi["r2"]:.0f}% of the '
                   f'yearly price changes. A rough guide, not a price forecast.')


@st.cache_data(show_spinner=False, max_entries=64)
def _answer(question: str, key: str, asof) -> str:
    return answer_local(question, key, "Commodity", asof)


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
        st.markdown(chain_panel(key, asof), unsafe_allow_html=True)
        with st.container(key="glass_chart"):
            st.markdown('<div style="font-family:Space Grotesk,sans-serif;font-weight:700;font-size:20px">'
                        'Risk index and futures price, last 64 weeks</div>', unsafe_allow_html=True)
            st.plotly_chart(index_chart(key, asof), use_container_width=True, config={"displayModeBar": False},
                            key=f"chart_{key}", theme=None)
            st.markdown(f'<div style="font-size:15px;color:{T["frost_2"]};line-height:1.6">How to read it: the orange '
                        f'line rises when this season\'s weather points to less {m["label"].lower()} than usual for this time of year. '
                        f'The shaded band is the {m["main_country_name"]} critical window, when weather matters most '
                        f'for the harvest. The white line is the price, for comparison.</div>', unsafe_allow_html=True)
        st.markdown(comove_panel(key), unsafe_allow_html=True)
    with right:
        st.markdown(price_panel(key), unsafe_allow_html=True)
        with st.container(key="glass_gpt"):
            lab = m["label"].lower()
            st.markdown(f'<div class="hr-caps">ASK ABOUT {m["label"].upper()}</div><div style="font-size:15px;'
                        f'color:{T["frost_2"]};margin:6px 0 12px">The answer appears here, written by the local model from '
                        f'this page\'s figures. Free, no account. It can be wrong: check the figures. Not investment '
                        f'advice.</div>', unsafe_allow_html=True)
            qkey = f"ask_q_{key}"
            for i, q in enumerate([f"What drives the {lab} risk index today, and how much does it matter for the price?",
                                   f"Build a {lab} trade idea from this page: direction, entry logic, invalidation and risks.",
                                   f"Which country or weather factor could change the {lab} reading most in the coming weeks?"]):
                if st.button(q, key=f"askb_{key}_{i}", use_container_width=True):
                    st.session_state[qkey] = q
            with st.form(key=f"askf_{key}", clear_on_submit=True, border=False):
                own = st.text_input("Your question", placeholder="Ask about this page...", label_visibility="collapsed")
                if st.form_submit_button("Ask", use_container_width=True) and own.strip():
                    st.session_state[qkey] = own.strip()
            q = st.session_state.get(qkey)
            if q:
                st.markdown(f'<div class="hr-mono" style="font-size:13px;color:{T["muted"]};margin-top:6px">QUESTION</div>'
                            f'<div style="color:{T["frost"]};margin-bottom:6px">{H.escape(q)}</div>', unsafe_allow_html=True)
                if local_model_available():
                    with st.spinner("The local model is writing the answer (about 20 to 60 seconds on a laptop)..."):
                        ans = _answer(q, key, asof)
                    st.markdown(ans)
                else:
                    st.markdown(f'The local model is not installed (pip install -r requirements-llm.lock). '
                                f'[Ask ChatGPT in a new tab]({chatgpt_url(q, key, "Commodity", asof)}) instead.')
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
```

## 22. `src/harvestradar/app/views/common.py`

```python
"""Shared page pieces: the live ticker and navigation callbacks."""

from __future__ import annotations

import streamlit as st

from harvestradar.app import components as C
from harvestradar.app import data

CROPS = ("maize", "coffee", "cocoa")


def set_crop(key: str) -> None:
    st.session_state.crop = key
    st.session_state.q_country = None


def go(page: str, **kw) -> None:
    st.session_state.nav = page
    st.session_state.page = page
    for k, v in kw.items():
        st.session_state[k] = v


def ticker() -> None:
    """Three glass cards, one per commodity; clicking a card selects it."""
    m = data.meta()["commodities"]
    asof = st.session_state.asof
    cols = st.columns(3)
    for col, key in zip(cols, CROPS):
        c = m[key]
        r = data.latest_risk(key, asof)
        s = data.risk_series(key, 26, asof)
        val = data.fmt_signed(r.get("risk_z")) if r else "n/a"
        with col:
            st.markdown(C.ticker_card(c["display"], c["glyph"], val, s["risk_z"].tolist(),
                                      key == st.session_state.crop, bool(r) and r["risk_z"] >= 2),
                        unsafe_allow_html=True)
            st.button(f"Select {c['label']}", key=f"pick_{key}", on_click=set_crop, args=(key,),
                      use_container_width=True)


def source(text: str) -> str:
    return f'<div class="hr-source">{text}</div>'
```

## 23. `src/harvestradar/app/views/fair_value.py`

```python
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
    text = (f'<div style="font-size:15px;color:{T["frost_2"]};line-height:1.65;margin-top:12px">The index moves with the '
            f'weather: every day it reads heat, rain and soil moisture where {m["label"].lower()} grows, turns them into a '
            f'harvest forecast for each producing country and adds them up into the world supply gap. The price only '
            f'follows when that gap matters for the market: prices also move with demand, stocks, the dollar, fund '
            f'positions, other origins and the official crop reports, and traders often price a weather scare before it '
            f'reaches the harvest forecasts. So the two lines can diverge for weeks. The climate fair value is the last '
            f'step: the price that the weather-driven supply gap justifies.</div>')
    return C.panel("WHY THE INDEX AND THE PRICE DO NOT MOVE TOGETHER", tiles + text,
                   f'Correlations, weekly data since {cm["from"][:4]} ({cm["weeks"]} weeks). 0 means no link, 1 means '
                   f'the two move as one.')


def chain_panel(key: str, asof) -> str:
    """From weather to price: the four steps behind every reading, with today's values."""
    m = data.meta()["commodities"][key]
    r = data.latest_risk(key, asof)
    pi = data.jsonfile("price_impact.json")
    imp, fv = pi.get("commodities", {}).get(key), pi.get("fair_value", {}).get(key)
    dk = data.stress(key).dekad_end.max()
    regions = " and ".join(data.top_regions(key, dk, 2).adm1_name.tolist())
    top = r["contributors"][0] if r["contributors"] else None

    def step(n, title, big, sub):
        return (f'<div style="flex:1;min-width:150px;padding:12px 14px;border:1px solid {T["line"]};border-radius:12px;'
                f'background:rgba(11,15,20,.35)"><div class="hr-caps">{n} &middot; {title}</div><div class="hr-mono" '
                f'style="font-size:24px;color:{T["frost"]};margin-top:6px">{big}</div><div style="font-size:14px;'
                f'color:{T["frost_2"]};line-height:1.5;margin-top:4px">{sub}</div></div>')
    price = f'{imp["implied_pct"]:+.1f}%' if imp and imp["reliable"] else "n/a"
    steps = [step("1", "WEATHER", f"10 days to {dk.day} {dk:%b}", f"Most stressed producing regions: {H.escape(regions)}."),
             step("2", "HARVEST", f"{r['delta_prod_pct']:+.2f}%", "Expected world supply vs normal"
                  + (f", led by {H.escape(top['name'])} ({top['contrib_pct']:+.2f} points)." if top else ".")),
             step("3", "RISK INDEX", f"{r['risk_z']:+.2f}", "How unusual this supply gap is for the time of year (+2 = rare)."),
             step("4", "PRICE", price, ("No reliable link between world supply and the price. " if imp and not imp["reliable"] else "")
                  + (f"Climate fair value {fmt(key, fv['fair'])}; last close {fmt(key, fv['close'])}."
                                        if fv else "Expected move over the marketing year."))]
    return C.panel(f"FROM WEATHER TO PRICE, {m['label'].upper()} TODAY",
                   f'<div style="display:flex;flex-wrap:wrap;gap:10px">{"".join(steps)}</div>',
                   "Every working day: new weather from NASA, harvest forecasts from the model, then the measured price reaction.")


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
```

## 24. `src/harvestradar/app/views/method.py`

```python
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
```

## 25. `src/harvestradar/app/views/replay.py`

```python
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
    # every region that intersects the view is drawn (neighbours give context), nothing else
    from shapely.geometry import box

    view = box(vb[0] * 1000, -(vb[1] + vb[3]) * 1000, (vb[0] + vb[2]) * 1000, -vb[1] * 1000)
    g = g[g.geometry.intersects(view)].reset_index(drop=True)
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
            chips.append(C.chip(f"THE MODEL ONLY KNEW HARVESTS UP TO {ev['model_trained_on_seasons_up_to']}", True))
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
           f"· {m['display']}", "labelWord": "", "rangeLabel": f"{dates[0]:%b %Y} · {dates[-1]:%b %Y}".upper(),
           "capture": st.session_state.capture, "autoplay": playing,
           "ariaLabel": f"Episode replay {ev['label']}", "borderWidth": 0.8}
    with left:
        st.iframe(maps.map_html(cfg, MAP_H, "episode"), height=MAP_H)
        base = data.meta()["climatology_base"]
        st.markdown(f'<div class="hr-source">Stress every 10 days, compared with {base[0]}-{base[1]}. Press play, '
                    f'or use the arrow keys to step.</div>', unsafe_allow_html=True)
    with right:
        def long(d):
            t = pd.Timestamp(d)
            return f"{t.day} {t:%B %Y}"
        if ev.get("first_above_2"):
            big, cap = long(ev["first_above_2"]), ev.get("lead_text", "")
            if ev.get("verdict") == "late":
                cap = f"after the price had already peaked on {long(ev.get('price_max_date'))}: too late"
            title = "INDEX FIRST ABOVE +2"
            border = "border-color:rgba(255,181,71,.75);box-shadow:0 0 30px rgba(255,181,71,.15), 0 20px 60px rgba(0,0,0,.35);"
        else:
            big = f"{ev['peak_risk_z']:+.2f}" if ev.get("peak_risk_z") is not None else "n/a"
            cap = f"on {long(ev.get('peak_date'))}: it never went above +2, the episode was missed"
            title = "HIGHEST INDEX IN THE EPISODE"
            border = ""
        st.markdown(f'<div class="hr-glass" style="height:190px;padding:22px 26px;{border}">'
                    f'<div class="hr-caps">{title}</div>'
                    f'<div class="hr-mono hr-glow" style="font-size:46px;line-height:1.15;color:{T["signal"]};'
                    f'margin-top:10px">{big}</div><div style="font-size:17px;color:{T["frost_2"]}">{cap}</div>'
                    f'<div class="hr-source" style="margin-top:6px">Weekly index during the episode.</div></div>',
                    unsafe_allow_html=True)
        with st.container(key="glass_path"):
            st.markdown(f'<div class="hr-caps" style="padding-top:6px">RISK INDEX, {pd.Timestamp(ev["start"]).year}'
                        f'{"-" + str(pd.Timestamp(ev["end"]).year) if pd.Timestamp(ev["end"]).year != pd.Timestamp(ev["start"]).year else ""}'
                        f'</div>', unsafe_allow_html=True)
            st.plotly_chart(path_chart(ev), use_container_width=True, config={"displayModeBar": False},
                            key=f"path_{name}", theme=None)
        p0, p1, ch = ev.get("price_from"), ev.get("price_to"), ev.get("price_change_pct")
        fmt = (lambda x: f"{x:,.0f}") if key == "cocoa" else (lambda x: f"{x:,.2f}".rstrip("0").rstrip("."))
        pi = data.jsonfile("price_impact.json").get("episodes", {}).get(name)
        exp = ""
        if pi:
            exp = (f'<div style="font-size:16px;color:{T["frost_2"]};margin-top:10px;line-height:1.6">Expected from the '
                   f'supply gap the model saw on {long(pi["date"])}: <span class="hr-mono">{pi["implied_pct"]:+.1f}%</span> '
                   f'(likely {pi["low_pct"]:+.1f}% to {pi["high_pct"]:+.1f}%) over the marketing year.</div>'
                   if pi["reliable"] else
                   f'<div style="font-size:16px;color:{T["frost_2"]};margin-top:10px">No reliable supply-price link for '
                   f'this crop, so no expected move is shown.</div>')
        if p0 and p1:
            frm = "from the signal" if ev.get("price_from_kind") == "signal" else "from the start of the episode"
            st.markdown(f'<div class="hr-glass" style="padding:20px 26px">'
                        f'<div class="hr-caps">{m["price_label"]}</div><div style="font-size:14px;color:{T["muted"]}">'
                        f'{frm}, {long(ev["price_from_date"])} to {long(ev["price_to_date"])}</div>'
                        f'<div style="display:flex;align-items:baseline;gap:16px;margin-top:12px">'
                        f'<span class="hr-mono" style="font-size:34px;color:{T["frost_2"]}">{fmt(p0)}</span>'
                        f'<span style="color:{T["muted"]};font-size:17px">to</span>'
                        f'<span class="hr-mono" style="font-size:40px;color:{T["heat"] if ch and ch > 0 else T["frost"]}">{fmt(p1)}</span>'
                        f'<span class="hr-mono" style="font-size:22px;color:{T["heat"] if ch and ch > 0 else T["frost_2"]}">{ch:+.1f}%</span></div>'
                        + exp + f'<div class="hr-source">{m["price_unit"][:1].upper() + m["price_unit"][1:]}'
                        + (f'. Highest price of the episode: {fmt(ev["price_max"])} on {long(ev["price_max_date"])}'
                           if ev.get("price_max") else "")
                        + '.</div></div>', unsafe_allow_html=True)
```

## 26. `src/harvestradar/app/views/stress_map.py`

```python
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
    wd = data.world()
    w = maps.project(wd[wd["iso3"] != "ATA"], tol_m=8000)
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
           "frames": frames, "start": start, "ringRadius": 230, "labelPrefix": "STRESS VS NORMAL", "labelWord": "",
           "rangeLabel": rng, "capture": st.session_state.capture,
           "autoplay": st.session_state.get("q_play") == "1",
           "ariaLabel": f"{m['label']} stress map, dekad {frames[start]['label']} {dekad.year}"}
    with left:
        st.iframe(maps.map_html(cfg, MAP_H, "world"), height=MAP_H)
        base = data.meta()["climatology_base"]
        st.markdown(f'<div class="hr-source">{m["label"]}: {m["regions"]} producing regions, '
                    f'{100 * m["coverage"]:.0f}% of world output (MapSPAM 2020). Stress combines heat, rainfall and '
                    f'soil moisture, compared with the same 10 days in {base[0]}-{base[1]}. Weather: NASA POWER.</div>',
                    unsafe_allow_html=True)
    with right:
        top = data.top_regions(key, dekad, 5)
        best = float(top["score"].max()) if len(top) and top["score"].max() > 0 else 1.0
        rows = [{"rank": i + 1, "name": r.adm1_name, "iso": r.country_name,
                 "frac": max(0.0, float(r.score) / best), "hot": i == 0 and r.stress >= 2}
                for i, r in enumerate(top.itertuples())]
        st.markdown(C.panel("MOST STRESSED REGIONS, WEIGHTED BY OUTPUT", C.ranking_rows(rows, m["glyph"]),
                            f"10 days to {dekad.day} {dekad:%B %Y}. Ranked by stress times the region's share of "
                            f"world output.", height=356), unsafe_allow_html=True)
        o = data.oni_latest(st.session_state.asof)
        if o:
            period = o["label"].replace("-", " to ").title().replace(" To ", " to ")
            st.markdown(C.climate_card(f"{o['value']:+.2f}", period, o["series"],
                                       f"NOAA Oceanic Niño Index, published {o['available_at']}. Shown for context: "
                                       f"it is not part of the index.", data.oni_strength(o["value"])),
                        unsafe_allow_html=True)
        n = data.notes()
        if len(n):
            wk = n[n.week <= st.session_state.asof]
            last = wk[wk.week == wk.week.max()] if len(wk) else n.iloc[0:0]
            row = last[last.commodity == key]
            if len(row):
                r = row.iloc[0]
                passed = int(r.numbers_ok) + int(r.get("context_ok", False)) + int(r.get("claims_ok", False))
                st.markdown(C.note_ready(passed, 3, "Today's note is ready"), unsafe_allow_html=True)
                st.button("Open today's note", key="pick_note", on_click=go, args=("note",),
                          use_container_width=True)
```

## 27. `src/harvestradar/app/views/weekly_note.py`

```python
"""Daily note page: inbox of notes, the selected note with figure pills (from its own payload), the three
checks and the data given to the model."""

from __future__ import annotations

import html as H
import json

import pandas as pd
import streamlit as st

from harvestradar.app import components as C
from harvestradar.app import data
from harvestradar.app.theme import T
from harvestradar.app.views.common import go
from harvestradar.report.checks import SLOT_RE, split_figure

ORDER = {"maize": 0, "coffee": 1, "cocoa": 2}


def body_html(template: str, payload: dict) -> str:
    paras = []
    for para in [p for p in template.split("\n\n") if p.strip()]:
        out, last = [], 0
        for m in SLOT_RE.finditer(para):
            out.append(H.escape(para[last:m.start()]))
            s = payload["slots"].get(m.group(1))
            if s is None:
                out.append(H.escape(m.group(0)))
            elif s["kind"] == "figure":
                pre, fig, rest = split_figure(s["text"])
                pill = (f'<span class="hr-pill" title="{H.escape(s["source"])} · {H.escape(s["date"])}">'
                        f'{H.escape(fig)}</span>' if fig else "")
                out.append(H.escape(pre) + pill + H.escape(rest))
            else:
                out.append(f'<span style="color:{T["frost"]};font-weight:600">{H.escape(s["text"])}</span>')
            last = m.end()
        out.append(H.escape(para[last:]))
        paras.append(f'<p style="font-size:18px;line-height:1.75;color:{T["frost_2"]};margin:0 0 14px 0">{"".join(out)}</p>')
    return "".join(paras)


def _select(k: str) -> None:
    st.session_state.note_sel = k


def render() -> None:
    n = data.notes()
    if n.empty:
        st.info("notes.parquet is missing from data/demo: run `harvestradar report notes`.")
        return
    n = n[n.week <= st.session_state.asof]
    weeks = sorted(n.week.unique(), reverse=True)
    q = st.session_state.get("q_week")
    if "note_sel" not in st.session_state:
        wk = pd.Timestamp(q) if q else weeks[0]
        st.session_state.note_sel = f"{pd.Timestamp(wk):%Y-%m-%d}|{st.session_state.crop}"
    left, right = st.columns([0.29, 0.71])
    with left:
        st.markdown('<div style="display:flex;justify-content:space-between;align-items:baseline;margin:4px 4px 6px 4px">'
                    '<span style="font-family:Space Grotesk,sans-serif;font-weight:700;font-size:28px">Inbox</span>'
                    '<span class="hr-caps">EVERY WORKING DAY, 07:00</span></div>', unsafe_allow_html=True)
        for wk in weeks:
            rows = n[n.week == wk].sort_values("commodity", key=lambda s: s.map(ORDER))
            for r in rows.itertuples():
                k = f"{pd.Timestamp(wk):%Y-%m-%d}|{r.commodity}"
                active = st.session_state.note_sel == k
                tp = int(getattr(r, "template_paragraphs", 0) or 0)
                label = ("Fixed template" if r.model == "deterministic-template"
                         else (f"{tp} of 3 paragraphs from the template" if tp else "Written by the AI model"))
                bg = "background:rgba(255,181,71,.08);border-color:rgba(255,181,71,.6);" if active else ""
                gk = data.meta()["commodities"][r.commodity]["glyph"]
                st.markdown(
                    f'<div class="hr-glass" style="height:64px;padding:10px 14px;display:flex;gap:12px;align-items:center;'
                    f'border-radius:14px;{bg}">{C.glyph(gk, 22, T["frost_2"])}<div style="flex:1;min-width:0">'
                    f'<div style="display:flex;justify-content:space-between;gap:8px"><span style="font-weight:600;'
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{H.escape(r.title)}</span>'
                    f'<span class="hr-mono" style="font-size:13px;color:{T["muted"]};flex:none">07:00</span></div>'
                    f'<div style="font-size:13px;color:{T["muted"]};margin-top:2px">{label}</div></div></div>',
                    unsafe_allow_html=True)
                st.button(f"Open {r.title}", key=f"pickn_{k}", on_click=_select, args=(k,), use_container_width=True)
    wk_s, key = st.session_state.note_sel.split("|")
    sel = n[(n.week == pd.Timestamp(wk_s)) & (n.commodity == key)]
    if sel.empty:
        sel = n[n.week == weeks[0]].head(1)
    row = sel.iloc[0]
    p = json.loads(row.payload)
    m = data.meta()
    with right:
        with st.container(key="glass_note"):
            st.markdown(
                f'<div style="display:flex;gap:16px;align-items:center;margin-bottom:18px;min-height:64px">'
                f'<span style="border-radius:12px;overflow:hidden;display:inline-flex;flex:none">{C.mark_on_signal(52)}</span>'
                f'<div><div style="font-family:Space Grotesk,sans-serif;font-weight:700;font-size:30px;line-height:1.15">'
                f'{H.escape(row.title)}</div><div style="font-size:16px;color:{T["muted"]}">HarvestRadar Daily &middot; '
                f'{pd.Timestamp(p["week"]).day} {pd.Timestamp(p["week"]):%B %Y}</div></div></div>',
                unsafe_allow_html=True)
            d0 = pd.Timestamp(p["week"])
            day_txt = f"{d0.day} {d0:%B %Y}".upper()
            st.markdown(f'<div class="hr-caps" style="margin-bottom:4px">RISK INDEX ON {day_txt}</div>',
                        unsafe_allow_html=True)
            cols = st.columns(3)
            for col, (k2, rd) in zip(cols, p.get("readings", {}).items()):
                s = data.risk_series(k2, 26, pd.Timestamp(rd["date"]))
                with col:
                    st.markdown(C.ticker_card(rd["display"], rd["glyph"], rd["text"], s["risk_z"].tolist(), k2 == key,
                                              rd["value"] >= 2, spark_w=96, suffix=""), unsafe_allow_html=True)
            st.markdown(f'<div style="margin-top:10px">{body_html(row.template, p)}</div>', unsafe_allow_html=True)
            checks = (C.badge("Numbers checked", bool(row.numbers_ok)) + C.badge("Context checked", bool(row.context_ok))
                      + C.badge("Claims checked", bool(row.claims_ok)))
            tp = int(row.get("template_paragraphs", 0) or 0)
            who = ("Written from the fixed template (the AI model failed the checks)"
                   if row.model == "deterministic-template"
                   else f"Written by a small AI model running locally ({m['llm']['display_name']})"
                   + (f"; {tp} of 3 paragraphs from the fixed template" if tp else ""))
            st.markdown(f'<div style="display:flex;flex-wrap:wrap;align-items:center">{checks}'
                        f'<span class="hr-mono" style="font-size:13px;color:{T["muted"]};margin-left:6px">{who}'
                        f'. Every figure is inserted by the software, with its source.</span></div>', unsafe_allow_html=True)
            b1, _ = st.columns([0.2, 0.8])
            with b1:
                st.button("Open the map", key="open_map", on_click=go, args=("stress",),
                          kwargs={"crop": key}, use_container_width=True)
        with st.expander("Data given to the model", expanded=st.session_state.get("q_data") == "1"):
            figs = [(k, s) for k, s in p["slots"].items() if s["kind"] == "figure"]
            cards = "".join(
                f'<div class="hr-glass" style="padding:14px 16px"><div class="hr-mono" style="font-size:24px;'
                f'color:{T["signal"]}">{H.escape(s["text"])}</div><div style="font-size:15px;color:{T["frost_2"]};'
                f'margin-top:4px">{H.escape(s["label"])}</div><div class="hr-source" style="margin-top:6px">source '
                f'&middot; {H.escape(s["source"])}<br>{H.escape(s["date"])} &middot; {H.escape(s.get("detail", ""))}</div></div>'
                for _, s in figs)
            st.markdown(f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px">{cards}</div>'
                        f'<div class="hr-source">INSERTED BY SOFTWARE, WITH SOURCE &middot; notes.parquet payload '
                        f'&middot; generated in {row.seconds:.0f} s, {int(row.attempts)} model attempt(s)</div>',
                        unsafe_allow_html=True)
```

## 28. `src/harvestradar/cli.py`

```python
"""HarvestRadar command line: `harvestradar <group> <command>`."""

from __future__ import annotations

import typer

app = typer.Typer(help="HarvestRadar: harvest-risk index for agricultural commodities.", no_args_is_help=True)
data_app = typer.Typer(help="Download sources (network).", no_args_is_help=True)
regions_app = typer.Typer(help="Producing regions and weights.", no_args_is_help=True)
features_app = typer.Typer(help="Stress variables and model features.", no_args_is_help=True)
model_app = typer.Typer(help="Yield model, validation, SHAP.", no_args_is_help=True)
index_app = typer.Typer(help="Risk index, episodes, backtest.", no_args_is_help=True)
report_app = typer.Typer(help="Daily notes and email export.", no_args_is_help=True)
demo_app = typer.Typer(help="Demo snapshot for the offline app.", no_args_is_help=True)
for name, sub in [("data", data_app), ("regions", regions_app), ("features", features_app),
                  ("model", model_app), ("index", index_app), ("report", report_app), ("demo", demo_app)]:
    app.add_typer(sub, name=name)


def _cfg():
    from harvestradar.config import get_config
    from harvestradar.paths import ensure_dirs

    ensure_dirs()
    return get_config()


@data_app.command("fao")
def data_fao() -> None:
    """FAOSTAT QCL production, area and yield."""
    from harvestradar.ingest.yields import load_faostat

    load_faostat(_cfg())


@data_app.command("oni")
def data_oni() -> None:
    """NOAA CPC Oceanic Nino Index."""
    from harvestradar.ingest.enso import fetch_oni

    fetch_oni()


@data_app.command("prices")
def data_prices() -> None:
    """Front-month futures via yfinance."""
    from harvestradar.ingest.prices import fetch_prices

    fetch_prices(_cfg())


@data_app.command("weather")
def data_weather(workers: int = 4, refresh: bool = False) -> None:
    """NASA POWER daily data for every sampled grid cell."""
    import pandas as pd

    from harvestradar.ingest.power import fetch_cells
    from harvestradar.paths import PROCESSED

    cfg = _cfg()
    cells = pd.read_parquet(PROCESSED / "sample_cells.parquet").drop_duplicates("cell_id")
    n = fetch_cells(cells, cfg.weather_start.isoformat(), cfg.as_of_end.isoformat(), workers, refresh)
    typer.echo(f"fetched {n} cells")


@regions_app.command("build")
def regions_build() -> None:
    """MapSPAM 2020 x geoBoundaries ADM1 -> regions, weights, sample cells."""
    from harvestradar.geo.regions import build_all

    build_all(_cfg())


@features_app.command("build")
def features_build() -> None:
    """Region daily series, dekad stress (map) and country-season features (model)."""
    from harvestradar.pipeline import build_features

    build_features(_cfg())


@model_app.command("train")
def model_train() -> None:
    """Rolling-origin vintages, predictions, evaluation and SHAP."""
    from harvestradar.pipeline import train_models

    train_models(_cfg())


@index_app.command("build")
def index_build() -> None:
    """Weekly risk index, episodes and backtest."""
    from harvestradar.pipeline import build_index

    build_index(_cfg())


@index_app.command("daily")
def index_daily() -> None:
    """Index every working day since dates.daily_start, and the implied price reaction."""
    from harvestradar.pipeline import build_daily

    build_daily(_cfg())


@index_app.command("price")
def index_price() -> None:
    """Price reaction, climate fair value and index-price co-movement (fast; run after each data update)."""
    from harvestradar.pipeline import build_price_layers

    build_price_layers(_cfg())


@report_app.command("notes")
def report_notes(days: int = typer.Option(None, help="Number of latest working days"),
                 deterministic: bool = typer.Option(False, help="Skip the LLM, use the template"),
                 commodity: list[str] = typer.Option(None, help="Regenerate only these commodities")) -> None:
    """Daily notes (local Hugging Face model, guarded by number and claim checks)."""
    from harvestradar.report.weekly_note import build_notes

    build_notes(_cfg(), days=days, deterministic=deterministic, only=commodity or None)


@report_app.command("email")
def report_email(week: str = typer.Option("latest", help="'latest' or a date YYYY-MM-DD (the note's day)"),
                 out_dir: str = typer.Option("reports/notes", help="Output directory")) -> None:
    """Write the latest daily notes as .eml and .html (offline: nothing is sent)."""
    from pathlib import Path

    from harvestradar.report.email_note import export_week

    for p in export_week(week, Path(out_dir)):
        typer.echo(str(p))


@demo_app.command("export")
def demo_export() -> None:
    """Write the offline snapshot used by the app to data/demo/."""
    from harvestradar.demo.export import export_demo

    export_demo(_cfg())


@app.command("update")
def update(date: str = typer.Option(None, help="Data as of YYYY-MM-DD (default: today if a working day, UTC)"),
           deterministic_notes: bool = typer.Option(False, help="Skip the LLM, write the notes from the template"),
           skip_weather: bool = typer.Option(False, help="Do not call NASA POWER (tests)")) -> None:
    """Daily incremental update: new data only, then index, fair value, notes and data/demo."""
    import datetime as dt

    from harvestradar.update import run_update

    run_update(_cfg(), dt.date.fromisoformat(date) if date else None, deterministic_notes, skip_weather)


@app.command("all")
def run_all(skip_download: bool = False, deterministic_notes: bool = False) -> None:
    """Run the full pipeline."""
    from harvestradar.pipeline import run_all as _run

    _run(_cfg(), skip_download=skip_download, deterministic_notes=deterministic_notes)


if __name__ == "__main__":
    app()
```

## 29. `src/harvestradar/config.py`

```python
"""Configuration: commodities.yaml and settings.yaml validated with pydantic."""

from __future__ import annotations

import datetime as dt
import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

from harvestradar.paths import CONFIG_DIR


class Window(BaseModel):
    start: str
    end: str
    stage: str
    year_offset: int = 0

    @field_validator("start", "end")
    @classmethod
    def _mmdd(cls, v: str) -> str:
        m, d = v.split("-")
        dt.date(2001, int(m), int(d))  # raises on invalid dates (29 Feb is not allowed)
        return v

    def dates(self, season: int) -> tuple[dt.date, dt.date]:
        """Calendar start and end of this window for a season (harvest) year."""
        y = season + self.year_offset
        sm, sd = (int(x) for x in self.start.split("-"))
        em, ed = (int(x) for x in self.end.split("-"))
        start = dt.date(y, sm, sd)
        end = dt.date(y, em, ed)
        if end < start:
            end = dt.date(y + 1, em, ed)
        return start, end


class Commodity(BaseModel):
    key: str = ""
    label: str
    display: str
    glyph: str
    spam_crop: str
    fao_item: int
    tickers: dict[str, str]
    price_label: str
    price_name: str
    price_unit: str
    coverage: float = Field(0.90, gt=0, le=1)
    weight_mode: str = "production"
    target: str = "yield"
    share_source: str = "fao"
    thresholds: dict[str, float]
    main_country: str
    windows: dict[str, list[Window]]

    @field_validator("weight_mode")
    @classmethod
    def _mode(cls, v: str) -> str:
        if v not in {"production", "exports"}:
            raise ValueError("weight_mode must be 'production' or 'exports'")
        return v

    @property
    def ticker(self) -> str:
        return next(iter(self.tickers.values()))

    @property
    def countries(self) -> list[str]:
        return list(self.windows)

    def season_span(self, country: str, season: int) -> tuple[dt.date, dt.date]:
        ds = [w.dates(season) for w in self.windows[country]]
        return min(d[0] for d in ds), max(d[1] for d in ds)


class Settings(BaseModel):
    paths: dict[str, str]
    seed: int
    dates: dict[str, str | int]
    climatology: dict
    regions: dict
    targets: dict
    features: dict
    model: dict
    index: dict
    backtest: dict
    llm: dict
    episodes: dict[str, dict]
    commodities: dict[str, Commodity] = {}

    @property
    def as_of_end(self) -> dt.date:
        """Last day of data. HARVESTRADAR_AS_OF_END (YYYY-MM-DD) overrides settings.yaml: the daily job sets it."""
        env = os.environ.get("HARVESTRADAR_AS_OF_END")
        return dt.date.fromisoformat(env or str(self.dates["as_of_end"]))

    @property
    def index_start(self) -> dt.date:
        return dt.date.fromisoformat(str(self.dates["index_start"]))

    @property
    def weather_start(self) -> dt.date:
        return dt.date.fromisoformat(str(self.dates["weather_start"]))

    @property
    def lag_days(self) -> int:
        return int(self.dates["publication_lag_days"])


def load_config(config_dir: str | Path | None = None) -> Settings:
    d = Path(config_dir) if config_dir else CONFIG_DIR
    with open(d / "settings.yaml", encoding="utf-8") as f:
        s = yaml.safe_load(f)
    with open(d / "commodities.yaml", encoding="utf-8") as f:
        c = yaml.safe_load(f)
    s["commodities"] = {k: Commodity(key=k, **v) for k, v in c.items()}
    return Settings(**s)


@lru_cache(maxsize=1)
def get_config() -> Settings:
    return load_config()
```

## 30. `src/harvestradar/demo/__init__.py`

```python

```

## 31. `src/harvestradar/demo/export.py`

```python
"""Write the offline snapshot read by the app (data/demo, versioned, < 50 MB)."""

from __future__ import annotations

import json
import shutil

import geopandas as gpd
import pandas as pd

from harvestradar.config import Settings
from harvestradar.ingest.manifest import download, record
from harvestradar.paths import DEMO, PROCESSED, RAW
from harvestradar.signal.risk_index import country_name

NE_URL = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"


def _world_110m() -> None:
    dest = DEMO / "world_110m.geojson"
    if dest.exists():
        return
    z = RAW / "naturalearth" / "ne_110m_admin_0_countries.zip"
    if not z.exists():
        download(NE_URL, z)
        record(z, "Natural Earth 1:110m admin 0 countries", NE_URL, "Public domain")
    g = gpd.read_file(f"zip://{z}")
    g = g[["ISO_A3", "NAME", "geometry"]].rename(columns={"ISO_A3": "iso3", "NAME": "name"})
    g.to_file(dest, driver="GeoJSON", COORDINATE_PRECISION=3)


def export_demo(cfg: Settings) -> None:
    DEMO.mkdir(parents=True, exist_ok=True)
    start = pd.Timestamp(cfg.index_start)
    risk = pd.read_parquet(PROCESSED / "risk_index.parquet")
    risk.to_parquet(DEMO / "risk_index.parquet", index=False)
    daily = pd.read_parquet(PROCESSED / "risk_index_daily.parquet")
    daily.drop(columns=["contributors_all"]).to_parquet(DEMO / "risk_index_daily.parquet", index=False)
    preds = pd.read_parquet(PROCESSED / "predictions_weekly.parquet")
    preds = preds[preds.as_of >= start].rename(columns={"as_of": "date"})
    preds[["commodity", "country_iso3", "season", "date", "pred_anom", "pred_lo", "pred_hi", "window_open",
           "progress", "vintage"]].to_parquet(DEMO / "predictions.parquet", index=False)
    shutil.copy(PROCESSED / "shap_latest.parquet", DEMO / "shap_latest.parquet")
    shutil.copy(PROCESSED / "oni.parquet", DEMO / "oni.parquet")
    if (PROCESSED / "notes.parquet").exists():
        shutil.copy(PROCESSED / "notes.parquet", DEMO / "notes.parquet")
    if (PROCESSED / "fair_value_daily.parquet").exists():
        fv = pd.read_parquet(PROCESSED / "fair_value_daily.parquet")
        fv[fv.date >= "2006-01-01"].round(4).to_parquet(DEMO / "fair_value_daily.parquet", index=False)
    for name in ["events.json", "model_eval.json", "backtest.json", "price_impact.json"]:
        shutil.copy(PROCESSED / name, DEMO / name)
    summary = json.loads((PROCESSED / "regions_summary.json").read_text())
    meta = {"as_of": cfg.as_of_end.isoformat(), "index_start": cfg.index_start.isoformat(),
            "climatology_base": cfg.climatology["base"], "weather": "NASA POWER daily (MERRA-2), since 1981",
            "cells": summary.get("cells"), "llm": {"model_id": cfg.llm["model_id"],
                                                   "display_name": cfg.llm["display_name"]},
            "commodities": {}}
    for key, c in cfg.commodities.items():
        st = pd.read_parquet(PROCESSED / f"stress_{key}.parquet")
        st = st[st.dekad_end >= start]
        st[["region_id", "dekad_end", "stress", "hdd_z", "precip_z", "sm_root_z", "tmax_z", "tmax"]].to_parquet(
            DEMO / f"stress_{key}.parquet", index=False)
        g = gpd.read_file(PROCESSED / f"regions_{key}.gpkg")
        g["geometry"] = g.geometry.simplify(0.02, preserve_topology=True)
        g["country_name"] = g["country_iso3"].map(country_name)
        g[["region_id", "country_iso3", "country_name", "adm1_name", "weight", "world_share", "lat", "lon",
           "geometry"]].to_file(DEMO / f"regions_{key}.geojson", driver="GeoJSON", COORDINATE_PRECISION=3)
        pr = pd.read_parquet(PROCESSED / f"prices_{key}.parquet")
        pr[["date", "close"]].to_parquet(DEMO / f"prices_{key}.parquet", index=False)
        r = risk[(risk.commodity == key) & (risk.date >= start)].dropna(subset=["risk_z"])
        meta["commodities"][key] = {
            "label": c.label, "display": c.display, "glyph": c.glyph, "ticker": c.ticker,
            "price_label": c.price_label, "price_name": c.price_name, "price_unit": c.price_unit,
            "main_country": c.main_country, "main_country_name": country_name(c.main_country),
            "target": c.target, "share_source": c.share_source,
            "windows": {k: [w.model_dump() for w in v] for k, v in c.windows.items()},
            "country_names": {k: country_name(k) for k in c.windows},
            "regions": summary.get(key, {}).get("regions"), "coverage": summary.get(key, {}).get("coverage"),
            "weeks": int(len(r)), "weeks_above_2_pct": round(100 * float((r.risk_z >= 2).mean()), 1),
            "latest_dekad_end": pd.Timestamp(st.dekad_end.max()).strftime("%Y-%m-%d"),
        }
    (DEMO / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    _world_110m()
    size = sum(p.stat().st_size for p in DEMO.glob("*")) / 1e6
    print(f"[demo] snapshot written to {DEMO} ({size:.1f} MB)")
```

## 32. `src/harvestradar/features/__init__.py`

```python

```

## 33. `src/harvestradar/features/aggregate.py`

```python
"""Aggregation: grid cells -> regions -> countries, dekads, and country-season features "as of" a date.

Leak-free by construction: a feature computed for date t only uses weather up to t - publication lag,
and every anomaly is measured against the same calendar span in strictly earlier years (expanding
climatology, at least `min_years`).
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from harvestradar.config import Commodity, Settings
from harvestradar.features.stress import frost_days, hargreaves_et0, heat_degree_days
from harvestradar.features.windows import active_season, season_switch

VARS = ["tmax_c", "tmin_c", "precip_mm", "sm_root", "sm_top", "et0_mm"]
FEATURES = ["hdd_z", "tmax_z", "precip_z", "sm_root_z", "sm_pre_z", "et_z", "frost_z",
            "oni", "anom_last", "progress"]


def region_daily(cells_w: pd.DataFrame, cell_data: pd.DataFrame) -> pd.DataFrame:
    """Weighted mean of cell series per region. cells_w: region_id, cell_id, lat, cell_weight."""
    d = cell_data.copy()
    lat = d["cell_id"].str.slice(0, 7).astype(float)
    d["et0_mm"] = hargreaves_et0(d["tmax_c"].to_numpy(), d["tmin_c"].to_numpy(), lat.to_numpy(),
                                 d["date"].dt.day_of_year.to_numpy())
    m = cells_w[["region_id", "cell_id", "cell_weight"]].merge(d, on="cell_id")
    num = m[VARS].mul(m["cell_weight"], axis=0)
    num[["region_id", "date"]] = m[["region_id", "date"]]
    den = m[VARS].notna().mul(m["cell_weight"], axis=0)
    den[["region_id", "date"]] = m[["region_id", "date"]]
    s = num.groupby(["region_id", "date"])[VARS].sum(min_count=1)
    w = den.groupby(["region_id", "date"])[VARS].sum()
    out = (s / w.replace(0, np.nan)).reset_index()
    return out


def country_daily(regions: pd.DataFrame, rdaily: pd.DataFrame) -> pd.DataFrame:
    """Production-weighted mean of region series per country (weights renormalised in each country)."""
    r = regions[["region_id", "country_iso3", "weight"]].copy()
    r["w"] = r["weight"] / r.groupby("country_iso3")["weight"].transform("sum")
    m = rdaily.merge(r[["region_id", "country_iso3", "w"]], on="region_id")
    num = m[VARS].mul(m["w"], axis=0)
    num[["country_iso3", "date"]] = m[["country_iso3", "date"]]
    den = m[VARS].notna().mul(m["w"], axis=0)
    den[["country_iso3", "date"]] = m[["country_iso3", "date"]]
    s = num.groupby(["country_iso3", "date"])[VARS].sum(min_count=1)
    w = den.groupby(["country_iso3", "date"])[VARS].sum()
    return (s / w.replace(0, np.nan)).reset_index()


class SeasonCube:
    """Daily country series laid out as (season year x day offset), aligned on each season's first
    window day, so that "the same calendar span in earlier years" is a column slice."""

    def __init__(self, c: Commodity, country: str, daily: pd.DataFrame, cfg: Settings):
        self.c, self.country = c, country
        self.pre = int(cfg.features["pre_window_days"])
        self.tail = int(cfg.features["tail_days"])
        self.min_years = int(cfg.climatology["min_years_expanding"])
        heat, frost = c.thresholds.get("heat_c", 30.0), c.thresholds.get("frost_c", 0.0)
        s = daily.set_index("date").sort_index()
        s = s[~s.index.duplicated()]
        self.first_year = s.index.min().year
        self.last_date = s.index.max().date()
        years = list(range(self.first_year, self.last_date.year + 3))
        spans = {y: c.season_span(country, y) for y in years}
        lengths = [(spans[y][1] - spans[y][0]).days + 1 for y in years]
        self.lead = 400  # days before the first window kept in the cube (covers the whole season)
        self.width = self.lead + max(lengths) + self.tail + 5
        self.years = years
        self.start = {y: spans[y][0] for y in years}
        idx = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=800))
        s = s.reindex(idx)
        variables = {
            "hdd": heat_degree_days(s["tmax_c"], heat),
            "tmax": s["tmax_c"],
            "precip": s["precip_mm"],
            "sm": s["sm_root"],
            "et": s["et0_mm"],
            "frost": frost_days(s["tmin_c"], frost).where(s["tmin_c"].notna()),
        }
        ny = len(years)
        self.data = {k: np.full((ny, self.width), np.nan) for k in variables}
        self.mask = np.zeros((ny, self.width), dtype=bool)
        base = idx[0].date()
        for i, y in enumerate(years):
            o0 = (self.start[y] - dt.timedelta(days=self.lead) - base).days
            lo, hi = max(o0, 0), min(o0 + self.width, len(idx))
            if hi <= lo:
                continue
            for k, v in variables.items():
                self.data[k][i, lo - o0:hi - o0] = v.to_numpy()[lo:hi]
            days = pd.date_range(self.start[y] - dt.timedelta(days=self.lead), periods=self.width).date
            for w in c.windows[country]:
                ws, we = w.dates(y)
                self.mask[i] |= (days >= ws) & (days <= we)
        # cumulative sums (NaN treated as missing: tracked with counts)
        self.cum, self.cnt = {}, {}
        for k, a in self.data.items():
            win = np.where(self.mask & np.isfinite(a), a, 0.0)
            self.cum[k] = np.cumsum(win, axis=1)
            self.cnt[k] = np.cumsum(self.mask & np.isfinite(a), axis=1)
            allv = np.where(np.isfinite(a), a, 0.0)
            self.cum[k + "_all"] = np.cumsum(allv, axis=1)
            self.cnt[k + "_all"] = np.cumsum(np.isfinite(a), axis=1)
        self.mask_cnt = np.cumsum(self.mask, axis=1)

    def offset(self, season: int, day: dt.date) -> int:
        return (day - self.start[season]).days + self.lead

    def _z(self, vals: np.ndarray, iy: int, floor: float) -> float:
        hist = vals[:iy]
        hist = hist[np.isfinite(hist)]
        if len(hist) < self.min_years or not np.isfinite(vals[iy]):
            return np.nan
        sd = max(np.std(hist, ddof=1), floor)
        return float((vals[iy] - hist.mean()) / sd)

    def features(self, season: int, cutoff: dt.date) -> dict:
        iy = self.years.index(season)
        k = min(self.offset(season, cutoff), self.width - 1)
        total = int(self.mask[iy].sum())
        if k < 0:
            elapsed = 0
        else:
            elapsed = int(self.mask_cnt[iy, k])
        out = {"progress": elapsed / total if total else 0.0}
        if elapsed == 0:
            for f in ["hdd_z", "tmax_z", "precip_z", "sm_root_z", "et_z", "frost_z"]:
                out[f] = 0.0
        else:
            # same elapsed window span in every year: value at column k
            def agg(name: str, mean: bool) -> np.ndarray:
                s = self.cum[name][:, k]
                n = self.cnt[name][:, k].astype(float)
                full = self.mask_cnt[:, k].astype(float)
                ok = (full > 0) & (n >= 0.9 * full)
                v = s / np.maximum(n, 1) if mean else s * full / np.maximum(n, 1)
                return np.where(ok, v, np.nan)

            out["hdd_z"] = self._z(agg("hdd", False), iy, 2.0)
            out["tmax_z"] = self._z(agg("tmax", True), iy, 0.2)
            out["precip_z"] = self._z(np.sqrt(np.clip(agg("precip", False), 0, None)), iy, 0.5)
            out["sm_root_z"] = self._z(agg("sm", True), iy, 0.01)
            out["et_z"] = self._z(agg("et", False), iy, 1.0)
            out["frost_z"] = self._z(agg("frost", False), iy, 0.5)
        # soil moisture over the `pre` days ending at min(cutoff, day before first window)
        k_end = min(k, self.lead - 1)
        k_beg = k_end - self.pre
        if k_beg >= 0:
            s = self.cum["sm_all"][:, k_end] - self.cum["sm_all"][:, k_beg]
            n = self.cnt["sm_all"][:, k_end] - self.cnt["sm_all"][:, k_beg]
            v = np.where(n >= 0.9 * self.pre, s / np.maximum(n, 1), np.nan)
            out["sm_pre_z"] = self._z(v, iy, 0.01)
        else:
            out["sm_pre_z"] = np.nan
        for f in list(out):
            if f != "progress" and out[f] is not None and np.isfinite(out[f]):
                out[f] = float(np.clip(out[f], -5, 5))
        return out


def to_country_season(cfg: Settings, key: str, cdaily: pd.DataFrame, dates: list[dt.date],
                      oni: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    """Features for every (country, as_of date): the active season of each country at that date."""
    from harvestradar.ingest.enso import oni_as_of

    c = cfg.commodities[key]
    lag = cfg.lag_days
    rows = []
    for country in c.countries:
        d = cdaily[cdaily.country_iso3 == country]
        if d.empty:
            print(f"[features] {key} {country}: no weather")
            continue
        cube = SeasonCube(c, country, d, cfg)
        for t in dates:
            season = active_season(c, country, t, cube.tail)
            if season not in cube.years:
                continue
            f = cube.features(season, t - dt.timedelta(days=lag))
            ws = [w.dates(season) for w in c.windows[country]]
            f.update(commodity=key, country_iso3=country, season=season, as_of=pd.Timestamp(t),
                     window_open=any(s <= t <= e for s, e in ws),
                     switch=pd.Timestamp(season_switch(c, country, season, cube.tail)))
            rows.append(f)
    feat = pd.DataFrame(rows)
    if feat.empty:
        return feat
    feat["oni"] = oni_as_of(oni, feat["as_of"]).to_numpy()
    feat = _attach_anom_last(feat, targets)
    return feat


def _attach_anom_last(feat: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    """Most recent published yield anomaly of an earlier season (published by as_of)."""
    t = targets[["commodity", "country_iso3", "season", "yield_anom", "available_at"]].dropna()
    t = t.assign(available_at=pd.to_datetime(t["available_at"]).astype("datetime64[ns]")).sort_values("available_at")
    feat = feat.assign(as_of=pd.to_datetime(feat["as_of"]).astype("datetime64[ns]"))
    out = []
    for (k, ctry), g in feat.groupby(["commodity", "country_iso3"]):
        tt = t[(t.commodity == k) & (t.country_iso3 == ctry)]
        g = g.sort_values("as_of")
        if tt.empty:
            g["anom_last"] = np.nan
        else:
            m = pd.merge_asof(g[["as_of"]].reset_index(), tt[["available_at", "season", "yield_anom"]]
                              .rename(columns={"season": "last_season"}),
                              left_on="as_of", right_on="available_at")
            m = m.set_index("index")
            ok = m["last_season"] < g["season"]
            g["anom_last"] = m["yield_anom"].where(ok)
        out.append(g)
    return pd.concat(out).sort_index()
```

## 34. `src/harvestradar/features/climatology.py`

```python
"""Climatologies (mean and standard deviation per region and dekad of year).

mode="fixed": one base period (used for the stress map).
mode="expanding": past years only, at least `min_years` (used for the model, to avoid look-ahead).
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd


def compute_climatology(df: pd.DataFrame, value_cols: list[str], base: tuple[int, int] = (2001, 2020),
                        mode: Literal["fixed", "expanding"] = "fixed", min_years: int = 10,
                        key: str = "region_id") -> pd.DataFrame:
    """df has columns key, year, dekad (0..35) and value_cols.
    fixed: returns key, dekad, <col>_mean, <col>_std.
    expanding: returns key, year, dekad, <col>_mean, <col>_std computed on years strictly before `year`."""
    if mode == "fixed":
        b = df[df.year.between(*base)]
        g = b.groupby([key, "dekad"])[value_cols]
        out = g.mean().add_suffix("_mean").join(g.std(ddof=1).add_suffix("_std")).reset_index()
        return out
    df = df.sort_values([key, "dekad", "year"]).reset_index(drop=True)
    out = df[[key, "year", "dekad"]].copy()
    for col in value_cols:
        g = df.groupby([key, "dekad"])[col]
        n = g.cumcount()  # number of strictly earlier years
        s1 = g.transform(lambda s: s.cumsum().shift(1))
        s2 = g.transform(lambda s: (s ** 2).cumsum().shift(1))
        mean = s1 / n.replace(0, np.nan)
        var = (s2 - n * mean ** 2) / (n - 1).replace(0, np.nan)
        out[f"{col}_mean"] = mean.where(n >= min_years)
        out[f"{col}_std"] = np.sqrt(var.clip(lower=0)).where(n >= min_years)
    return out


def zscore(x: pd.Series, mean: pd.Series, std: pd.Series, floor: float) -> pd.Series:
    return (x - mean) / std.clip(lower=floor)
```

## 35. `src/harvestradar/features/stress.py`

```python
"""Daily and dekad stress variables.

- heat degree days above a crop threshold (Schlenker and Roberts 2009: maize 29 C)
- frost days (tmin below a threshold, coffee)
- Hargreaves reference evapotranspiration (FAO-56 eq. 52), from tmax, tmin and latitude
- dekad composite stress: mean of heat, dryness (30-day rain) and root-zone soil moisture anomalies,
  re-standardised against the fixed base period so that it reads as a z-score.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from harvestradar.features.climatology import compute_climatology, zscore


def heat_degree_days(tmax: pd.Series, threshold_c: float) -> pd.Series:
    return (tmax - threshold_c).clip(lower=0)


def frost_days(tmin: pd.Series, threshold_c: float = 2.0) -> pd.Series:
    return (tmin < threshold_c).astype(float)


def extraterrestrial_radiation(lat_deg: np.ndarray, doy: np.ndarray) -> np.ndarray:
    """Ra in MJ m-2 day-1 (FAO-56 eq. 21)."""
    phi = np.deg2rad(lat_deg)
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    delta = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1, 1))
    return (24 * 60 / np.pi) * 0.0820 * dr * (ws * np.sin(phi) * np.sin(delta)
                                              + np.cos(phi) * np.cos(delta) * np.sin(ws))


def hargreaves_et0(tmax: np.ndarray, tmin: np.ndarray, lat_deg: np.ndarray, doy: np.ndarray) -> np.ndarray:
    ra = extraterrestrial_radiation(lat_deg, doy)
    tmean = (tmax + tmin) / 2
    return 0.0023 * (ra / 2.45) * (tmean + 17.8) * np.sqrt(np.clip(tmax - tmin, 0, None))


def spi_like(precip_sum: pd.Series) -> pd.Series:
    """Square-root transform before z-scoring: closer to normal than raw rainfall sums."""
    return np.sqrt(precip_sum.clip(lower=0))


def dekad_of(dates: pd.Series) -> pd.Series:
    d = pd.to_datetime(dates)
    return (d.dt.month - 1) * 3 + np.minimum((d.dt.day - 1) // 10, 2)


def dekad_end(year: pd.Series, dekad: pd.Series) -> pd.Series:
    month = dekad // 3 + 1
    k = dekad % 3
    first = pd.to_datetime(dict(year=year, month=month, day=1))
    last = first + pd.offsets.MonthEnd(0)
    day = np.where(k == 0, 10, np.where(k == 1, 20, last.dt.day))
    return pd.to_datetime(dict(year=year, month=month, day=day))


def to_dekad(daily: pd.DataFrame, heat_c: float) -> pd.DataFrame:
    """daily: region_id, date, tmax_c, tmin_c, precip_mm, sm_root. Returns dekad table."""
    d = daily.copy()
    d["year"] = d["date"].dt.year
    d["dekad"] = dekad_of(d["date"])
    d["hdd"] = heat_degree_days(d["tmax_c"], heat_c)
    g = d.groupby(["region_id", "year", "dekad"])
    out = g.agg(tmax=("tmax_c", "mean"), precip=("precip_mm", "sum"), sm_root=("sm_root", "mean"),
                hdd=("hdd", "sum"), n=("tmax_c", "count")).reset_index()
    out = out.sort_values(["region_id", "year", "dekad"])
    out["precip30"] = out.groupby("region_id")["precip"].transform(lambda s: s.rolling(3, min_periods=3).sum())
    out["precip30_t"] = spi_like(out["precip30"])
    out["dekad_end"] = dekad_end(out["year"], out["dekad"])
    return out


def dekad_stress(dek: pd.DataFrame, base: tuple[int, int]) -> pd.DataFrame:
    """Anomalies vs a fixed base period and the composite stress index."""
    cols = ["tmax", "hdd", "precip30_t", "sm_root"]
    clim = compute_climatology(dek, cols, base=base, mode="fixed")
    m = dek.merge(clim, on=["region_id", "dekad"], how="left")
    m["tmax_z"] = zscore(m["tmax"], m["tmax_mean"], m["tmax_std"], 0.3)
    m["hdd_z"] = zscore(m["hdd"], m["hdd_mean"], m["hdd_std"], 2.0)
    m["precip_z"] = zscore(m["precip30_t"], m["precip30_t_mean"], m["precip30_t_std"], 0.5)
    m["sm_root_z"] = zscore(m["sm_root"], m["sm_root_mean"], m["sm_root_std"], 0.01)
    for c in ["tmax_z", "hdd_z", "precip_z", "sm_root_z"]:
        m[c] = m[c].clip(-4, 4)
    heat = m[["tmax_z", "hdd_z"]].mean(axis=1)
    m["raw"] = (heat - m["precip_z"] - m["sm_root_z"]) / 3
    c2 = compute_climatology(m[["region_id", "year", "dekad", "raw"]], ["raw"], base=base, mode="fixed")
    m = m.merge(c2, on=["region_id", "dekad"], how="left")
    m["stress"] = zscore(m["raw"], m["raw_mean"], m["raw_std"], 0.1).clip(-4, 4)
    out = m[["region_id", "dekad_end", "year", "dekad", "stress", "hdd_z", "precip_z", "sm_root_z",
             "tmax_z", "tmax"]].copy()
    for c in ["stress", "hdd_z", "precip_z", "sm_root_z", "tmax_z", "tmax"]:
        out[c] = out[c].astype("float32").round(3)
    return out.dropna(subset=["stress"])
```

## 36. `src/harvestradar/features/windows.py`

```python
"""Critical windows: membership tests and active-season logic (windows may cross the year end)."""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from harvestradar.config import Commodity, Window


def in_critical_window(dates: pd.Series | pd.DatetimeIndex, windows: list[Window], season: int) -> np.ndarray:
    """True where a date falls inside any window of the given season."""
    d = pd.to_datetime(pd.Series(dates)).dt.date.to_numpy()
    out = np.zeros(len(d), dtype=bool)
    for w in windows:
        s, e = w.dates(season)
        out |= (d >= s) & (d <= e)
    return out


def window_open_on(day: dt.date, windows: list[Window]) -> bool:
    """Is any window of any season open on this day? (checks the seasons around the date)"""
    for season in (day.year - 1, day.year, day.year + 1, day.year + 2):
        for w in windows:
            s, e = w.dates(season)
            if s <= day <= e:
                return True
    return False


def season_switch(c: Commodity, country: str, season: int, tail_days: int) -> dt.date:
    """Last day on which `season` is the active (tracked) season for a country: the earlier of
    (end of its last window + tail) and (the day before the next season's first window)."""
    _, end = c.season_span(country, season)
    nxt, _ = c.season_span(country, season + 1)
    return min(end + dt.timedelta(days=tail_days), nxt - dt.timedelta(days=1))


def active_season(c: Commodity, country: str, day: dt.date, tail_days: int) -> int:
    for season in range(day.year - 2, day.year + 3):
        if day <= season_switch(c, country, season, tail_days):
            return season
    raise ValueError("no active season found")
```

## 37. `src/harvestradar/geo/__init__.py`

```python

```

## 38. `src/harvestradar/geo/regions.py`

```python
"""Producing regions (ADM1) and production weights from MapSPAM 2020 (CC BY 4.0).

For each commodity: sum MapSPAM production per ADM1 polygon, sort, keep regions until they cover
`coverage` of world production, weight = prod_r / sum(prod_r). Then sample up to N NASA POWER grid
cells per region on the most productive pixels, each with a weight.
"""

from __future__ import annotations

import json

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from exactextract import exact_extract

from harvestradar.config import Settings
from harvestradar.ingest import boundaries
from harvestradar.ingest.manifest import record
from harvestradar.ingest.power import cell_id, snap
from harvestradar.paths import PROCESSED, RAW

SPAM_DIR = RAW / "spam"


def spam_raster(crop: str):
    hits = sorted(SPAM_DIR.glob(f"*_P_{crop}_A.tif")) or sorted(SPAM_DIR.glob(f"*{crop}*_A.tif"))
    if not hits:
        raise FileNotFoundError(
            f"MapSPAM 2020 production raster for {crop} not found in {SPAM_DIR}. "
            "Download spam2020V2r2_global_production.geotiff.zip from https://doi.org/10.7910/DVN/SWPENT "
            "(guestbook required) and extract the *_P_{crop}_A.tif files there.")
    return hits[0]


def candidate_countries(cfg: Settings, key: str, fao: pd.DataFrame, share: float = 0.995) -> list[str]:
    c = cfg.commodities[key]
    last = fao[(fao.commodity == key)].year.max()
    p = fao[(fao.commodity == key) & (fao.year.between(last - 4, last))]
    p = p.groupby("country_iso3").production_t.mean().sort_values(ascending=False)
    cum = p.cumsum() / p.sum()
    keep = list(cum[cum.shift(fill_value=0) < share].index)
    return sorted(set(keep) | set(c.countries))


def build_regions(cfg: Settings, key: str, fao: pd.DataFrame) -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    c = cfg.commodities[key]
    path = spam_raster(c.spam_crop)
    with rasterio.open(path) as src:
        arr = src.read(1, masked=True)
        world_total = float(arr.sum())
    adm = boundaries.fetch_many(candidate_countries(cfg, key, fao))
    adm = adm[adm.geometry.notna() & ~adm.geometry.is_empty].reset_index(drop=True)
    adm["rid"] = np.arange(len(adm))
    sums = exact_extract(str(path), adm, ["sum"], include_cols=["rid"], output="pandas")
    adm = adm.merge(sums, on="rid")
    adm = adm.rename(columns={"sum": "prod_t"}).sort_values("prod_t", ascending=False)
    adm["cum_share"] = adm["prod_t"].cumsum() / world_total
    shares = (adm.groupby("country_iso3")["prod_t"].sum() / world_total).rename("share").reset_index()
    shares["source"] = "MapSPAM 2020"
    shares.to_parquet(PROCESSED / f"country_shares_{key}.parquet", index=False)
    keep = adm[adm["cum_share"].shift(fill_value=0) < c.coverage].copy()
    keep["world_share"] = keep["prod_t"] / world_total
    keep["weight"] = keep["prod_t"] / keep["prod_t"].sum()
    code = keep["shape_iso"].where(keep["shape_iso"].notna() & (keep["shape_iso"].astype(str).str.len() > 0),
                                   keep["shape_id"])
    keep["region_id"] = keep["country_iso3"] + "-" + code.astype(str)
    dup = keep["region_id"].duplicated(keep=False)
    keep.loc[dup, "region_id"] = keep.loc[dup, "country_iso3"] + "-" + keep.loc[dup, "shape_id"].astype(str)
    keep["commodity"] = key
    rp = keep.geometry.representative_point()
    keep["lat"], keep["lon"] = rp.y.round(4), rp.x.round(4)
    keep = keep[["region_id", "commodity", "country_iso3", "adm1_name", "prod_t", "world_share", "weight",
                 "lat", "lon", "geometry"]].reset_index(drop=True)
    cells = sample_cells(path, keep, int(cfg.regions["max_cells_per_region"]))
    return gpd.GeoDataFrame(keep, crs=4326), cells


def sample_cells(path, regions: gpd.GeoDataFrame, n_max: int) -> pd.DataFrame:
    """Up to n_max POWER cells per region, chosen on the most productive pixels."""
    vals = exact_extract(str(path), regions, ["values", "coverage", "center_x", "center_y"],
                         include_cols=["region_id"], output="pandas")
    rows = []
    for r in vals.itertuples():
        v = np.asarray(r.values, dtype=float)
        cov = np.asarray(r.coverage, dtype=float)
        x = np.asarray(r.center_x, dtype=float)
        y = np.asarray(r.center_y, dtype=float)
        ok = np.isfinite(v) & (v > 0)
        if not ok.any():
            continue
        lat, lon = snap(y[ok], x[ok])
        d = pd.DataFrame({"lat": lat, "lon": lon, "p": v[ok] * cov[ok]}).groupby(["lat", "lon"]).p.sum()
        d = d.sort_values(ascending=False).head(n_max)
        for (la, lo), p in d.items():
            rows.append((r.region_id, cell_id(la, lo), la, lo, p))
    cells = pd.DataFrame(rows, columns=["region_id", "cell_id", "lat", "lon", "p"])
    cells["cell_weight"] = cells["p"] / cells.groupby("region_id")["p"].transform("sum")
    return cells.drop(columns="p")


def build_all(cfg: Settings) -> dict[str, gpd.GeoDataFrame]:
    from harvestradar.ingest.yields import load_faostat

    fao_p = PROCESSED / "fao_qcl.parquet"
    fao = pd.read_parquet(fao_p) if fao_p.exists() else load_faostat(cfg)
    out, all_cells = {}, []
    for key in cfg.commodities:
        regions, cells = build_regions(cfg, key, fao)
        regions.to_file(PROCESSED / f"regions_{key}.gpkg", driver="GPKG")
        regions.drop(columns="geometry").to_parquet(PROCESSED / f"regions_{key}.parquet", index=False)
        cells["commodity"] = key
        all_cells.append(cells)
        out[key] = regions
        cov = regions["world_share"].sum()
        print(f"[regions] {key}: {len(regions)} regions, coverage {cov:.3f}, weights sum "
              f"{regions['weight'].sum():.6f}, {cells.cell_id.nunique()} cells")
    cells = pd.concat(all_cells, ignore_index=True)
    cells.to_parquet(PROCESSED / "sample_cells.parquet", index=False)
    for p in sorted(SPAM_DIR.glob("*.tif")):
        record(p, "MapSPAM 2020 V2r2 (IFPRI), global production", "https://doi.org/10.7910/DVN/SWPENT",
               "CC BY 4.0")
    summary = {k: {"regions": int(len(v)), "coverage": round(float(v["world_share"].sum()), 4)}
               for k, v in out.items()}
    summary["cells"] = int(cells.cell_id.nunique())
    (PROCESSED / "regions_summary.json").write_text(json.dumps(summary, indent=2))
    return out
```

## 39. `src/harvestradar/ingest/__init__.py`

```python

```

## 40. `src/harvestradar/ingest/boundaries.py`

```python
"""geoBoundaries gbOpen ADM1 (simplified geometry), one file per country. Licence per country, mostly
CC BY 4.0 or public domain; recorded in the manifest."""

from __future__ import annotations

import json
import re

import geopandas as gpd
import pandas as pd

from harvestradar.ingest.manifest import download, record
from harvestradar.paths import RAW

API = "https://www.geoboundaries.org/api/current/gbOpen/{iso}/ADM1/"
GB_DIR = RAW / "geoboundaries"


def media_url(url: str) -> str:
    """geoBoundaries files are stored with Git LFS: github.com/<o>/<r>/raw/<ref>/<path> serves a pointer
    or redirects; media.githubusercontent.com/media/<o>/<r>/<ref>/<path> serves the file itself."""
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/raw/([^/]+)/(.+)", url)
    return f"https://media.githubusercontent.com/media/{m[1]}/{m[2]}/{m[3]}/{m[4]}" if m else url


def fetch_adm1(iso3: str) -> gpd.GeoDataFrame:
    meta_path = GB_DIR / f"{iso3}_ADM1_meta.json"
    geo_path = GB_DIR / f"{iso3}_ADM1_simplified.geojson"
    if not geo_path.exists():
        download(API.format(iso=iso3), meta_path)
        meta = json.loads(meta_path.read_text())
        url = media_url(meta["simplifiedGeometryGeoJSON"])
        download(url, geo_path, timeout=300)
        record(geo_path, f"geoBoundaries gbOpen ADM1 {iso3} ({meta.get('boundarySource', '')})", url,
               meta.get("boundaryLicense", "see geoBoundaries"))
    g = gpd.read_file(geo_path)
    g = g.rename(columns={"shapeName": "adm1_name", "shapeID": "shape_id", "shapeISO": "shape_iso"})
    g["country_iso3"] = iso3
    keep = ["country_iso3", "adm1_name", "shape_id", "shape_iso", "geometry"]
    for k in keep:
        if k not in g:
            g[k] = None
    return g[keep].to_crs(4326)


def fetch_many(isos: list[str]) -> gpd.GeoDataFrame:
    frames = []
    for iso in sorted(set(isos)):
        try:
            frames.append(fetch_adm1(iso))
        except Exception as e:  # noqa: BLE001
            print(f"[boundaries] {iso}: {e}")
    return gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=4326)
```

## 41. `src/harvestradar/ingest/enso.py`

```python
"""NOAA CPC Oceanic Nino Index (ONI): 3-month running mean of ERSST.v5 SST anomalies in Nino 3.4.

Public domain (NOAA). Season codes DJF, JFM, ... NDJ; the value of a season is published early in the
month after its last month.
"""

from __future__ import annotations

import pandas as pd

from harvestradar.ingest.manifest import download, record
from harvestradar.paths import PROCESSED, RAW

ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
SEASONS = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]
SEASON_LABEL = {s: f"{m1}-{m3}" for s, (m1, m3) in zip(SEASONS, [
    ("DEC", "FEB"), ("JAN", "MAR"), ("FEB", "APR"), ("MAR", "MAY"), ("APR", "JUN"), ("MAY", "JUL"),
    ("JUN", "AUG"), ("JUL", "SEP"), ("AUG", "OCT"), ("SEP", "NOV"), ("OCT", "DEC"), ("NOV", "JAN")])}


def fetch_oni() -> pd.DataFrame:
    dest = RAW / "oni" / "oni.ascii.txt"
    download(ONI_URL, dest)
    record(dest, "NOAA CPC ONI", ONI_URL, "Public domain (NOAA)")
    rows = []
    for line in dest.read_text().splitlines()[1:]:
        parts = line.split()
        if len(parts) != 4:
            continue
        seas, yr, total, anom = parts
        rows.append((seas, int(yr), float(total), float(anom)))
    df = pd.DataFrame(rows, columns=["season", "year", "total", "oni"])
    idx = df["season"].map(SEASONS.index)
    # centre month of the 3-month season; DJF of year Y is centred on January Y
    df["centre"] = pd.to_datetime(dict(year=df.year, month=idx + 1, day=1))
    # last month of the season, then published around the 10th of the following month
    last = df["centre"] + pd.offsets.MonthBegin(1)
    df["available_at"] = last + pd.offsets.MonthBegin(1) + pd.Timedelta(days=9)
    df["label"] = df["season"].map(SEASON_LABEL) + " " + df["year"].astype(str)
    df = df.sort_values("centre").reset_index(drop=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED / "oni.parquet", index=False)
    return df


def oni_as_of(oni: pd.DataFrame, dates: pd.Series) -> pd.Series:
    """Latest ONI value published on or before each date."""
    o = oni.sort_values("available_at")[["available_at", "oni"]].copy()
    o["available_at"] = pd.to_datetime(o["available_at"]).astype("datetime64[ns]")
    d = pd.DataFrame({"date": pd.to_datetime(pd.Series(dates).to_numpy()).astype("datetime64[ns]")}).reset_index()
    m = pd.merge_asof(d.sort_values("date"), o, left_on="date", right_on="available_at")
    return m.set_index("index").sort_index()["oni"]
```

## 42. `src/harvestradar/ingest/manifest.py`

```python
"""Provenance of every downloaded file: data/manifest.json (source, URL, date, licence, SHA-256)."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import time
from pathlib import Path

import requests

from harvestradar.paths import DATA, ROOT

MANIFEST = DATA / "manifest.json"
USER_AGENT = "HarvestRadar/0.1 (research prototype)"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"files": {}}


def record(path: Path, source: str, url: str, licence: str, note: str = "") -> None:
    m = _load()
    full = Path(path).resolve()
    try:
        rel = str(full.relative_to(ROOT))
    except ValueError:
        rel = str(full.relative_to(DATA.resolve().parent)) if full.is_relative_to(DATA.resolve().parent) else str(full)
    m["files"][rel] = {
        "source": source,
        "url": url,
        "licence": licence,
        "collected_at": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": sha256(Path(path)),
        "bytes": Path(path).stat().st_size,
        **({"note": note} if note else {}),
    }
    m["files"] = dict(sorted(m["files"].items()))
    MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def record_group(key: str, source: str, url: str, licence: str, count: int, note: str = "") -> None:
    """For sources fetched as many small files (e.g. one NASA POWER request per grid cell)."""
    m = _load()
    m.setdefault("groups", {})[key] = {
        "source": source,
        "url": url,
        "licence": licence,
        "collected_at": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "files": count,
        **({"note": note} if note else {}),
    }
    MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def download(url: str, dest: Path, retries: int = 4, timeout: int = 120, params: dict | None = None) -> Path:
    """GET with retries and exponential backoff. Writes atomically."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with requests.get(url, params=params, timeout=timeout, stream=True,
                              headers={"User-Agent": USER_AGENT}) as r:
                r.raise_for_status()
                tmp = dest.with_suffix(dest.suffix + ".part")
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                tmp.replace(dest)
                return dest
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"download failed after {retries} attempts: {url}: {last}")
```

## 43. `src/harvestradar/ingest/power.py`

```python
"""NASA POWER daily point data (MERRA-2 based, 0.5 x 0.625 degree native grid), 1981 to present.

No key, public NASA data. One request per grid cell for the full history.
Variables: T2M_MAX, T2M_MIN (deg C), PRECTOTCORR (mm/day), GWETROOT, GWETTOP (soil wetness, 0-1).
"""

from __future__ import annotations

import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import requests

from harvestradar.ingest.manifest import USER_AGENT, record_group
from harvestradar.paths import RAW

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMS = ["T2M_MAX", "T2M_MIN", "PRECTOTCORR", "GWETROOT", "GWETTOP"]
RENAME = {"T2M_MAX": "tmax_c", "T2M_MIN": "tmin_c", "PRECTOTCORR": "precip_mm",
          "GWETROOT": "sm_root", "GWETTOP": "sm_top"}
POWER_DIR = RAW / "power"
LAT_STEP, LON_STEP = 0.5, 0.625


def snap(lat: np.ndarray, lon: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Centre of the MERRA-2 cell containing each point."""
    return np.round(np.asarray(lat) / LAT_STEP) * LAT_STEP, np.round(np.asarray(lon) / LON_STEP) * LON_STEP


def cell_id(lat: float, lon: float) -> str:
    return f"{lat:+07.2f}_{lon:+08.3f}"


def _fetch_one(lat: float, lon: float, start: str, end: str, session: requests.Session) -> pd.DataFrame:
    params = dict(parameters=",".join(PARAMS), community="AG", latitude=lat, longitude=lon,
                  start=start.replace("-", ""), end=end.replace("-", ""), format="CSV", header="false")
    last = None
    for attempt in range(5):
        try:
            r = session.get(URL, params=params, timeout=120, headers={"User-Agent": USER_AGENT})
            if r.status_code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            r.raise_for_status()
            df = pd.read_csv(io.StringIO(r.text))
            df["date"] = pd.to_datetime(df["YEAR"].astype(str), format="%Y") + pd.to_timedelta(df["DOY"] - 1, "D")
            df = df.drop(columns=["YEAR", "DOY"]).rename(columns=RENAME)
            df = df.replace(-999.0, np.nan)
            return df
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"POWER failed for {lat},{lon}: {last}")


def fetch_cells(cells: pd.DataFrame, start: str, end: str, workers: int = 4, refresh: bool = False) -> int:
    """cells: DataFrame with cell_id, lat, lon. Each cell is written to data/raw/power/<cell_id>.parquet."""
    POWER_DIR.mkdir(parents=True, exist_ok=True)
    todo = []
    for row in cells.itertuples():
        p = POWER_DIR / f"{row.cell_id}.parquet"
        if refresh or not p.exists():
            todo.append(row)
    done = 0
    with requests.Session() as s, ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(_fetch_one, r.lat, r.lon, start, end, s): r for r in todo}
        for f in as_completed(futs):
            r = futs[f]
            try:
                df = f.result()
            except Exception as e:  # noqa: BLE001
                print(f"[power] {r.cell_id}: {e}")
                continue
            df.to_parquet(POWER_DIR / f"{r.cell_id}.parquet", index=False)
            done += 1
            if done % 100 == 0:
                print(f"[power] {done}/{len(todo)} cells")
    n = len(list(POWER_DIR.glob("*.parquet")))
    record_group("data/raw/power", "NASA POWER daily point API (MERRA-2)", URL,
                 "NASA open data, free of charge", n, note=f"{start} to {end}, parameters {','.join(PARAMS)}")
    return done


def update_cells(cells: pd.DataFrame, end: str, first: str, overlap_days: int = 10, workers: int = 4) -> int:
    """Append the days since each cell's last complete day (minus an overlap) up to `end`. Cells never fetched
    get their full history from `first`. Trailing days that NASA has not filled yet (all missing) are dropped,
    so the next run asks for them again."""
    POWER_DIR.mkdir(parents=True, exist_ok=True)
    end_ts = pd.Timestamp(end)
    jobs = []
    for row in cells.drop_duplicates("cell_id").itertuples():
        p = POWER_DIR / f"{row.cell_id}.parquet"
        if p.exists():
            last = pd.read_parquet(p, columns=["date", "tmax_c"]).dropna().date.max()
            start = min(last - pd.Timedelta(days=overlap_days), end_ts)
        else:
            start = pd.Timestamp(first)
        if start <= end_ts:
            jobs.append((row, start))
    done = failed = 0
    with requests.Session() as s, ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(_fetch_one, r.lat, r.lon, st.strftime("%Y-%m-%d"), end_ts.strftime("%Y-%m-%d"), s): (r, st)
                for r, st in jobs}
        for f in as_completed(futs):
            r, st = futs[f]
            try:
                new = f.result()
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"[power] {r.cell_id}: {e}")
                continue
            p = POWER_DIR / f"{r.cell_id}.parquet"
            old = pd.read_parquet(p) if p.exists() else new.iloc[0:0]
            d = pd.concat([old[old.date < st], new], ignore_index=True).sort_values("date").reset_index(drop=True)
            vals = [c for c in RENAME.values() if c in d.columns]
            filled = d[vals].notna().any(axis=1)
            if filled.any():
                d = d.loc[: filled[filled].index[-1]]
            d.to_parquet(p, index=False)
            done += 1
            if done % 250 == 0:
                print(f"[power] {done}/{len(jobs)} cells updated")
    print(f"[power] {done} cells updated to {end}, {failed} failed")
    record_group("data/raw/power", "NASA POWER daily point API (MERRA-2)", URL,
                 "NASA open data, free of charge", len(list(POWER_DIR.glob("*.parquet"))),
                 note=f"incremental update to {end}, parameters {','.join(PARAMS)}")
    if failed > 0.05 * max(1, len(jobs)):
        raise RuntimeError(f"NASA POWER: {failed} of {len(jobs)} cells failed")
    return done


def load_cells(cell_ids: list[str]) -> pd.DataFrame:
    frames = []
    for cid in cell_ids:
        p = POWER_DIR / f"{cid}.parquet"
        if p.exists():
            d = pd.read_parquet(p)
            d["cell_id"] = cid
            frames.append(d)
    return pd.concat(frames, ignore_index=True)
```

## 44. `src/harvestradar/ingest/prices.py`

```python
"""Front-month continuous futures from yfinance (Yahoo terms: personal or research use).

The continuous series jumps at each roll; returns on detected roll days are neutralised (NaN).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from harvestradar.config import Settings
from harvestradar.ingest.manifest import record
from harvestradar.paths import PROCESSED, RAW


def load_futures(ticker: str, start: str, end: str) -> pd.DataFrame:
    import yfinance as yf

    df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.reset_index().rename(columns={"Date": "date", "Close": "close"})
    df = df[["date", "close"]].dropna()
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    return df


def detect_rolls(df: pd.DataFrame, k: float = 4.0) -> pd.Series:
    """Flag days whose absolute log return is larger than k rolling MADs AND fall in a roll month
    (the last days before expiry). Conservative: only isolated jumps are flagged."""
    r = np.log(df["close"]).diff()
    mad = r.abs().rolling(60, min_periods=20).median()
    big = r.abs() > k * mad.clip(lower=1e-4) * 1.4826
    # a roll jump is isolated: the next day does not reverse it fully
    return big.fillna(False)


def settled_until(now: pd.Timestamp | None = None) -> pd.Timestamp:
    """First day without a settled close: today before 21:00 UTC (CBOT and ICE settle by then), tomorrow after."""
    now = now or pd.Timestamp.now(tz="UTC")
    day = now.tz_localize(None).normalize() if now.tzinfo else now.normalize()
    return day + pd.Timedelta(days=1) if now.hour >= 21 else day


def fetch_prices(cfg: Settings) -> dict[str, pd.DataFrame]:
    out = {}
    end = (pd.Timestamp(cfg.as_of_end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    for key, c in cfg.commodities.items():
        df = load_futures(c.ticker, "2000-01-01", end)
        df = df[df["date"] <= pd.Timestamp(cfg.as_of_end)]
        df = df[df["date"] < settled_until()]  # today's bar is not a close until the exchanges have settled
        df["ticker"] = c.ticker
        df["ret_1d"] = np.log(df["close"]).diff()
        df["roll_flag"] = detect_rolls(df)
        df.loc[df["roll_flag"], "ret_1d"] = np.nan
        raw = RAW / "prices" / f"{key}_{c.ticker.replace('=', '')}.csv"
        raw.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(raw, index=False)
        record(raw, f"Yahoo Finance via yfinance ({c.ticker})",
               f"https://finance.yahoo.com/quote/{c.ticker}", "Yahoo terms: personal or research use")
        PROCESSED.mkdir(parents=True, exist_ok=True)
        df.to_parquet(PROCESSED / f"prices_{key}.parquet", index=False)
        out[key] = df
    return out
```

## 45. `src/harvestradar/ingest/yields.py`

```python
"""FAOSTAT QCL (crops and livestock products): production, area and yield per country and year.

Licence: CC BY 4.0 (FAO). Year Y is published around December of Y+1.
"""

from __future__ import annotations

import zipfile

import pandas as pd
import pycountry

from harvestradar.config import Settings
from harvestradar.ingest.manifest import download, record
from harvestradar.paths import PROCESSED, RAW

FAO_URL = "https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_All_Data_(Normalized).zip"
FAO_DIR = RAW / "faostat"
ELEMENTS = {"Production": "production_t", "Area harvested": "area_ha", "Yield": "yield_kg_ha"}


def fetch_faostat() -> None:
    z = FAO_DIR / "Production_Crops_Livestock_E_All_Data_Normalized.zip"
    if not z.exists():
        download(FAO_URL, z, timeout=600)
        record(z, "FAOSTAT QCL", FAO_URL, "CC BY 4.0")
    with zipfile.ZipFile(z) as zf:
        zf.extractall(FAO_DIR)


def _m49_to_iso3(code: str) -> str | None:
    code = str(code).strip("'").zfill(3)
    if code == "156":  # FAO "China, mainland" uses 156; the aggregate "China" (159) is excluded below
        return "CHN"
    c = pycountry.countries.get(numeric=code)
    return c.alpha_3 if c else None


def load_faostat(cfg: Settings) -> pd.DataFrame:
    """Tidy table: commodity, country_iso3, year, production_t, area_ha, yield_t_ha, world_production_t."""
    csv = FAO_DIR / "Production_Crops_Livestock_E_All_Data_(Normalized).csv"
    if not csv.exists():
        fetch_faostat()
    items = {c.fao_item: k for k, c in cfg.commodities.items()}
    usecols = ["Area Code", "Area Code (M49)", "Area", "Item Code", "Element", "Year", "Value"]
    chunks = []
    for ch in pd.read_csv(csv, usecols=usecols, chunksize=500_000, encoding="utf-8"):
        chunks.append(ch[ch["Item Code"].isin(items) & ch["Element"].isin(ELEMENTS)])
    df = pd.concat(chunks)
    world = df[(df["Area Code"] == 5000) & (df.Element == "Production")]
    world = world.assign(commodity=world["Item Code"].map(items))[["commodity", "Year", "Value"]]
    world = world.rename(columns={"Year": "year", "Value": "world_production_t"})
    # countries only: FAO area codes < 5000, excluding aggregates (China = 351, China incl. Taiwan etc.)
    df = df[(df["Area Code"] < 5000) & (~df["Area Code"].isin([351]))].copy()
    df["country_iso3"] = df["Area Code (M49)"].map(_m49_to_iso3)
    df = df.dropna(subset=["country_iso3"])
    df["commodity"] = df["Item Code"].map(items)
    wide = df.pivot_table(index=["commodity", "country_iso3", "Year"], columns="Element", values="Value",
                          aggfunc="sum").reset_index().rename(columns={"Year": "year", **ELEMENTS})
    wide["yield_t_ha"] = wide["production_t"] / wide["area_ha"]
    wide.loc[wide["area_ha"] <= 0, "yield_t_ha"] = float("nan")
    wide = wide.merge(world, on=["commodity", "year"], how="left")
    wide["available_at"] = pd.to_datetime((wide["year"] + 1).astype(str) + "-12-31")
    out = wide[["commodity", "country_iso3", "year", "production_t", "area_ha", "yield_t_ha",
                "world_production_t", "available_at"]].sort_values(["commodity", "country_iso3", "year"])
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out.to_parquet(PROCESSED / "fao_qcl.parquet", index=False)
    return out
```

## 46. `src/harvestradar/models/__init__.py`

```python

```

## 47. `src/harvestradar/models/baselines.py`

```python
"""Baselines reported next to the model, without selection: trend only (zero anomaly), persistence
(latest published anomaly) and a 3-variable linear regression."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

LINEAR_VARS = ["hdd_z", "precip_z", "sm_root_z"]


def zero(df: pd.DataFrame) -> np.ndarray:
    return np.zeros(len(df))


def persistence(df: pd.DataFrame) -> np.ndarray:
    return df["anom_last"].fillna(0.0).to_numpy()


def fit_linear(train: pd.DataFrame) -> LinearRegression:
    X = train[LINEAR_VARS].fillna(0.0)
    return LinearRegression().fit(X, train["yield_anom"])


def linear(model: LinearRegression, df: pd.DataFrame) -> np.ndarray:
    return model.predict(df[LINEAR_VARS].fillna(0.0))
```

## 48. `src/harvestradar/models/explain.py`

```python
"""SHAP explanations of the median model, in percentage points of yield (or production) anomaly."""

from __future__ import annotations

import numpy as np
import pandas as pd
import shap

from harvestradar.models.yield_model import MODEL_FEATURES, YieldModel, design


def shap_by_prediction(model: YieldModel, df: pd.DataFrame) -> pd.DataFrame:
    X = design(df)
    ex = shap.TreeExplainer(model.median.booster_)
    vals = ex.shap_values(X)
    out = pd.DataFrame(np.asarray(vals) * 100.0, columns=[f"shap_{c}" for c in MODEL_FEATURES], index=df.index)
    out["shap_base"] = float(np.atleast_1d(ex.expected_value)[0]) * 100.0
    return out
```

## 49. `src/harvestradar/models/targets.py`

```python
"""Model target: yield anomaly vs a trend fitted ONLY on earlier years.

anom(Y) = (yield(Y) - trend(Y)) / trend(Y), trend = linear fit on the previous `trend_years` years
(at least `min_trend_years`). FAOSTAT year Y is published in December of Y+1: available_at.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from harvestradar.config import Settings


def yield_anomaly(df: pd.DataFrame, trend_years: int = 15, min_years: int = 8,
                  value: str = "yield_t_ha") -> pd.DataFrame:
    """df: commodity, country_iso3, year, <value>. Adds trend_t_ha (trend of <value>) and yield_anom."""
    out = []
    for _, g in df.sort_values("year").groupby(["commodity", "country_iso3"]):
        g = g.copy()
        yrs = g["year"].to_numpy()
        ys = g[value].to_numpy(dtype=float)
        trend = np.full(len(g), np.nan)
        for i, y in enumerate(yrs):
            m = (yrs < y) & (yrs >= y - trend_years) & np.isfinite(ys) & (ys > 0)
            if m.sum() >= min_years:
                b, a = np.polyfit(yrs[m], ys[m], 1)
                trend[i] = a + b * y
        g["trend_t_ha"] = trend
        g["yield_anom"] = (g[value] - trend) / trend
        out.append(g)
    return pd.concat(out, ignore_index=True)


def build_targets(cfg: Settings, fao: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for key, c in cfg.commodities.items():
        value = "yield_t_ha" if c.target == "yield" else "production_t"
        a = yield_anomaly(fao[fao.commodity == key], int(cfg.targets["trend_years"]),
                          int(cfg.targets["min_trend_years"]), value=value)
        a["target_kind"] = c.target
        parts.append(a)
    t = pd.concat(parts, ignore_index=True).rename(columns={"year": "season"})
    t["source"] = "FAOSTAT QCL"
    # guard against absurd anomalies from data breaks (e.g. area redefinitions)
    t.loc[t["yield_anom"].abs() > 0.8, "yield_anom"] = np.nan
    return t[["commodity", "country_iso3", "season", "yield_t_ha", "trend_t_ha", "yield_anom",
              "production_t", "world_production_t", "available_at", "source", "target_kind"]]


def country_shares(fao: pd.DataFrame, key: str, as_of: pd.Timestamp, years: int = 3) -> pd.Series:
    """Share of world production per country, mean of the latest `years` published years at as_of."""
    f = fao[(fao.commodity == key) & (fao.available_at <= as_of)]
    if f.empty:
        return pd.Series(dtype=float)
    last = f.year.max()
    f = f[f.year > last - years]
    p = f.groupby("country_iso3").production_t.mean()
    w = f.groupby("year").world_production_t.first().mean()
    return p / w
```

## 50. `src/harvestradar/models/validation.py`

```python
"""Rolling-origin validation with real publication dates.

Vintage V (calendar year of the forecast date) is trained only on seasons whose FAOSTAT figures were
published before 1 January of V, then predicts every week of year V. This is the "real-time" record:
the 2012 forecasts never saw a target published in or after 2012.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from harvestradar.config import Settings
from harvestradar.models import baselines
from harvestradar.models.yield_model import YieldModel, train


def training_rows(panel: pd.DataFrame, vintage: int, cfg: Settings, stride_days: int = 14) -> pd.DataFrame:
    cut = pd.Timestamp(f"{vintage}-01-01")
    r = panel[(panel["season"] >= int(cfg.features["first_season"])) & panel["yield_anom"].notna()
              & (panel["target_available_at"] < cut)]
    # one sample every `stride_days` per country-season (weekly rows are strongly autocorrelated)
    days = (r["as_of"] - pd.Timestamp("1990-01-05")).dt.days
    return r[(days % stride_days) == 0]


def rolling_origin(panel: pd.DataFrame, cfg: Settings, first: int, last: int,
                   store=None) -> tuple[pd.DataFrame, dict]:
    """Returns weekly out-of-sample predictions for vintages first..last and vintage metadata."""
    preds, meta = [], {}
    for v in range(first, last + 1):
        tr = training_rows(panel, v, cfg)
        if tr["season"].nunique() < 5:
            continue
        model: YieldModel = train(tr, cfg)
        lin = baselines.fit_linear(tr)
        test = panel[panel["as_of"].dt.year == v]
        if test.empty:
            continue
        p = model.predict(test)
        p["pred_linear"] = baselines.linear(lin, test)
        p["vintage"] = v
        preds.append(pd.concat([test, p], axis=1))
        meta[v] = {"trained_on_seasons_up_to": int(tr["season"].max()),
                   "first_season": int(tr["season"].min()), "rows": int(len(tr)),
                   "country_seasons": int(model.n_seasons)}
        if store is not None:
            store(v, model)
        print(f"[model] vintage {v}: trained on seasons {meta[v]['first_season']}-"
              f"{meta[v]['trained_on_seasons_up_to']} ({len(tr)} rows), predicted {len(test)} weeks")
    return pd.concat(preds, ignore_index=True), meta


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    ok = np.isfinite(y) & np.isfinite(p)
    y, p = y[ok], p[ok]
    if len(y) < 3:
        return {"n": int(len(y))}
    rho = spearmanr(y, p).statistic if np.std(p) > 0 else float("nan")
    return {"n": int(len(y)), "rmse": float(np.sqrt(np.mean((y - p) ** 2))), "mae": float(np.mean(np.abs(y - p))),
            "spearman": float(rho) if np.isfinite(rho) else None,
            "sign_accuracy": float(np.mean(np.sign(y) == np.sign(p))) if np.std(p) > 0 else None}
```

## 51. `src/harvestradar/models/yield_model.py`

```python
"""LightGBM yield-anomaly model: one model shared by all commodities (commodity as a feature),
a median model plus 10 % / 90 % quantile models for the uncertainty band."""

from __future__ import annotations

from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd

from harvestradar.config import Settings
from harvestradar.features.aggregate import FEATURES

COMMODITY_CODES = {"maize": 0, "coffee": 1, "cocoa": 2}
MODEL_FEATURES = FEATURES + ["commodity_code"]


def design(df: pd.DataFrame) -> pd.DataFrame:
    X = df[FEATURES].astype(float).copy()
    X["commodity_code"] = df["commodity"].map(COMMODITY_CODES).astype(int)
    return X


@dataclass
class YieldModel:
    median: lgb.LGBMRegressor
    lo: lgb.LGBMRegressor
    hi: lgb.LGBMRegressor
    trained_up_to: int
    n_rows: int
    n_seasons: int

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        X = design(df)
        p = self.median.predict(X)
        lo, hi = self.lo.predict(X), self.hi.predict(X)
        lo, hi = np.minimum(lo, p), np.maximum(hi, p)
        return pd.DataFrame({"pred_anom": p, "pred_lo": lo, "pred_hi": hi}, index=df.index)


def _params(cfg: Settings) -> dict:
    m = cfg.model
    return dict(num_leaves=int(m["num_leaves"]), min_child_samples=int(m["min_data_in_leaf"]),
                learning_rate=float(m["learning_rate"]), n_estimators=int(m["n_estimators"]),
                colsample_bytree=float(m["feature_fraction"]), subsample=0.8, subsample_freq=1,
                reg_lambda=float(m.get("reg_lambda", 0.0)),
                random_state=int(cfg.seed), deterministic=True, force_row_wise=True, n_jobs=4, verbose=-1)


def train(rows: pd.DataFrame, cfg: Settings) -> YieldModel:
    """rows: training samples (features + yield_anom). Each country-season gets the same total weight."""
    X = design(rows)
    y = rows["yield_anom"].astype(float)
    key = rows["commodity"] + "|" + rows["country_iso3"] + "|" + rows["season"].astype(str)
    w = 1.0 / key.map(key.value_counts())
    mode = cfg.model.get("sample_weight", "equal")
    if mode in ("sqrt_share", "share") and "target_share" in rows:
        s = rows["target_share"].fillna(rows["target_share"].median()).clip(lower=1e-4)
        w = w * (np.sqrt(s) if mode == "sqrt_share" else s)
    base = _params(cfg)
    mono = [0] * len(MODEL_FEATURES)
    if cfg.model.get("monotone_heat", True):
        mono[MODEL_FEATURES.index("hdd_z")] = -1  # more heat in the window cannot raise the forecast
    med = lgb.LGBMRegressor(objective="regression", monotone_constraints=mono, **base)
    med.fit(X, y, sample_weight=w, categorical_feature=["commodity_code"])
    q = cfg.model.get("quantiles", [0.1, 0.9])
    lo = lgb.LGBMRegressor(objective="quantile", alpha=float(q[0]), **base)
    hi = lgb.LGBMRegressor(objective="quantile", alpha=float(q[1]), **base)
    lo.fit(X, y, sample_weight=w, categorical_feature=["commodity_code"])
    hi.fit(X, y, sample_weight=w, categorical_feature=["commodity_code"])
    return YieldModel(med, lo, hi, int(rows["season"].max()), len(rows), int(key.nunique()))
```

## 52. `src/harvestradar/paths.py`

```python
"""Repository paths. Everything is resolved from the repository root."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
# HARVESTRADAR_DATA_DIR relocates the whole data tree (used by tests and development fixtures)
DATA = Path(os.environ.get("HARVESTRADAR_DATA_DIR", ROOT / "data"))
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
DEMO = DATA / "demo"
REPORTS = ROOT / "reports"
MODELS_STORE = ROOT / "models_store"


def ensure_dirs() -> None:
    for p in (RAW, INTERIM, PROCESSED, DEMO, REPORTS, MODELS_STORE):
        p.mkdir(parents=True, exist_ok=True)
```

## 53. `src/harvestradar/pipeline.py`

```python
"""Pipeline orchestration: features -> models -> index -> notes -> demo snapshot."""

from __future__ import annotations

import json

import pandas as pd

from harvestradar.config import Settings
from harvestradar.paths import INTERIM, MODELS_STORE, PROCESSED, REPORTS


def build_features(cfg: Settings) -> None:
    from harvestradar.features.aggregate import country_daily, region_daily, to_country_season
    from harvestradar.features.stress import dekad_stress, to_dekad
    from harvestradar.ingest.power import load_cells

    INTERIM.mkdir(parents=True, exist_ok=True)
    cells = pd.read_parquet(PROCESSED / "sample_cells.parquet")
    oni = pd.read_parquet(PROCESSED / "oni.parquet")
    targets = pd.read_parquet(PROCESSED / "targets.parquet")
    end = pd.Timestamp(cfg.as_of_end)
    fridays = list(pd.date_range("1990-01-05", end, freq="W-FRI").date)
    base = tuple(int(x) for x in cfg.climatology["base"])
    for key, c in cfg.commodities.items():
        regions = pd.read_parquet(PROCESSED / f"regions_{key}.parquet")
        cw = cells[cells.commodity == key]
        data = load_cells(sorted(cw.cell_id.unique()))
        data = data[data.date <= end]
        rd = region_daily(cw, data)
        rd.to_parquet(INTERIM / f"region_daily_{key}.parquet", index=False)
        dek = to_dekad(rd, c.thresholds.get("heat_c", 30.0))
        dek = dek[dek["n"] >= 8]  # complete dekads only
        stress = dekad_stress(dek, base)
        stress.to_parquet(PROCESSED / f"stress_{key}.parquet", index=False)
        cd = country_daily(regions, rd)
        cd.to_parquet(INTERIM / f"country_daily_{key}.parquet", index=False)
        feat = to_country_season(cfg, key, cd, fridays, oni, targets)
        feat.to_parquet(PROCESSED / f"features_weekly_{key}.parquet", index=False)
        print(f"[features] {key}: {len(rd):,} region-days, {len(stress):,} region-dekads, "
              f"{len(feat):,} country-weeks")


def _panel(cfg: Settings) -> pd.DataFrame:
    feats = pd.concat([pd.read_parquet(PROCESSED / f"features_weekly_{k}.parquet") for k in cfg.commodities],
                      ignore_index=True)
    t = pd.read_parquet(PROCESSED / "targets.parquet")
    t["target_share"] = t["production_t"] / t["world_production_t"]  # known when the target is published
    t = t[["commodity", "country_iso3", "season", "yield_anom", "available_at", "target_share"]].rename(
        columns={"available_at": "target_available_at"})
    return feats.merge(t, on=["commodity", "country_iso3", "season"], how="left")


def _horizon_rows(p: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """For each country-season: the last pre-window week, the mid-window week, the end-of-season week."""
    out = {"pre": [], "mid": [], "end": []}
    for _, g in p.groupby(["commodity", "country_iso3", "season"]):
        g = g.sort_values("as_of")
        pre = g[g.progress == 0]
        pre = pre[pre.as_of < g[g.progress > 0].as_of.min()] if (g.progress > 0).any() else pre
        if len(pre):
            out["pre"].append(pre.iloc[[-1]])
        mid = g[(g.progress > 0) & (g.progress < 1)]
        if len(mid):
            out["mid"].append(mid.iloc[[(mid.progress - 0.5).abs().argmin()]])
        end = g[g.progress >= 1]
        if len(end):
            out["end"].append(end.iloc[[-1]])
    return {k: pd.concat(v) if v else pd.DataFrame() for k, v in out.items()}


def evaluate(cfg: Settings, preds: pd.DataFrame, meta: dict) -> dict:
    from harvestradar.models.validation import metrics

    first, last = int(cfg.model["first_test_year"]), int(cfg.model["last_test_year"])
    p = preds[preds.season.between(first, last) & preds.yield_anom.notna()]
    res: dict = {"test_seasons": [first, last], "target": {k: c.target for k, c in cfg.commodities.items()},
                 "horizons": {"pre": "last week before the first window", "mid": "middle of the window(s)",
                              "end": "last week the season is tracked (after its windows)"},
                 "by_commodity": {}, "pooled": {}, "vintages": {str(k): v for k, v in meta.items()}}
    hz = _horizon_rows(p)
    for h, d in hz.items():
        if d.empty:
            continue
        groups = [("pooled", d)] + [(k, d[d.commodity == k]) for k in cfg.commodities]
        for name, g in groups:
            y = g.yield_anom.to_numpy()
            r = {"model": metrics(y, g.pred_anom.to_numpy()), "trend_only": metrics(y, 0 * y),
                 "persistence": metrics(y, g.anom_last.fillna(0).to_numpy()),
                 "linear_3var": metrics(y, g.pred_linear.to_numpy())}
            rm, rz = r["model"].get("rmse"), r["trend_only"].get("rmse")
            r["rmse_vs_trend_pct"] = round(100 * (rm / rz - 1), 1) if rm and rz else None
            # headline metric (fixed before looking at the test period): weighted by share of world output
            ok = g.yield_anom.notna() & g.pred_anom.notna()
            w = g.loc[ok, "target_share"].fillna(0).to_numpy()
            if w.sum() > 0:
                e_m = (g.loc[ok, "yield_anom"] - g.loc[ok, "pred_anom"]).to_numpy()
                e_t = g.loc[ok, "yield_anom"].to_numpy()
                rmw, rzw = (float((w * e_m ** 2).sum() / w.sum()) ** 0.5, float((w * e_t ** 2).sum() / w.sum()) ** 0.5)
                r["rmse_weighted"] = {"model": rmw, "trend_only": rzw}
                r["rmse_vs_trend_weighted_pct"] = round(100 * (rmw / rzw - 1), 1)
            inside = ((g.yield_anom >= g.pred_lo) & (g.yield_anom <= g.pred_hi)).mean()
            r["band_coverage_p10_p90"] = round(float(inside), 3)
            if name == "pooled":
                res["pooled"][h] = r
            else:
                res["by_commodity"].setdefault(name, {})[h] = r
    return res


def _eval_markdown(ev: dict) -> str:
    lines = ["# Model evaluation (rolling origin, real publication dates)", "",
             f"Test seasons {ev['test_seasons'][0]} to {ev['test_seasons'][1]}. Each forecast uses a model trained "
             "only on seasons published before 1 January of the forecast year. All baselines are reported, "
             "without selection.", ""]
    for scope, block in [("Pooled", ev["pooled"])] + [(k, v) for k, v in ev["by_commodity"].items()]:
        lines += [f"## {scope}", "", "| Horizon | Method | n | RMSE | MAE | Spearman | Sign accuracy |",
                  "|---|---|---|---|---|---|---|"]
        for h, r in block.items():
            for m in ["model", "trend_only", "persistence", "linear_3var"]:
                x = r[m]

                def f(v):
                    return "" if v is None else f"{v:.3f}"
                lines.append(f"| {h} | {m} | {x.get('n', '')} | {f(x.get('rmse'))} | {f(x.get('mae'))} | "
                             f"{f(x.get('spearman'))} | {f(x.get('sign_accuracy'))} |")
            lines.append(f"| {h} | model RMSE vs trend only | | {r['rmse_vs_trend_pct']} % | | | |")
            if r.get("rmse_vs_trend_weighted_pct") is not None:
                lines.append(f"| {h} | same, weighted by share of world output (headline) | | "
                             f"{r['rmse_vs_trend_weighted_pct']} % | | | |")
        lines.append("")
    return "\n".join(lines)


def train_models(cfg: Settings) -> None:
    import joblib

    from harvestradar.models.explain import shap_by_prediction
    from harvestradar.models.validation import rolling_origin

    MODELS_STORE.mkdir(parents=True, exist_ok=True)
    panel = _panel(cfg)
    panel.to_parquet(PROCESSED / "model_panel.parquet", index=False)

    def store(v, model):
        joblib.dump(model, MODELS_STORE / f"yield_model_{v}.joblib")

    first = int(cfg.model.get("first_vintage", min(cfg.index_start.year, int(cfg.model["first_test_year"]))))
    preds, meta = rolling_origin(panel, cfg, first, cfg.as_of_end.year, store=store)
    preds.to_parquet(PROCESSED / "predictions_weekly.parquet", index=False)
    ev = evaluate(cfg, preds, meta)
    (PROCESSED / "model_eval.json").write_text(json.dumps(ev, indent=2))
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "model_eval.md").write_text(_eval_markdown(ev))
    latest = joblib.load(MODELS_STORE / f"yield_model_{cfg.as_of_end.year}.joblib")
    last = panel[panel.as_of == pd.Timestamp(cfg.as_of_end)]
    sh = shap_by_prediction(latest, last)
    shap = pd.concat([last[["commodity", "country_iso3", "season", "as_of"]], sh], axis=1)
    shap.to_parquet(PROCESSED / "shap_latest.parquet", index=False)
    print("[model] pooled end-of-season:", json.dumps(ev["pooled"].get("end", {}), indent=1)[:800])


def predict_weekly(cfg: Settings) -> None:
    """Daily job: predictions for the new Fridays with the stored vintage models (no retraining).
    Earlier rows are kept as they were published; training happens once a year (train_models)."""
    import joblib

    panel = _panel(cfg)
    panel.to_parquet(PROCESSED / "model_panel.parquet", index=False)
    old = pd.read_parquet(PROCESSED / "predictions_weekly.parquet")
    new = panel[panel.as_of > old.as_of.max()]
    if new.empty:
        print("[model] no new week to predict")
        return
    parts = []
    for y, g in new.groupby(new.as_of.dt.year):
        model = joblib.load(MODELS_STORE / f"yield_model_{y}.joblib")
        parts.append(pd.concat([g, model.predict(g).assign(vintage=y)], axis=1))
    preds = pd.concat([old] + parts, ignore_index=True)
    preds.to_parquet(PROCESSED / "predictions_weekly.parquet", index=False)
    print(f"[model] predicted {sum(len(p) for p in parts)} new rows up to {new.as_of.max():%Y-%m-%d}")


def build_index(cfg: Settings, reuse_climatology: bool = False) -> None:
    from harvestradar.signal.backtest import run_backtest
    from harvestradar.signal.events import build_events
    from harvestradar.signal.risk_index import build_risk_index

    preds = pd.read_parquet(PROCESSED / "predictions_weekly.parquet")
    targets = pd.read_parquet(PROCESSED / "targets.parquet")
    fao = pd.read_parquet(PROCESSED / "fao_qcl.parquet")
    import joblib

    from harvestradar.signal.risk_index import hindcast_climatology

    def load(v):
        p = MODELS_STORE / f"yield_model_{v}.joblib"
        return joblib.load(p) if p.exists() else None

    panel = pd.read_parquet(PROCESSED / "model_panel.parquet")
    ix = cfg.index
    vintages = sorted(preds.vintage.unique().tolist())
    cpath = PROCESSED / "model_climatology.parquet"
    if reuse_climatology and cpath.exists() and set(vintages) <= set(pd.read_parquet(cpath).vintage.unique()):
        clim = pd.read_parquet(cpath)  # hindcasts of past seasons: unchanged until a new vintage appears
    else:
        clim = hindcast_climatology(cfg, panel, load, fao, vintages, int(ix["standardize_years"]),
                                    int(ix["calendar_window_weeks"]), float(ix["sigma_floor"]))
        clim.to_parquet(cpath, index=False)
    risk = build_risk_index(cfg, preds, targets, fao, clim)
    risk = risk[risk.date >= pd.Timestamp(cfg.index_start)].reset_index(drop=True)
    risk.to_parquet(PROCESSED / "risk_index.parquet", index=False)
    prices = {k: pd.read_parquet(PROCESSED / f"prices_{k}.parquet") for k in cfg.commodities}
    ev = json.loads((PROCESSED / "model_eval.json").read_text())
    events = build_events(cfg, risk, prices, ev["vintages"])
    (PROCESSED / "events.json").write_text(json.dumps(events, indent=2, default=str))
    bt = run_backtest(cfg, risk, prices)
    (PROCESSED / "backtest.json").write_text(json.dumps(bt, indent=2, default=str))
    last = risk[risk.date == risk.date.max()][["commodity", "risk_z", "delta_prod_pct"]]
    print("[index] latest:", last.to_dict("records"))
    for k, e in events.items():
        print(f"[events] {k}: first above +2 {e['first_above_2']}, peak {e['peak_risk_z']} on {e['peak_date']}")


def build_daily(cfg: Settings) -> None:
    """Index every working day from `dates.daily_start`: features as of each day, predictions from the stored
    vintage of that year, standardised with the same model climatology. Then the price reaction."""
    import joblib

    from harvestradar.features.aggregate import to_country_season
    from harvestradar.signal.risk_index import build_risk_index

    oni = pd.read_parquet(PROCESSED / "oni.parquet")
    targets = pd.read_parquet(PROCESSED / "targets.parquet")
    fao = pd.read_parquet(PROCESSED / "fao_qcl.parquet")
    days = list(pd.bdate_range(cfg.dates["daily_start"], cfg.as_of_end).date)
    t = targets[["commodity", "country_iso3", "season", "yield_anom", "available_at"]]
    feats = []
    for key in cfg.commodities:
        cd = pd.read_parquet(INTERIM / f"country_daily_{key}.parquet")
        feats.append(to_country_season(cfg, key, cd, days, oni, targets))
    f = pd.concat(feats, ignore_index=True)
    f = f.merge(t.rename(columns={"available_at": "target_available_at"}), on=["commodity", "country_iso3", "season"],
                how="left")
    parts = []
    for y, g in f.groupby(f.as_of.dt.year):
        model = joblib.load(MODELS_STORE / f"yield_model_{y}.joblib")
        parts.append(pd.concat([g, model.predict(g).assign(vintage=y)], axis=1))
    preds = pd.concat(parts, ignore_index=True)
    preds.to_parquet(PROCESSED / "predictions_daily.parquet", index=False)
    # SHAP of the latest day, with that year's model (the Commodity page shows it)
    from harvestradar.models.explain import shap_by_prediction

    last = f[f.as_of == f.as_of.max()]
    model = joblib.load(MODELS_STORE / f"yield_model_{last.as_of.max().year}.joblib")
    shap = pd.concat([last[["commodity", "country_iso3", "season", "as_of"]], shap_by_prediction(model, last)], axis=1)
    shap.to_parquet(PROCESSED / "shap_latest.parquet", index=False)
    clim = pd.read_parquet(PROCESSED / "model_climatology.parquet")
    risk = build_risk_index(cfg, preds, targets, fao, clim)
    risk.to_parquet(PROCESSED / "risk_index_daily.parquet", index=False)
    last = risk[risk.date == risk.date.max()][["commodity", "risk_z", "delta_prod_pct"]]
    print("[daily] latest:", last.round(3).to_dict("records"))
    build_price_layers(cfg)


def build_price_layers(cfg: Settings) -> None:
    """Price reaction implied by the expected supply gap (descriptive, small sample), the climate fair value
    every trading day, and how closely index and price moved together. Re-run on every data update."""
    from harvestradar.signal.fair_value import build_fair_value, comovement, summary
    from harvestradar.signal.price_impact import implied_move, price_flexibility

    targets = pd.read_parquet(PROCESSED / "targets.parquet")
    risk = pd.read_parquet(PROCESSED / "risk_index_daily.parquet")
    weekly = pd.read_parquet(PROCESSED / "risk_index.parquet")
    prices = {k: pd.read_parquet(PROCESSED / f"prices_{k}.parquet") for k in cfg.commodities}
    flex = price_flexibility(cfg, targets, prices)
    events = json.loads((PROCESSED / "events.json").read_text())
    out = {"method": "price change of the average futures price over the marketing year, regressed on the realised "
                     "world supply gap of that year (FAOSTAT), 2002 onwards; applied to the model's expected gap",
           "commodities": {}, "episodes": {}}
    for key, fx in flex.items():
        last = risk[risk.commodity == key].dropna(subset=["risk_z"]).iloc[-1]
        out["commodities"][key] = {**fx, "date": last.date.strftime("%Y-%m-%d"),
                                   "delta_prod_pct": round(float(last.delta_prod_pct), 2),
                                   "reliable": fx["p_value"] < 0.10, **implied_move(fx, float(last.delta_prod_pct))}
    for name, ev in events.items():
        key, fx = ev["commodity"], flex.get(ev["commodity"])
        day = ev.get("first_above_2") or ev.get("peak_date")
        row = weekly[(weekly.commodity == key) & (weekly.date == pd.Timestamp(day))]
        if fx is None or row.empty:
            continue
        dp = float(row.delta_prod_pct.iloc[0])
        out["episodes"][name] = {"date": day, "delta_prod_pct": round(dp, 2), "reliable": fx["p_value"] < 0.10,
                                 **implied_move(fx, dp), "actual_pct": ev.get("price_change_pct"),
                                 "actual_window": [ev.get("price_from_date"), ev.get("price_to_date")]}
    fv = build_fair_value(cfg, flex, weekly, risk, prices)
    fv.to_parquet(PROCESSED / "fair_value_daily.parquet", index=False)
    out["fair_value"] = summary(fv, flex)
    out["comovement"] = comovement(weekly, prices)
    (PROCESSED / "price_impact.json").write_text(json.dumps(out, indent=2))
    print("[price] implied move now:", {k: (v["implied_pct"], v["reliable"]) for k, v in out["commodities"].items()})
    print("[price] fair value now:", {k: (v["fair"], v["close"], v["gap_to_fair_pct"]) for k, v in out["fair_value"].items()})


def run_all(cfg: Settings, skip_download: bool = False, deterministic_notes: bool = False) -> None:
    from harvestradar.demo.export import export_demo
    from harvestradar.report.email_note import export_week
    from harvestradar.report.weekly_note import build_notes

    if not skip_download:
        from harvestradar.geo.regions import build_all
        from harvestradar.ingest.enso import fetch_oni
        from harvestradar.ingest.power import fetch_cells
        from harvestradar.ingest.prices import fetch_prices
        from harvestradar.ingest.yields import load_faostat
        from harvestradar.models.targets import build_targets

        fao = load_faostat(cfg)
        build_targets(cfg, fao).to_parquet(PROCESSED / "targets.parquet", index=False)
        fetch_oni()
        fetch_prices(cfg)
        build_all(cfg)
        cells = pd.read_parquet(PROCESSED / "sample_cells.parquet").drop_duplicates("cell_id")
        fetch_cells(cells, cfg.weather_start.isoformat(), cfg.as_of_end.isoformat())
    build_features(cfg)
    train_models(cfg)
    build_index(cfg)
    build_daily(cfg)
    build_notes(cfg, deterministic=deterministic_notes)
    export_demo(cfg)
    export_week("latest", REPORTS / "notes")
```

## 54. `src/harvestradar/report/__init__.py`

```python

```

## 55. `src/harvestradar/report/checks.py`

```python
"""Guard rails for the daily note.

numbers: the model types no digit; after the software inserts the figures, every number in the note
         exists in the payload (rounding tolerance).
context: only known slots are used, the index slot is present, no country or region outside the
         payload is named, length is within bounds.
claims:  direction words agree with the signs of the figures (level, change, supply, price), El Nino is
         never presented as the driver, no investment advice.
"""

from __future__ import annotations

import re
from functools import lru_cache

SLOT_RE = re.compile(r"\{([A-Z][A-Z0-9_]*)\}")
NUM_RE = re.compile(r"(?<![\w.])[-+]?\d[\d,]*(?:\.\d+)?")


def slots_in(template: str) -> list[str]:
    return SLOT_RE.findall(template)


def fill(template: str, payload: dict) -> str:
    return SLOT_RE.sub(lambda m: payload["slots"][m.group(1)]["text"] if m.group(1) in payload["slots"]
                       else m.group(0), template)


def split_figure(text: str) -> tuple[str, str, str]:
    """'up 0.7% on the previous close' -> ('up ', '0.7%', ' on the previous close'): only the number goes in the
    pill, the words stay plain text. A text without a number gives ('', '', text)."""
    m = re.search(r"[-+]?[\d,]*\.?\d+(?:\s?(?:%|pp|points))?", text)
    return (text[:m.start()], m.group(0), text[m.end():]) if m else ("", "", text)


def _num(s: str) -> float:
    return float(s.replace(",", "").replace("+", ""))


def extract_numbers(text: str) -> list[float]:
    return [_num(x) for x in NUM_RE.findall(text)]


def check_numbers(template: str, payload: dict) -> tuple[bool, list[str]]:
    reasons = []
    bare = SLOT_RE.sub(" ", template)
    if re.search(r"\d", bare):
        reasons.append("the model typed a digit")
    if re.search(r"[-+\u2212]\s?\{[A-Z]", template):
        reasons.append("a sign typed in front of a figure that already carries its sign")
    allowed = []
    for s in payload["slots"].values():
        allowed += extract_numbers(s["text"])
    for x in extract_numbers(fill(template, payload)):
        if not any(abs(abs(x) - abs(a)) <= 0.006 * max(1.0, abs(a)) for a in allowed):
            reasons.append(f"number {x} not in payload")
    return (not reasons), reasons


@lru_cache(maxsize=1)
def _known_names() -> set[str]:
    import pycountry

    names = set()
    for c in pycountry.countries:
        for attr in ("name", "common_name", "official_name"):
            v = getattr(c, attr, None)
            if v:
                names.add(v)
    names |= {"United States", "US", "USA", "Russia", "Vietnam", "Ivory Coast", "Côte d'Ivoire", "China",
              "Brazil", "Argentina", "Ukraine", "India", "Mexico", "Ghana", "Indonesia", "Colombia",
              "Ethiopia", "Honduras", "Peru", "Nigeria", "Cameroon", "Ecuador", "Europe", "Africa",
              "Asia", "Iowa", "Illinois", "Mato Grosso", "Minas Gerais", "Corn Belt"}
    return names


def check_context(template: str, payload: dict, min_words: int = 50, max_words: int = 220,
                  require_index: bool = True) -> tuple[bool, list[str]]:
    reasons = []
    used = set(slots_in(template))
    unknown = used - set(payload["slots"])
    if unknown:
        reasons.append(f"unknown slots {sorted(unknown)}")
    if require_index and "RISK" not in used:
        reasons.append("index slot {RISK} missing")
    allowed = {s["text"] for s in payload["slots"].values() if s["kind"] == "name"}
    allowed |= set(payload.get("allowed_names", []))
    bare = SLOT_RE.sub(" ", template)
    for name in _known_names() | set(payload.get("all_region_names", [])):
        if len(name) < 4:
            continue
        if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", bare) and name not in allowed:
            reasons.append(f"name not in payload: {name}")
    n = len(fill(template, payload).split())
    if not (min_words <= n <= max_words):
        reasons.append(f"length {n} words")
    if "#" in template or re.search(r"^\s*[-*] ", template, re.M) or re.search(r"^\s*\*\*[^*]+\*\*:?\s*$", template, re.M):
        reasons.append("headings or bullets")
    counts = {}
    for sl in slots_in(template):
        if sl in payload["slots"] and payload["slots"][sl]["kind"] == "figure":
            counts[sl] = counts.get(sl, 0) + 1
    reused = [k for k, v in counts.items() if v > 1]
    if reused:
        reasons.append(f"figure used more than once: {reused}")
    low = bare.lower()
    for concept in ("stay tuned", "stability", "coming months", "dynamics", "suggest", "demand", "consumption", "stockpile", "stocks", "inventor", "export", "import", "disease",
                    "pest", "tariff", "currency", "dollar", "speculat", "investor", "balanced market", "sentiment"):
        if concept in low:
            reasons.append(f"concept not in the fact sheet: {concept}")
    return (not reasons), reasons


DOWN = r"\b(eas(e|ed|ing)|fell|fall(en|ing)?|declin\w*|decreas\w*|drop\w*|lower\w*|soften\w*|weaken\w*)\b"
UP = r"\b(rose|ris(en|ing)|increas\w*|climb\w*|jump\w*|higher|rall\w*|surg\w*|strengthen\w*|up)\b"


def _sentences(text: str) -> list[str]:
    return [s.strip().lower() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def check_claims(template: str, payload: dict) -> tuple[bool, list[str]]:
    f = payload["facts"]
    text = fill(template, payload)
    low = text.lower()
    reasons = []
    z = f["risk_z"]
    if z >= 1 and re.search(r"\b(low risk|below normal|near normal|calm|subdued|minimal)\b", low):
        reasons.append("level contradicts an elevated index")
    if -1 < z < 1 and re.search(r"\b(elevated|high risk|severe|alarming|sharp)\b", low):
        reasons.append("level contradicts a near-normal index")
    if z <= -1 and re.search(r"\b(elevated|high risk|severe)\b", low):
        reasons.append("level contradicts a low index")
    d = f["delta_prod_pct"]
    if d < 0 and re.search(r"\b(above trend|surplus|bumper|larger than usual)\b", low):
        reasons.append("supply direction contradicts the figure")
    if d > 0 and re.search(r"\b(below trend|shortfall|deficit)\b", low):
        reasons.append("supply direction contradicts the figure")
    for s in _sentences(text):
        if ("index" in s or "risk" in s) and "price" not in s and "futures" not in s:
            ch = f["risk_change_4w"]
            if ch > 0.05 and re.search(DOWN, s) and "supply" not in s:
                reasons.append(f"index change direction: '{s[:60]}'")
            if ch < -0.05 and re.search(UP, s) and "supply" not in s:
                reasons.append(f"index change direction: '{s[:60]}'")
        if ("price" in s or "futures" in s) and "index" not in s and "risk" not in s:
            pc = f["price_change_4w_pct"]
            if pc > 0.5 and re.search(DOWN, s):
                reasons.append(f"price direction: '{s[:60]}'")
            if pc < -0.5 and re.search(UP, s):
                reasons.append(f"price direction: '{s[:60]}'")
    if re.search(r"el ni(n|ñ)o[^.]*\b(driv\w*|caus\w*|explain\w*|behind|push\w*|fuel\w*)", low) or \
            re.search(r"\b(driv\w*|caus\w*|explain\w*|fuel\w*)\b[^.]*el ni(n|ñ)o", low):
        reasons.append("El Nino presented as a driver")
    vals = {k: v.get("value") for k, v in payload["slots"].items() if v["kind"] == "figure"}
    for sent in re.split(r"(?<=[.!?])\s+", template):
        sl = set(slots_in(sent))
        lo_s = SLOT_RE.sub(" ", sent).lower()
        if re.search(r"\b(due to|because of|caused by|from)\s*\{REGION\d_STRESS\}", sent):
            reasons.append("a stress level is presented as a cause")
        if re.search(r"\b(from|was|previous(ly)?)\s*\{RISK_CHANGE\}", sent):
            reasons.append("the four-week change is read as a previous level")
        if "RISK_CHANGE" in sl and "trend" in lo_s and "supply" not in lo_s:
            reasons.append("the four-week change is not described as a change over time")
        if re.search(r"el ni(n|ñ)o|\boni\b", lo_s) and re.search(
                r"\b(impact\w*|chance\w*|neutral|indicat\w*|suggest\w*|likely|effect\w*|affect\w*|influenc\w*|weak|strong|falls? into)\b", lo_s):
            reasons.append("El Nino reading interpreted beyond the fact sheet")
        if "supply" in lo_s and "price" not in lo_s and "futures" not in lo_s:
            if d < 0 and re.search(r"(higher|above|more|increas\w*|greater)[- ]?(than[- ]?)?(trend|usual|normal)?[- ]?supply|supply[^.]*\b(above|higher|increas\w*|surplus)", lo_s):
                reasons.append("supply said to be higher while the figure is below trend")
            if d > 0 and re.search(r"(lower|below|less|reduc\w*|short\w*)[- ]?(than[- ]?)?(trend|usual|normal)?[- ]?supply|supply[^.]*\b(below|lower|reduc\w*|shortfall|deficit)", lo_s):
                reasons.append("supply said to be lower while the figure is above trend")
            if re.search(r"(month ago|last month|four weeks|past weeks)", lo_s) and "index" not in lo_s:
                reasons.append("unsupported change in supply over time")
        contribs = [vals.get(k) for k in sl if k.startswith("DRIVER") and k.endswith("_CONTRIB")]
        contribs = [c for c in contribs if c is not None]
        if contribs and re.search(r"\b(risk|lower supply|reduc\w*|shortfall|decrease)", lo_s) and any(c > 0 for c in contribs):
            reasons.append("a supply-raising contribution is presented as a risk")
        if contribs and re.search(r"\b(increased supply|higher supply|surplus|adds? to supply)", lo_s) and any(c < 0 for c in contribs):
            reasons.append("a supply-lowering contribution is presented as adding supply")
    for clause in re.split(r"(?<=[.!?;])\s+", template):
        cl = SLOT_RE.sub(" ", clause).lower()
        cv = [vals.get(k) for k in slots_in(clause) if k.startswith("DRIVER") and k.endswith("_CONTRIB")]
        cv = [c for c in cv if c is not None]
        if any(c < 0 for c in cv) and re.search(r"lower(s|ing)? (the )?risk|reduc\w* (the )?risk|contribut\w* positively|"
                                                r"rais(e|es|ing) (world )?supply|add(s|ing)? (to )?supply", cl):
            reasons.append("a supply-lowering contribution is described as lowering the risk")
        if any(c > 0 for c in cv) and re.search(r"rais(e|es|ing) (the )?risk|contribut\w* negatively|"
                                                r"lower(s|ing)? (world )?supply", cl):
            reasons.append("a supply-raising contribution is described as raising the risk")
    if re.search(r"over four weeks,? (over|from|in|compared)|weeks over (the past )?four weeks", low) or \
            re.search(r"working day,? (since|from|compared|over)|previous close,? (since|from|compared|over)|"
                      r"\b(up|down|unchanged|rose|fell|increased|decreased|moved) (up|down|unchanged)\b|\bdekad", low):
        reasons.append("repeated timing or direction phrase")
    if re.search(r"\bel nino\b", low):
        reasons.append("El Niño misspelt")
    causes = f.get("region_causes", {})
    for sent in re.split(r"(?<=[.!?])\s+", template):
        regs = [x for x in slots_in(sent) if re.fullmatch(r"REGION\d", x)]
        said = [c for c in ("heat", "dry soils", "low rainfall") if c in sent.lower()]
        if regs and len(said) == 1 and any(causes.get(r) and causes.get(r) != said[0] for r in regs):
            reasons.append(f"cause '{said[0]}' given for a region whose main cause differs")
    wins = f.get("windows_open", [])
    if wins and re.search(r"\bno (critical )?windows? (is |are )?open", low):
        reasons.append("says no window is open while one is")
    if not wins:
        for s in _sentences(text):
            if re.search(r"window[^.]*\b(is|are) (now |currently )?open\b|window[^.]*\bhas opened", s) and \
                    not re.search(r"\bno (critical )?windows?\b|\bnot open\b|\bnone\b", s):
                reasons.append("says a window is open while none is")
    if re.search(r"\bnext (month|week)\b|\bcoming weeks\b", low):
        reasons.append("unsupported timing")
    if re.search(r"el ni(n|ñ)o[^.]*\b(may|could|will|likely to|expected to)\b[^.]*\b(impact|affect|influenc\w*|hurt)", low):
        reasons.append("El Nino presented as an expected cause")
    if re.search(r"\b(buy|sell|hedg\w*|go long|go short|investors should|we recommend|recommend\w*)\b", low):
        reasons.append("investment advice")
    return (not reasons), reasons
```

## 56. `src/harvestradar/report/email_note.py`

```python
"""Daily note as an email: a self-contained HTML email (inline CSS, table layout, 640 px, dark theme)
plus a plain-text alternative, written as .eml and .html. Offline: nothing is sent.

Every figure is taken from the note's own payload (slots and readings), never recomputed.
"""

from __future__ import annotations

import base64
import datetime as dt
import html as H
import json
import re
from email.message import EmailMessage
from email.utils import format_datetime
from importlib import resources
from pathlib import Path

import pandas as pd

from harvestradar.paths import DEMO, PROCESSED, ROOT
from harvestradar.report.checks import SLOT_RE, fill, split_figure

C = {"night": "#0B0F14", "console": "#131C27", "line": "#1E2935", "line_strong": "#2A3646", "frost": "#EAF0F5",
     "frost_2": "#C7D1DB", "muted": "#8A9AAB", "faint": "#6F7F90", "signal": "#FFB547", "heat": "#FF5A36"}
SANS = "Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
DISPLAY = "'Space Grotesk', Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', Menlo, Consolas, 'Courier New', monospace"
CHECKS = [("numbers_ok", "Numbers checked"), ("context_ok", "Context checked"), ("claims_ok", "Claims checked")]


def _logo_png() -> bytes:
    return resources.files("harvestradar.app").joinpath("static/brand/mark_on_signal_96.png").read_bytes()


def _pill(text: str, slot: str) -> str:
    return (f'<span data-fig="{slot}" style="font-family:{MONO};color:{C["signal"]};background:rgba(255,181,71,0.10);'
            f'border:1px solid rgba(255,181,71,0.55);border-radius:6px;padding:1px 6px;white-space:nowrap;'
            f'font-variant-numeric:tabular-nums;">{H.escape(text)}</span>')


def _body_html(template: str, payload: dict) -> str:
    paras = []
    for para in [p for p in template.split("\n\n") if p.strip()]:
        out, last = [], 0
        for m in SLOT_RE.finditer(para):
            out.append(H.escape(para[last:m.start()]))
            s = payload["slots"].get(m.group(1))
            if s is None:
                out.append(H.escape(m.group(0)))
            elif s["kind"] == "figure":
                pre, fig, rest = split_figure(s["text"])
                out.append(H.escape(pre) + (_pill(fig, m.group(1)) if fig else "") + H.escape(rest))
            else:
                out.append(f'<span style="color:{C["frost"]};font-weight:600;">{H.escape(s["text"])}</span>')
            last = m.end()
        out.append(H.escape(para[last:]))
        paras.append(f'<p style="margin:0 0 14px 0;font-family:{SANS};font-size:16px;line-height:26px;'
                     f'color:{C["frost_2"]};">{"".join(out)}</p>')
    return "".join(paras)


def _week_label(week: str) -> str:
    ts = pd.Timestamp(week)
    return f"{ts.day} {ts.strftime('%b %Y')}"


def render_note_email(note_row: dict | pd.Series, risk_rows: pd.DataFrame | None = None,
                      prices: dict | None = None, logo_src: str = "cid:hr-logo") -> str:
    """note_row: a row of notes.parquet. risk_rows and prices are accepted for API symmetry; the email uses
    the readings frozen in the note payload so that every figure matches the note."""
    row = dict(note_row)
    p = json.loads(row["payload"])
    week = p["week"]
    readings = "".join(
        f'<td width="33%" style="padding:0 5px;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{C["console"]};'
        f'border:1px solid {C["line_strong"]};border-radius:12px;"><tr><td style="padding:12px 14px;">'
        f'<div style="font-family:{MONO};font-size:13px;letter-spacing:2px;color:{C["muted"]};">'
        f'{H.escape(r["display"])} &middot; RISK INDEX</div>'
        f'<div data-fig="READING_{k.upper()}" style="font-family:{MONO};font-size:28px;line-height:36px;'
        f'color:{C["signal"]};font-variant-numeric:tabular-nums;">{H.escape(r["text"])}</div>'
        f'</td></tr></table></td>' for k, r in p.get("readings", {}).items())
    checks = "".join(
        f'<span style="display:inline-block;margin:0 8px 6px 0;padding:4px 10px;border:1px solid {C["line_strong"]};'
        f'border-radius:999px;font-family:{SANS};font-size:13px;color:{C["frost_2"]};">'
        f'{"&#10003;" if row.get(k) else "&#10005;"} {label}</span>' for k, label in CHECKS)
    model = row.get("model", "")
    tp = int(row.get("template_paragraphs", 0) or 0)
    who = ("Written from the fixed template" if model == "deterministic-template"
           else f"Written by a small AI model running locally ({H.escape(p.get('model_display', model.split('/')[-1]))})"
           + (f"; {tp} of 3 paragraphs from the fixed template" if tp else ""))
    sources = "".join(
        f'<tr><td style="padding:6px 0;border-top:1px solid {C["line"]};font-family:{MONO};font-size:13px;'
        f'color:{C["signal"]};white-space:nowrap;" data-fig="{k}">{H.escape(s["text"])}</td>'
        f'<td style="padding:6px 10px;border-top:1px solid {C["line"]};font-family:{SANS};font-size:13px;'
        f'color:{C["frost_2"]};">{H.escape(s["label"])}</td>'
        f'<td style="padding:6px 0;border-top:1px solid {C["line"]};font-family:{MONO};font-size:13px;'
        f'color:{C["faint"]};">{H.escape(s["source"])} &middot; {H.escape(s["date"])}</td></tr>'
        for k, s in p["slots"].items() if s["kind"] == "figure")
    title = H.escape(row.get("title") or p["title"])
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark"><title>{title}</title></head>
<body style="margin:0;padding:0;background:{C["night"]};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{C["night"]};">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="width:640px;max-width:640px;
background:{C["console"]};border:1px solid {C["line_strong"]};border-radius:18px;">
<tr><td style="padding:24px 28px 8px 28px;">
 <table role="presentation" cellpadding="0" cellspacing="0"><tr>
  <td style="padding-right:14px;"><img src="{logo_src}" width="48" height="48" alt="HarvestRadar" style="display:block;border-radius:11px;"></td>
  <td><div style="font-family:{DISPLAY};font-size:22px;line-height:28px;font-weight:700;color:{C["frost"]};">{title}</div>
  <div style="font-family:{SANS};font-size:14px;color:{C["muted"]};">HarvestRadar Daily &middot; {_week_label(week)}</div></td>
 </tr></table>
</td></tr>
<tr><td style="padding:16px 23px 8px 23px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>{readings}</tr></table></td></tr>
<tr><td style="padding:16px 28px 4px 28px;">{_body_html(row["template"], p)}</td></tr>
<tr><td style="padding:0 28px 6px 28px;">{checks}</td></tr>
<tr><td style="padding:0 28px 18px 28px;font-family:{MONO};font-size:13px;color:{C["muted"]};">{who}. Every figure is inserted by the software, with its source.</td></tr>
<tr><td style="padding:0 28px 20px 28px;">
 <div style="font-family:{MONO};font-size:13px;letter-spacing:2px;color:{C["muted"]};padding-bottom:6px;">SOURCES OF EVERY FIGURE</div>
 <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{sources}</table>
</td></tr>
<tr><td style="padding:14px 28px 22px 28px;border-top:1px solid {C["line"]};font-family:{MONO};font-size:13px;color:{C["faint"]};">
 Research output, not investment advice.<br>Produced offline by HarvestRadar. Nothing was sent by the app.
</td></tr>
</table></td></tr></table></body></html>"""


def render_text(note_row: dict | pd.Series) -> str:
    row = dict(note_row)
    p = json.loads(row["payload"])
    lines = [row.get("title") or p["title"], f"HarvestRadar Daily, {_week_label(p['week'])}", ""]
    lines += [f"{r['display']} risk index {r['text']}" for r in p.get("readings", {}).values()]
    lines += ["", fill(row["template"], p), ""]
    lines += ["Checks: " + ", ".join(f"{label} {'passed' if row.get(k) else 'FAILED'}" for k, label in CHECKS)]
    lines += ["", "Sources:"]
    lines += [f"  {s['text']}  {s['label']}  ({s['source']}, {s['date']})" for s in p["slots"].values()
              if s["kind"] == "figure"]
    lines += ["", "Research output, not investment advice."]
    return "\n".join(lines)


def write_eml(html: str, subject: str, week: str, commodity: str = "note", text: str = "",
              out_dir: Path | None = None, logo_png: bytes | None = None) -> Path:
    out_dir = Path(out_dir or ROOT / "reports" / "notes")
    out_dir.mkdir(parents=True, exist_ok=True)
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = "HarvestRadar Daily <daily@harvestradar.invalid>"
    msg["To"] = "undisclosed-recipients:;"
    sent = dt.datetime.fromisoformat(f"{week}T07:00:00+00:00")  # 07:00 on the note's day, deterministic
    msg["Date"] = format_datetime(sent)
    msg["Message-ID"] = f"<{week}.{commodity}@harvestradar.invalid>"
    msg.set_content(text or re.sub(r"<[^>]+>", " ", html))
    msg.add_alternative(html, subtype="html")
    logo = logo_png if logo_png is not None else _logo_png()
    msg.get_payload()[1].add_related(logo, "image", "png", cid="<hr-logo>", filename="harvestradar.png")
    eml = out_dir / f"{week}_{commodity}.eml"
    eml.write_bytes(bytes(msg))
    data_uri = "data:image/png;base64," + base64.b64encode(logo).decode()
    (out_dir / f"{week}_{commodity}.html").write_text(html.replace("cid:hr-logo", data_uri), encoding="utf-8")
    return eml


def eml_bytes(note_row: dict | pd.Series) -> tuple[bytes, str]:
    """For the app download button: (bytes of the .eml, file name)."""
    import tempfile

    row = dict(note_row)
    p = json.loads(row["payload"])
    with tempfile.TemporaryDirectory() as d:
        path = write_eml(render_note_email(row), row.get("title") or p["title"], p["week"], row["commodity"],
                         render_text(row), Path(d))
        return path.read_bytes(), path.name


def load_notes() -> pd.DataFrame:
    for d in (DEMO, PROCESSED):
        if (d / "notes.parquet").exists():
            return pd.read_parquet(d / "notes.parquet")
    raise FileNotFoundError("notes.parquet not found: run `harvestradar report notes` first")


def export_week(week: str = "latest", out_dir: Path | None = None) -> list[Path]:
    notes = load_notes()
    notes["week"] = pd.to_datetime(notes["week"])
    wk = notes["week"].max() if week == "latest" else pd.Timestamp(week)
    sel = notes[notes["week"] == wk]
    if sel.empty:
        raise ValueError(f"no notes for week {week}")
    out = []
    for row in sel.to_dict("records"):
        p = json.loads(row["payload"])
        out.append(write_eml(render_note_email(row), row["title"], p["week"], row["commodity"], render_text(row),
                             out_dir))
    return out
```

## 57. `src/harvestradar/report/llm.py`

```python
"""Local Hugging Face model (default Qwen/Qwen2.5-1.5B-Instruct) run on CPU with transformers.

Only used by the pipeline (make notes). The app never calls a model: it reads notes.parquet offline.
"""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def _load(model_id: str):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(4)
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32)
    model.eval()
    return tok, model


def generate(model_id: str, system: str, user: str, max_new_tokens: int = 320, seed: int = 42,
             sample: bool = False) -> str:
    import torch

    tok, model = _load(model_id)
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inputs = tok([text], return_tensors="pt")
    torch.manual_seed(seed)
    kw = dict(max_new_tokens=max_new_tokens, repetition_penalty=1.05)
    if sample:
        kw.update(do_sample=True, temperature=0.7, top_p=0.9)
    else:
        kw.update(do_sample=False)
    with torch.no_grad():
        out = model.generate(**inputs, **kw)
    return tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
```

## 58. `src/harvestradar/report/prompts/weekly_note_system.md`

```markdown
You write the HarvestRadar weekly note: a short, plain-English summary of harvest risk for one
agricultural commodity, for buyers, analysts and journalists.

Hard rules:
1. Never type a digit. Every figure is already prepared by the software as a slot in curly braces,
   for example {RISK} or {SUPPLY}. Copy slots exactly as written, including the braces, where the figure
   belongs. The software replaces each slot with the sourced figure.
2. Only use facts from the FACT SHEET. Do not add countries, regions, weather events, causes or prices
   that are not in it. Names of countries and regions are also slots (for example {DRIVER1}).
3. The El Nino reading is context only. Never say it drives, causes or explains the index.
4. No investment advice: never tell anyone to buy, sell, hedge or trade.
5. Write 3 short paragraphs, 80 to 150 words in total, no headings, no bullet points, no title:
   - what the index says this week and how it changed,
   - where the risk comes from (the contributors and the stressed regions),
   - what to watch next (open critical windows, price, climate context).
6. Calm, precise tone. No exclamation marks.
```

## 59. `src/harvestradar/report/weekly_note.py`

```python
"""Daily note (one per commodity and working day): payload -> local LLM writes text with slots -> software inserts sourced figures ->
three checks -> up to 2 retries -> deterministic template if the model keeps failing.

Output: data/processed/notes.parquet (commodity, week, title, template, markdown, numbers_ok, context_ok,
claims_ok, model, payload, seconds, attempts, failures).
"""

from __future__ import annotations


import json
import time
from importlib import resources

import pandas as pd

from harvestradar.config import Settings
from harvestradar.features.windows import window_open_on
from harvestradar.paths import PROCESSED
from harvestradar.report.checks import check_claims, check_context, check_numbers, fill
from harvestradar.signal.risk_index import country_name

FALLBACK_ID = "deterministic-template"


def fmt_signed(x: float, nd: int = 2, suffix: str = "") -> str:
    return f"{x:+.{nd}f}{suffix}"


def fmt_price(key: str, x: float) -> str:
    return f"{x:,.0f}" if key == "cocoa" else f"{x:,.2f}"


def move_phrase(x: float, nd: int, unit: str, since: str) -> str:
    """Direction written by the software, number unsigned: 'up 0.09 since the previous working day'."""
    if round(abs(x), nd) == 0:
        return f"unchanged {since}"
    return f"{'up' if x > 0 else 'down'} {abs(x):.{nd}f}{unit} {since}"


def level_word(z: float) -> str:
    return "elevated" if z >= 1 else ("below normal" if z <= -1 else "near normal")


def _top_regions(key: str, n: int = 3) -> tuple[list[dict], str, list[str]]:
    st = pd.read_parquet(PROCESSED / f"stress_{key}.parquet")
    rg = pd.read_parquet(PROCESSED / f"regions_{key}.parquet")
    last = st.dekad_end.max()
    s = st[st.dekad_end == last].merge(rg[["region_id", "adm1_name", "country_iso3", "weight"]], on="region_id")
    s["score"] = s["stress"].clip(lower=0) * s["weight"]
    top = s.sort_values("score", ascending=False).head(n)
    comp = pd.DataFrame({"heat": top[["tmax_z", "hdd_z"]].max(axis=1), "low rainfall": -top["precip_z"],
                         "dry soils": -top["sm_root_z"]})
    top = top.assign(cause=comp.idxmax(axis=1))
    return ([{"name": r.adm1_name, "country": r.country_iso3, "stress": float(r.stress), "cause": r.cause}
             for r in top.itertuples()],
            pd.Timestamp(last).strftime("%Y-%m-%d"), rg["adm1_name"].tolist())


def next_major_window(cfg: Settings, key: str, week: pd.Timestamp, contributors: list[dict]):
    """Next window to open among countries holding at least `major_share` of world supply."""
    c = cfg.commodities[key]
    major = float(cfg.index["major_share"]) * 100
    big = [ct["country"] for ct in json.loads(json.dumps(contributors)) if ct["share_pct"] >= major] or [c.main_country]
    best = None
    for ctry in big:
        for w in c.windows.get(ctry, []):
            for season in range(week.year - 1, week.year + 3):
                s0, _ = w.dates(season)
                if s0 > week.date() and (best is None or s0 < best[0]):
                    best = (s0, ctry, w.stage)
    if best is None:
        return None
    s0, ctry, stage = best
    return (f"{country_name(ctry)} {stage}", s0.strftime("%B %Y"), f"opens {s0.isoformat()}")


def build_payload(cfg: Settings, key: str, week: pd.Timestamp, risk: pd.DataFrame, prices: pd.DataFrame,
                  oni: pd.DataFrame) -> dict:
    c = cfg.commodities[key]
    r = risk[(risk.commodity == key) & (risk.date <= week)].dropna(subset=["risk_z"]).sort_values("date")
    cur = r.iloc[-1]
    prev = r.iloc[-2]
    px = prices[prices.date <= week].iloc[-1]
    px0 = prices[prices.date < px.date].iloc[-1]
    o = oni[oni.available_at <= week].iloc[-1]
    wk = week.strftime("%Y-%m-%d")
    d = lambda ts: pd.Timestamp(ts).strftime("%Y-%m-%d")  # noqa: E731
    slots: dict[str, dict] = {
        "RISK": dict(kind="figure", text=fmt_signed(cur.risk_z), value=round(float(cur.risk_z), 2),
                     label=f"{c.display} harvest-risk index", source="risk_index.parquet", date=wk,
                     detail=f"week of {week.strftime('%d %b %Y')}"),
        "RISK_CHANGE": dict(kind="figure", text=move_phrase(cur.risk_z - prev.risk_z, 2, "", "since the previous working day"),
                            value=round(float(cur.risk_z - prev.risk_z), 2), label="Change since the previous working day",
                            source="risk_index.parquet", date=wk, detail=f"vs {d(prev.date)}"),
        "SUPPLY": dict(kind="figure", text=fmt_signed(cur.delta_prod_pct, 1, "%"),
                       value=round(float(cur.delta_prod_pct), 1), label="Expected world supply vs normal",
                       source="model predictions", date=wk,
                       detail=f"p10 / p90 band {cur.delta_prod_lo_pct:+.1f}% to {cur.delta_prod_hi_pct:+.1f}%"),
        "PRICE": dict(kind="figure", text=fmt_price(key, px.close), value=round(float(px.close), 2),
                      label=f"{c.price_name} close", source=f"prices_{key}.parquet", date=d(px.date),
                      detail=f"{c.price_name} close, {c.price_unit}"),
        "PRICE_CHANGE": dict(kind="figure", text=move_phrase(100 * (px.close / px0.close - 1), 1, "%", "on the previous close"),
                             value=round(float(100 * (px.close / px0.close - 1)), 1), label="Price change on the previous close",
                             source=f"prices_{key}.parquet", date=d(px.date), detail=f"vs close of {d(px0.date)}"),
        "ONI": dict(kind="figure", text=fmt_signed(o.oni), value=round(float(o.oni), 2), label="El Niño index (ONI, sea temperature anomaly)",
                    source="oni.parquet", date=d(o.available_at), detail=f"ONI {o.label}, NOAA CPC"),
        "ONI_PERIOD": dict(kind="label", text=o.label.replace("-", " to ").title().replace(" To ", " to "), label="ONI season", source="oni.parquet",
                           date=d(o.available_at), detail="three-month season"),
    }
    contributors = json.loads(cur.contributors)
    drivers = []
    for i, ct in enumerate(contributors[:3], start=1):
        slots[f"DRIVER{i}"] = dict(kind="name", text=ct["name"], label=f"Contributor {i}",
                                   source="risk_index.parquet (contributors)", date=wk, detail=ct["country"])
        slots[f"DRIVER{i}_CONTRIB"] = dict(kind="figure", text=fmt_signed(ct["contrib_pct"], 2, " points"),
                                           value=round(ct["contrib_pct"], 2), label=f"{ct['name']}, world supply",
                                           source="risk_index.parquet (contributors)", date=wk,
                                           detail=f"season {ct['season']}, share {ct['share_pct']:.1f}%")
        drivers.append({"slot": f"DRIVER{i}", "effect": "lowers supply" if ct["contrib_pct"] < 0
                        else "raises supply", "window_open": ct["window_open"]})
    regions, dekad, all_regions = _top_regions(key)
    for i, rg in enumerate(regions, start=1):
        slots[f"REGION{i}"] = dict(kind="name", text=rg["name"], label=f"Stressed region {i}",
                                   source=f"stress_{key}.parquet", date=dekad, detail=rg["country"])
        slots[f"REGION{i}_STRESS"] = dict(kind="figure", text=fmt_signed(rg["stress"], 1),
                                          value=round(rg["stress"], 1), label=f"{rg['name']} stress",
                                          source=f"stress_{key}.parquet", date=dekad,
                                          detail=f"dekad ending {dekad}, z vs 2001-2020")
    open_now = [f"{country_name(ctry)} ({w.stage})" for ctry, ws in c.windows.items()
                for w in ws if window_open_on(week.date(), [w])]
    nxt = next_major_window(cfg, key, week, contributors)
    if nxt:
        slots["NEXT_WINDOW"] = dict(kind="name", text=nxt[0], label="Next major critical window",
                                    source="config/commodities.yaml", date=wk, detail=nxt[2])
        slots["NEXT_WINDOW_MONTH"] = dict(kind="label", text=nxt[1], label="Opens in",
                                          source="config/commodities.yaml", date=wk, detail=nxt[2])
    facts = {"risk_z": float(cur.risk_z), "risk_change_4w": float(cur.risk_z - prev.risk_z),
             "risk_change_1d": float(cur.risk_z - prev.risk_z),
             "delta_prod_pct": float(cur.delta_prod_pct),
             "price_change_4w_pct": float(100 * (px.close / px0.close - 1)), "oni": float(o.oni),
             "level": level_word(float(cur.risk_z)), "drivers": drivers, "windows_open": open_now,
             "oni_label": f"ONI {o.label}", "region_causes": {f"REGION{i}": rg["cause"]
                                                            for i, rg in enumerate(regions, start=1)}}
    names = [country_name(x) for x in c.countries] + [s.split(" (")[0] for s in open_now]
    readings = {}
    for k2, c2 in cfg.commodities.items():
        r2 = risk[(risk.commodity == k2) & (risk.date <= week)].dropna(subset=["risk_z"]).sort_values("date")
        if len(r2):
            readings[k2] = {"display": c2.display, "glyph": c2.glyph, "text": fmt_signed(r2.risk_z.iloc[-1]),
                            "value": round(float(r2.risk_z.iloc[-1]), 2), "source": "risk_index.parquet",
                            "date": r2.date.iloc[-1].strftime("%Y-%m-%d")}
    return {"commodity": key, "label": c.label, "display": c.display, "week": wk, "slots": slots,
            "readings": readings, "model_display": cfg.llm["display_name"],
            "facts": facts, "allowed_names": sorted(set(names)), "all_region_names": all_regions,
            "title": f"{c.label} risk {facts['level']}: {slots['RISK']['text']}"}


EXAMPLE = (
    "Cocoa harvest risk is near normal this week. The index reads {RISK}, a little lower than a month ago "
    "({RISK_CHANGE}), and expected world supply sits at {SUPPLY} against trend.\n\n"
    "Most of the movement comes from {DRIVER1}, at {DRIVER1_CONTRIB} of world supply, while {DRIVER2} adds "
    "{DRIVER2_CONTRIB}. Compared with their own history, the most stressed producing regions in the latest "
    "dekad were {REGION1} ({REGION1_STRESS}) and {REGION2} ({REGION2_STRESS}).\n\n"
    "The next period to watch is {NEXT_WINDOW}, which opens in {NEXT_WINDOW_MONTH}. Futures closed at {PRICE}, "
    "{PRICE_CHANGE}. For context, the El Niño reading is {ONI} ({ONI_PERIOD}).")


def fact_sheet(p: dict) -> str:
    f = p["facts"]
    sup = "below trend" if f["delta_prod_pct"] < 0 else "above trend"
    parts = [f"The commodity is {p['label']}. The harvest-risk index this week is {{RISK}}; its level is "
             f"{f['level']}. {{RISK_CHANGE}} tells how the index moved since the previous working day; it already "
             f"carries its direction, so write it as it is, without 'up', 'down', '+' or '-' before it. Expected world supply against trend is {{SUPPLY}}, which is {sup}. "
             "There is no information on how supply changed over time."]
    drv = []
    for d in f["drivers"]:
        s = d["slot"]
        drv.append(f"{{{s}}} contributes {{{s}_CONTRIB}} of world supply and {d['effect']}"
                   + (" (its critical window is open)" if d["window_open"] else ""))
    if drv:
        parts.append("The largest contributions to world supply, in points of world supply (negative values lower supply and raise the risk, "
                     "positive values add supply and lower the risk): " + "; ".join(drv) + ".")
    if "REGION1" in p["slots"]:
        regs = [f"{{REGION{i}}} ({{REGION{i}_STRESS}}, mainly {f['region_causes'][f'REGION{i}']})"
                for i in range(1, 4) if f"REGION{i}" in p["slots"]]
        parts.append("The most stressed producing regions over the last ten days, compared with their own history, "
                     "are " + ", ".join(regs) + ".")
    parts.append("Critical windows open now: " + (", ".join(f["windows_open"]) if f["windows_open"] else "none") + ".")
    if "NEXT_WINDOW" in p["slots"]:
        parts.append("The next major critical window to open is {NEXT_WINDOW}, in {NEXT_WINDOW_MONTH}.")
    parts.append("The futures price is {PRICE}, {PRICE_CHANGE} (the slot carries its direction).")
    parts.append("Climate context only, not a driver of the index: the El Niño reading is {ONI} ({ONI_PERIOD}).")
    return " ".join(parts)


def user_prompt(p: dict) -> str:
    return ("FACT SHEET\n" + fact_sheet(p) + "\n\nEXAMPLE OF THE EXPECTED STYLE (another commodity, other facts; "
            "do not copy its facts):\n" + EXAMPLE + "\n\nNow write the note for " + p["label"] + ". Three short "
            "paragraphs of prose, no title, no list, no digits: copy the {SLOTS} exactly.")


def template_note(p: dict) -> str:
    f = p["facts"]
    move = "{RISK_CHANGE}"
    first = (f"{p['label']} harvest risk is {f['level']} today. The index stands at {{RISK}}, {move}. "
             f"Expected world supply is {{SUPPLY}} compared with normal.")
    drv = [d["slot"] for d in f["drivers"]]
    second = ""
    if drv:
        second = "The largest contributions, in points of world supply, come from " + " and ".join(
            f"{{{s}}} ({{{s}_CONTRIB}})" for s in drv[:2]) + "."
    if "REGION1" in p["slots"]:
        second += (" The most stressed producing regions over the last ten days are {REGION1}, {REGION2} and {REGION3}."
                   if "REGION3" in p["slots"] else " The most stressed producing region over the last ten days is {REGION1}.")
    wins = f["windows_open"]
    third = ("Critical windows open now: " + ", ".join(wins) + ". " if wins else
             "No critical window is open for the main producers today. ")
    if "NEXT_WINDOW" in p["slots"]:
        third += "The next major window is {NEXT_WINDOW}, which opens in {NEXT_WINDOW_MONTH}. "
    third += ("Futures settled at {PRICE}, {PRICE_CHANGE}. "
              "Climate context: the El Niño reading is {ONI} ({ONI_PERIOD}), shown as background only.")
    return "\n\n".join(x.strip() for x in (first, second, third) if x.strip())


PARA_TASKS = [
    ("What the index says", "Write two sentences. First: the harvest-risk level today with {RISK}, and how the "
     "index moved with {RISK_CHANGE}. Second: expected world supply against trend with {SUPPLY}.",
     "Cocoa harvest risk is near normal today: the index reads {RISK}, {RISK_CHANGE}. Expected world supply "
     "sits at {SUPPLY} against trend."),
    ("Where the risk comes from", "Write two sentences. First: the countries with the largest contributions to "
     "world supply, each followed by its contribution slot in brackets. Second: the most stressed producing regions "
     "and the main cause given for them.",
     "The largest contributions to world supply come from {DRIVER1} ({DRIVER1_CONTRIB}) and {DRIVER2} "
     "({DRIVER2_CONTRIB}). The most stressed producing regions are {REGION1} and {REGION2}, mainly from heat."),
    ("What to watch", "Write two or three sentences: the critical windows (open now, or the next one), the futures "
     "price with {PRICE} and {PRICE_CHANGE}, and the El Niño reading {ONI} ({ONI_PERIOD}) as background only.",
     "No critical window is open today; the next one is {NEXT_WINDOW}, in {NEXT_WINDOW_MONTH}. Futures closed "
     "at {PRICE}, {PRICE_CHANGE}. For background, the El Niño reading is {ONI} ({ONI_PERIOD})."),
]


def paragraph_prompt(p: dict, i: int) -> str:
    title, task, example = PARA_TASKS[i]
    return ("FACT SHEET\n" + fact_sheet(p) + f"\n\nTASK: paragraph {i + 1} of 3, '{title}'. {task}\n"
            "Rules: plain prose, no title, no list, no digits, copy each {SLOT} exactly and at most once, never "
            "write + or - in front of a slot, use only facts from the sheet.\n"
            f"EXAMPLE (another commodity, other facts, do not copy its facts): {example}\n\nParagraph:")


def run_checks(template: str, p: dict, min_words: int = 50, max_words: int = 220, require_index: bool = True) -> dict:
    n_ok, n_r = check_numbers(template, p)
    c_ok, c_r = check_context(template, p, min_words=min_words, max_words=max_words, require_index=require_index)
    k_ok, k_r = check_claims(template, p)
    return {"numbers_ok": n_ok, "context_ok": c_ok, "claims_ok": k_ok, "reasons": n_r + c_r + k_r}


def write_note(cfg: Settings, p: dict, deterministic: bool = False) -> dict:
    """Three paragraphs, each written by the model and checked on its own (2 retries); a paragraph that keeps
    failing is replaced by the matching paragraph of the deterministic template. The whole note is checked again."""
    from harvestradar.report import llm

    system = resources.files("harvestradar.report").joinpath("prompts/weekly_note_system.md").read_text()
    fallback = template_note(p).split("\n\n")
    t0 = time.time()
    failures, attempts, paras, from_template = [], 0, [], 0
    model_id = cfg.llm["model_id"]
    for i in range(3):
        text = None
        if not deterministic:
            for attempt in range(1 + int(cfg.llm["retries"])):
                attempts += 1
                try:
                    out = llm.generate(model_id, system, paragraph_prompt(p, i), 160,
                                       seed=int(cfg.seed) + 10 * i + attempt, sample=attempt > 0)
                except Exception as e:  # noqa: BLE001
                    failures.append(f"paragraph {i + 1}: generation error {e}")
                    break
                out = out.strip().strip('"').strip()
                res = run_checks(out, p, min_words=12, max_words=90, require_index=(i == 0))
                if res["numbers_ok"] and res["context_ok"] and res["claims_ok"]:
                    text = out
                    break
                failures.append(f"paragraph {i + 1}, attempt {attempt + 1}: " + "; ".join(res["reasons"][:4]))
        if text is None:
            text = fallback[i] if i < len(fallback) else ""
            from_template += 1
        paras.append(text)
    note = "\n\n".join(x for x in paras if x)
    res = run_checks(note, p)
    if not (res["numbers_ok"] and res["context_ok"] and res["claims_ok"]):
        failures.append("whole note: " + "; ".join(res["reasons"][:4]))
        note, from_template = template_note(p), 3
        res = run_checks(note, p)
    model = FALLBACK_ID if from_template == 3 else model_id
    return {"template": note, "model": model, "seconds": round(time.time() - t0, 1), "attempts": attempts,
            "template_paragraphs": from_template, "failures": failures, **res}


def build_notes(cfg: Settings, days: int | None = None, deterministic: bool = False,
                only: list[str] | None = None, new_only: bool = False) -> pd.DataFrame:
    """only: regenerate these commodities and keep the other notes already in notes.parquet.
    new_only: write the days that have no note yet and keep the others of the window (daily job)."""
    risk = pd.read_parquet(PROCESSED / "risk_index_daily.parquet")
    oni = pd.read_parquet(PROCESSED / "oni.parquet")
    n = int(days or cfg.llm["days"])
    wk_list = list(pd.bdate_range(end=pd.Timestamp(cfg.as_of_end), periods=n))[::-1]
    path = PROCESSED / "notes.parquet"
    kept = pd.DataFrame()
    if new_only and path.exists():
        old = pd.read_parquet(path)
        old["week"] = pd.to_datetime(old["week"])
        kept = old[old.week.isin(wk_list)]
        have = set(kept.week)
        wk_list = [w for w in wk_list if w not in have]
    rows = []
    for week in wk_list:
        for key in cfg.commodities:
            if only and key not in only:
                continue
            prices = pd.read_parquet(PROCESSED / f"prices_{key}.parquet")
            p = build_payload(cfg, key, week, risk, prices, oni)
            res = write_note(cfg, p, deterministic=deterministic)
            md = f"# {p['title']}\n\n" + fill(res["template"], p)
            rows.append({"commodity": key, "week": week, "title": p["title"], "template": res["template"],
                         "markdown": md, "numbers_ok": res["numbers_ok"], "context_ok": res["context_ok"],
                         "claims_ok": res["claims_ok"], "model": res["model"],
                         "payload": json.dumps(p, ensure_ascii=False), "seconds": res["seconds"],
                         "attempts": res["attempts"], "template_paragraphs": res["template_paragraphs"],
                         "failures": json.dumps(res["failures"])})
            print(f"[notes] {week.date()} {key}: {res['model']} in {res['seconds']}s, attempts {res['attempts']}, "
                  f"template paragraphs {res['template_paragraphs']}, "
                  f"checks {res['numbers_ok']}/{res['context_ok']}/{res['claims_ok']}"
                  + (f" | {res['failures']}" if res["failures"] else ""))
    df = pd.DataFrame(rows)
    if len(kept):
        df = pd.concat([kept, df], ignore_index=True)
    if only and (PROCESSED / "notes.parquet").exists():
        old = pd.read_parquet(PROCESSED / "notes.parquet")
        df = pd.concat([old[~old.commodity.isin(only)], df], ignore_index=True)
    df = df.sort_values(["week", "commodity"], ascending=[False, True]).reset_index(drop=True)
    df.to_parquet(PROCESSED / "notes.parquet", index=False)
    return df
```

## 60. `src/harvestradar/signal/__init__.py`

```python

```

## 61. `src/harvestradar/signal/backtest.py`

```python
"""Pre-registered trading-rule test (research only, not investment advice).

signal_t = change of risk_z over `delta_weeks` weeks.
position = +1 if signal > theta and a major critical window is open; -1 if signal < -theta; else 0.
Computed on Friday, executed at the close of the next trading day (Monday), held one week.
Returns: front-month continuous futures, roll days neutralised. Costs in bps per unit of turnover.
Reported against buy and hold, long-in-major-windows, and 1,000 random permutations of the positions.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from harvestradar.config import Settings


def weekly_returns(prices: pd.DataFrame, dates: pd.Series) -> pd.Series:
    """Log return from the first trading close after each Friday to the first close after the next Friday."""
    px = prices.set_index("date").sort_index()
    r = px["ret_1d"].fillna(0.0)
    cum = r.cumsum()
    idx = px.index
    out = []
    for d in dates:
        i0 = idx.searchsorted(d + pd.Timedelta(days=1))
        i1 = idx.searchsorted(d + pd.Timedelta(days=8))
        if i1 >= len(idx) or i0 >= len(idx):
            out.append(np.nan)
            continue
        out.append(float(cum.iloc[i1] - cum.iloc[i0]))
    return pd.Series(out, index=dates.index)


def positions(risk: pd.DataFrame, theta: float, delta_weeks: int, long_only: bool = False) -> pd.Series:
    sig = risk["risk_z"].diff(delta_weeks)
    pos = np.where((sig > theta) & risk["major_window_open"], 1, np.where(sig < -theta, -1, 0))
    if long_only:
        pos = np.maximum(pos, 0)
    return pd.Series(pos, index=risk.index).fillna(0)


def perf(ret: pd.Series, pos: pd.Series, cost_bps: float) -> dict:
    turnover = pos.diff().abs().fillna(pos.abs())
    net = pos * ret - turnover * cost_bps / 1e4
    net = net.dropna()
    if net.std() == 0 or len(net) < 20:
        return {"weeks": int(len(net)), "ann_return": 0.0, "sharpe": 0.0, "trades": int((turnover > 0).sum())}
    ann = net.mean() * 52
    vol = net.std() * np.sqrt(52)
    down = net[net < 0].std() * np.sqrt(52)
    eq = net.cumsum()
    dd = float((eq - eq.cummax()).min())
    X = np.ones((len(net), 1))
    nw = sm.OLS(net.to_numpy(), X).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
    active = net[pos.loc[net.index] != 0]
    return {"weeks": int(len(net)), "ann_return": float(ann), "ann_vol": float(vol),
            "sharpe": float(ann / vol), "sortino": float(ann / down) if down > 0 else None,
            "max_drawdown_log": dd, "hit_rate": float((active > 0).mean()) if len(active) else None,
            "trades": int((turnover > 0).sum()), "exposure": float((pos != 0).mean()),
            "nw_tstat": float(nw.tvalues[0])}


def _sharpe(ret: np.ndarray, pos: np.ndarray, cost_bps: float) -> float:
    turnover = np.abs(np.diff(pos, prepend=0))
    net = pos * ret - turnover * cost_bps / 1e4
    net = net[np.isfinite(net)]
    sd = net.std(ddof=1)
    return float(net.mean() / sd * np.sqrt(52)) if sd > 0 else 0.0


def permutation_p(ret: pd.Series, pos: pd.Series, cost_bps: float, n: int, seed: int) -> float:
    """Share of random re-orderings of the same positions with a Sharpe ratio at least as high."""
    rng = np.random.default_rng(seed)
    r, p = ret.to_numpy(dtype=float), pos.to_numpy(dtype=float)
    obs = _sharpe(r, p, cost_bps)
    count = sum(_sharpe(r, rng.permutation(p), cost_bps) >= obs for _ in range(n))
    return float((count + 1) / (n + 1))


def run_backtest(cfg: Settings, risk: pd.DataFrame, prices: dict[str, pd.DataFrame]) -> dict:
    b = cfg.backtest
    cost = float(b["cost_bps_per_trade"]) + float(b.get("slippage_bps", 0))
    out = {"rule": {"signal": f"change in risk_z over {b['delta_weeks']} weeks",
                    "long": "signal > theta and a major critical window open", "short": "signal < -theta",
                    "execution": "next trading day close after the Friday update, held one week",
                    "theta": b["theta"], "delta_weeks": b["delta_weeks"], "cost_bps_per_trade": cost,
                    "permutations": b["permutations"], "start": b["start"]},
           "disclaimer": "Research output, not investment advice.", "commodities": {}}
    for key in cfg.commodities:
        r = risk[(risk.commodity == key) & (risk.date >= pd.Timestamp(b["start"]))].dropna(subset=["risk_z"])
        r = r.reset_index(drop=True)
        ret = weekly_returns(prices[key], r["date"])
        pos = positions(r, float(b["theta"]), int(b["delta_weeks"]))
        res = perf(ret, pos, cost)
        res["permutation_p"] = permutation_p(ret, pos, cost, int(b["permutations"]), int(cfg.seed))
        bench = {"buy_and_hold": perf(ret, pd.Series(1, index=r.index), 0.0),
                 "long_in_major_windows": perf(ret, r["major_window_open"].astype(int), cost),
                 "long_only_rule": perf(ret, positions(r, float(b["theta"]), int(b["delta_weeks"]), True), cost)}
        grid = []
        for th in b["grid_theta"]:
            for dw in b["grid_delta"]:
                pp = positions(r, float(th), int(dw))
                g = perf(ret, pp, cost)
                g.update(theta=th, delta_weeks=dw,
                         permutation_p=permutation_p(ret, pp, cost, int(b["permutations"]) // 4, int(cfg.seed)))
                grid.append(g)
        out["commodities"][key] = {"rule": res, "benchmarks": bench, "grid": grid,
                                   "best_grid_p": min(g["permutation_p"] for g in grid)}
    n_c = len(out["commodities"])
    n_g = len(b["grid_theta"]) * len(b["grid_delta"])
    out["best_p_overall"] = min(v["best_grid_p"] for v in out["commodities"].values())
    out["best_rule_p"] = min(v["rule"]["permutation_p"] for v in out["commodities"].values())
    # multiple testing: Bonferroni over the commodities (rule) and over commodities x grid (best of the grid)
    out["best_rule_p_corrected"] = min(1.0, out["best_rule_p"] * n_c)
    out["best_p_overall_corrected"] = min(1.0, out["best_p_overall"] * n_c * n_g)
    out["tests"] = {"commodities": n_c, "grid_cells": n_g, "correction": "Bonferroni"}
    return out
```

## 62. `src/harvestradar/signal/events.py`

```python
"""Event studies: 2012 US drought (maize), 2021 Brazil frost (arabica), 2023-2024 cocoa.

Nothing is assumed: for each episode we report when risk_z first crossed +2 (if it did), its peak,
the futures price path and a lagged cross-correlation between index changes and price returns.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from harvestradar.config import Settings

WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
         10: "ten", 11: "eleven", 12: "twelve"}


def price_on(prices: pd.DataFrame, day: pd.Timestamp) -> tuple[pd.Timestamp, float] | tuple[None, None]:
    p = prices[prices.date <= day]
    if p.empty:
        return None, None
    r = p.iloc[-1]
    return r.date, float(r.close)


def lag_correlation(idx: pd.DataFrame, prices: pd.DataFrame, max_lag: int = 8) -> dict[int, float]:
    """corr(change in risk_z at week t, weekly log price return at week t + lag)."""
    w = prices.set_index("date")["close"].resample("W-FRI").last().dropna()
    r = np.log(w).diff()
    z = idx.set_index("date")["risk_z"].diff()
    out = {}
    for lag in range(-max_lag, max_lag + 1):
        a = pd.concat([z, r.shift(-lag)], axis=1).dropna()
        out[lag] = round(float(a.iloc[:, 0].corr(a.iloc[:, 1])), 3) if len(a) > 10 else None
    return out


def episode(cfg: Settings, name: str, spec: dict, risk: pd.DataFrame, prices: pd.DataFrame,
            vintages: dict) -> dict:
    key = spec["commodity"]
    c = cfg.commodities[key]
    start, end = pd.Timestamp(spec["start"]), pd.Timestamp(spec["end"])
    show_end = pd.Timestamp(spec.get("show_end", spec["end"]))
    r = risk[(risk.commodity == key) & risk.date.between(start, end)].sort_values("date")
    above = r[r.risk_z >= 2.0]
    first = above.date.iloc[0] if len(above) else None
    peak = r.loc[r.risk_z.idxmax()] if len(r) else None
    pr = prices[prices.date.between(start - pd.Timedelta(days=7), end)]
    path = []
    for row in r.itertuples():
        d, close = price_on(prices, row.date)
        path.append({"date": row.date.strftime("%Y-%m-%d"), "risk_z": round(float(row.risk_z), 3),
                     "close": close})
    out = {"name": name, "label": spec["label"], "commodity": key, "start": spec["start"], "end": spec["end"],
           "show_end": show_end.strftime("%Y-%m-%d"), "price_name": c.price_name, "price_unit": c.price_unit,
           "first_above_2": first.strftime("%Y-%m-%d") if first is not None else None,
           "peak_risk_z": round(float(peak.risk_z), 3) if peak is not None else None,
           "peak_date": peak.date.strftime("%Y-%m-%d") if peak is not None else None,
           "verdict": "missed"}
    # price window: from the first +2 crossing (or from the episode start when the index missed it)
    from_day = first if first is not None and first <= show_end else start
    d0, p0 = price_on(prices, from_day)
    d1, p1 = price_on(prices, show_end)
    out.update(price_from=p0, price_from_date=d0.strftime("%Y-%m-%d") if d0 is not None else None,
               price_from_kind="signal" if first is not None and first <= show_end else "episode start",
               price_to=p1, price_to_date=d1.strftime("%Y-%m-%d") if d1 is not None else None,
               price_change_pct=round(100 * (p1 / p0 - 1), 1) if p0 and p1 else None)
    if len(pr):
        mx = pr.loc[pr.close.idxmax()]
        out.update(price_max=float(mx.close), price_max_date=mx.date.strftime("%Y-%m-%d"))
        # "caught" only if the index crossed +2 before the futures price peaked: before the price does
        if first is not None:
            out["verdict"] = "caught" if first <= mx.date else "late"
    # weeks between the signal and the opening of the main country's window, from config
    stage_country = spec.get("stage_country", c.main_country)
    if first is not None:
        fd = first.date()
        spans = []
        for season in (fd.year - 1, fd.year, fd.year + 1):
            for w in c.windows[stage_country]:
                ws, we = w.dates(season)
                spans.append((ws, we, w.stage))
        inside = [(ws, we, st) for ws, we, st in spans if ws <= fd <= we]
        ahead = sorted((ws, st) for ws, we, st in spans if ws > fd)
        if inside:
            ws, _, stage = inside[0]
            days = (fd - ws).days
            out["window_stage"], out["window_open_date"] = stage, ws.isoformat()
            out["weeks_before_window"] = -round(days / 7)
            out["lead_text"] = (f"as {stage} began" if days == 0 else
                                f"{WORDS.get(days, str(days))} day{'s' if days != 1 else ''} into {stage}")
        elif ahead and (ahead[0][0] - fd).days <= 120:
            ws, stage = ahead[0]
            weeks = round((ws - fd).days / 7)
            out["window_stage"], out["window_open_date"], out["weeks_before_window"] = stage, ws.isoformat(), weeks
            out["lead_text"] = f"{WORDS.get(weeks, str(weeks))} week{'s' if weeks != 1 else ''} before {stage}"
    v = vintages.get(int(start.year)) or vintages.get(str(start.year))
    if v:
        out["model_trained_on_seasons_up_to"] = v["trained_on_seasons_up_to"]
    out["lag_correlation"] = lag_correlation(r[["date", "risk_z"]], prices)
    out["path"] = path
    return out


def build_events(cfg: Settings, risk: pd.DataFrame, prices: dict[str, pd.DataFrame], vintages: dict) -> dict:
    return {name: episode(cfg, name, spec, risk, prices[spec["commodity"]], vintages)
            for name, spec in cfg.episodes.items()}
```

## 63. `src/harvestradar/signal/fair_value.py`

```python
"""Climate fair value: the futures price that today's expected world supply gap justifies, on its own.

For each crop and each trading day t:
  anchor  A_t = average close over the last 12 months (252 trading days): "no new weather news"
  gap     G_t = expected world supply vs normal from the index (in %), latest value known on day t
  slope   b   = price flexibility from price_impact.py (% price change per 1 % of world supply gap)
  fair    F_t = A_t x exp(b x G_t / 100)
  band    80 %: A_t x exp((b +/- 1.28 se_b) x G_t / 100), the same range as the implied move on the price card.
          It covers the uncertainty of the price reaction, not of the harvest forecast itself (the index's own
          80 % range of world supply sums country ranges, so it is a worst case and far too wide to price on).
  gap to fair value = close / F_t - 1

What it is: the climate component of fair value. What it is not: a full valuation. Demand, stocks, the dollar,
fund positioning and other origins move prices too; the distance between the price and F_t is what they
explain. The index is weekly before `dates.daily_start` and daily after.

Also here: how closely the index and the price moved together (weekly changes, critical windows, the next
13 weeks), so the app can say plainly why the two lines need not move together.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

Z80 = 1.2816
ANCHOR_DAYS = 252


def index_path(weekly: pd.DataFrame, daily: pd.DataFrame, key: str, daily_start: str) -> pd.DataFrame:
    """Weekly index before daily_start, daily index from it: one series of (date, gap, gap_lo, gap_hi, z)."""
    cols = ["date", "delta_prod_pct", "delta_prod_lo_pct", "delta_prod_hi_pct", "risk_z"]
    w = weekly[(weekly.commodity == key) & (weekly.date < pd.Timestamp(daily_start))][cols]
    d = daily[(daily.commodity == key) & (daily.date >= pd.Timestamp(daily_start))][cols]
    out = pd.concat([w, d], ignore_index=True).dropna(subset=["delta_prod_pct"]).sort_values("date")
    out["date"] = out["date"].astype("datetime64[ns]")
    return out.reset_index(drop=True)


def fair_value_series(prices: pd.DataFrame, path: pd.DataFrame, flex: dict) -> pd.DataFrame:
    b, se = float(flex["slope_pct_per_pct"]), float(flex["se"])
    p = prices[["date", "close"]].dropna().sort_values("date").copy()
    p["date"] = p["date"].astype("datetime64[ns]")
    p["anchor"] = p["close"].rolling(ANCHOR_DAYS, min_periods=200).mean()
    path = path.assign(date=path["date"].astype("datetime64[ns]")).sort_values("date")
    p = pd.merge_asof(p, path, on="date", direction="backward").dropna(subset=["anchor", "delta_prod_pct"])
    g = p["delta_prod_pct"]
    mid, s = b * g, (Z80 * se * g).abs()
    out = pd.DataFrame({
        "date": p["date"], "close": p["close"], "anchor": p["anchor"], "supply_gap_pct": g, "risk_z": p["risk_z"],
        "premium_pct": 100 * (np.exp(mid / 100) - 1),
        "fair": p["anchor"] * np.exp(mid / 100),
        "fair_lo": p["anchor"] * np.exp((mid - s) / 100),
        "fair_hi": p["anchor"] * np.exp((mid + s) / 100),
    })
    out["gap_to_fair_pct"] = 100 * (out["close"] / out["fair"] - 1)
    return out.reset_index(drop=True)


def build_fair_value(cfg, flex: dict, weekly: pd.DataFrame, daily: pd.DataFrame,
                     prices: dict[str, pd.DataFrame]) -> pd.DataFrame:
    parts = []
    for key, fx in flex.items():
        path = index_path(weekly, daily, key, str(cfg.dates["daily_start"]))
        parts.append(fair_value_series(prices[key], path, fx).assign(commodity=key))
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)


def summary(fv: pd.DataFrame, flex: dict) -> dict:
    """Latest reading per crop, for the app and the notes."""
    out = {}
    for key, g in fv.groupby("commodity"):
        last = g.iloc[-1]
        fx = flex[key]
        out[key] = {"date": last.date.strftime("%Y-%m-%d"), "close": round(float(last.close), 2),
                    "anchor": round(float(last.anchor), 2), "supply_gap_pct": round(float(last.supply_gap_pct), 2),
                    "premium_pct": round(float(last.premium_pct), 2), "fair": round(float(last.fair), 2),
                    "fair_lo": round(float(last.fair_lo), 2), "fair_hi": round(float(last.fair_hi), 2),
                    "gap_to_fair_pct": round(float(last.gap_to_fair_pct), 2),
                    "slope_pct_per_pct": fx["slope_pct_per_pct"], "se": fx["se"], "reliable": fx["p_value"] < 0.10,
                    "anchor_days": ANCHOR_DAYS}
    return out


def comovement(weekly: pd.DataFrame, prices: dict[str, pd.DataFrame], start: str = "2006-01-01") -> dict:
    """Correlations between the weekly index and the futures price since `start`."""
    out = {}
    for key, pr in prices.items():
        r = weekly[(weekly.commodity == key) & (weekly.date >= pd.Timestamp(start))].dropna(subset=["risk_z"])
        if len(r) < 100:
            continue
        r = r.set_index("date").sort_index()
        p = pr.assign(date=pr.date.astype("datetime64[ns]")).set_index("date")["close"].sort_index()
        lp = np.log(p).resample("W-FRI").last().reindex(r.index, method="ffill")
        dz, ret = r.risk_z.diff(), 100 * lp.diff()
        win = r.major_window_open.astype(bool)
        fwd = 100 * (lp.shift(-13) - lp)

        def c(a, b):
            v = a.corr(b)
            return None if v is None or math.isnan(v) else round(float(v), 2)

        out[key] = {"from": start, "weeks": int(len(r)), "weeks_in_windows": int(win.sum()),
                    "weekly_changes": c(dz, ret), "weekly_changes_in_windows": c(dz[win], ret[win]),
                    "index_vs_next_13_weeks": c(r.risk_z, fwd)}
    return out
```

## 64. `src/harvestradar/signal/price_impact.py`

```python
"""How much should the futures price move for a given supply gap? (price flexibility)

For each crop and marketing year Y (2002 to the latest published season):
  x = realised world supply gap: sum over modelled countries of share x production (or yield) anomaly, in %
  y = change of the average front-month futures price, marketing year Y vs Y-1, in % (log)
Slope b = % price change per 1 % of world supply gap (expected negative: a shortfall lifts prices).
Applied to the model's expected supply gap today: implied move = b x dP, with an 80 % band (b +/- 1.28 se).
A small-sample, descriptive estimate: reported with n, R2 and p-value, never as a forecast of the price.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

MARKETING_START = {"maize": 9, "coffee": 7, "cocoa": 10}  # first month of the marketing year


def marketing_year_prices(prices: pd.DataFrame, start_month: int) -> pd.Series:
    p = prices.set_index("date")["close"]
    my = p.index.year - (p.index.month < start_month).astype(int)
    avg = np.log(p).groupby(my).mean()
    counts = p.groupby(my).size()
    return avg[counts >= 200]  # complete marketing years only


def world_gap(targets: pd.DataFrame, key: str, countries: list[str]) -> pd.Series:
    t = targets[(targets.commodity == key) & targets.country_iso3.isin(countries)].dropna(subset=["yield_anom"])
    t = t.assign(share=t.production_t / t.world_production_t)
    return (100 * t.share * t.yield_anom).groupby(t.season).sum()


def price_flexibility(cfg, targets: pd.DataFrame, prices: dict[str, pd.DataFrame]) -> dict:
    out = {}
    for key, c in cfg.commodities.items():
        lp = marketing_year_prices(prices[key], MARKETING_START[key])
        dy = (100 * lp.diff()).dropna()
        gap = world_gap(targets, key, c.countries)
        d = pd.concat([gap.rename("gap"), dy.rename("dprice")], axis=1).dropna()
        d = d[d.index >= 2002]
        if len(d) < 8:
            continue
        m = sm.OLS(d["dprice"], sm.add_constant(d["gap"])).fit(cov_type="HC1")
        b, se = float(m.params["gap"]), float(m.bse["gap"])
        out[key] = {"slope_pct_per_pct": round(b, 2), "se": round(se, 2), "p_value": round(float(m.pvalues["gap"]), 3),
                    "r2": round(float(m.rsquared), 2), "n": int(len(d)), "years": [int(d.index.min()), int(d.index.max())],
                    "marketing_year_start_month": MARKETING_START[key],
                    "points": [[int(y), round(float(r.gap), 2), round(float(r.dprice), 1)] for y, r in d.iterrows()]}
    return out


def implied_move(flex: dict, delta_prod_pct: float) -> dict:
    b, se = flex["slope_pct_per_pct"], flex["se"]
    lo, hi = sorted([(b - 1.28 * se) * delta_prod_pct, (b + 1.28 * se) * delta_prod_pct])
    return {"implied_pct": round(b * delta_prod_pct, 1), "low_pct": round(lo, 1), "high_pct": round(hi, 1)}
```

## 65. `src/harvestradar/signal/risk_index.py`

```python
"""Harvest-risk index (SPEC 5.9).

Expected world production gap:   dP_c(t) = sum_country share(t) x pred_anom(t)   (percent)
Risk index:                      risk_z(t) = -(dP_c(t) - mean) / sd

mean and sd are the model climatology, as in seasonal forecasting: the same vintage model re-forecasts the
same weeks of the year (within +/- `calendar_window_weeks`) over the previous `standardize_years` years
(rolling history, past years only), so the index reads "how unusual is this week's forecast for this time of
year". This removes the drift between vintages that a raw history of past forecasts would carry. The sd is
floored at `sigma_floor` x the sd of all weeks of the same hindcast, so that calm periods stay calm.
(`standardize` below, on the raw history of past forecasts, was the first version; it gave a skewed index.)
Positive risk_z = higher supply risk than usual for this time of year. Shares are those known at t
(FAOSTAT, latest published years) or MapSPAM 2020 country totals where FAOSTAT cannot split the crop
(arabica).
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pycountry

from harvestradar.config import Settings
from harvestradar.models.targets import country_shares
from harvestradar.paths import PROCESSED


def country_name(iso3: str) -> str:
    special = {"USA": "United States", "RUS": "Russia", "IRN": "Iran", "VNM": "Vietnam", "BOL": "Bolivia",
               "TZA": "Tanzania", "VEN": "Venezuela", "LAO": "Laos", "COD": "DR Congo", "CIV": "Côte d'Ivoire",
               "KOR": "South Korea", "PRK": "North Korea", "SYR": "Syria", "MDA": "Moldova"}
    if iso3 in special:
        return special[iso3]
    c = pycountry.countries.get(alpha_3=iso3)
    return getattr(c, "common_name", None) or (c.name if c else iso3)


def shares_at(cfg: Settings, key: str, fao: pd.DataFrame, t: pd.Timestamp) -> pd.Series:
    c = cfg.commodities[key]
    if c.share_source == "mapspam":
        s = pd.read_parquet(PROCESSED / f"country_shares_{key}.parquet").set_index("country_iso3")["share"]
        return s
    return country_shares(fao, key, t)


def standardize(delta: pd.Series, years: int, window_weeks: int, min_years: int, floor: float) -> pd.DataFrame:
    """delta: weekly dP indexed by date. Returns mean, sd (floored) and z, from past history only."""
    d = delta.sort_index()
    dates = d.index
    woy = dates.isocalendar().week.to_numpy().astype(int)
    vals = d.to_numpy()
    out = []
    for i, t in enumerate(dates):
        lo, hi = t - pd.DateOffset(years=years), t - pd.Timedelta(weeks=52)
        m = (dates >= lo) & (dates <= hi)
        if not m.any():
            out.append((np.nan, np.nan, np.nan))
            continue
        diff = np.abs(woy[m] - woy[i])
        diff = np.minimum(diff, 52 - diff)
        near = diff <= window_weeks
        hv = vals[m][near]
        yrs = pd.DatetimeIndex(dates[m][near]).year.nunique()
        if yrs < min_years or len(hv) < 3:
            out.append((np.nan, np.nan, np.nan))
            continue
        mu, sd = float(np.mean(hv)), float(np.std(hv, ddof=1))
        sd_all = float(np.std(vals[m], ddof=1))
        sd = max(sd, floor * sd_all)
        out.append((mu, sd, -(vals[i] - mu) / sd if sd > 0 else np.nan))
    return pd.DataFrame(out, index=dates, columns=["mu", "sd", "risk_z"])


def build_risk_index(cfg: Settings, preds: pd.DataFrame, targets: pd.DataFrame, fao: pd.DataFrame,
                     clim: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = []
    major = float(cfg.index["major_share"])
    for key, c in cfg.commodities.items():
        p = preds[preds.commodity == key]
        cache: dict = {}
        for t, g in p.groupby("as_of"):
            ykey = (t.year, t.month)  # shares and sigma change at most monthly
            if ykey not in cache:
                cache[ykey] = shares_at(cfg, key, fao, t)
            sh = cache[ykey]
            g = g.assign(share=g.country_iso3.map(sh).fillna(0.0))
            contrib = 100 * g.share * g.pred_anom
            delta = float(contrib.sum())
            lo = float((100 * g.share * g.pred_lo).sum())
            hi = float((100 * g.share * g.pred_hi).sum())
            cov = float(g.share.sum())
            g = g.assign(contrib=contrib).sort_values("contrib", key=np.abs, ascending=False)
            contributors = [{
                "country": r.country_iso3, "name": country_name(r.country_iso3),
                "contrib_pct": round(float(r.contrib), 3), "pred_anom_pct": round(100 * float(r.pred_anom), 2),
                "pred_lo_pct": round(100 * float(r.pred_lo), 2), "pred_hi_pct": round(100 * float(r.pred_hi), 2),
                "share_pct": round(100 * float(r.share), 2), "season": int(r.season),
                "window_open": bool(r.window_open)} for r in g.itertuples()]
            rows.append({
                "commodity": key, "date": t,
                "delta_prod_pct": round(delta, 4), "delta_prod_lo_pct": round(lo, 4),
                "delta_prod_hi_pct": round(hi, 4),
                "coverage_share": round(cov, 4),
                "major_window_open": bool((g.window_open & (g.share >= major)).any()),
                "contributors": json.dumps(contributors[:5], ensure_ascii=False),
                "contributors_all": json.dumps(contributors, ensure_ascii=False),
                "vintage": int(g.vintage.iloc[0]),
            })
    df = pd.DataFrame(rows).sort_values(["commodity", "date"]).reset_index(drop=True)
    cols = ["commodity", "date", "risk_z", "delta_prod_pct", "delta_prod_lo_pct", "delta_prod_hi_pct", "mu_pct",
            "sigma_pct", "coverage_share", "major_window_open", "contributors", "contributors_all", "vintage"]
    if clim is not None:
        return apply_climatology(df, clim)[cols].reset_index(drop=True)
    ix = cfg.index
    parts = []
    for key, g in df.groupby("commodity"):
        st = standardize(g.set_index("date")["delta_prod_pct"], int(ix["standardize_years"]),
                         int(ix["calendar_window_weeks"]), int(ix["min_years"]), float(ix["sigma_floor"]))
        g = g.assign(risk_z=st["risk_z"].round(4).to_numpy(), mu_pct=st["mu"].round(4).to_numpy(),
                     sigma_pct=st["sd"].round(4).to_numpy())
        parts.append(g)
    return pd.concat(parts)[cols].reset_index(drop=True)


def hindcast_climatology(cfg: Settings, panel: pd.DataFrame, load_model, fao: pd.DataFrame, vintages: list[int],
                         years: int, window_weeks: int, floor: float) -> pd.DataFrame:
    """Model climatology, as in seasonal forecasting: for each vintage V, the vintage-V model re-forecasts the
    same weeks of the previous `years` years; dP of those hindcasts gives the mean and sd of "what this model
    says at this time of year". Removes the drift between vintages. Returns commodity, vintage, woy, mu, sd."""
    rows = []
    for v in vintages:
        model = load_model(v)
        if model is None:
            continue
        past = panel[(panel.as_of.dt.year >= v - years) & (panel.as_of.dt.year < v)]
        if past.empty:
            continue
        p = past[["commodity", "country_iso3", "as_of"]].copy()
        p["pred"] = model.predict(past)["pred_anom"].to_numpy()
        for key in cfg.commodities:
            q = p[p.commodity == key]
            if q.empty:
                continue
            sh = shares_at(cfg, key, fao, pd.Timestamp(f"{v}-01-01"))
            q = q.assign(c=100 * q.country_iso3.map(sh).fillna(0.0) * q.pred)
            d = q.groupby("as_of").c.sum()
            woy = d.index.isocalendar().week.to_numpy().astype(int)
            sd_all = float(d.std(ddof=1))
            for w in range(1, 54):
                diff = np.abs(woy - w)
                diff = np.minimum(diff, 52 - diff)
                hv = d.to_numpy()[diff <= window_weeks]
                if len(hv) < 3:
                    continue
                rows.append({"commodity": key, "vintage": v, "woy": w, "mu": float(hv.mean()),
                             "sd": max(float(hv.std(ddof=1)), floor * sd_all)})
    return pd.DataFrame(rows)


def apply_climatology(risk: pd.DataFrame, clim: pd.DataFrame) -> pd.DataFrame:
    r = risk.copy()
    r["woy"] = r["date"].dt.isocalendar().week.astype(int).to_numpy()
    r = r.drop(columns=[c for c in ("risk_z", "mu_pct", "sigma_pct") if c in r]).merge(
        clim.rename(columns={"mu": "mu_pct", "sd": "sigma_pct"}), on=["commodity", "vintage", "woy"], how="left")
    r["risk_z"] = (-(r["delta_prod_pct"] - r["mu_pct"]) / r["sigma_pct"]).round(4)
    r["mu_pct"], r["sigma_pct"] = r["mu_pct"].round(4), r["sigma_pct"].round(4)
    return r.drop(columns="woy")
```

## 66. `src/harvestradar/update.py`

```python
"""Daily update (run by .github/workflows/daily.yml every working day).

Fetches the new days only: NASA POWER weather since each cell's last complete day, futures closes, ONI.
Then features, weekly predictions with the stored vintage models (a full training only when the vintage of
the year is missing, i.e. once a year), weekly and daily index, events, backtest, price reaction, climate
fair value, the notes of the new days and the offline snapshot in data/demo.
"""

from __future__ import annotations

import datetime as dt
import os
import time

import pandas as pd

from harvestradar.config import Settings
from harvestradar.paths import MODELS_STORE, PROCESSED


def latest_business_day(today: dt.date | None = None) -> dt.date:
    """The note's day: today on a working day (UTC), else the last working day. Prices stay the last settled close."""
    today = today or dt.datetime.now(dt.timezone.utc).date()
    ts = pd.Timestamp(today)
    return (ts if ts.day_of_week < 5 else ts - pd.offsets.BDay(1)).date()


def run_update(cfg: Settings, end: dt.date | None = None, deterministic_notes: bool = False,
               skip_weather: bool = False) -> dt.date:
    from harvestradar.demo.export import export_demo
    from harvestradar.ingest.enso import fetch_oni
    from harvestradar.ingest.power import update_cells
    from harvestradar.ingest.prices import fetch_prices
    from harvestradar.pipeline import build_daily, build_features, build_index, predict_weekly, train_models
    from harvestradar.report.weekly_note import build_notes

    end = end or latest_business_day()
    os.environ["HARVESTRADAR_AS_OF_END"] = end.isoformat()
    t0 = time.time()

    def step(name, fn, *a, **k):
        s = time.time()
        fn(*a, **k)
        print(f"[update] {name}: {time.time() - s:.0f} s")

    print(f"[update] data as of {end}")
    if not skip_weather:
        cells = pd.read_parquet(PROCESSED / "sample_cells.parquet")
        step("weather", update_cells, cells, end.isoformat(), cfg.weather_start.isoformat())
    step("El Nino", fetch_oni)
    step("prices", fetch_prices, cfg)
    step("features", build_features, cfg)
    if (MODELS_STORE / f"yield_model_{end.year}.joblib").exists():
        step("predictions", predict_weekly, cfg)
    else:
        step("training (new vintage)", train_models, cfg)
    step("weekly index, events, backtest", build_index, cfg, reuse_climatology=True)
    step("daily index, price reaction, fair value", build_daily, cfg)
    step("notes", build_notes, cfg, deterministic=deterministic_notes, new_only=True)
    step("snapshot", export_demo, cfg)
    print(f"[update] done in {(time.time() - t0) / 60:.1f} min")
    return end
```

## 67. `web/app.js`

```javascript
/* HarvestRadar static web edition: renders the seven pages from the embedded data snapshot. */
(function () {
  "use strict";
  const D = JSON.parse(document.getElementById("data").textContent);
  const CROPS = ["maize", "coffee", "cocoa"];
  const VIEWS = { stress: "Stress map", commodity: "Commodity", fair: "Fair value", replay: "Replay", note: "Daily note", method: "Method", ask: "Assistant" };
  const S = { crop: "maize", episode: Object.keys(D.episodes)[0], note: null, shap: {}, range: "recent", calc: {}, hist: {}, pending: null, view: null, prev: null, scroll: {}, goto: null, restore: false,
              chat: { turns: [], busy: false, stop: false, error: "" } };
  let mapHandle = null;

  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const sg = (x, n = 2) => (x == null || !isFinite(x) ? "n/a" : (x >= 0 ? "+" : "") + x.toFixed(n));
  const fmtPrice = (key, x) => key === "cocoa" ? Math.round(x).toLocaleString("en-US") : x.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const dLabel = (s) => { const d = new Date(s + "T00:00:00Z"); return d.getUTCDate() + " " + MON[d.getUTCMonth()] + " " + d.getUTCFullYear(); };
  const MONTH = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const dLong = (s) => { const d = new Date(s + "T00:00:00Z"); return d.getUTCDate() + " " + MONTH[d.getUTCMonth()] + " " + d.getUTCFullYear(); };
  const pct = (x, n = 1) => (x != null && Math.abs(x) < 0.5 * Math.pow(10, -n) ? (0).toFixed(n) : sg(x, n)) + "%";
  const glyph = (k, size = 22) => '<span class="gl">' + D.glyphs[k].replace(/width="\d+" height="\d+"/, 'width="' + size + '" height="' + size + '"') + "</span>";

  function sparkline(values, w = 132, h = 46, color = "var(--signal)") {
    const v = values.filter((x) => x != null && isFinite(x));
    if (v.length < 2) return '<svg width="' + w + '" height="' + h + '"></svg>';
    const pad = 5, lo = Math.min(...v), hi = Math.max(...v) === lo ? lo + 1 : Math.max(...v);
    const xs = v.map((_, i) => pad + (i * (w - 2 * pad)) / (v.length - 1));
    const ys = v.map((y) => h - pad - ((y - lo) / (hi - lo)) * (h - 2 * pad));
    let d = "M" + xs[0].toFixed(1) + "," + ys[0].toFixed(1);
    for (let i = 1; i < v.length; i++) { const cx = (xs[i - 1] + xs[i]) / 2; d += " C" + cx.toFixed(1) + "," + ys[i - 1].toFixed(1) + " " + cx.toFixed(1) + "," + ys[i].toFixed(1) + " " + xs[i].toFixed(1) + "," + ys[i].toFixed(1); }
    const id = "g" + Math.random().toString(36).slice(2, 8);
    return '<svg class="spark" width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + " " + h + '" aria-hidden="true"><defs><linearGradient id="' + id + '" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFB547" stop-opacity=".28"/><stop offset="1" stop-color="#FFB547" stop-opacity="0"/></linearGradient></defs>' +
      '<path d="' + d + " L" + xs[xs.length - 1].toFixed(1) + "," + h + " L" + xs[0].toFixed(1) + "," + h + ' Z" fill="url(#' + id + ')"/><path d="' + d + '" fill="none" stroke="#FFB547" stroke-width="2" stroke-linecap="round"/>' +
      '<circle cx="' + xs[xs.length - 1].toFixed(1) + '" cy="' + ys[ys.length - 1].toFixed(1) + '" r="3.6" fill="#FFB547" style="filter:drop-shadow(0 0 5px #FFB547)"/></svg>';
  }

  const panel = (title, body, source, extra = "") => '<section class="glass" style="' + extra + '"><div class="caps" style="margin-bottom:12px">' + title + "</div>" + body + (source ? '<div class="source">' + source + "</div>" : "") + "</section>";
  const chip = (t, amber) => '<span class="chip' + (amber ? " amber" : "") + '">' + esc(t) + "</span>";
  const badge = (t, ok) => '<span class="tag plain ' + (ok ? "good" : "bad") + '">' + esc(t) + (ok ? "" : ": failed") + "</span>";
  const tag = (t, tone) => '<span class="tag ' + (tone || "") + '">' + esc(t) + "</span>";

  function barRows(rows, unit, labelW) {
    if (!rows.length) return '<p style="color:var(--muted)">No data.</p>';
    const m = Math.max(...rows.map((r) => Math.abs(r.value))) || 1;
    return rows.map((r) => {
      const f = Math.min(1, Math.abs(r.value) / m), amber = r.raises;
      const b = '<div class="b" style="width:' + Math.max(2, 100 * f).toFixed(1) + "%;background:" + (amber ? "linear-gradient(90deg,#8A6424,#F5A93A);box-shadow:0 0 12px rgba(255,181,71,.45)" : "#3F74D8;box-shadow:0 0 10px rgba(63,116,216,.4);margin-left:auto") + '"></div>';
      return '<div class="brow" style="grid-template-columns:minmax(110px,' + (labelW || 200) + 'px) minmax(0,1fr) minmax(0,1fr) 84px"><div class="lab"><div>' + esc(r.label) + "</div>" + (r.note ? '<div class="mono" style="font-size:13px;color:var(--muted)">' + esc(r.note) + "</div>" : "") +
        '</div><div class="neg">' + (amber ? "" : b) + '</div><div class="pos">' + (amber ? b : "") + '</div><div class="v" style="color:' + (amber ? "var(--signal)" : "var(--frost-2)") + '">' + sg(r.value) + (unit ? " " + unit : "") + "</div></div>";
    }).join("");
  }

  function ticker() {
    return '<div class="grid3">' + CROPS.map((k) => {
      const c = D.crops[k], z = c.latest.z, s = c.risk.z.slice(-26);
      return '<button class="glass tick-card' + (k === S.crop ? " sel" : "") + '" data-crop="' + k + '" aria-label="Select ' + esc(c.label) + '">' + glyph(c.glyph, 26) +
        '<div style="min-width:0"><div class="caps" style="white-space:nowrap">' + esc(c.display) + '<span class="hide-sm"> &middot; RISK INDEX</span></div><div class="val' + (z >= 2 ? " glow" : "") + '">' + sg(z) + "</div></div>" + sparkline(s) + "</button>";
    }).join("") + "</div>";
  }

  /* ---------- map ---------- */
  const PLAY = '<svg class="i-play" viewBox="0 0 24 24"><path d="M7 4.5v15l13-7.5z" fill="#0B0F14"/></svg><svg class="i-pause" viewBox="0 0 24 24"><path d="M6 4h4.5v16H6zM13.5 4H18v16h-4.5z" fill="#0B0F14"/></svg>';
  const LEG = ["#7EB0FF", "#3F74D8", "#26406A", "#1E2833", "#8A6424", "#F5A93A", "#FF5A36"].map((c) => '<i style="background:' + c + '"></i>').join("");
  function mapShell(mode, height, range) {
    return '<div class="radar ' + mode + '" tabindex="0" style="height:' + height + 'px"><div class="map-stage"></div>' +
      '<div class="map-label"></div><div class="legend"><div class="sw">' + LEG + '</div><div class="lg"><span>lower stress</span><span>higher stress</span></div></div>' +
      '<div class="bar"><button class="play" aria-label="Play">' + PLAY + '</button><div class="ticks"></div><div class="range">' + esc(range) + '</div><button class="speed" aria-label="Playback speed">x1</button></div>' +
      (mode === "episode" ? '<div class="strip"></div>' : "") + '<div class="tip"></div></div>';
  }
  function mountMap(cfg) {
    const el = document.querySelector(".radar");
    if (!el) return;
    if (mapHandle && mapHandle.stop) mapHandle.stop();
    mapHandle = window.RadarMap(el, cfg);
  }
  const mapH = () => (window.innerWidth < 700 ? 360 : 700);

  /* ---------- charts ---------- */
  function niceTicks(lo, hi, n) {
    const span = hi - lo, step0 = span / n, mag = Math.pow(10, Math.floor(Math.log10(step0)));
    const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => span / s <= n) || 10 * mag;
    const out = []; for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(6)); return out;
  }
  function indexChart(key) {
    const small = window.innerWidth < 700, c = D.crops[key], W = small ? Math.max(300, window.innerWidth - 72) : 1000, H = small ? 320 : 480, m = { l: small ? 44 : 62, r: small ? 52 : 78, t: 40, b: 34 };
    const end = new Date(c.latest.date + "T00:00:00Z"), start = new Date(end.getTime() - 64 * 7 * 864e5);
    const R = c.riskRecent.d.map((d, i) => [new Date(d + "T00:00:00Z"), c.riskRecent.z[i]]).filter((p) => p[0] >= start && p[1] != null);
    const P = c.pricesRecent.d.map((d, i) => [new Date(d + "T00:00:00Z"), c.pricesRecent.c[i]]).filter((p) => p[0] >= start);
    const zs = R.map((p) => p[1]), lo = Math.min(-0.5, Math.min(...zs) - 0.4), hi = Math.max(2.6, Math.max(...zs) + 0.4);
    const pv = P.map((p) => p[1]), plo = Math.min(...pv), phi = Math.max(...pv);
    const x = (d) => m.l + ((d - start) / (end - start)) * (W - m.l - m.r);
    const y = (v) => m.t + (1 - (v - lo) / (hi - lo)) * (H - m.t - m.b);
    const y2 = (v) => m.t + (1 - (v - plo) / (phi - plo || 1)) * (H - m.t - m.b);
    let g = "";
    c.windows.forEach(([s0, e0, st]) => {
      const xs = x(new Date(s0 + "T00:00:00Z")), xe = x(new Date(e0 + "T00:00:00Z"));
      g += '<rect x="' + xs + '" y="' + m.t + '" width="' + Math.max(1, xe - xs) + '" height="' + (H - m.t - m.b) + '" fill="rgba(255,181,71,.07)"/>' +
        '<text x="' + (xs + xe) / 2 + '" y="' + (m.t - 10) + '" text-anchor="middle" font-size="13" fill="#8A9AAB">' + esc((small ? st : c.mainCountry + " " + st + " window").toUpperCase()) + "</text>";
    });
    niceTicks(lo, hi, 7).forEach((v) => { g += '<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(v) + '" y2="' + y(v) + '" stroke="' + (v === 0 ? "#2A3646" : "#1E2935") + '"/><text x="' + (m.l - 8) + '" y="' + (y(v) + 4) + '" text-anchor="end" font-size="13" fill="#FFB547">' + (v > 0 ? "+" : "") + v + "</text>"; });
    niceTicks(plo, phi, 6).forEach((v) => { g += '<text x="' + (W - m.r + 8) + '" y="' + (y2(v) + 4) + '" font-size="13" fill="#C7D1DB">' + (key === "cocoa" ? Math.round(v).toLocaleString("en-US") : v) + "</text>"; });
    if (!small) g += '<text transform="translate(16,' + (m.t + (H - m.t - m.b) / 2) + ') rotate(-90)" text-anchor="middle" font-size="13" fill="#FFB547">RISK INDEX (0 = NORMAL)</text>';
    if (!small) g += '<text transform="translate(' + (W - 12) + "," + (m.t + (H - m.t - m.b) / 2) + ') rotate(90)" text-anchor="middle" font-size="13" fill="#C7D1DB">' + esc(c.priceUnit.toUpperCase()) + "</text>";
    for (let k = 0; k < 16; k++) { const d = new Date(Date.UTC(start.getUTCFullYear(), start.getUTCMonth() + 1 + (small ? 5 : 2) * k, 1)); if (d > end) break; g += '<text x="' + x(d) + '" y="' + (H - 10) + '" text-anchor="middle" font-size="13" fill="#8A9AAB">' + MON[d.getUTCMonth()] + " " + d.getUTCFullYear() + "</text>"; }
    g += '<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(2) + '" y2="' + y(2) + '" stroke="#F5A93A" stroke-dasharray="6 6" stroke-width="1.2"/><text x="' + (m.l + 6) + '" y="' + (y(2) - 6) + '" font-size="13" fill="#F5A93A">+2: RARE</text>';
    const pl = P.map((p, i) => (i ? "L" : "M") + x(p[0]).toFixed(1) + "," + y2(p[1]).toFixed(1)).join(" ");
    const il = R.map((p, i) => (i ? "L" : "M") + x(p[0]).toFixed(1) + "," + y(p[1]).toFixed(1)).join(" ");
    const last = R[R.length - 1];
    g += '<path d="' + pl + '" fill="none" stroke="#EAF0F5" stroke-opacity=".7" stroke-width="1.5"/>';
    g += '<path d="' + il + " L" + x(last[0]) + "," + y(0) + " L" + x(R[0][0]) + "," + y(0) + ' Z" fill="rgba(255,181,71,.08)"/>';
    g += '<path d="' + il + '" fill="none" stroke="rgba(255,181,71,.2)" stroke-width="10" stroke-linejoin="round"/><path d="' + il + '" fill="none" stroke="#FFB547" stroke-width="3" stroke-linejoin="round"/>';
    g += '<circle cx="' + x(last[0]) + '" cy="' + y(last[1]) + '" r="9" fill="rgba(255,181,71,.25)"/><circle cx="' + x(last[0]) + '" cy="' + y(last[1]) + '" r="4.5" fill="#FFB547"/>';
    return '<svg viewBox="0 0 ' + W + " " + H + '" width="100%" role="img" aria-label="Harvest-risk index and futures price, last 64 weeks">' + g + "</svg>";
  }
  function pathChart(ev) {
    const W = 600, H = 200, m = { l: 34, r: 12, t: 12, b: 28 };
    const P = ev.path.map((p) => [new Date(p.date + "T00:00:00Z"), p.risk_z]);
    const zs = P.map((p) => p[1]), lo = Math.min(-0.5, Math.min(...zs) - 0.3), hi = Math.max(2.5, Math.max(...zs) + 0.4);
    const t0 = P[0][0], t1 = P[P.length - 1][0];
    const x = (d) => m.l + ((d - t0) / (t1 - t0)) * (W - m.l - m.r), y = (v) => m.t + (1 - (v - lo) / (hi - lo)) * (H - m.t - m.b);
    let g = "";
    niceTicks(lo, hi, 4).forEach((v) => { g += '<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(v) + '" y2="' + y(v) + '" stroke="#1E2935"/><text x="' + (m.l - 6) + '" y="' + (y(v) + 4) + '" text-anchor="end" font-size="13" fill="#8A9AAB">' + v + "</text>"; });
    const months = []; for (let d = new Date(Date.UTC(t0.getUTCFullYear(), t0.getUTCMonth() + 1, 1)); d < t1; d = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1))) months.push(d);
    const stepM = Math.ceil(months.length / 5);
    months.forEach((d, i) => { if (i % stepM === 0) g += '<text x="' + x(d) + '" y="' + (H - 8) + '" text-anchor="middle" font-size="13" fill="#8A9AAB">' + MON[d.getUTCMonth()] + " " + String(d.getUTCFullYear()).slice(2) + "</text>"; });
    g += '<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(2) + '" y2="' + y(2) + '" stroke="#F5A93A" stroke-dasharray="6 6"/>';
    const l = P.map((p, i) => (i ? "L" : "M") + x(p[0]).toFixed(1) + "," + y(p[1]).toFixed(1)).join(" ");
    g += '<path d="' + l + '" fill="none" stroke="rgba(255,181,71,.2)" stroke-width="9"/><path d="' + l + '" fill="none" stroke="#FFB547" stroke-width="2.6"/>';
    const mk = ev.first_above_2 || ev.peak_date, pt = P.find((p) => p[0].toISOString().slice(0, 10) === mk);
    if (pt) g += '<circle cx="' + x(pt[0]) + '" cy="' + y(pt[1]) + '" r="10" fill="rgba(255,181,71,.28)"/><circle cx="' + x(pt[0]) + '" cy="' + y(pt[1]) + '" r="5" fill="#FFB547"/>';
    return '<svg viewBox="0 0 ' + W + " " + H + '" width="100%" role="img" aria-label="Index path during the episode">' + g + "</svg>";
  }

  /* ---------- views ---------- */
  function viewStress() {
    const c = D.crops[S.crop], mp = c.map, f = mp.frames;
    const first = new Date(f[0].date + "T00:00:00Z"), lastF = new Date(f[f.length - 1].date + "T00:00:00Z");
    const rng = (MON[first.getUTCMonth()] + " · " + MON[lastF.getUTCMonth()] + " " + lastF.getUTCFullYear()).toUpperCase();
    const rows = mp.top5.map((r) => '<div class="rank"><span class="mono" style="font-size:13px;color:var(--muted)">' + String(r.rank).padStart(2, "0") + "</span>" + glyph(c.glyph, 18) + '<span class="name">' + esc(r.name) + '</span><span style="font-size:14px;color:var(--muted)">' + esc(r.iso) + '</span><span class="bar"><i style="width:' + Math.max(3, 100 * r.frac).toFixed(0) + "%;background:linear-gradient(90deg,#8A6424,#F5A93A 70%," + (r.hot ? "#FF5A36" : "#FFB547") + ')"></i></span></div>').join("");
    const n = D.notes.find((x) => x.week === D.asOf && x.commodity === S.crop);
    const o = D.oni;
    const html = ticker() + '<div class="main"><div class="col">' + mapShell("world", mapH(), rng) +
      '<div class="source" style="margin-top:0">' + esc(c.label) + ": " + c.regionsN + " producing regions, " + Math.round(100 * c.coverage) + "% of world output (MapSPAM 2020). Stress combines heat, rainfall and soil moisture, compared with the same 10 days in " + D.meta.climBase[0] + "-" + D.meta.climBase[1] + ". Weather: NASA POWER.</div></div>" +
      '<div class="col">' + panel("MOST STRESSED REGIONS, WEIGHTED BY OUTPUT", rows, "10 days to " + dLong(mp.dekad) + ". Ranked by stress times the region's share of world output.") +
      '<section class="glass"><div class="caps">EL NI&Ntilde;O &middot; BACKGROUND</div><div style="font-family:var(--display);font-weight:700;font-size:22px;margin-top:8px">' + esc(o.strength.charAt(0).toUpperCase() + o.strength.slice(1)) + '</div><div style="display:flex;align-items:flex-end;justify-content:space-between;gap:12px;flex-wrap:wrap"><div><span class="mono" style="font-size:30px;color:var(--signal)">' + sg(o.value) + ' &deg;C</span><div style="font-size:14px;color:var(--muted);margin-top:2px">Pacific sea temperature vs normal, ' + esc(o.period) + "</div></div>" + sparkline(o.series, 200, 48) + '</div><div class="source">NOAA Oceanic Ni&ntilde;o Index, published ' + dLong(o.available_at) + ". Shown for context: it is not part of the index.</div></section>" +
      (n ? '<a class="glass" href="#note" style="display:flex;align-items:center;gap:16px;text-decoration:none;color:var(--frost)"><span style="border-radius:10px;overflow:hidden;display:inline-flex;flex:none">' + D.marks.signal + '</span><div><div style="font-size:17px;font-weight:500">Today\'s note is ready</div><div style="font-size:14px;color:var(--muted)">' + n.checks.filter(Boolean).length + ' of 3 checks passed</div></div><span class="mono" style="margin-left:auto;font-size:13px;color:var(--signal)">OPEN</span></a>' : "") +
      "</div></div>";
    return { html: html, after: () => mountMap({ viewBox: D.map.viewBox, base: Object.assign({}, D.map.base, { href: BASE_IMG }), countries: mp.borders, regions: mp.regions, frames: f, start: mp.start, ringRadius: 230, labelPrefix: "STRESS VS NORMAL", labelWord: "", rangeLabel: rng, capture: false, autoplay: false, ariaLabel: c.label + " stress map" }) };
  }

  function priceCard(k) {
    const c = D.crops[k], pi = (D.priceImpact.commodities || {})[k];
    if (!pi) return "";
    if (!pi.reliable) {
      return panel("WHAT IT MEANS FOR THE PRICE", '<div style="font-size:17px;color:var(--frost-2);line-height:1.6">No reliable link between world supply gaps and the ' + esc(c.label.toLowerCase()) + " price since " + pi.years[0] + " (" + pi.n + " years). No price estimate is shown.</div>", "Marketing-year average futures price against the realised world supply gap, " + pi.years[0] + "-" + pi.years[1] + ".");
    }
    const per = -pi.slope_pct_per_pct, fv = c.fair && c.fair.now;
    const fvLine = fv ? '<div style="font-size:16px;color:var(--frost-2);margin-top:12px;line-height:1.6;padding-top:12px;border-top:1px solid var(--line)">Climate fair value today: <span class="mono" style="color:var(--signal)">' + fmtPrice(k, fv.fair) + "</span>. The price (" + '<span class="mono">' + fmtPrice(k, fv.close) + "</span>) is " + gapWords(fv.gap_to_fair_pct) + '. <a href="#fair" data-goto="calc">Open the pricing tool</a></div>' : "";
    return panel("WHAT IT MEANS FOR THE PRICE", '<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap"><span class="mono" style="font-size:40px;color:var(--signal)">' + pct(pi.implied_pct) + '</span><span style="color:var(--frost-2)">expected move of the futures price over the marketing year</span></div>' +
      '<div style="font-size:16px;color:var(--frost-2);margin-top:8px;line-height:1.6">Likely between <span class="mono">' + pct(pi.low_pct) + '</span> and <span class="mono">' + pct(pi.high_pct) + "</span> (8 chances in 10). Since " + pi.years[0] + ", each 1% of world supply missing came with about <span class=\"mono\">" + pct(per) + "</span> on the " + esc(c.label.toLowerCase()) + " price.</div>" + fvLine,
      "Based on " + pi.n + " marketing years, " + pi.years[0] + "-" + pi.years[1] + "; the supply gap explains " + Math.round(100 * pi.r2) + "% of the yearly price changes. A rough guide, not a price forecast.");
  }

  function viewCommodity() {
    const k = S.crop, c = D.crops[k], L = c.latest;
    const rows = L.contributors.map((x) => ({ label: x.name, value: x.contrib_pct, raises: x.contrib_pct < 0, note: x.season + " harvest: " + pct(x.pred_anom_pct) + " vs normal" + (x.window_open ? ", critical window open" : "") }));
    const countries = L.contributors.map((x) => x.country).filter((iso) => c.shap[iso]);
    const sel = S.shap[k] && countries.includes(S.shap[k]) ? S.shap[k] : countries[0];
    const name = (iso) => (L.contributors.find((x) => x.country === iso) || {}).name || iso;
    const sh = c.shap[sel];
    const shapRows = sh ? sh.rows.map(([lab, v]) => ({ label: lab, value: v, raises: v < 0 })) : [];
    const html = ticker() + '<div class="main c65"><div class="col"><div class="cards3">' +
      '<section class="glass" style="display:flex;align-items:center;gap:22px;min-height:164px">' + glyph(c.glyph, 52) + '<div style="min-width:0"><div class="caps">' + esc(c.display) + ' &middot; HARVEST-RISK INDEX</div><div class="mono glow hero-val" style="font-size:72px;line-height:1;color:var(--signal);font-weight:500;margin-top:6px">' + sg(L.z) + '</div><div class="source">' + dLong(L.date) + ". 0 is a normal season, above +2 is rare.</div></div></section>" +
      '<section class="glass" style="min-height:164px"><div class="caps">EXPECTED WORLD SUPPLY VS NORMAL</div><div class="mono" style="font-size:34px;margin-top:12px">' + pct(L.dp) + '</div><div class="source">Likely between ' + pct(L.lo) + " and " + pct(L.hi) + " (8 chances in 10), from the model's forecasts by country.</div></section>" +
      '<section class="glass" style="min-height:164px"><div class="caps">' + esc(c.priceLabel) + '</div><div class="mono" style="font-size:34px;margin-top:12px">' + fmtPrice(k, c.lastPrice.close) + '</div><div class="source">' + esc(c.priceUnit.charAt(0).toUpperCase() + c.priceUnit.slice(1)) + ", nearest contract, close on " + dLong(c.lastPrice.date) + ".</div></section></div>" +
      chainPanel(k) +
      '<section class="glass" style="padding:16px 18px"><div style="display:flex;flex-wrap:wrap;gap:8px 22px;align-items:center;margin-bottom:6px"><span style="font-family:var(--display);font-weight:700;font-size:20px">Risk index and futures price, last 64 weeks</span><span style="display:inline-flex;align-items:center;gap:8px;color:var(--frost-2);font-size:14px"><i style="width:22px;height:3px;background:#FFB547;display:inline-block;border-radius:2px"></i>Risk index, left scale</span><span style="display:inline-flex;align-items:center;gap:8px;color:var(--frost-2);font-size:14px"><i style="width:22px;height:2px;background:#EAF0F5;display:inline-block;border-radius:2px"></i>' + esc(c.priceName) + ', right scale</span></div>' + indexChart(k) +
      '<div style="font-size:15px;color:var(--frost-2);line-height:1.6;margin-top:6px">How to read it: the orange line rises when this season\'s weather points to less ' + esc(c.label.toLowerCase()) + " than usual for this time of year. The shaded band is the " + esc(c.mainCountry) + " critical window, when weather matters most for the harvest. The white line is the price, for comparison.</div></section>" +
      comovePanel(k, true) + "</div>" +
      '<div class="col">' + priceCard(k) + askPanel(k) + panel("WHICH COUNTRIES DRIVE TODAY'S READING", barRows(rows, "", 240), "In points of world supply: each country's share of world output times its expected harvest gap. Amber raises the risk, blue lowers it.") +
      '<div class="chips" role="group" aria-label="Country">' + countries.map((iso) => '<button class="chip' + (iso === sel ? " on" : "") + '" data-shap="' + iso + '">' + esc(name(iso)) + "</button>").join("") + "</div>" +
      panel("WHICH WEATHER DRIVES THE FORECAST <span style='float:right;color:var(--signal)'>" + esc(name(sel).toUpperCase()) + "</span>", barRows(shapRows, "", 220), "In points of " + c.target + " vs normal. Contribution of each weather factor to the forecast for the " + (sh ? sh.season : "") + " harvest (SHAP values).") +
      "</div></div>";
    return { html: html, after: null };
  }

  /* ---------- climate fair value and pricing tool ---------- */
  function gapWords(g) {
    if (g == null || !isFinite(g)) return "not comparable";
    if (Math.abs(g) < 1) return "in line with it";
    return Math.abs(g).toFixed(1) + "% " + (g < 0 ? "below" : "above") + " it";
  }
  const corrWord = (r) => (r == null ? "n/a" : Math.abs(r) < 0.1 ? "no link" : Math.abs(r) < 0.3 ? "weak link" : Math.abs(r) < 0.5 ? "moderate link" : "strong link");

  /* From weather to price: the four steps behind every reading, with today's values. */
  function chainPanel(k) {
    const c = D.crops[k], L = c.latest, f = c.fair, pi = (D.priceImpact.commodities || {})[k], top = L.contributors[0];
    const regions = c.map.top5.slice(0, 2).map((r) => r.name).join(" and ");
    const step = (n, title, big, sub, href) => '<a class="chain-step" href="' + href + '"><div class="caps">' + n + " &middot; " + title + '</div><div class="mono" style="font-size:24px;color:var(--frost);margin-top:6px">' + big + '</div><div style="font-size:14px;color:var(--frost-2);line-height:1.5;margin-top:4px">' + sub + "</div></a>";
    const price = pi && pi.reliable ? pct(pi.implied_pct) : "n/a";
    return '<section class="glass"><div class="caps" style="margin-bottom:12px">FROM WEATHER TO PRICE, ' + esc(c.label.toUpperCase()) + " TODAY</div><div class=\"chain\">" +
      step("1", "WEATHER", "10 days to " + dLabel(c.map.dekad), "Most stressed producing regions: " + esc(regions) + ".", "#stress") +
      step("2", "HARVEST", pct(L.dp, 2), "Expected world supply vs normal" + (top ? ", led by " + esc(top.name) + " (" + sg(top.contrib_pct) + " points)" : "") + ".", "#commodity") +
      step("3", "RISK INDEX", sg(L.z), "How unusual this supply gap is for the time of year (+2 = rare).", "#commodity") +
      step("4", "PRICE", price, (pi && !pi.reliable ? "No reliable link between world supply and the " + esc(c.label.toLowerCase()) + " price. " : "") + (f ? "Climate fair value " + fmtPrice(k, f.now.fair) + "; last close " + fmtPrice(k, f.now.close) + "." : "Expected move over the marketing year."), "#fair") +
      '</div><div class="source">Every working day: new weather from NASA, harvest forecasts from the model, then the price reaction measured on ' + (f ? f.flex.years[0] + "-" + f.flex.years[1] : "past years") + ".</div></section>";
  }

  function comovePanel(k, compact) {
    const c = D.crops[k], cm = c.fair && c.fair.comove;
    if (!cm) return "";
    const tile = (v, lab) => '<div class="stat"><div class="mono">' + (v == null ? "n/a" : sg(v)) + '</div><div class="lab">' + lab + " <span style=\"color:var(--muted)\">(" + corrWord(v) + ")</span></div></div>";
    const tiles = '<div class="grid3" style="margin-top:4px">' + tile(cm.weekly_changes, "Week-to-week changes of the index and of the price") +
      tile(cm.weekly_changes_in_windows, "Same, only in critical weather windows (" + cm.weeks_in_windows + " weeks)") +
      tile(cm.index_vs_next_13_weeks, "Index level vs the price change over the next 13 weeks") + "</div>";
    const text = '<div style="font-size:15px;color:var(--frost-2);line-height:1.65;margin-top:12px">The index moves with the weather: every day it reads heat, rain and soil moisture where ' + esc(c.label.toLowerCase()) +
      " grows, turns them into a harvest forecast for each producing country and adds them up into the world supply gap. The price only follows when that gap matters for the market: prices also move with demand, stocks, the dollar, fund positions, other origins and the official crop reports, and traders often price a weather scare before it reaches the harvest forecasts. " +
      "So the two lines can diverge for weeks. The " + (compact ? '<a href="#fair">climate fair value</a>' : "climate fair value") + " is the last step: the price that the weather-driven supply gap justifies.</div>";
    return '<section class="glass"><div class="caps" style="margin-bottom:12px">WHY THE INDEX AND THE PRICE DO NOT MOVE TOGETHER</div>' + tiles + text +
      '<div class="source">Correlations, weekly data since ' + cm.from.slice(0, 4) + " (" + cm.weeks + " weeks). 0 means no link, 1 means the two move as one.</div></section>";
  }

  function fairChart(k, mode) {
    const f = D.crops[k].fair, s = mode === "long" ? f.long : f.recent, small = window.innerWidth < 700;
    const W = small ? Math.max(300, window.innerWidth - 72) : 1000, H = small ? 300 : 440, m = { l: small ? 46 : 70, r: small ? 10 : 128, t: 18, b: 34 };
    const T = s.d.map((d) => new Date(d + "T00:00:00Z"));
    const vals = [].concat(s.close, s.fair_lo, s.fair_hi, s.anchor).filter((v) => v != null && isFinite(v));
    let lo = Math.min(...vals), hi = Math.max(...vals); const pad = (hi - lo) * 0.06; lo -= pad; hi += pad;
    const t0 = T[0], t1 = T[T.length - 1];
    const x = (d) => m.l + ((d - t0) / (t1 - t0)) * (W - m.l - m.r);
    const y = (v) => m.t + (1 - (v - lo) / (hi - lo)) * (H - m.t - m.b);
    const line = (arr) => arr.map((v, i) => (i ? "L" : "M") + x(T[i]).toFixed(1) + "," + y(v).toFixed(1)).join(" ");
    let g = "";
    niceTicks(lo, hi, 6).forEach((v) => { g += '<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(v) + '" y2="' + y(v) + '" stroke="#1E2935"/><text x="' + (m.l - 8) + '" y="' + (y(v) + 4) + '" text-anchor="end" font-size="13" fill="#8A9AAB">' + (k === "cocoa" ? Math.round(v).toLocaleString("en-US") : v) + "</text>"; });
    if (mode === "long") {
      const step = small ? 5 : 2;
      for (let yr = t0.getUTCFullYear() + 1; yr <= t1.getUTCFullYear(); yr++) if (yr % step === 0) { const d = new Date(Date.UTC(yr, 0, 1)); g += '<text x="' + x(d) + '" y="' + (H - 10) + '" text-anchor="middle" font-size="13" fill="#8A9AAB">' + yr + "</text>"; }
    } else {
      const step = small ? 6 : 3;
      for (let d = new Date(Date.UTC(t0.getUTCFullYear(), t0.getUTCMonth() + 1, 1)); d <= t1; d = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1))) if (d.getUTCMonth() % step === 0) g += '<text x="' + x(d) + '" y="' + (H - 10) + '" text-anchor="middle" font-size="13" fill="#8A9AAB">' + MON[d.getUTCMonth()] + " " + d.getUTCFullYear() + "</text>";
    }
    const band = s.fair_hi.map((v, i) => (i ? "L" : "M") + x(T[i]).toFixed(1) + "," + y(v).toFixed(1)).join(" ") + " " +
      s.fair_lo.map((v, i) => [i, v]).reverse().map(([i, v]) => "L" + x(T[i]).toFixed(1) + "," + y(v).toFixed(1)).join(" ") + " Z";
    g += '<path d="' + band + '" fill="rgba(255,181,71,.16)"/>';
    g += '<path d="' + line(s.anchor) + '" fill="none" stroke="#8A9AAB" stroke-width="1.3" stroke-dasharray="5 6"/>';
    g += '<path d="' + line(s.close) + '" fill="none" stroke="#EAF0F5" stroke-opacity=".85" stroke-width="1.6"/>';
    g += '<path d="' + line(s.fair) + '" fill="none" stroke="#FFB547" stroke-width="2.6" stroke-linejoin="round"/>';
    const n = T.length - 1, xf = x(T[n]);
    let yf = y(s.fair[n]), yp = y(s.close[n]);
    g += '<circle cx="' + xf + '" cy="' + yf + '" r="4.5" fill="#FFB547"/><circle cx="' + xf + '" cy="' + yp + '" r="4" fill="#EAF0F5"/>';
    if (!small) {
      if (Math.abs(yf - yp) < 34) { const mid = (yf + yp) / 2, up = yf < yp ? -1 : 1; yf = mid + up * 17; yp = mid - up * 17; }
      g += '<text x="' + (xf + 10) + '" y="' + (yf - 2) + '" font-size="13" fill="#FFB547">FAIR VALUE</text><text x="' + (xf + 10) + '" y="' + (yf + 14) + '" font-size="13" fill="#FFB547">' + fmtPrice(k, s.fair[n]) + "</text>";
      g += '<text x="' + (xf + 10) + '" y="' + (yp - 2) + '" font-size="13" fill="#EAF0F5">PRICE</text><text x="' + (xf + 10) + '" y="' + (yp + 14) + '" font-size="13" fill="#EAF0F5">' + fmtPrice(k, s.close[n]) + "</text>";
    }
    g += '<line class="cross" x1="0" x2="0" y1="' + m.t + '" y2="' + (H - m.b) + '" stroke="#C7D1DB" stroke-opacity=".5" visibility="hidden"/>';
    return '<div class="chart-wrap" data-chart="fair" data-mode="' + mode + '" data-w="' + W + '" data-l="' + m.l + '" data-r="' + m.r + '"><svg viewBox="0 0 ' + W + " " + H + '" width="100%" role="img" aria-label="Futures price and climate fair value">' + g + '</svg><div class="chart-tip"></div></div>';
  }

  function hookFairChart() {
    const wrap = document.querySelector('[data-chart="fair"]');
    if (!wrap) return;
    const k = S.crop, f = D.crops[k].fair, s = wrap.dataset.mode === "long" ? f.long : f.recent;
    const W = +wrap.dataset.w, L = +wrap.dataset.l, R = +wrap.dataset.r, svg = wrap.querySelector("svg"), tip = wrap.querySelector(".chart-tip"), cross = svg.querySelector(".cross");
    const T = s.d.map((d) => Date.parse(d + "T00:00:00Z")), t0 = T[0], t1 = T[T.length - 1];
    const move = (e) => {
      const b = svg.getBoundingClientRect(), vx = ((e.clientX - b.left) / b.width) * W;
      const t = t0 + ((vx - L) / (W - L - R)) * (t1 - t0);
      let lo = 0, hi = T.length - 1; while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (T[mid] < t) lo = mid; else hi = mid; }
      const i = Math.abs(T[lo] - t) < Math.abs(T[hi] - t) ? lo : hi, cx = L + ((T[i] - t0) / (t1 - t0)) * (W - L - R);
      cross.setAttribute("x1", cx); cross.setAttribute("x2", cx); cross.setAttribute("visibility", "visible");
      const gp = 100 * (s.close[i] / s.fair[i] - 1);
      tip.innerHTML = '<div style="color:var(--frost);font-weight:600;margin-bottom:2px">' + dLong(s.d[i]) + '</div><div><span class="k">Price</span><span class="mono">' + fmtPrice(k, s.close[i]) + '</span></div><div><span class="k" style="color:var(--signal)">Fair value</span><span class="mono">' + fmtPrice(k, s.fair[i]) +
        '</span></div><div><span class="k">80% range</span><span class="mono">' + fmtPrice(k, s.fair_lo[i]) + " to " + fmtPrice(k, s.fair_hi[i]) + '</span></div><div><span class="k">12-month average</span><span class="mono">' + fmtPrice(k, s.anchor[i]) + '</span></div><div><span class="k">Price vs fair value</span><span class="mono">' + pct(gp) + "</span></div>";
      const px = (cx / W) * b.width, wb = wrap.getBoundingClientRect();
      tip.style.left = Math.min(wb.width - tip.offsetWidth - 4, Math.max(4, px + 14)) + "px"; tip.style.top = "8px"; tip.style.opacity = 1;
    };
    svg.addEventListener("mousemove", move);
    svg.addEventListener("mouseleave", () => { tip.style.opacity = 0; cross.setAttribute("visibility", "hidden"); });
  }

  function flexChart(k) {
    const small = window.innerWidth < 700, f = D.crops[k].fair, fx = f.flex, P = fx.points, W = small ? Math.max(300, window.innerWidth - 72) : 600, H = small ? 300 : 380, m = { l: 58, r: 16, t: 16, b: 52 };
    const xs = P.map((p) => p[1]), ys = P.map((p) => p[2]), gNow = f.now.supply_gap_pct;
    const xr = Math.max(2, ...xs.map(Math.abs), Math.abs(gNow)) * 1.12, yr = Math.max(10, ...ys.map(Math.abs)) * 1.1;
    const x = (v) => m.l + ((v + xr) / (2 * xr)) * (W - m.l - m.r), y = (v) => m.t + (1 - (v + yr) / (2 * yr)) * (H - m.t - m.b);
    const mx = xs.reduce((a, b) => a + b, 0) / xs.length, my = ys.reduce((a, b) => a + b, 0) / ys.length, b = fx.slope_pct_per_pct, a = my - b * mx;
    let g = "";
    niceTicks(-yr, yr, 5).forEach((v) => { g += '<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(v) + '" y2="' + y(v) + '" stroke="' + (v === 0 ? "#2A3646" : "#1E2935") + '"/><text x="' + (m.l - 6) + '" y="' + (y(v) + 4) + '" text-anchor="end" font-size="13" fill="#8A9AAB">' + (v > 0 ? "+" : "") + v + "</text>"; });
    niceTicks(-xr, xr, 6).forEach((v) => { g += '<line x1="' + x(v) + '" x2="' + x(v) + '" y1="' + m.t + '" y2="' + (H - m.b) + '" stroke="' + (v === 0 ? "#2A3646" : "#1E2935") + '"/><text x="' + x(v) + '" y="' + (H - m.b + 18) + '" text-anchor="middle" font-size="13" fill="#8A9AAB">' + (v > 0 ? "+" : "") + v + "</text>"; });
    g += '<text x="' + ((m.l + W - m.r) / 2) + '" y="' + (H - 8) + '" text-anchor="middle" font-size="13" fill="#C7D1DB">WORLD SUPPLY VS NORMAL (%)</text>';
    g += '<text transform="translate(14,' + ((m.t + H - m.b) / 2) + ') rotate(-90)" text-anchor="middle" font-size="13" fill="#C7D1DB">PRICE CHANGE IN THE YEAR (%)</text>';
    g += '<line x1="' + x(-xr) + '" y1="' + y(a - b * xr) + '" x2="' + x(xr) + '" y2="' + y(a + b * xr) + '" stroke="#FFB547" stroke-width="2.4"/>';
    g += '<line x1="' + x(gNow) + '" x2="' + x(gNow) + '" y1="' + m.t + '" y2="' + (H - m.b) + '" stroke="#FFB547" stroke-dasharray="5 5" stroke-opacity=".8"/><text x="' + (x(gNow) + (gNow > 0 ? -6 : 6)) + '" y="' + (H - m.b - 8) + '" text-anchor="' + (gNow > 0 ? "end" : "start") + '" font-size="13" fill="#FFB547">TODAY</text>';
    P.forEach((p) => { g += '<circle cx="' + x(p[1]).toFixed(1) + '" cy="' + y(p[2]).toFixed(1) + '" r="5" fill="#C7D1DB" fill-opacity=".75"><title>' + p[0] + ": supply " + pct(p[1]) + ", price " + pct(p[2]) + "</title></circle>"; });
    return '<svg viewBox="0 0 ' + W + " " + H + '" width="100%" role="img" aria-label="World supply gap and price change, one dot per marketing year">' + g + "</svg>";
  }

  function calcDefaults(k) {
    const f = D.crops[k].fair;
    return { gap: f.now.supply_gap_pct, r: -f.flex.slope_pct_per_pct, anchor: f.now.anchor, scen: "today" };
  }
  function calcResult(k, st) {
    const f = D.crops[k].fair, se = f.flex.se, e = (r) => Math.exp((r * -st.gap) / 100), d0 = calcDefaults(k), nw = f.now;
    if (st.gap === d0.gap && st.r === d0.r && st.anchor === d0.anchor) return { fair: nw.fair, lo: nw.fair_lo, hi: nw.fair_hi, prem: nw.premium_pct, vs: nw.gap_to_fair_pct, z: D.crops[k].latest.z };
    const fair = st.anchor * e(st.r), a = st.anchor * e(st.r - 1.2816 * se), b = st.anchor * e(st.r + 1.2816 * se);
    return { fair: fair, lo: Math.min(a, b), hi: Math.max(a, b), prem: 100 * (e(st.r) - 1), vs: 100 * (f.now.close / fair - 1), z: (f.mu - st.gap) / f.sigma };
  }
  function calcPanel(k) {
    const f = D.crops[k].fair, st = S.calc[k] || (S.calc[k] = calcDefaults(k)), fx = f.flex;
    const scen = [["Today", null], ["Normal season (index 0)", 0], ["Rare (index +2)", 2], ["Extreme (index +3)", 3], ["Good harvest (index -2)", -2]];
    const gmin = Math.floor(Math.min(-6, f.mu - 4 * f.sigma)), gmax = Math.ceil(Math.max(6, f.mu + 4 * f.sigma));
    const back = S.prev && S.prev !== "fair" && VIEWS[S.prev] ? '<a href="#' + S.prev + '" data-back="1" style="display:inline-flex;align-items:center;gap:8px;margin-bottom:14px;font-size:15px;color:var(--signal);text-decoration:none;min-height:32px">Back to ' + esc(VIEWS[S.prev]) + "</a>" : "";
    return '<section class="glass calc" id="calc" style="scroll-margin-top:12px">' + back + '<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap"><div class="caps">PRICING TOOL &middot; ' + esc(D.crops[k].display) + '</div><div style="display:flex;gap:8px"><button class="btn sm" id="calc-undo" type="button">Undo</button><button class="btn sm" id="calc-reset" type="button">Back to today</button></div></div>' +
      '<div style="font-size:15px;color:var(--frost-2);margin-top:8px;line-height:1.55">Move the expected world supply, or pick a scenario, to see the fair value it would justify.</div>' +
      '<div class="chips" style="margin-top:12px" role="group" aria-label="Scenario">' + scen.map(([l, z]) => { const v = z == null ? "today" : String(z); return '<button class="chip' + (st.scen === v ? " on" : "") + '" data-scen="' + v + '" aria-pressed="' + (st.scen === v) + '">' + l + "</button>"; }).join("") + "</div>" +
      '<label for="i-gap"><span>Expected world supply vs normal</span><output id="o-gap"></output></label><input type="range" id="i-gap" min="' + gmin + '" max="' + gmax + '" step="0.05" value="' + st.gap + '"><div class="hint" id="o-z"></div>' +
      '<label for="i-r"><span>Price reaction to 1% of world supply missing</span><output id="o-r"></output></label><input type="range" id="i-r" min="0" max="8" step="0.05" value="' + st.r + '"><div class="hint">Measured ' + fx.years[0] + "-" + fx.years[1] + ": " + (-fx.slope_pct_per_pct).toFixed(2) + "% (uncertainty " + fx.se.toFixed(2) + ")</div>" +
      '<label for="i-anchor"><span>Anchor price, ' + esc(D.crops[k].priceUnit) + '</span></label><input type="number" id="i-anchor" step="any" value="' + (+st.anchor.toFixed(2)) + '"><div class="hint">Default: average close of the last 12 months (' + fmtPrice(k, f.now.anchor) + ")</div>" +
      '<div class="result"><div class="caps">FAIR VALUE IN THIS SCENARIO</div><div class="mono glow" id="o-fair" style="font-size:44px;color:var(--signal);margin-top:6px"></div><div id="o-range" style="font-size:15px;color:var(--frost-2);line-height:1.6"></div><div id="o-vs" style="font-size:15px;color:var(--frost-2);line-height:1.6;margin-top:6px"></div><button class="btn sm" style="margin-top:12px" data-askopen="Explain the scenario I set in the pricing tool and what would have to happen for it to play out.">Ask the assistant about this scenario</button></div>' +
      '<div class="source">Fair value = anchor &times; exp(reaction &times; supply missing / 100). The 80% range comes from the uncertainty of the measured reaction. Research tool, not investment advice.</div></section>';
  }
  const snap = (st) => ({ gap: st.gap, r: st.r, anchor: st.anchor, scen: st.scen });
  function calcPush(k, prev) { const h = S.hist[k] || (S.hist[k] = []); h.push(prev); if (h.length > 50) h.shift(); }
  function calcSync() {
    const k = S.crop, st = S.calc[k], el = (id) => document.getElementById(id);
    if (!el("i-gap")) return;
    el("i-gap").value = st.gap; el("i-r").value = st.r;
    if (document.activeElement !== el("i-anchor")) el("i-anchor").value = +(+st.anchor).toFixed(2);
    calcUpdate();
  }
  function calcUpdate() {
    const k = S.crop, st = S.calc[k], el = (id) => document.getElementById(id);
    if (!el("o-fair")) return;
    document.querySelectorAll("[data-scen]").forEach((b) => { const on = b.dataset.scen === st.scen; b.classList.toggle("on", on); b.setAttribute("aria-pressed", on); });
    const d0 = calcDefaults(k), atToday = st.gap === d0.gap && st.r === d0.r && st.anchor === d0.anchor;
    el("calc-undo").disabled = !(S.hist[k] || []).length; el("calc-reset").disabled = atToday;
    const r = calcResult(k, st), c = D.crops[k];
    el("o-gap").textContent = pct(st.gap, 2); el("o-r").textContent = st.r.toFixed(2) + "%";
    el("o-z").textContent = "Same as a risk index of " + sg(r.z) + " today";
    el("o-fair").textContent = fmtPrice(k, r.fair);
    el("o-range").textContent = "Likely between " + fmtPrice(k, r.lo) + " and " + fmtPrice(k, r.hi) + " (8 chances in 10). Climate premium " + pct(r.prem) + " on the anchor.";
    el("o-vs").textContent = "Last close " + fmtPrice(k, c.fair.now.close) + " (" + dLong(c.fair.now.date) + ") is " + gapWords(r.vs) + ".";
  }

  function viewFair() {
    const k = S.crop, c = D.crops[k], f = c.fair;
    if (!f) return { html: ticker() + '<section class="glass" style="margin-top:16px">No fair value in this data snapshot. Run <span class="mono">harvestradar index price</span>.</section>', after: null };
    const nw = f.now, fx = f.flex, unreliable = !nw.reliable;
    const warn = unreliable ? '<div class="warnbox" style="margin-top:16px">No reliable link between world supply gaps and the ' + esc(c.label.toLowerCase()) + " price was found over " + fx.years[0] + "-" + fx.years[1] + " (" + Math.round(100 * fx.p_value) + "% chance that the measured slope is pure luck). The fair value therefore stays close to the 12-month average whatever the weather. Use it with care.</div>" : "";
    const cards = '<div class="cards3">' +
      '<section class="glass' + (unreliable ? "" : " amber") + '" style="min-height:170px"><div class="caps">CLIMATE FAIR VALUE</div><div class="mono glow hero-val" style="font-size:56px;line-height:1.1;color:var(--signal);margin-top:8px">' + fmtPrice(k, nw.fair) + '</div><div class="source">Likely between ' + fmtPrice(k, nw.fair_lo) + " and " + fmtPrice(k, nw.fair_hi) + ". The price that today's expected supply justifies on its own.</div></section>" +
      '<section class="glass" style="min-height:170px"><div class="caps">' + esc(c.priceLabel) + '</div><div class="mono" style="font-size:34px;margin-top:12px">' + fmtPrice(k, nw.close) + '</div><div style="margin-top:10px">' + tag(Math.abs(nw.gap_to_fair_pct) < 1 ? "In line with fair value" : Math.abs(nw.gap_to_fair_pct).toFixed(1) + "% " + (nw.gap_to_fair_pct < 0 ? "below" : "above") + " fair value", nw.gap_to_fair_pct < 0 ? "good" : "warn") + '</div><div class="source">Close on ' + dLong(nw.date) + ".</div></section>" +
      '<section class="glass" style="min-height:170px"><div class="caps">CLIMATE PREMIUM</div><div class="mono" style="font-size:34px;margin-top:12px">' + pct(nw.premium_pct) + '</div><div class="source">On the 12-month average of ' + fmtPrice(k, nw.anchor) + ", for an expected world supply of " + pct(nw.supply_gap_pct, 2) + " vs normal.</div></section></div>";
    const rng = '<div class="chips" role="group" aria-label="Period">' + [["recent", "2 years"], ["long", "Since 2006"]].map(([v, l]) => '<button class="chip' + (S.range === v ? " on" : "") + '" data-range="' + v + '">' + l + "</button>").join("") + "</div>";
    const chart = '<section class="glass" style="padding:16px 18px"><div style="display:flex;flex-wrap:wrap;gap:10px 20px;align-items:center;justify-content:space-between;margin-bottom:8px"><span style="font-family:var(--display);font-weight:700;font-size:20px">Futures price and climate fair value</span>' + rng + "</div>" +
      '<div class="legend-row" style="margin-bottom:6px"><span><i style="background:#FFB547"></i>Climate fair value</span><span><i style="background:rgba(255,181,71,.35);height:10px"></i>80% range</span><span><i style="background:#EAF0F5"></i>' + esc(c.priceName) + '</span><span><i style="background:repeating-linear-gradient(90deg,#8A9AAB 0 5px,transparent 5px 10px)"></i>12-month average (anchor)</span></div>' +
      fairChart(k, S.range) +
      '<div style="font-size:15px;color:var(--frost-2);line-height:1.6;margin-top:6px">How to read it: the orange line is the 12-month average price moved up or down by what the expected world supply implies. When the white price line is below it, the market prices less weather risk than the supply forecast suggests; above it, more. The gap is what other drivers explain (demand, stocks, the dollar, funds). Hover the chart for the values of each day.</div>' +
      '<div class="source">' + (S.range === "long" ? "Weekly (Fridays) since 2006" : "Every trading day, last 2 years") + ". Updated with every data run. The price reaction is measured on " + fx.years[0] + "-" + fx.years[1] + ", so values before " + (fx.years[1] + 1) + " are in-sample.</div></section>";
    const scatter = panel("HOW THE PRICE REACTION IS MEASURED", flexChart(k) + '<div style="font-size:15px;color:var(--frost-2);line-height:1.6;margin-top:8px">One dot per marketing year: the realised world supply vs normal (FAOSTAT) and the change of the average futures price. The orange line is the fitted reaction: ' + (-fx.slope_pct_per_pct).toFixed(2) + "% on the price for each 1% of world supply missing.</div>",
      fx.n + " marketing years, " + fx.years[0] + "-" + fx.years[1] + ". Share of yearly price changes explained: " + Math.round(100 * fx.r2) + "%. Chance the link is pure luck: " + (fx.p_value < 0.01 ? "under 1%" : Math.round(100 * fx.p_value) + "%") + ".");
    const back = S.prev && S.prev !== "fair" && VIEWS[S.prev] ? '<div style="margin-bottom:12px"><a class="chip" href="#' + S.prev + '" data-back="1" style="text-decoration:none;letter-spacing:.04em;text-transform:none;font-family:var(--body);font-size:15px">Back to ' + esc(VIEWS[S.prev]) + "</a></div>" : "";
    const html = back + ticker() + warn + '<div class="main c65"><div class="col">' + cards + chart + comovePanel(k, false) + '</div><div class="col">' + calcPanel(k) + scatter + "</div></div>";
    return { html: html, after: () => { hookFairChart(); calcUpdate(); } };
  }

  function viewReplay() {
    const names = Object.keys(D.episodes), ev = D.episodes[S.episode], c = D.crops[ev.commodity];
    const fmt = (x) => ev.commodity === "cocoa" ? Math.round(x).toLocaleString("en-US") : String(+x.toFixed(2));
    let card;
    if (ev.first_above_2) {
      const cap = ev.verdict === "late" ? "after the price had already peaked on " + dLong(ev.price_max_date) + ": too late" : (ev.lead_text || "");
      card = '<section class="glass' + (ev.verdict === "late" ? "" : " amber") + '"><div class="caps">INDEX FIRST ABOVE +2</div><div class="mono glow" style="font-size:clamp(34px,3.4vw,52px);line-height:1.15;color:var(--signal);margin-top:10px">' + dLong(ev.first_above_2) + '</div><div style="font-size:17px;color:var(--frost-2)">' + esc(cap) + '</div><div class="source">Weekly index during the episode.</div></section>';
    } else {
      card = '<section class="glass"><div class="caps">HIGHEST INDEX IN THE EPISODE</div><div class="mono" style="font-size:clamp(34px,3.4vw,52px);line-height:1.15;color:var(--signal);margin-top:10px">' + sg(ev.peak_risk_z) + '</div><div style="font-size:17px;color:var(--frost-2)">on ' + dLong(ev.peak_date) + ": it never went above +2, the episode was missed.</div></section>";
    }
    const ch = ev.price_change_pct, hot = ch > 0, pi = (D.priceImpact.episodes || {})[S.episode];
    const exp = pi ? (pi.reliable ? '<div style="font-size:16px;color:var(--frost-2);margin-top:10px;line-height:1.6">Expected from the supply gap the model saw on ' + dLong(pi.date) + ': <span class="mono">' + pct(pi.implied_pct) + "</span> (likely " + pct(pi.low_pct) + " to " + pct(pi.high_pct) + ") over the marketing year. Actual move shown above.</div>" : '<div style="font-size:16px;color:var(--frost-2);margin-top:10px">No reliable supply-price link for this crop, so no expected move is shown.</div>') : "";
    const fromLabel = ev.price_from_kind === "signal" ? "from the signal" : "from the start of the episode";
    const price = '<section class="glass"><div class="caps">' + esc(c.priceLabel) + '</div><div style="font-size:14px;color:var(--muted);margin-top:4px">' + fromLabel + ", " + dLong(ev.price_from_date) + " to " + dLong(ev.price_to_date) + '</div><div style="display:flex;align-items:baseline;gap:16px;margin-top:10px;flex-wrap:wrap"><span class="mono" style="font-size:34px;color:var(--frost-2)">' + fmt(ev.price_from) + '</span><span style="color:var(--muted)">to</span><span class="mono" style="font-size:40px;color:' + (hot ? "var(--heat)" : "var(--frost)") + '">' + fmt(ev.price_to) + '</span><span class="mono" style="font-size:22px;color:' + (hot ? "var(--heat)" : "var(--frost-2)") + '">' + pct(ch) + "</span></div>" + exp + '<div class="source">' + esc(c.priceUnit.charAt(0).toUpperCase() + c.priceUnit.slice(1)) + (ev.price_max ? ". Highest price of the episode: " + fmt(ev.price_max) + " on " + dLong(ev.price_max_date) : "") + ".</div></section>";
    const y0 = ev.start.slice(0, 4), y1 = ev.end.slice(0, 4);
    const html = '<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap"><div class="chips" role="group" aria-label="Episode">' + names.map((n) => '<button class="chip' + (n === S.episode ? " on" : "") + '" data-episode="' + n + '">' + esc(D.episodes[n].label) + "</button>").join("") + "</div>" +
      (ev.model_trained_on_seasons_up_to ? chip("THE MODEL ONLY KNEW HARVESTS UP TO " + ev.model_trained_on_seasons_up_to, true) : "") + "</div>" +
      '<div class="main c65"><div class="col">' + mapShell("episode", mapH() + 60, ev.range) + '<div class="source" style="margin-top:0">Stress every 10 days, compared with ' + D.meta.climBase[0] + "-" + D.meta.climBase[1] + ". Press play, or use the arrow keys to step.</div></div>" +
      '<div class="col">' + card + '<section class="glass"><div class="caps">RISK INDEX, ' + y0 + (y1 !== y0 ? " TO " + y1 : "") + '</div><div style="font-size:14px;color:var(--muted);margin-top:4px">Dashed line: +2, the rare level</div>' + pathChart(ev) + "</section>" + price + "</div></div>";
    let startI = ev.strip[0];
    return { html: html, after: () => mountMap({ viewBox: ev.viewBox, base: Object.assign({}, D.map.base, { href: BASE_IMG }), regions: ev.regions, frames: ev.frames, start: startI, strip: ev.strip, ringRadius: ev.viewBox[2] / 40, labelPrefix: "EPISODE REPLAY · " + ev.label.toUpperCase() + " · " + c.display, labelWord: "", rangeLabel: ev.range, capture: false, autoplay: false, ariaLabel: "Episode replay " + ev.label, borderWidth: 0.8 }) };
  }

  function splitFigure(t) { const m = /[-+]?[\d,]*\.?\d+(?:\s?(?:%|pp|points))?/.exec(t); return m ? [t.slice(0, m.index), m[0], t.slice(m.index + m[0].length)] : ["", "", t]; }
  function noteBody(n) {
    return n.template.split("\n\n").filter((p) => p.trim()).map((p) => "<p>" + esc(p).replace(/\{([A-Z][A-Z0-9_]*)\}/g, (all, k) => {
      const s = n.slots[k]; if (!s) return all;
      if (s.kind === "figure") { const [pre, f, rest] = splitFigure(s.text); return esc(pre) + (f ? '<span class="pill" title="' + esc(s.source + " \u00b7 " + s.date) + '">' + esc(f) + "</span>" : "") + esc(rest); }
      return "<b>" + esc(s.text) + "</b>";
    }) + "</p>").join("");
  }
  function viewNote() {
    const keyOf = (n) => n.week + "|" + n.commodity;
    if (!S.note) S.note = D.asOf + "|" + S.crop;
    const n = D.notes.find((x) => keyOf(x) === S.note) || D.notes[0];
    let lastDay = "";
    const inbox = D.notes.map((x) => {
      const tag = x.model === "deterministic-template" ? "Fixed template" : (x.templateParagraphs ? x.templateParagraphs + " of 3 paragraphs from the template" : "Written by the AI model");
      const head = x.week !== lastDay ? '<div class="caps" style="margin:8px 4px 0">' + dLong(x.week) + "</div>" : "";
      lastDay = x.week;
      return head + '<button class="glass inbox-item' + (keyOf(x) === keyOf(n) ? " on" : "") + '" data-note="' + keyOf(x) + '">' + glyph(D.crops[x.commodity].glyph, 22) + '<div style="flex:1;min-width:0"><div style="display:flex;justify-content:space-between;gap:8px;align-items:baseline"><span style="font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + esc(x.title) + '</span><span class="mono" style="font-size:13px;color:var(--muted);flex:none">07:00</span></div><div style="font-size:13px;color:var(--muted);margin-top:2px">' + tag + "</div></div></button>";
    }).join("");
    const readings = '<div><div class="caps" style="margin-bottom:8px">RISK INDEX ON ' + dLong(n.week).toUpperCase() + '</div><div class="grid3">' + Object.keys(n.readings).map((k) => {
      const r = n.readings[k], s = D.crops[k].riskRecent, i = s.d.indexOf(r.date), series = s.z.slice(Math.max(0, i - 25), i + 1);
      return '<div class="glass tick-card' + (k === n.commodity ? " sel" : "") + '" style="cursor:default">' + glyph(r.glyph, 26) + '<div style="min-width:0"><div class="caps" style="white-space:nowrap">' + esc(r.display) + '</div><div class="val' + (r.value >= 2 ? " glow" : "") + '">' + esc(r.text) + "</div></div>" + sparkline(series, 96) + "</div>";
    }).join("") + "</div></div>";
    const who = n.model === "deterministic-template" ? "Written from the fixed template (the AI model failed the checks)" : "Written by a small AI model running locally (" + esc(D.meta.llm.display_name) + ")" + (n.templateParagraphs ? "; " + n.templateParagraphs + " of 3 paragraphs from the fixed template" : "");
    const figs = Object.values(n.slots).filter((s) => s.kind === "figure").map((s) => '<div class="glass" style="padding:14px 16px"><div class="mono" style="font-size:22px;color:var(--signal)">' + esc(s.text) + '</div><div style="font-size:15px;color:var(--frost-2);margin-top:4px">' + esc(s.label) + '</div><div class="source" style="margin-top:6px">Source: ' + esc(s.source) + "<br>" + esc(s.date) + (s.detail ? ", " + esc(s.detail) : "") + "</div></div>").join("");
    const html = '<div class="main c30"><div class="col"><div style="display:flex;justify-content:space-between;align-items:baseline;margin:4px 4px 0"><span style="font-family:var(--display);font-weight:700;font-size:28px">Inbox</span><span class="caps">EVERY WORKING DAY, 07:00</span></div><div class="inbox-list">' + inbox + "</div></div>" +
      '<div class="col"><section class="glass" style="padding:22px 24px;display:flex;flex-direction:column;gap:16px"><div style="display:flex;gap:16px;align-items:center"><span style="border-radius:12px;overflow:hidden;display:inline-flex;flex:none">' + D.marks.signal.replace(/width="40" height="40"/, 'width="52" height="52"') + '</span><div><div style="font-family:var(--display);font-weight:700;font-size:30px;line-height:1.15">' + esc(n.title) + '</div><div style="color:var(--muted)">HarvestRadar Daily &middot; ' + dLong(n.week) + "</div></div></div>" + readings +
      '<div class="note-body">' + noteBody(n) + '</div><div class="chips">' + badge("Numbers checked", n.checks[0]) + badge("Context checked", n.checks[1]) + badge("Claims checked", n.checks[2]) + "</div>" +
      '<div style="font-size:14px;color:var(--muted)">' + who + ". Every figure is inserted by the software, with its source; hover a figure to see it.</div>" +
      '<div class="chips"><a class="btn primary" href="#stress" data-crop-link="' + n.commodity + '" style="display:inline-flex;align-items:center;text-decoration:none">Open the map</a></div></section>' +
      '<details class="glass"><summary>Data given to the model</summary><div class="figs">' + figs + '</div><div class="source">Written in ' + n.seconds + " seconds, " + n.attempts + " model attempt(s).</div></details></div></div>";
    return { html: html, after: null };
  }

  function viewMethod() {
    const M = D.method, ev = M.eval, pooled = ev.pooled || {};
    const rmW = pooled.rmse_vs_trend_weighted_pct, rmU = pooled.rmse_vs_trend_pct;
    const ramp = (z) => { const R = [[-3, [126, 176, 255]], [-2, [63, 116, 216]], [-1, [38, 64, 106]], [0, [30, 40, 51]], [1, [138, 100, 36]], [2, [245, 169, 58]], [3, [255, 90, 54]]]; z = Math.max(-3, Math.min(3, z)); for (let i = 0; i < 6; i++) { const [a, ca] = R[i], [b, cb] = R[i + 1]; if (z >= a && z <= b) { const t = (z - a) / (b - a); return "rgb(" + ca.map((v, j) => Math.round(v + (cb[j] - v) * t)).join(",") + ")"; } } return "rgb(255,90,54)"; };
    const totalR = CROPS.reduce((s0, k) => s0 + D.crops[k].regionsN, 0);
    const maize = D.crops.maize.latest;
    const shares = maize.contributors.slice().sort((a, b) => b.share_pct - a.share_pct).slice(0, 3);
    const card = (num, t, big, sub, extra, on) => '<section class="glass' + (on ? " amber" : "") + '" style="min-height:290px"><div class="mono" style="font-size:13px;color:' + (on ? "var(--signal)" : "var(--muted)") + '">STEP ' + num + '</div><div style="font-family:var(--display);font-weight:700;font-size:28px;margin-top:6px">' + t + '</div><div class="mono" style="font-size:40px;margin-top:8px">' + big + '</div><div style="color:var(--frost-2)">' + sub + "</div>" + (extra || "") + "</section>";
    const strip = '<div style="display:flex;gap:3px;margin-top:22px">' + M.strip.values.map((v) => '<i style="flex:1;height:22px;border-radius:3px;background:' + ramp(v) + '"></i>').join("") + '</div><div class="source">' + esc(M.strip.name) + ", summer 2012, every 10 days</div>";
    const bars = shares.map((x) => '<div style="display:grid;grid-template-columns:110px minmax(0,1fr) 46px;gap:10px;align-items:center;margin-top:8px"><span style="color:var(--frost-2);font-size:15px">' + esc(x.name) + '</span><div style="height:6px;border-radius:3px;background:var(--line)"><div style="height:6px;border-radius:3px;width:' + Math.min(100, 2 * x.share_pct).toFixed(0) + '%;background:var(--frost-2)"></div></div><span class="mono" style="font-size:13px;color:var(--muted);text-align:right">' + Math.round(x.share_pct) + "%</span></div>").join("");
    const row = (t, f, v, tone) => '<tr><td class="t">' + t + '</td><td class="f">' + f + '</td><td class="v">' + tag(v, tone) + "</td></tr>";
    const gain = (x) => (x <= -10 ? ["Clear gain", "good"] : x < 0 ? ["Small gain", "good"] : ["No gain", "bad"]);
    const errTxt = (x) => Math.abs(x).toFixed(1) + "% " + (x < 0 ? "smaller" : "larger") + " error than the trend";
    let ledger = row("Harvest forecasts vs a simple trend, " + ev.test[0] + " to " + ev.test[1] + ", weighted by world share", errTxt(rmW), ...gain(rmW)) + row("Same, every country counted equally", errTxt(rmU), ...gain(rmU));
    Object.values(M.events).forEach((e) => {
      const f = e.first_above_2 ? "Above +2 on " + dLong(e.first_above_2) + (e.verdict === "late" ? ", after the price peak" : ", before the price peak") : "Highest " + sg(e.peak_risk_z) + ", never above +2";
      ledger += row(esc(e.label), f, ...({ caught: ["Caught", "good"], late: ["Too late", "warn"], missed: ["Missed", "bad"] }[e.verdict]));
    });
    const bt = M.backtest, sig = bt.best_rule_p_corrected < 0.05;
    ledger += row("Trading on the index, after costs", Math.round(100 * bt.best_rule_p_corrected) + "% chance the gain is luck", sig ? "Significant" : "Not significant", sig ? "good" : "neutral");
    ledger = '<section class="glass"><table class="ledger"><thead><tr><th>TEST</th><th>RESULT</th><th class="r">VERDICT</th></tr></thead><tbody>' + ledger + "</tbody></table></section>";
    const trs = Object.entries(ev.byCrop).map(([k, b]) => { const m = b.model || {}, t = b.trend_only || {}; return "<tr><td>" + esc(D.crops[k].label) + "</td><td>" + m.n + "</td><td>" + (100 * m.rmse).toFixed(1) + "</td><td>" + (100 * t.rmse).toFixed(1) + "</td><td>" + sg(m.spearman || 0) + "</td><td>" + Math.round(100 * (m.sign_accuracy || 0)) + "%</td></tr>"; }).join("");
    const html = '<h1 class="ttl">Under the hood, four steps.</h1><div class="grid4">' +
      card("1", "Crop maps", totalR.toLocaleString("en-US"), "producing regions, covering 90% of world output of each crop (MapSPAM 2020)", '<div style="display:flex;gap:14px;margin-top:26px">' + glyph("maize", 26) + glyph("arabica", 26) + glyph("cocoa", 26) + "</div>") +
      card("2", "Weather", D.meta.cells.toLocaleString("en-US"), "NASA weather points, read every day since 1981", strip) +
      card("3", "Model", pct(rmW), "smaller harvest-forecast error than a simple trend, on harvests the model had never seen, weighted by world share", '<div class="chips" style="margin-top:20px">' + chip("Gradient boosting") + chip("Explained factor by factor", true) + "</div>", true) +
      card("4", "World index", sg(maize.z), "maize today: country forecasts weighted by their share of world output", bars) + "</div>" +
      '<div class="chips" style="margin-top:16px"><span class="caps" style="margin-right:8px">BEYOND THE COURSE</span>' + ["Weather weighted by where crops grow", "Testing without peeking at the future", "Explanations by weather factor (SHAP)", "Local AI writer with fact checks", "Trading test against luck"].map((t) => chip(t)).join("") + "</div>" +
      '<div class="main c65" style="margin-top:8px"><div class="col"><h2 class="ttl">Tested like sceptics.</h2>' + ledger + '<div class="source">HarvestRadar is a radar, not a crystal ball. "Caught" means the index went above +2 before the futures price peaked.</div></div>' +
      '<div class="col"><h2 class="ttl">Forecast errors by crop</h2><section class="glass scroll-x"><table class="ev"><thead><tr><th>CROP</th><th>HARVESTS</th><th>MODEL ERROR</th><th>TREND ERROR</th><th>RANK MATCH</th><th>RIGHT DIRECTION</th></tr></thead><tbody>' + trs + '</tbody></table><div class="source">Typical error, in percentage points of yield (maize) or production (tree crops) vs normal, harvests ' + ev.test[0] + " to " + ev.test[1] + ". Rank match: how well the model orders good and bad harvests (1 = perfectly). Each year is forecast by a model trained only on harvests published before it.</div></section>" +
      '<section class="glass"><div class="caps" style="margin-bottom:8px">CREDITS</div><div style="font-size:15px;line-height:1.7;color:var(--frost-2)"><b>Data</b>: NASA POWER weather, MapSPAM 2020 crop maps (IFPRI), geoBoundaries regions, FAOSTAT harvests, NOAA El Ni&ntilde;o index, futures prices via Yahoo Finance, Natural Earth.<br><b>Imagery</b>: NASA Blue Marble (public domain).<br><b>Model</b>: LightGBM gradient boosting, SHAP explanations; daily note by ' + esc(D.meta.llm.display_name) + " (Hugging Face), run locally.<br><b>Fonts</b>: Space Grotesk, Inter, JetBrains Mono.</div></section></div></div>";
    return { html: html, after: null };
  }

  /* ---------- Assistant: answers in the page, from a small open model running in the browser ---------- */
  const NOTE_TEXT = (n) => n.template.replace(/\{([A-Z][A-Z0-9_]*)\}/g, (all, k) => (n.slots[k] ? n.slots[k].text : all));
  /* What the viewer is looking at: added to every question, so the assistant answers about this page. */
  function viewContext() {
    const v = current(), k = S.crop, c = D.crops[k], L = ["## What the user is looking at now", "- Page: " + VIEWS[v] + (v === "ask" || v === "method" ? "" : ", crop: " + c.label) + "."];
    if (v === "commodity") {
      const cs = c.latest.contributors.map((x) => x.country).filter((iso) => c.shap[iso]), sel = S.shap[k] && cs.includes(S.shap[k]) ? S.shap[k] : cs[0], sh = c.shap[sel];
      L.push("- On screen: the " + c.label + " risk index (" + sg(c.latest.z) + "), expected world supply (" + pct(c.latest.dp, 2) + "), the last close (" + fmtPrice(k, c.lastPrice.close) + "), the index against the price over 64 weeks, what it means for the price, the countries behind the reading and the weather factors" + (sh ? " for " + ((c.latest.contributors.find((x) => x.country === sel) || {}).name || sel) + " (" + sh.rows.map((r) => r[0] + " " + sg(r[1])).join(", ") + ")" : "") + ".");
    } else if (v === "fair" && c.fair) {
      const st = S.calc[k] || calcDefaults(k), r = calcResult(k, st);
      L.push("- On screen: " + c.label + " futures price vs climate fair value (" + (S.range === "long" ? "since 2006" : "last 2 years") + ").");
      L.push("- Pricing tool scenario set by the user: " + (st.scen === "today" ? "today's values" : st.scen != null ? "risk index " + sg(+st.scen, 0) : "custom") + "; expected world supply " + pct(st.gap, 2) + " (same as a risk index of " + sg(r.z) + "), price reaction " + st.r.toFixed(2) + "% per 1% missing, anchor " + fmtPrice(k, st.anchor) + " -> fair value " + fmtPrice(k, r.fair) + " (80% range " + fmtPrice(k, r.lo) + " to " + fmtPrice(k, r.hi) + "); last close is " + gapWords(r.vs) + ".");
    } else if (v === "stress") {
      L.push("- On screen: the " + c.label + " stress map for the 10 days to " + dLong(c.map.dekad) + ". Most stressed regions weighted by output: " + c.map.top5.map((r) => r.name + " (" + r.iso + ")").join(", ") + ".");
    } else if (v === "replay") {
      const e = D.episodes[S.episode], pi = (D.priceImpact.episodes || {})[S.episode];
      L.push("- On screen: the replay of " + e.label + ": " + (e.first_above_2 ? "index first above +2 on " + dLong(e.first_above_2) + " (" + ({ caught: "before", late: "after" }[e.verdict] || "") + " the price peak)" : "index never above +2, highest " + sg(e.peak_risk_z)) + "; futures " + pct(e.price_change_pct) + " from " + dLong(e.price_from_date) + " to " + dLong(e.price_to_date) + (pi && pi.reliable ? "; move expected from the supply gap " + pct(pi.implied_pct) : "") + ".");
    } else if (v === "note") {
      const n = D.notes.find((x) => x.week + "|" + x.commodity === S.note) || D.notes[0];
      L.push("- On screen: the daily note of " + dLong(n.week) + " on " + D.crops[n.commodity].label + ": " + NOTE_TEXT(n).replace(/\s+/g, " "));
    }
    return L.join("\n");
  }

  function suggestions() {
    const v = current(), c = D.crops[S.crop], lab = c.label.toLowerCase(), e = D.episodes[S.episode];
    return ({
      commodity: ["What drives the " + lab + " risk index today, and how much does it matter for the price?", "Build a " + lab + " trade idea from this page: direction, entry logic, invalidation and risks.", "Which country or weather factor could change the " + lab + " reading most in the coming weeks?"],
      fair: ["Is " + lab + " cheap or expensive against its climate fair value, and what could close the gap?", "Explain the scenario I set in the pricing tool and what would have to happen for it to play out.", "How reliable is this fair value, and how should I use it in a trade?"],
      stress: ["Which regions matter most for " + lab + " right now, and why?", "Is the stress on this map already in the " + lab + " price?", "What weather should I watch next for " + lab + "?"],
      replay: ["What can a trader learn from " + e.label + "?", "Would trading on the index have worked in " + e.label + "?", "Why did the price move more or less than the supply gap suggests?"],
      note: ["Summarise this note for a trader in three bullet points.", "What should I watch tomorrow for " + lab + "?", "Does this note change the trade idea on " + lab + "?"],
      method: ["How much should I trust this model, given its track record?", "What are the main weaknesses of this approach?", "How should I combine this index with other information in a trade?"],
    })[v] || ["Summarise today's signals across the three crops for a trader.", "Is maize cheap or expensive against its climate fair value, and what could close the gap?",
      "Build a cocoa trade idea from today's data: direction, entry logic, invalidation and risks.", "What would make the maize index wrong this month?", "How should I size a weather trade given this level of uncertainty?"];
  }
  const ctxLabel = () => { const v = current(); return v === "ask" || v === "method" ? "all three crops" : VIEWS[v] + " \u00b7 " + D.crops[S.crop].label; };
  const GPT_URL = "https://chatgpt.com/?q=";
  const RULES = "You are the HarvestRadar assistant, inside a research dashboard on weather risk for maize, arabica coffee and cocoa futures. Use only the HarvestRadar figures below for numbers, and say plainly when something is not in them (stocks, positioning, news). The risk index compares the expected world harvest with normal for the time of year: 0 = normal, above +2 = rare; it moves with the weather and is weakly linked to prices week to week. Less supply than normal (index above 0) tends to push prices up; more supply pushes them down. The climate fair value is the 12-month average price moved by the price reaction to the expected world supply gap. Give trade ideas as scenarios with entry logic, invalidation level and risks, never personalised advice. Answer in at most 150 words, in the language of the question.";
  function cropLine(k, full) {
    const c = D.crops[k], la = c.latest, f = c.fair;
    let s = "- " + c.label + " (" + c.priceName + ", " + c.priceUnit + "): risk index " + sg(la.z) + "; expected world supply " + pct(la.dp, 2) + " vs normal; last close " + fmtPrice(k, c.lastPrice.close) + " (" + dLong(c.lastPrice.date) + ")";
    if (f) s += "; climate fair value " + fmtPrice(k, f.now.fair) + " (80% range " + fmtPrice(k, f.now.fair_lo) + " to " + fmtPrice(k, f.now.fair_hi) + "), price " + gapWords(f.now.gap_to_fair_pct) + "; price reaction " + (-f.flex.slope_pct_per_pct).toFixed(2) + "% per 1% of world supply missing" + (f.now.reliable ? "" : " (not statistically reliable)");
    s += ".";
    if (!full) return s;
    s += "\n  Countries behind the reading (points of world supply): " + la.contributors.slice(0, 4).map((x) => x.name + " " + sg(x.contrib_pct) + (x.window_open ? " (critical window open)" : "")).join(", ") + ".";
    const top = la.contributors[0], sh = top && c.shap[top.country];
    if (sh) s += "\n  Weather factors behind the " + top.name + " forecast: " + sh.rows.slice(0, 3).map((r) => r[0] + " " + sg(r[1])).join(", ") + ".";
    const pw = c.pricesWeekly.c, n = pw.length;
    if (n > 14) s += "\n  Price change: 4 weeks " + pct(100 * (pw[n - 1] / pw[n - 5] - 1)) + ", 13 weeks " + pct(100 * (pw[n - 1] / pw[n - 14] - 1)) + ".";
    return s;
  }
  function contextText(rich) {
    const v = current(), focus = v === "ask" || v === "method" ? null : S.crop;
    return RULES + "\n\nHarvestRadar data of " + dLong(D.asOf) + ":\n" + CROPS.map((k) => cropLine(k, rich && (focus === null || k === focus))).join("\n") +
      "\n- El Nino index " + sg(D.oni.value) + " C (" + D.oni.strength + "), context only.\n\n" + viewContext();
  }
  const gptLink = (q) => { let p = contextText(true) + "\n\nMy question: " + q; if (encodeURIComponent(p).length > 7000) p = contextText(false) + "\n\nMy question: " + q; return GPT_URL + encodeURIComponent(p); };

  /* The model runs in the viewer's browser on the processor (wllama: llama.cpp compiled to WebAssembly), so it
     works without a graphics card: free, no account, nothing leaves the computer except the one-time model
     download (about 400 MB from Hugging Face, then kept by the browser). */
  const WLLAMA = "https://cdn.jsdelivr.net/npm/@wllama/wllama@3.8.1/esm/index.js";
  const WLLAMA_WASM = "https://cdn.jsdelivr.net/npm/@wllama/wllama@3.8.1/esm/wasm/wllama.wasm";
  const GGUF = { repo: "Qwen/Qwen2.5-0.5B-Instruct-GGUF", file: "qwen2.5-0.5b-instruct-q4_k_m.gguf" };
  const LLM = { engine: null, loading: null, state: "idle", pct: 0, error: "", ctl: null };
  function loadEngine() {
    if (LLM.engine) return Promise.resolve(LLM.engine);
    if (LLM.loading) return LLM.loading;
    LLM.loading = (async () => {
      if (typeof WebAssembly !== "object") { LLM.state = "unsupported"; throw new Error("WebAssembly is not available"); }
      LLM.state = "loading"; LLM.pct = 0; askRefresh();
      const { Wllama } = await import(WLLAMA);
      const w = new Wllama({ default: WLLAMA_WASM }, { suppressNativeLog: true });
      await w.loadModelFromHF(GGUF, { n_ctx: 2048, n_gpu_layers: 0, progressCallback: ({ loaded, total }) => { LLM.pct = total ? loaded / total : 0; showProgress(); } });
      LLM.engine = w; LLM.state = "ready"; askRefresh();
      return w;
    })().catch((e) => {
      LLM.loading = null;
      if (LLM.state !== "unsupported") { LLM.state = "failed"; LLM.error = String((e && e.message) || e).split("\n")[0].slice(0, 200); }
      askRefresh();
      throw e;
    });
    return LLM.loading;
  }
  function showProgress() {
    const b = document.getElementById("llm-bar"), t = document.getElementById("llm-text");
    if (b) b.style.width = Math.round(100 * LLM.pct) + "%";
    if (t) t.textContent = LLM.pct < 1 ? "Downloading the model: " + Math.round(100 * LLM.pct) + "% of about 400 MB (once: your browser keeps it)." : "Starting the model on this computer...";
  }

  function md(src) {
    const inline = (t) => esc(t).replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
    const out = []; let list = null, para = [];
    const flush = () => { if (para.length) { out.push("<p>" + para.map(inline).join("<br>") + "</p>"); para = []; } if (list) { out.push("</" + list + ">"); list = null; } };
    src.replace(/\s*—\s*/g, ", ").replace(/\r/g, "").split("\n").forEach((ln) => {
      let m;
      if ((m = /^\s*#{1,6}\s+(.*)$/.exec(ln))) { flush(); out.push("<h4>" + inline(m[1]) + "</h4>"); }
      else if ((m = /^\s*[-*•]\s+(.*)$/.exec(ln)) || (m = /^\s*\d+[.)]\s+(.*)$/.exec(ln))) {
        const kind = /^\s*\d/.test(ln) ? "ol" : "ul";
        if (para.length) { out.push("<p>" + para.map(inline).join("<br>") + "</p>"); para = []; }
        if (list !== kind) { if (list) out.push("</" + list + ">"); out.push("<" + kind + ">"); list = kind; }
        out.push("<li>" + inline(m[1]) + "</li>");
      } else if (!ln.trim()) flush();
      else { if (list) { out.push("</" + list + ">"); list = null; } para.push(ln); }
    });
    flush();
    return out.join("");
  }

  /* One chat, moved between the Ask page and the side panel, so the conversation follows the viewer. */
  let chatEl = null;
  function chatWidget() {
    if (chatEl) return chatEl;
    chatEl = document.createElement("div");
    chatEl.className = "chat-widget";
    chatEl.innerHTML = '<div id="llm-status"></div><div class="chat-log" id="chat-log" aria-live="polite"></div><div class="chips" id="ask-suggest" style="margin-top:10px"></div>' +
      '<form class="composer" id="ask-form"><textarea id="ask-input" rows="2" placeholder="Ask about this page..." aria-label="Your question"></textarea><button class="btn primary" id="ask-send" type="submit">Send</button><button class="btn" id="ask-stop" type="button" hidden>Stop</button></form>' +
      '<div class="ctx-line" id="ask-ctx"></div>' +
      '<details style="margin-top:8px"><summary style="cursor:pointer;color:var(--frost-2);font-size:14px">What the assistant receives</summary><pre id="gpt-preview" class="mono" style="white-space:pre-wrap;font-size:13px;color:var(--muted);line-height:1.5;margin:8px 0 0"></pre></details>' +
      '<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-top:10px"><span class="source" style="margin:0">Free, no account: a small open model (Qwen 2.5, 0.5B) runs in your browser. It can be wrong: check figures on the page. Not investment advice.</span><button class="btn sm" id="ask-clear" type="button">Clear</button></div>';
    chatEl.querySelector("#ask-form").addEventListener("submit", (e) => { e.preventDefault(); askSend(chatEl.querySelector("#ask-input").value); });
    chatEl.querySelector("#ask-input").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); askSend(e.target.value); } });
    chatEl.querySelector("#ask-stop").addEventListener("click", () => { S.chat.stop = true; if (LLM.ctl) LLM.ctl.abort(); });
    chatEl.querySelector("#ask-clear").addEventListener("click", () => { if (S.chat.busy) { S.chat.stop = true; if (LLM.ctl) LLM.ctl.abort(); } S.chat.turns = []; S.chat.error = ""; askRefresh(); });
    return chatEl;
  }
  function askRefresh() {
    const log = document.getElementById("chat-log");
    if (!log) return;
    const C = S.chat;
    let h = C.turns.length ? "" : '<div class="msg bot"><p>Ask anything about what you see: what it means for prices, trade ideas, scenarios or risks. The assistant reads this page (' + esc(ctxLabel()) + ") and the HarvestRadar data of " + dLong(D.asOf) + ".</p></div>";
    C.turns.forEach((t, i) => { h += t.role === "user" ? '<div class="msg user">' + esc(t.content) + '<div class="meta">' + esc(t.where || "") + "</div></div>" : '<div class="msg bot" data-i="' + i + '">' + (t.content ? md(t.content) : '<span class="thinking">Writing...</span>') + (t.meta ? '<div class="meta">' + esc(t.meta) + "</div>" : "") + "</div>"; });
    if (C.busy && C.turns.length && C.turns[C.turns.length - 1].role === "user") h += '<div class="msg bot"><span class="thinking">' + (LLM.state === "loading" ? "Loading the model..." : "Thinking...") + "</span></div>";
    if (C.error) h += '<div class="warnbox">' + C.error + "</div>";
    log.innerHTML = h;
    log.scrollTop = log.scrollHeight;
    const st = document.getElementById("llm-status");
    if (st) {
      if (LLM.state === "loading") st.innerHTML = '<div style="margin-bottom:10px"><div style="height:6px;border-radius:3px;background:var(--line)"><div id="llm-bar" style="height:6px;border-radius:3px;background:var(--signal);width:0"></div></div><div class="ctx-line" id="llm-text" style="margin-top:6px"></div></div>';
      else if (LLM.state === "idle") st.innerHTML = '<div class="ctx-line" style="margin:0 0 10px">The first question downloads the model (about 400 MB, once). It then runs on this computer\'s processor: an answer takes about 30 to 60 seconds.</div>';
      else st.innerHTML = "";
      if (LLM.state === "loading") showProgress();
    }
    ["ask-send", "ask-input"].forEach((id) => { const e = document.getElementById(id); if (e) e.disabled = C.busy; });
    const stop = document.getElementById("ask-stop"); if (stop) stop.hidden = !C.busy;
    const sug = document.getElementById("ask-suggest");
    if (sug) { sug.hidden = C.turns.length > 0; sug.innerHTML = suggestions().map((x) => '<button class="chip" data-ask="' + esc(x) + '">' + esc(x) + "</button>").join(""); }
    const cx = document.getElementById("ask-ctx"); if (cx) cx.textContent = "The assistant sees: " + ctxLabel() + ", data of " + dLong(D.asOf);
    const pv = document.getElementById("gpt-preview"); if (pv) pv.textContent = contextText(false);
    const dl = document.getElementById("drawer-ctx"); if (dl) dl.textContent = ctxLabel();
    document.querySelectorAll("[data-ask]").forEach((b) => { b.disabled = C.busy; });
  }
  function fallbackHtml(q) {
    const why = LLM.state === "unsupported" ? "This browser cannot run the assistant (it needs WebAssembly)."
      : "The model could not be loaded here" + (LLM.error ? " (" + esc(LLM.error) + ")" : "") + ".";
    return why + ' You can still <a href="' + esc(gptLink(q)) + '" target="_blank" rel="noopener noreferrer">ask ChatGPT in a new tab</a>, with the same question and data.';
  }
  async function askSend(text) {
    const C = S.chat;
    text = (text || "").trim();
    if (!text || C.busy) return;
    C.error = ""; C.stop = false; C.turns.push({ role: "user", content: text, where: ctxLabel() }); C.busy = true;
    const inp = document.getElementById("ask-input"); if (inp) inp.value = "";
    askRefresh();
    let eng;
    try { eng = await loadEngine(); } catch (e) { C.busy = false; C.error = fallbackHtml(text); askRefresh(); return; }
    const history = [];
    C.turns.slice(-5, -1).forEach((t) => {
      if (!t.content) return;
      const m = { role: t.role, content: t.content.slice(0, 800) };
      if (history.length && history[history.length - 1].role === m.role) history[history.length - 1] = m; else history.push(m);
    });
    while (history.length && history[0].role !== "user") history.shift();
    if (history.length && history[history.length - 1].role === "user") history.pop();
    const msgs = [{ role: "system", content: contextText(false) }].concat(history, [{ role: "user", content: text }]);
    const slot = { role: "assistant", content: "" };
    C.turns.push(slot); askRefresh();
    const live = () => { const el = document.querySelector('#chat-log .msg.bot[data-i="' + (C.turns.length - 1) + '"]'), log = document.getElementById("chat-log"); if (el) { el.innerHTML = md(slot.content); if (log) log.scrollTop = log.scrollHeight; } };
    const run = async (engine, messages, maxTokens) => {
      LLM.ctl = new AbortController();
      const stream = await engine.createChatCompletion({ messages: messages, stream: true, temperature: 0.3, max_tokens: maxTokens, abortSignal: LLM.ctl.signal });
      let last = 0;
      for await (const ch of stream) {
        slot.content += (ch.choices && ch.choices[0] && ch.choices[0].delta && ch.choices[0].delta.content) || "";
        const now = Date.now();
        if (now - last > 80) { last = now; live(); }
      }
    };
    try {
      try {
        await run(eng, msgs, 450);
      } catch (e1) {
        console.error("HarvestRadar assistant, first attempt:", e1);
        if (C.stop || slot.content) throw e1;
        slot.content = "";  // second attempt: no history, a shorter answer
        await run(eng, [{ role: "system", content: contextText(false) }, { role: "user", content: text }], 300);
      }
      if (C.stop) slot.meta = "Stopped.";
      if (!slot.content.trim()) slot.content = "No answer came back. Try a shorter question.";
    } catch (e) {
      console.error("HarvestRadar assistant:", e);
      if (C.stop) { if (!slot.content) C.turns.pop(); else slot.meta = "Stopped."; return; }
      if (!slot.content) C.turns.pop(); else slot.meta = "Interrupted.";
      if (LLM.state === "loading") LLM.state = "failed";
      const detail = String((e && e.message) || e).split("\n")[0].slice(0, 220);
      C.error = "The model stopped with an error" + (detail ? ': <span class="mono" style="font-size:13px">' + esc(detail) + "</span>" : "") + '. Try again, or <a href="' + esc(gptLink(text)) + '" target="_blank" rel="noopener noreferrer">ask ChatGPT in a new tab</a>.';
    } finally { C.busy = false; C.stop = false; askRefresh(); }
  }

  /* Side panel available on every page; the floating button opens it with the page as context. */
  function drawerShell() {
    if (document.getElementById("drawer")) return;
    const fab = document.createElement("button");
    fab.id = "fab"; fab.className = "fab"; fab.type = "button"; fab.setAttribute("aria-controls", "drawer");
    fab.innerHTML = '<span class="dot"></span>Ask the assistant';
    const dr = document.createElement("aside");
    dr.id = "drawer"; dr.className = "drawer"; dr.setAttribute("aria-label", "Assistant"); dr.hidden = true;
    dr.innerHTML = '<div class="drawer-head"><div style="min-width:0"><div style="font-family:var(--display);font-weight:700;font-size:20px">Ask the assistant</div><div class="mono" id="drawer-ctx" style="font-size:13px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis"></div></div><button class="btn sm" id="drawer-close" type="button" aria-label="Close the panel">Close</button></div><div class="drawer-body"></div>';
    document.body.appendChild(fab); document.body.appendChild(dr);
    fab.addEventListener("click", () => openDrawer());
    dr.querySelector("#drawer-close").addEventListener("click", closeDrawer);
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && S.drawer) closeDrawer(); });
  }
  function openDrawer(q) {
    drawerShell();
    S.drawer = true;
    document.body.classList.add("drawer-open");
    const dr = document.getElementById("drawer");
    dr.querySelector(".drawer-body").appendChild(chatWidget());
    dr.hidden = false; requestAnimationFrame(() => dr.classList.add("open"));
    document.getElementById("fab").hidden = true;
    askRefresh();
    if (q) askSend(q); else { const i = document.getElementById("ask-input"); if (i) i.focus(); }
  }
  function closeDrawer() {
    S.drawer = false;
    document.body.classList.remove("drawer-open");
    const dr = document.getElementById("drawer");
    if (dr) { dr.classList.remove("open"); setTimeout(() => { if (!S.drawer) dr.hidden = true; }, 220); }
    const f = document.getElementById("fab"); if (f) f.hidden = current() === "ask";
  }
  function placeChat(v) {
    drawerShell();
    const fab = document.getElementById("fab"), dr = document.getElementById("drawer");
    if (v === "ask") {
      S.drawer = false; document.body.classList.remove("drawer-open"); dr.classList.remove("open"); dr.hidden = true; fab.hidden = true;
      document.getElementById("ask-slot").appendChild(chatWidget());
    } else {
      fab.hidden = !!S.drawer;
      if (S.drawer) dr.querySelector(".drawer-body").appendChild(chatWidget());
    }
    askRefresh();
  }
  function askPanel(k) {
    const c = D.crops[k], qs = suggestions();
    return panel("ASK ABOUT " + esc(c.label.toUpperCase()), '<div style="font-size:15px;color:var(--frost-2);line-height:1.55">The answer appears in the side panel. Free, no account: the assistant runs in your browser (about 30 to 60 seconds per answer).</div><div class="chips" style="margin-top:12px">' +
      qs.map((q) => '<button class="chip" data-askopen="' + esc(q) + '">' + esc(q) + "</button>").join("") + '<button class="chip" data-askopen="">Write your own question</button></div>', "It reads this page's figures. Not investment advice.");
  }

  function viewAsk() {
    const html = '<div class="main c65"><div class="col"><section class="glass" style="padding:18px 20px"><div style="font-family:var(--display);font-weight:700;font-size:24px;margin-bottom:12px">Ask about today\'s signals</div><div id="ask-slot"></div></section></div>' +
      '<div class="col">' + panel("HOW IT WORKS", '<div style="font-size:15px;color:var(--frost-2);line-height:1.65">The "Ask the assistant" button on every page opens this chat in a side panel, with that page as context: the crop, the readings on screen and, on the Fair value page, the scenario you set. The answers come from a small open model (Qwen 2.5, 0.5 billion parameters) that runs in your browser on the processor, so no graphics card is needed: free, no account, and your questions stay on your computer. The first question downloads the model (about 400 MB, once); each answer then takes about 30 to 60 seconds. If the model cannot load (for example inside Claude), a link offers to ask ChatGPT instead.</div>') + "</div></div>";
    return { html: html, after: null };
  }

  const RENDER = { stress: viewStress, commodity: viewCommodity, fair: viewFair, replay: viewReplay, note: viewNote, method: viewMethod, ask: viewAsk };
  function current() { const v = location.hash.slice(1); return RENDER[v] ? v : "stress"; }
  function render() {
    const v = current();
    const changed = v !== S.view;
    if (changed) { if (S.view) S.scroll[S.view] = window.scrollY; S.prev = S.view; S.view = v; }
    if (mapHandle && mapHandle.stop) { mapHandle.stop(); mapHandle = null; }
    document.getElementById("tabs").innerHTML = Object.entries(VIEWS).map(([k, l]) => '<a class="tab' + (k === v ? " on" : "") + '" href="#' + k + '"' + (k === v ? ' aria-current="page"' : "") + ">" + l + "</a>").join("");
    const out = RENDER[v]();
    document.getElementById("view").innerHTML = out.html;
    if (out.after) out.after();
    placeChat(v);
    if (changed) {
      const tgt = S.goto && document.getElementById(S.goto);
      if (tgt) tgt.scrollIntoView({ block: "start" });
      else window.scrollTo(0, S.restore ? S.scroll[v] || 0 : 0);
      S.goto = null; S.restore = false;
    }
    if (window.innerWidth < 700) { const on = document.querySelector(".tab.on"), tb = document.getElementById("tabs"); if (on && tb) tb.scrollLeft = on.offsetLeft - (tb.clientWidth - on.offsetWidth) / 2; }
  }

  document.getElementById("brand").innerHTML = D.marks.small + "<span>Harvest<b>Radar</b></span>";
  document.getElementById("status").textContent = "DATA AS OF " + D.weekLabel;
  document.addEventListener("click", (e) => {
    const nav = e.target.closest("a[data-goto],a[data-back]");
    if (nav) { if (nav.dataset.goto) S.goto = nav.dataset.goto; if (nav.dataset.back) S.restore = true; }
    const t = e.target.closest("[data-crop],[data-shap],[data-episode],[data-note],[data-crop-link],[data-range],[data-scen],#calc-reset,#calc-undo,[data-ask],[data-askopen]");
    if (!t) return;
    if (t.dataset.ask) { askSend(t.dataset.ask); return; }
    if (t.dataset.askopen !== undefined) { openDrawer(t.dataset.askopen || null); return; }
    if (t.dataset.range) { S.range = t.dataset.range; render(); return; }
    if (t.dataset.scen) {
      const k = S.crop, f = D.crops[k].fair, st = S.calc[k] || (S.calc[k] = calcDefaults(k));
      if (st.scen === t.dataset.scen) return;
      calcPush(k, snap(st));
      if (t.dataset.scen === "today") Object.assign(st, calcDefaults(k));
      else { st.gap = f.mu - +t.dataset.scen * f.sigma; st.scen = t.dataset.scen; }
      calcSync(); return;
    }
    if (t.id === "calc-reset") { const k = S.crop; calcPush(k, snap(S.calc[k])); S.calc[k] = calcDefaults(k); calcSync(); return; }
    if (t.id === "calc-undo") { const k = S.crop, h = S.hist[k] || []; if (h.length) { S.calc[k] = h.pop(); calcSync(); } return; }
    if (t.dataset.crop) { S.crop = t.dataset.crop; render(); }
    else if (t.dataset.shap) { S.shap[S.crop] = t.dataset.shap; render(); }
    else if (t.dataset.episode) { S.episode = t.dataset.episode; render(); }
    else if (t.dataset.note) { S.note = t.dataset.note; render(); }
    else if (t.dataset.cropLink) { S.crop = t.dataset.cropLink; }
  });
  document.addEventListener("input", (e) => {
    const id = e.target.id, st = S.calc[S.crop];
    if (!st || !["i-gap", "i-r", "i-anchor"].includes(id)) return;
    const v = parseFloat(e.target.value);
    if (!isFinite(v)) return;
    if (!S.pending) S.pending = snap(st);
    if (id === "i-gap") { st.gap = v; st.scen = null; } else if (id === "i-r") st.r = v; else if (v > 0) st.anchor = v;
    calcUpdate();
  });
  document.addEventListener("change", (e) => {
    if (!["i-gap", "i-r", "i-anchor"].includes(e.target.id) || !S.pending) return;
    calcPush(S.crop, S.pending); S.pending = null; calcUpdate();
  });
  window.addEventListener("hashchange", render);
  let rw = window.innerWidth;
  window.addEventListener("resize", () => { if ((rw < 700) !== (window.innerWidth < 700)) { rw = window.innerWidth; render(); } });
  render();
})();
```

## 68. `web/template.html`

```html
<title>HarvestRadar</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="Harvest-risk index for maize, arabica coffee and cocoa: weather where crops grow, one number per commodity, every week.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Space+Grotesk:wght@500;700&display=swap">
<style>
/* Radar Night: one dark "command center" look (deliberately single-theme). Layout: top bar, live ticker,
   then a wide working area (map or chart, about 70 %) beside a column of glass panels. */
:root {
  color-scheme: dark;
  --night: #0B0F14; --console: #131C27; --line: #1E2935; --line-strong: #2A3646;
  --frost: #EAF0F5; --frost-2: #C7D1DB; --muted: #8A9AAB; --faint: #6F7F90;
  --signal: #FFB547; --heat: #FF5A36; --blue: #3F74D8; --amber-dark: #8A6424; --amber-mid: #F5A93A;
  --glow-bg: #142030; --ice: #7EB0FF;
  --display: 'Space Grotesk', 'Segoe UI', Helvetica, Arial, sans-serif;
  --body: 'Inter', 'Segoe UI', Helvetica, Arial, sans-serif;
  --mono: 'JetBrains Mono', Menlo, Consolas, 'Courier New', monospace;
  --glass: linear-gradient(180deg, rgba(25,36,50,.82), rgba(13,19,27,.82));
  --glass-border: rgba(126,176,255,.15);
}
*, *::before, *::after { box-sizing: border-box; }
[hidden] { display: none !important; }
html { background: var(--night); }
body { margin: 0; background: radial-gradient(1200px 700px at 30% 20%, var(--glow-bg) 0%, var(--night) 70%) fixed; background-color: var(--night);
  color: var(--frost); font-family: var(--body); font-size: 16px; -webkit-font-smoothing: antialiased; }
.wrap { container: wrap / inline-size; max-width: 1840px; margin: 0 auto; padding-block: 14px 32px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
@media (min-width: 900px) { .wrap { padding-left: max(40px, env(safe-area-inset-left, 0px)); padding-right: max(40px, env(safe-area-inset-right, 0px)); } }
a { color: var(--signal); }
:focus-visible { outline: 2px solid var(--signal); outline-offset: 2px; }
button { font: inherit; color: inherit; }
.mono { font-family: var(--mono); font-variant-numeric: tabular-nums; }
.caps { font-family: var(--mono); font-size: 13px; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); }
.source { font-family: var(--mono); font-size: 13px; color: var(--faint); margin-top: 10px; line-height: 1.5; }
.glow { text-shadow: 0 0 30px rgba(255,181,71,.45); }
.glass { background: var(--glass); border: 1px solid var(--glass-border); border-radius: 18px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.05), 0 20px 60px rgba(0,0,0,.35); padding: 18px 20px; min-width: 0; }
.glass.amber { border-color: rgba(255,181,71,.7); box-shadow: 0 0 30px rgba(255,181,71,.15), 0 20px 60px rgba(0,0,0,.35); }

/* top bar */
.topbar { display: flex; align-items: center; gap: 18px; flex-wrap: wrap; min-height: 56px; border-bottom: 1px solid var(--line); padding-bottom: 10px; margin-bottom: 16px; }
.brand { display: flex; align-items: center; gap: 12px; font-family: var(--display); font-weight: 700; font-size: 22px; letter-spacing: -0.02em; text-decoration: none; color: var(--frost); }
.brand b { color: var(--signal); }
.tabs { display: flex; gap: 6px; flex-wrap: wrap; flex: 1; justify-content: center; }
.tab { padding: 7px 14px; border-radius: 10px; color: var(--frost-2); text-decoration: none; font-weight: 500; border: 1px solid transparent; }
.tab:hover { color: var(--frost); background: rgba(255,255,255,.04); }
.tab.on { color: var(--signal); background: rgba(255,181,71,.12); box-shadow: inset 0 0 0 1px rgba(255,181,71,.55); }
.status { display: flex; align-items: center; gap: 12px; font-family: var(--mono); font-size: 14px; letter-spacing: .14em; color: var(--frost-2); white-space: nowrap; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: var(--signal); box-shadow: 0 0 0 4px rgba(255,181,71,.18), 0 0 14px var(--signal); flex: none; }

/* layout */
.grid3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.main { display: grid; grid-template-columns: minmax(0, 7fr) minmax(0, 3fr); gap: 20px; margin-top: 16px; align-items: start; }
.main.c65 { grid-template-columns: minmax(0, 6.5fr) minmax(0, 3.5fr); }
.main.c30 { grid-template-columns: minmax(0, 3fr) minmax(0, 7fr); }
.col { display: flex; flex-direction: column; gap: 16px; min-width: 0; }
.cards3 { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr) minmax(0, 1fr); gap: 16px; }
.grid4 { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
@media (max-width: 1100px) {
  .main, .main.c65, .main.c30 { grid-template-columns: minmax(0, 1fr); }
  .grid4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .status { order: 3; }
}
@media (max-width: 700px) {
  .grid3, .cards3, .grid4 { grid-template-columns: minmax(0, 1fr); }
  .tabs { order: 2; flex: 1 1 100%; flex-wrap: nowrap; overflow-x: auto; justify-content: flex-start; scrollbar-width: none; margin: 0 -4px; padding: 2px 4px; }
  .tabs::-webkit-scrollbar { display: none; }
  .tab { flex: none; white-space: nowrap; }
  .hide-sm { display: none; }
  .status { white-space: normal; font-size: 13px; letter-spacing: .06em; min-width: 0; }
  .hero-val { font-size: 52px !important; }
}

/* ticker */
.tick-card { display: flex; align-items: center; gap: 16px; height: 88px; padding: 14px 20px; cursor: pointer; text-align: left; width: 100%; }
.tick-card.sel { border-color: rgba(255,181,71,.55); box-shadow: 0 0 0 1px rgba(255,181,71,.25), 0 20px 60px rgba(0,0,0,.35); }
.tick-card .val { font-family: var(--mono); font-size: 32px; line-height: 40px; color: var(--signal); font-weight: 500; }
.tick-card .spark { margin-left: auto; flex: 0 1 auto; min-width: 0; max-width: 42%; height: auto; }
.grid3 > * { min-width: 0; overflow: hidden; }
.tick-card .caps { overflow: hidden; text-overflow: ellipsis; }
.gl { display: inline-flex; flex: none; color: var(--frost-2); }

/* rows and bars */
.rank { display: grid; grid-template-columns: 34px 24px minmax(0, 1fr) auto; align-items: center; gap: 6px 10px; margin-bottom: 10px; }
.rank .name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rank .bar { grid-column: 3 / span 2; height: 4px; border-radius: 3px; background: var(--line); }
.rank .bar i { display: block; height: 4px; border-radius: 3px; box-shadow: 0 0 8px rgba(255,181,71,.35); }
.brow { display: grid; grid-template-columns: minmax(110px, 200px) minmax(0, 1fr) minmax(0, 1fr) 84px; align-items: center; gap: 10px; min-height: 46px; }
.brow .lab { min-width: 0; } .brow .lab div:first-child { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.brow .neg { display: flex; } .brow .pos { display: flex; border-left: 1px solid var(--line-strong); }
.brow .b { height: 12px; border-radius: 7px; }
.brow .v { text-align: right; font-family: var(--mono); font-size: 15px; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.chip { display: inline-flex; align-items: center; gap: 8px; padding: 7px 14px; border-radius: 10px; border: 1px solid var(--line-strong);
  background: rgba(19,28,39,.7); font-family: var(--mono); font-size: 13px; letter-spacing: .14em; text-transform: uppercase; color: var(--frost-2); }
.chip.amber { border-color: rgba(255,181,71,.7); color: var(--frost); box-shadow: 0 0 18px rgba(255,181,71,.18); }
button.chip { text-align: left; cursor: pointer; letter-spacing: .04em; text-transform: none; font-family: var(--body); font-size: 15px; }
button.chip.on { color: var(--signal); background: rgba(255,181,71,.12); border-color: rgba(255,181,71,.55); }
.pill { font-family: var(--mono); color: var(--signal); background: rgba(255,181,71,.10); border: 1px solid rgba(255,181,71,.55); border-radius: 7px; padding: 1px 7px; white-space: nowrap; font-variant-numeric: tabular-nums; }
.badge { display: inline-flex; align-items: center; gap: 7px; padding: 6px 12px; border-radius: 999px; border: 1px solid var(--line-strong); background: rgba(19,28,39,.7); font-size: 15px; color: var(--frost-2); }
.btn { border-radius: 12px; font-weight: 600; font-size: 16px; min-height: 44px; padding: 0 22px; cursor: pointer; border: 1px solid var(--line-strong); background: transparent; color: var(--frost); }
.btn.primary { background: var(--signal); color: var(--night); border: none; }
.btn.sm { min-height: 36px; padding: 0 14px; font-size: 14px; font-weight: 500; }

/* map (same structure as the Streamlit component) */
.radar { position: relative; width: 100%; border-radius: 16px; overflow: hidden; outline: none;
  background: radial-gradient(900px 500px at 40% 35%, rgba(20,32,48,.65), rgba(11,15,20,0) 70%); }
.radar:focus-visible { box-shadow: 0 0 0 2px var(--signal) inset; }
.map-stage { position: absolute; inset: 0 0 88px 0; }
.radar.episode .map-stage { inset: 0 0 238px 0; }
.map-svg { width: 100%; height: 100%; display: block; }
.corner { position: absolute; width: 22px; height: 22px; border: 0 solid rgba(255,181,71,.7); pointer-events: none; z-index: 4; }
.c-tl { top: 0; left: 0; border-top-width: 2px; border-left-width: 2px; border-top-left-radius: 6px; }
.c-tr { top: 0; right: 0; border-top-width: 2px; border-right-width: 2px; border-top-right-radius: 6px; }
.c-bl { bottom: 0; left: 0; border-bottom-width: 2px; border-left-width: 2px; border-bottom-left-radius: 6px; }
.c-br { bottom: 0; right: 0; border-bottom-width: 2px; border-right-width: 2px; border-bottom-right-radius: 6px; }
.map-label { position: absolute; top: 16px; left: 22px; right: 22px; z-index: 3; font-family: var(--mono); font-size: 14px; letter-spacing: .14em; color: var(--frost-2); text-transform: uppercase; text-shadow: 0 1px 8px rgba(0,0,0,.8); }
.legend { position: absolute; left: 22px; bottom: 94px; z-index: 3; }
.radar.episode .legend { bottom: 246px; }
.legend .sw { display: flex; gap: 4px; } .legend .sw i { width: 32px; height: 8px; border-radius: 3px; display: block; }
.legend .lg { display: flex; justify-content: space-between; font-family: var(--mono); font-size: 13px; color: var(--muted); margin-top: 5px; }
.radar .bar { position: absolute; left: 12px; right: 12px; bottom: 12px; height: 64px; display: flex; align-items: center; gap: 14px; padding: 0 14px 0 10px; z-index: 5;
  background: var(--glass); border: 1px solid var(--glass-border); border-radius: 18px; }
.radar.episode .bar { bottom: 164px; }
.play { width: 44px; height: 44px; flex: none; border-radius: 50%; border: none; cursor: pointer; background: var(--signal);
  box-shadow: 0 0 0 5px rgba(255,181,71,.16), 0 0 18px rgba(255,181,71,.55); display: grid; place-items: center; }
.play svg { width: 18px; height: 18px; } .play .i-pause { display: none; }
.playing .play .i-pause { display: block; } .playing .play .i-play { display: none; }
.ticks { flex: 1; min-width: 0; height: 40px; display: flex; align-items: center; justify-content: space-between; gap: 2px; }
.tick { flex: 1; max-width: 10px; height: var(--h); border: none; padding: 0; border-radius: 2px; cursor: pointer; background: rgba(138,154,171,.28); }
.tick.on { background: rgba(255,181,71,.75); } .tick.now { background: var(--signal); box-shadow: 0 0 10px rgba(255,181,71,.8); }
.range { font-family: var(--mono); font-size: 14px; letter-spacing: .14em; color: var(--frost-2); white-space: nowrap; }
.speed { font-family: var(--mono); font-size: 13px; color: var(--muted); background: transparent; cursor: pointer; border: 1px solid var(--line-strong); border-radius: 8px; padding: 4px 8px; }
.speed.on { color: var(--signal); border-color: rgba(255,181,71,.6); }
.tip { position: absolute; z-index: 9; pointer-events: none; opacity: 0; transition: opacity .12s; padding: 8px 11px; background: var(--console);
  border: 1px solid var(--line-strong); border-radius: 10px; font-size: 14px; display: flex; gap: 8px; align-items: baseline; white-space: nowrap; }
.tip span { color: var(--muted); font-family: var(--mono); font-size: 13px; } .tip em { font-style: normal; color: var(--signal); font-family: var(--mono); }
.ping { transform-box: fill-box; transform-origin: center; animation: ping 2.4s ease-out infinite; }
@keyframes ping { 0% { opacity: .55; } 50% { opacity: 1; } 100% { opacity: .55; } }
.strip { position: absolute; left: 12px; right: 12px; bottom: 12px; height: 140px; display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px; padding: 10px; z-index: 5;
  background: var(--glass); border: 1px solid var(--glass-border); border-radius: 18px; }
.thumb { position: relative; border: 1px solid var(--line-strong); border-radius: 10px; overflow: hidden; padding: 0; background: var(--night); cursor: pointer; min-width: 0; }
.thumb svg { width: 100%; height: calc(100% - 24px); display: block; }
.thumb-label { height: 24px; line-height: 24px; font-family: var(--mono); font-size: 13px; color: var(--muted); text-align: left; padding-left: 8px; }
.thumb.active { border-color: rgba(255,181,71,.9); box-shadow: 0 0 16px rgba(255,181,71,.45); } .thumb.active .thumb-label { color: var(--signal); }
@media (max-width: 700px) {
  .legend { display: none; } .range { display: none; }
  .strip { grid-template-columns: repeat(3, minmax(0, 1fr)); height: 140px; }
  .strip .thumb:nth-child(n+4) { display: none; }
}
@media (prefers-reduced-motion: reduce) { .ping { animation: none; } }

/* note */
.inbox-list { display: flex; flex-direction: column; gap: 8px; max-height: calc(100vh - 150px); overflow-y: auto; padding-right: 4px; }
@media (max-width: 1100px) { .inbox-list { max-height: 360px; } }
.inbox-item { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-radius: 14px; cursor: pointer; text-align: left; width: 100%; }
.inbox-item.on { background: rgba(255,181,71,.08); border-color: rgba(255,181,71,.6); }
.note-body p { font-size: 18px; line-height: 1.75; color: var(--frost-2); margin: 0 0 14px 0; max-width: 1100px; }
.note-body b { color: var(--frost); font-weight: 600; }
details.glass summary { cursor: pointer; color: var(--frost-2); font-size: 16px; }
.figs { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; margin-top: 14px; }
.email-wrap { min-width: 0; }
.email-wrap table { max-width: 100%; }

/* method */
table.ledger { width: 100%; border-collapse: collapse; }
table.ledger th { font-family: var(--mono); font-size: 13px; letter-spacing: .12em; color: var(--muted); font-weight: 400; text-align: left; padding: 0 10px 10px; }
table.ledger th.r, table.ledger td.v { text-align: right; }
table.ledger td { padding: 14px 10px; border-top: 1px solid var(--line); vertical-align: middle; }
table.ledger .t { font-size: 17px; line-height: 1.45; color: var(--frost); }
table.ledger .f { font-family: var(--mono); font-size: 15px; line-height: 1.45; color: var(--frost-2); }
table.ledger td.v { white-space: nowrap; }
@media (max-width: 700px) {
  table.ledger thead { display: none; }
  table.ledger tr { display: grid; grid-template-columns: minmax(0, 1fr) auto; border-top: 1px solid var(--line); padding: 10px 0; }
  table.ledger td { border: 0; padding: 3px 6px; }
  table.ledger .f { grid-column: 1 / -1; grid-row: 2; }
}
/* status tags (verdicts, checks): a coloured dot and a word, no symbols */
.tag { display: inline-flex; align-items: center; gap: 8px; padding: 5px 11px; border-radius: 8px; border: 1px solid var(--line-strong);
  background: rgba(19,28,39,.7); font-family: var(--mono); font-size: 13px; letter-spacing: .08em; text-transform: uppercase; color: var(--frost-2); white-space: nowrap; }
.tag::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor; flex: none; }
.tag.good { color: var(--ice); border-color: rgba(126,176,255,.45); background: rgba(63,116,216,.14); }
.tag.warn { color: var(--signal); border-color: rgba(255,181,71,.5); background: rgba(255,181,71,.10); }
.tag.bad { color: var(--heat); border-color: rgba(255,90,54,.5); background: rgba(255,90,54,.10); }
.tag.neutral { color: var(--muted); }
.tag.plain { text-transform: none; letter-spacing: 0; font-family: var(--body); font-size: 14px; }
table.ev { width: 100%; border-collapse: collapse; font-size: 16px; color: var(--frost-2); }
table.ev th { font-family: var(--mono); font-size: 13px; letter-spacing: .1em; color: var(--muted); text-align: right; font-weight: 400; padding: 6px; }
table.ev th:first-child, table.ev td:first-child { text-align: left; }
table.ev td { padding: 8px 6px; border-top: 1px solid var(--line); text-align: right; font-family: var(--mono); }
table.ev td:first-child { font-family: var(--body); }
.scroll-x { overflow-x: auto; }
/* fair value and pricing tool */
.chart-wrap { position: relative; }
.chart-tip { position: absolute; z-index: 6; pointer-events: none; opacity: 0; transition: opacity .1s; min-width: 190px; padding: 10px 12px;
  background: var(--console); border: 1px solid var(--line-strong); border-radius: 10px; font-size: 14px; line-height: 1.6; }
.chart-tip .k { color: var(--muted); } .chart-tip .mono { float: right; margin-left: 14px; }
.legend-row { display: flex; flex-wrap: wrap; gap: 8px 20px; align-items: center; color: var(--frost-2); font-size: 14px; }
.legend-row i { display: inline-block; width: 22px; height: 3px; border-radius: 2px; vertical-align: middle; margin-right: 8px; }
.stat { padding: 14px 16px; border: 1px solid var(--line); border-radius: 12px; background: rgba(11,15,20,.35); min-width: 0; }
.stat .mono { font-size: 28px; color: var(--frost); }
.stat .lab { font-size: 14px; color: var(--frost-2); margin-top: 4px; line-height: 1.45; }
.calc label { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; margin-top: 18px; font-size: 15px; color: var(--frost-2); }
.calc output { font-family: var(--mono); font-size: 18px; color: var(--frost); white-space: nowrap; }
.calc input[type=range] { width: 100%; margin: 10px 0 2px; accent-color: var(--signal); height: 28px; }
.calc input[type=number] { width: 100%; margin-top: 8px; min-height: 44px; padding: 0 12px; border-radius: 10px; border: 1px solid var(--line-strong);
  background: var(--night); color: var(--frost); font-family: var(--mono); font-size: 16px; }
.calc .hint { font-size: 13px; color: var(--muted); font-family: var(--mono); line-height: 1.5; }
.calc .result { margin-top: 20px; padding: 16px 18px; border-radius: 14px; border: 1px solid rgba(255,181,71,.45); background: rgba(255,181,71,.06); }
.warnbox { padding: 12px 14px; border-radius: 12px; border: 1px solid rgba(255,90,54,.45); background: rgba(255,90,54,.08); color: var(--frost-2); font-size: 15px; line-height: 1.55; }
/* assistant */
.chat-log { display: flex; flex-direction: column; gap: 14px; min-height: 320px; max-height: min(62vh, 720px); overflow-y: auto; padding: 4px 2px 8px; }
.msg { max-width: 92%; padding: 12px 16px; border-radius: 14px; font-size: 16px; line-height: 1.6; overflow-wrap: anywhere; }
.msg.user { align-self: flex-end; background: rgba(255,181,71,.10); border: 1px solid rgba(255,181,71,.4); color: var(--frost); white-space: pre-wrap; }
.msg.bot { align-self: flex-start; background: rgba(11,15,20,.45); border: 1px solid var(--line-strong); color: var(--frost-2); }
.msg.bot p { margin: 0 0 10px; } .msg.bot p:last-child { margin-bottom: 0; }
.msg.bot ul, .msg.bot ol { margin: 0 0 10px; padding-left: 22px; } .msg.bot li { margin: 3px 0; }
.msg.bot h3, .msg.bot h4 { font-family: var(--display); color: var(--frost); margin: 12px 0 6px; font-size: 17px; }
.msg.bot b, .msg.bot strong { color: var(--frost); }
.msg.bot code { font-family: var(--mono); font-size: 14px; background: rgba(255,255,255,.06); padding: 1px 5px; border-radius: 5px; }
.msg.bot table { border-collapse: collapse; margin: 6px 0 10px; font-size: 14px; display: block; overflow-x: auto; }
.msg.bot th, .msg.bot td { border: 1px solid var(--line-strong); padding: 5px 8px; text-align: left; }
.msg .meta { font-family: var(--mono); font-size: 13px; color: var(--muted); margin-top: 8px; }
.composer { display: flex; gap: 10px; align-items: flex-end; margin-top: 12px; }
.composer textarea { flex: 1; min-width: 0; min-height: 52px; max-height: 200px; resize: vertical; padding: 12px 14px; border-radius: 12px; border: 1px solid var(--line-strong);
  background: var(--night); color: var(--frost); font: inherit; font-size: 16px; line-height: 1.5; }
.composer textarea:focus { outline: 2px solid rgba(255,181,71,.6); outline-offset: 1px; }
.btn:disabled { opacity: .5; cursor: default; }
.thinking { color: var(--muted); font-style: italic; }
.ctx-line { font-family: var(--mono); font-size: 13px; color: var(--muted); margin-top: 10px; }
.chat-widget { display: flex; flex-direction: column; min-height: 0; }
.fab { position: fixed; right: max(20px, env(safe-area-inset-right, 0px)); bottom: max(20px, env(safe-area-inset-bottom, 0px)); z-index: 40;
  display: inline-flex; align-items: center; gap: 10px; min-height: 48px; padding: 0 20px; border-radius: 999px; cursor: pointer;
  border: 1px solid rgba(255,181,71,.65); background: var(--console); color: var(--frost); font-weight: 600; font-size: 16px;
  box-shadow: 0 0 24px rgba(255,181,71,.22), 0 12px 30px rgba(0,0,0,.5); }
.fab .dot { width: 9px; height: 9px; }
.fab[hidden], .drawer[hidden] { display: none; }
.drawer { position: fixed; top: 0; right: 0; bottom: 0; width: min(480px, 100vw); z-index: 50; display: flex; flex-direction: column; gap: 12px;
  padding: 16px 18px max(16px, env(safe-area-inset-bottom, 0px)); background: var(--console); border-left: 1px solid var(--line-strong);
  box-shadow: -20px 0 60px rgba(0,0,0,.55); transform: translateX(100%); transition: transform .2s ease-out; }
.drawer.open { transform: none; }
.drawer-head { display: flex; align-items: center; gap: 10px; padding-bottom: 12px; border-bottom: 1px solid var(--line); }
.drawer-head > div:first-child { flex: 1; }
.drawer-body { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.drawer .chat-widget { flex: 1; }
.drawer .chat-log { flex: 1; max-height: none; min-height: 0; }
.drawer .msg { max-width: 100%; }
@media (prefers-reduced-motion: reduce) { .drawer { transition: none; } }
/* the page reflows to the width left by the side panel */
@container wrap (max-width: 1080px) {
  .main, .main.c65, .main.c30 { grid-template-columns: minmax(0, 1fr); }
  .grid4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .hide-sm { display: none; }
}
.chat-widget .chip { text-align: left; }
.chain { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; align-items: stretch; }
.chain-step { display: block; padding: 12px 14px; border: 1px solid var(--line); border-radius: 12px; background: rgba(11,15,20,.35); text-decoration: none; color: inherit; min-width: 0; }
.chain-step:hover { border-color: rgba(255,181,71,.5); }
@container wrap (max-width: 1080px) { .chain { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 700px) { .chain { grid-template-columns: minmax(0, 1fr); } }
@media (min-width: 1100px) { body.drawer-open .wrap { padding-right: calc(min(480px, 100vw) + 24px); max-width: none; } }
@media (max-width: 700px) { .drawer-head .ask-state { display: none; } }
h1.ttl { font-family: var(--display); font-weight: 700; font-size: clamp(30px, 3vw, 40px); letter-spacing: -0.02em; margin: 6px 0 16px 0; text-wrap: balance; }
h2.ttl { font-family: var(--display); font-weight: 700; font-size: 28px; letter-spacing: -0.02em; margin: 20px 0 6px 0; }
svg text { font-family: var(--mono); }
</style>

<div class="wrap">
  <header class="topbar">
    <a class="brand" href="#stress" id="brand"></a>
    <nav class="tabs" id="tabs" aria-label="Pages"></nav>
    <div class="status"><span class="dot"></span><span id="status"></span></div>
  </header>
  <main id="view"></main>
  <p class="source" style="margin-top:28px">Research output, not investment advice. Web edition of the HarvestRadar app, built from the same data as the app.</p>
</div>
<script type="application/json" id="data">__DATA__</script>
<script>const BASE_IMG = "__BASE_IMG__";</script>
<script>/*__RADAR_JS__*/</script>
<script>/*__APP_JS__*/</script>
```

## 69. `scripts/build_map_base.py`

```python
"""Project the graded Blue Marble (equirectangular) to Equal Earth, once, offline. Output is committed.

Writes static/img/equal_earth_radar_night.webp (transparent outside the globe outline) and a JSON file
with the extent in projected kilometres, so that SVG layers can be drawn in the same coordinates.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "src" / "harvestradar" / "app" / "static" / "img"
SRC = IMG / "blue_marble_radar_night.jpg"
EQ = "+proj=eqearth +lon_0=0 +datum=WGS84 +units=m +no_defs"
LAT_MIN, LAT_MAX = -58.0, 84.0
WIDTH = 3600


def main() -> None:
    fwd = Transformer.from_crs("EPSG:4326", EQ, always_xy=True)
    inv = Transformer.from_crs(EQ, "EPSG:4326", always_xy=True)
    xmax, _ = fwd.transform(180.0, 0.0)
    _, ytop = fwd.transform(0.0, LAT_MAX)
    _, ybot = fwd.transform(0.0, LAT_MIN)
    height = int(round(WIDTH * (ytop - ybot) / (2 * xmax)))
    xs = np.linspace(-xmax, xmax, WIDTH)
    ys = np.linspace(ytop, ybot, height)
    X, Y = np.meshgrid(xs, ys)
    lon, lat = inv.transform(X.ravel(), Y.ravel())
    lon, lat = np.asarray(lon), np.asarray(lat)
    # inside the globe outline: re-project and compare (pyproj extrapolates outside)
    bx, by = fwd.transform(np.clip(lon, -180, 180), np.clip(lat, -90, 90))
    inside = np.isfinite(lon) & np.isfinite(lat) & (np.abs(lon) <= 180) & \
        (np.hypot(np.asarray(bx) - X.ravel(), np.asarray(by) - Y.ravel()) < 2000)
    src = np.asarray(Image.open(SRC).convert("RGB"))
    h, w, _ = src.shape
    col = np.clip(((lon + 180) / 360 * w).astype(int), 0, w - 1)
    row = np.clip(((90 - lat) / 180 * h).astype(int), 0, h - 1)
    rgb = src[np.where(inside, row, 0), np.where(inside, col, 0)]
    alpha = np.where(inside, 255, 0).astype(np.uint8)
    out = np.concatenate([rgb.reshape(height, WIDTH, 3), alpha.reshape(height, WIDTH, 1)], axis=2)
    Image.fromarray(out, "RGBA").save(IMG / "equal_earth_radar_night.webp", quality=82, method=6)
    meta = {"projection": EQ, "x_min_km": -xmax / 1000, "x_max_km": xmax / 1000, "y_top_km": ytop / 1000,
            "y_bottom_km": ybot / 1000, "lat_min": LAT_MIN, "lat_max": LAT_MAX, "width_px": WIDTH,
            "height_px": height, "source": "NASA Blue Marble Next Generation (public domain), graded"}
    (IMG / "equal_earth_radar_night.json").write_text(json.dumps(meta, indent=2))
    print(meta)


if __name__ == "__main__":
    main()
```

## 70. `scripts/build_web.py`

```python
"""Build the static web version of the app (one self-contained HTML file) from data/demo.

The Streamlit app needs a Python server; this page runs in any browser, for example as a claude.ai
Artifact. Same data, same map code (static/js/radar_map.js), same design tokens.
Usage: python scripts/build_web.py  ->  dist/web/index.html
"""

from __future__ import annotations

import base64
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "web"


def r(x, n=3):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), n)


def fair_block(data, key: str, today: pd.Timestamp) -> dict | None:
    """Price vs climate fair value: daily for the last 2 years, weekly (Friday) since 2006, plus the
    scenario parameters the pricing tool needs."""
    fv = data.fair_value(key)
    if fv.empty:
        return None
    pi = data.jsonfile("price_impact.json")
    fx, sm = pi["commodities"].get(key), pi.get("fair_value", {}).get(key)
    if fx is None or sm is None:
        return None
    d2 = fv[fv.date >= today - pd.Timedelta(days=740)]
    wk = fv.set_index("date").resample("W-FRI").last().dropna(subset=["fair"]).reset_index()
    cols = ("close", "anchor", "fair", "fair_lo", "fair_hi")
    ser = lambda f: {"d": f.date.dt.strftime("%Y-%m-%d").tolist(), **{c: [r(x, 2) for x in f[c]] for c in cols}}  # noqa: E731
    lr = data.risk_daily()
    lr = lr[lr.commodity == key].dropna(subset=["risk_z"]).iloc[-1]
    return {"recent": ser(d2), "long": ser(wk), "now": sm,
            "flex": {k: fx[k] for k in ("slope_pct_per_pct", "se", "p_value", "r2", "n", "years", "points",
                                         "marketing_year_start_month")},
            "mu": r(lr.mu_pct, 3), "sigma": r(lr.sigma_pct, 3),
            "comove": pi.get("comovement", {}).get(key)}


def main() -> None:
    import logging

    logging.getLogger("streamlit").setLevel(logging.ERROR)
    from harvestradar.app import components as C
    from harvestradar.app import data, maps
    from harvestradar.app.views import replay as RP
    from harvestradar.app.views import stress_map as SM
    from harvestradar.app.views.commodity import SHAP_LABELS
    from harvestradar.report.email_note import render_note_email

    meta = data.meta()
    today = data.today()
    out: dict = {"asOf": today.strftime("%Y-%m-%d"), "weekLabel": f"{today.day} {today:%b %Y}".upper(),
                 "priceImpact": data.jsonfile("price_impact.json"),
                 "meta": {"cells": meta["cells"], "climBase": meta["climatology_base"], "llm": meta["llm"]},
                 "crops": {}, "glyphs": {k: C._svg(f"glyph_{k}") for k in ("maize", "arabica", "cocoa")},
                 "marks": {"small": C.mark(30), "signal": C.mark_on_signal(40)}}
    out["map"] = {"viewBox": maps.world_viewbox(), "base": maps.base_layer()}
    for key, c in meta["commodities"].items():
        rs = data.risk_series(key)
        rs = rs[rs.date >= "2001-01-01"]
        rd = data.risk_daily()
        rd = rd[(rd.commodity == key) & (rd.date >= today - pd.Timedelta(weeks=66))].dropna(subset=["risk_z"])
        latest = data.latest_risk(key)
        px = data.prices(key)
        wk = px.set_index("date")["close"].resample("W-FRI").last().dropna()
        d_recent = px[px.date >= today - pd.Timedelta(weeks=66)]
        start = today - pd.Timedelta(weeks=64)
        spans = data.window_spans(key, c["main_country"], start, today)
        sh = data.shap_latest()
        sh = sh[sh.commodity == key]
        shap = {}
        for row in sh.itertuples():
            cols = [k for k in sh.columns if k.startswith("shap_") and k not in ("shap_base", "shap_commodity_code")]
            vals = pd.Series({k: getattr(row, k) for k in cols}).astype(float)
            top = vals.reindex(vals.abs().sort_values(ascending=False).index).head(4)
            shap[row.country_iso3] = {"season": int(row.season), "rows": [[SHAP_LABELS.get(k, k), r(v, 2)] for k, v in top.items()]}
        regs, borders, _ = SM.world_layers(key)
        frames = SM.frames_for(key, today.year)
        dk = data.stress(key).dekad_end.max()
        top5 = data.top_regions(key, dk, 5)
        best = float(top5["score"].max()) if len(top5) and top5["score"].max() > 0 else 1.0
        out["crops"][key] = {
            "label": c["label"], "display": c["display"], "glyph": c["glyph"], "priceLabel": c["price_label"],
            "priceName": c["price_name"], "priceUnit": c["price_unit"], "ticker": c["ticker"],
            "mainCountry": c["main_country_name"], "regionsN": c["regions"], "coverage": c["coverage"],
            "above2": c["weeks_above_2_pct"], "target": c["target"],
            "risk": {"d": rs.date.dt.strftime("%Y-%m-%d").tolist(), "z": [r(x) for x in rs.risk_z],
                     "dp": [r(x) for x in rs.delta_prod_pct]},
            "latest": {"z": r(latest["risk_z"]), "dp": r(latest["delta_prod_pct"], 2),
                       "lo": r(latest["delta_prod_lo_pct"], 2), "hi": r(latest["delta_prod_hi_pct"], 2),
                       "date": latest["date"].strftime("%Y-%m-%d"), "contributors": latest["contributors"]},
            "riskRecent": {"d": rd.date.dt.strftime("%Y-%m-%d").tolist(), "z": [r(x) for x in rd.risk_z]},
            "pricesWeekly": {"d": [d.strftime("%Y-%m-%d") for d in wk.index], "c": [r(x, 2) for x in wk]},
            "pricesRecent": {"d": d_recent.date.dt.strftime("%Y-%m-%d").tolist(), "c": [r(x, 2) for x in d_recent.close]},
            "lastPrice": {"date": px.date.iloc[-1].strftime("%Y-%m-%d"), "close": r(px.close.iloc[-1], 2)},
            "windows": [[s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d"), st] for s, e, st in spans],
            "shap": shap,
            "fair": fair_block(data, key, today),
            "map": {"regions": regs, "borders": borders, "frames": frames,
                    "start": len(frames) - 1, "dekad": dk.strftime("%Y-%m-%d"),
                    "top5": [{"rank": i + 1, "name": t.adm1_name, "iso": t.country_name,
                              "frac": max(0.0, float(t.score) / best), "hot": bool(i == 0 and t.stress >= 2)}
                             for i, t in enumerate(top5.itertuples())]},
        }
    o = data.oni_latest(today)
    o["strength"] = data.oni_strength(o["value"])
    o["period"] = o["label"].replace("-", " to ").title().replace(" To ", " to ")
    out["oni"] = o
    # episodes
    events = data.jsonfile("events.json")
    eps = {}
    for name, ev in events.items():
        key = ev["commodity"]
        focus = {"maize": "USA", "coffee": "BRA", "cocoa": "CIV"}[key]
        regs, vb, _, _ = RP.episode_layers(key, focus)
        frames = RP.episode_frames(key, focus, ev["start"], ev["end"])
        dates = [pd.Timestamp(f["date"]) for f in frames]
        se = pd.Timestamp(ev["show_end"])
        last_i = max(i for i, d in enumerate(dates) if d <= se)
        strip = sorted(set(int(round(x)) for x in np.linspace(max(0, last_i - 5), last_i, 6)))
        eps[name] = {**{k: v for k, v in ev.items() if k != "lag_correlation"}, "viewBox": vb, "regions": regs,
                     "frames": frames, "strip": strip,
                     "range": f"{dates[0]:%b %Y} · {dates[-1]:%b %Y}".upper()}
    out["episodes"] = eps
    # notes
    n = data.notes()
    notes = []
    order = {"maize": 0, "coffee": 1, "cocoa": 2}
    n = n.assign(o=n.commodity.map(order)).sort_values(["week", "o"], ascending=[False, True]).drop(columns="o")
    for row in n.to_dict("records"):
        p = json.loads(row["payload"])
        logo = base64.b64encode((ROOT / "src/harvestradar/app/static/brand/mark_on_signal_96.png").read_bytes()).decode()
        email = render_note_email(row, logo_src="data:image/png;base64," + logo)
        notes.append({"commodity": row["commodity"], "week": pd.Timestamp(row["week"]).strftime("%Y-%m-%d"),
                      "title": row["title"], "template": row["template"], "slots": p["slots"],
                      "readings": p.get("readings", {}), "checks": [bool(row["numbers_ok"]), bool(row["context_ok"]),
                                                                    bool(row["claims_ok"])],
                      "model": row["model"], "templateParagraphs": int(row.get("template_paragraphs", 0) or 0),
                      "seconds": r(row["seconds"], 0), "attempts": int(row["attempts"]), "email": email})
    out["notes"] = notes
    # method
    ev = data.jsonfile("model_eval.json")
    bt = data.jsonfile("backtest.json")
    st = data.stress("maize")
    top = data.regions("maize").sort_values("weight", ascending=False).iloc[0]
    x = st[(st.region_id == top.region_id) & (st.dekad_end >= "2012-05-01") & (st.dekad_end <= "2012-08-31")]
    out["method"] = {
        "eval": {"pooled": ev["pooled"].get("end", {}), "test": ev["test_seasons"],
                 "byCrop": {k: v.get("end", {}) for k, v in ev["by_commodity"].items()}},
        "events": {k: {kk: v.get(kk) for kk in ("label", "verdict", "first_above_2", "peak_risk_z", "peak_date",
                                                 "price_max_date")} for k, v in events.items()},
        "backtest": {k: bt.get(k) for k in ("best_rule_p", "best_rule_p_corrected", "best_p_overall",
                                            "best_p_overall_corrected")},
        "strip": {"name": top.adm1_name, "values": [r(v, 2) for v in x.stress]},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    tpl = (ROOT / "web" / "template.html").read_text()
    js = (ROOT / "src/harvestradar/app/static/js/radar_map.js").read_text()
    img = base64.b64encode((ROOT / "src/harvestradar/app/static/img/equal_earth_radar_night.webp").read_bytes()).decode()
    payload = json.dumps(out, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    html = (tpl.replace("/*__RADAR_JS__*/", js).replace("__BASE_IMG__", "data:image/webp;base64," + img)
            .replace("/*__APP_JS__*/", (ROOT / "web" / "app.js").read_text())
            .replace("__DATA__", payload))
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(f"written {OUT / 'index.html'} ({len(html) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
```

## 71. `scripts/capture.py`

```python
"""Capture every page in an exact state at 1920 x 1080 (device scale factor 2 by default).

Usage: python scripts/capture.py [--url http://localhost:8501] [--out captures] [--scale 2]
Starts the app itself if nothing answers on --url. Uses ?capture=1 (animations frozen, hovers off).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOTS = {
    "01_stress_map": "page=stress&crop=maize",
    "02_commodity": "page=commodity&crop=maize",
    "03_replay_2012": "page=replay&episode=us_drought_2012",
    "04_weekly_note": "page=note&crop=maize",
    "05_method": "page=method",
    "06_stress_map_cocoa": "page=stress&crop=cocoa",
    "07_replay_frost_2021": "page=replay&episode=brazil_frost_2021",
    "08_replay_cocoa": "page=replay&episode=cocoa_2023_2024",
    "09_fair_value": "page=fair&crop=maize",
}


def chromium_path() -> str | None:
    for p in sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux*/chrome")):
        return str(p)
    return os.environ.get("CHROMIUM_PATH")


def wait_up(url: str, timeout: float = 60) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            urllib.request.urlopen(url + "/_stcore/health", timeout=2)
            return True
        except Exception:  # noqa: BLE001
            time.sleep(0.5)
    return False


def start_app(port: int) -> subprocess.Popen:
    return subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(ROOT / "src/harvestradar/app/streamlit_app.py"),
                             "--server.port", str(port), "--server.headless", "true"], cwd=ROOT,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> None:
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8501")
    ap.add_argument("--out", default=str(ROOT / "captures"))
    ap.add_argument("--scale", type=float, default=2)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--wait", type=float, default=4.0)
    a = ap.parse_args()
    proc = None
    if not wait_up(a.url, 2):
        proc = start_app(int(a.url.rsplit(":", 1)[-1]))
        if not wait_up(a.url):
            sys.exit("app did not start")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path=chromium_path())
            ctx = b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=a.scale)
            page = ctx.new_page()
            for name, q in SHOTS.items():
                if a.only and name not in a.only:
                    continue
                page.goto(f"{a.url}/?{q}&capture=1", wait_until="networkidle")
                page.wait_for_timeout(int(a.wait * 1000))
                page.screenshot(path=str(out / f"{name}.png"))
                print("captured", out / f"{name}.png")
            b.close()
    finally:
        if proc:
            proc.terminate()


if __name__ == "__main__":
    main()
```

## 72. `scripts/code_listing.py`

````python
"""Print the whole source code of HarvestRadar into one PDF (cover, contents, every file with line numbers).

Usage: python scripts/code_listing.py  ->  dist/doc/HarvestRadar_source_code.pdf and .md (same files, plain text)
Files: every tracked source and configuration file (Python, JavaScript, HTML, YAML, TOML, prompts, lock files);
data, images, fonts and documentation are left out (they are in the repository).
"""

from __future__ import annotations

import datetime as dt
import html
import subprocess
from pathlib import Path

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_for_filename, TextLexer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "doc" / "HarvestRadar_source_code.pdf"
MD = OUT.with_suffix(".md")
FENCE = {".py": "python", ".js": "javascript", ".html": "html", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml", ".md": "markdown"}
KEEP = (".py", ".js", ".html", ".yaml", ".yml", ".toml", ".lock", ".cfg")
EXTRA = {"Makefile", ".gitignore"}
ORDER = ["pyproject.toml", "Makefile", "requirements.lock", "requirements-llm.lock", ".gitignore", ".streamlit/",
         "config/", ".github/", "src/harvestradar/", "web/", "scripts/", "tests/"]


def files() -> list[str]:
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    keep = [f for f in tracked if (f.endswith(KEEP) or Path(f).name in EXTRA or f.startswith("src/harvestradar/report/prompts/"))
            and not f.startswith(("data/", "docs/", "reports/"))]

    def rank(f: str) -> tuple[int, str]:
        return next((i for i, p in enumerate(ORDER) if f == p or f.startswith(p)), len(ORDER)), f
    return sorted(keep, key=rank)


def lexer(name: str):
    try:
        return get_lexer_for_filename(name if not name.endswith(".lock") else "x.txt")
    except Exception:  # noqa: BLE001
        return TextLexer()


def main() -> None:
    from playwright.sync_api import sync_playwright

    fs = files()
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    fmt = HtmlFormatter(style="friendly", linenos="inline", nowrap=False)
    parts, toc, total = [], [], 0
    for i, f in enumerate(fs, 1):
        text = (ROOT / f).read_text(encoding="utf-8", errors="replace")
        n = text.count("\n") + (0 if text.endswith("\n") else 1)
        total += n
        toc.append(f'<tr><td>{i}</td><td><a href="#f{i}">{html.escape(f)}</a></td><td class="r">{n:,}</td></tr>')
        parts.append(f'<section class="file" id="f{i}"><h2>{i}. {html.escape(f)} <span>{n:,} lines</span></h2>'
                     f'{highlight(text, lexer(f), fmt)}</section>')
    today = dt.date.today()
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>HarvestRadar source code</title><style>
{fmt.get_style_defs('.highlight')}
body {{ font-family: Helvetica, Arial, sans-serif; color: #111; }}
.cover {{ height: 240mm; display: flex; flex-direction: column; justify-content: center; }}
.cover h1 {{ font-size: 34pt; margin: 0 0 8mm; }} .cover p {{ font-size: 12pt; line-height: 1.6; margin: 0; }}
h2 {{ font-size: 11pt; background: #f1f3f5; padding: 2mm 3mm; border-left: 3px solid #f5a93a; margin: 0 0 2mm; }}
h2 span {{ font-weight: 400; color: #666; float: right; }}
table.toc {{ border-collapse: collapse; width: 100%; font-size: 9.5pt; }} table.toc td {{ padding: 1.2mm 2mm; border-bottom: 1px solid #e5e5e5; }}
td.r {{ text-align: right; }} a {{ color: #111; text-decoration: none; }}
section.file {{ break-before: page; }}
.highlight pre {{ font-family: Menlo, Consolas, 'DejaVu Sans Mono', monospace; font-size: 7.6pt; line-height: 1.35;
  white-space: pre-wrap; word-break: break-all; margin: 0; }}
.highlight .linenos {{ color: #999; }}
</style></head><body>
<div class="cover"><h1>HarvestRadar<br>source code</h1>
<p>Complete source of the HarvestRadar app and pipeline: {len(fs)} files, {total:,} lines.</p>
<p>Commit {commit} of github.com/whiterockk/harvestradar, printed {today.day} {today:%B %Y}.</p>
<p>Data, images, fonts and documentation are in the repository and are not printed here.</p></div>
<section style="break-before: page"><h2>Contents</h2><table class="toc"><tr><td></td><td><b>File</b></td><td class="r"><b>Lines</b></td></tr>{''.join(toc)}</table></section>
{''.join(parts)}</body></html>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".html")
    tmp.write_text(doc, encoding="utf-8")
    with sync_playwright() as p:
        exe = next(iter(sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux*/chrome"))), None)
        b = p.chromium.launch(executable_path=str(exe) if exe else None)
        page = b.new_page()
        page.goto(tmp.as_uri(), wait_until="load")
        page.pdf(path=str(OUT), format="A4", print_background=True, display_header_footer=True,
                 margin={"top": "14mm", "bottom": "16mm", "left": "12mm", "right": "12mm"},
                 header_template="<span></span>",
                 footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#888">HarvestRadar source code'
                                 ' · page <span class="pageNumber"></span> of <span class="totalPages"></span></div>')
        b.close()
    tmp.unlink()
    # the same code as one Markdown file: a contents list, then each file in a fenced block
    md = [f"# HarvestRadar source code\n\nCommit {commit} of https://github.com/whiterockk/harvestradar, {len(fs)} files, "
          f"{total:,} lines, printed {today.day} {today:%B %Y}. To rebuild the project, copy each block into the file "
          "named in its heading (or download the repository as a zip from GitHub).\n\n## Contents\n"]
    md += [f"{i}. `{f}`" for i, f in enumerate(fs, 1)]
    for i, f in enumerate(fs, 1):
        text = (ROOT / f).read_text(encoding="utf-8", errors="replace")
        fence = "````" if "```" in text else "```"
        md.append(f"\n## {i}. `{f}`\n\n{fence}{FENCE.get(Path(f).suffix, '')}\n{text.rstrip()}\n{fence}")
    MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"written {OUT} ({OUT.stat().st_size / 1e6:.1f} MB) and {MD} ({MD.stat().st_size / 1e6:.1f} MB): "
          f"{len(fs)} files, {total:,} lines")


if __name__ == "__main__":
    main()
````

## 73. `scripts/grade_blue_marble.py`

```python
"""Grade NASA Blue Marble once, offline, for the Radar Night map base. Output is committed.

Source: NASA Visible Earth "Blue Marble Next Generation" (public domain), as shipped in the
three-globe npm package (example/img/earth-blue-marble.jpg, 4096 x 2048, equirectangular).

Grade: desaturate to about 45 %, brightness about 0.5, cool tint (R x0.86, G x0.95, B x1.08),
compress highlights above 0.30 so ice and deserts never outshine the data.
Also writes a darker variant for the episode replay (zoomed views).
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC_URL = "https://cdn.jsdelivr.net/npm/three-globe@2.31.0/example/img/earth-blue-marble.jpg"
SRC = ROOT / "data" / "raw" / "img" / "earth-blue-marble.jpg"
OUT = ROOT / "src" / "harvestradar" / "app" / "static" / "img"


def grade(rgb: np.ndarray, saturation: float = 0.45, brightness: float = 0.5,
          knee: float = 0.30, slope: float = 0.35) -> np.ndarray:
    x = rgb.astype(np.float32) / 255.0
    lum = (0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2])[..., None]
    x = lum + (x - lum) * saturation
    x = x * brightness
    x = x * np.array([0.86, 0.95, 1.08], dtype=np.float32)
    x = np.where(x > knee, knee + (x - knee) * slope, x)
    return (np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8)


def main() -> None:
    if not SRC.exists():
        SRC.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(SRC_URL, SRC)
    im = np.asarray(Image.open(SRC).convert("RGB"))
    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray(grade(im)).save(OUT / "blue_marble_radar_night.jpg", quality=86, optimize=True,
                                    progressive=True)
    Image.fromarray(grade(im, brightness=0.42)).resize((2048, 1024), Image.LANCZOS).save(
        OUT / "blue_marble_radar_night_2k.jpg", quality=84, optimize=True)
    print("written", sorted(p.name for p in OUT.glob("blue_marble*")), file=sys.stderr)


if __name__ == "__main__":
    main()
```

## 74. `scripts/offline_check.py`

```python
"""Offline check: start the app, open every page (and play the map), record every network request,
fail if any request leaves localhost. Fonts, images, map, Plotly and scripts must all be local.

Usage: python scripts/offline_check.py [--url http://localhost:8502]
"""

from __future__ import annotations

import argparse
import sys
from urllib.parse import urlparse

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from capture import SHOTS, chromium_path, start_app, wait_up  # noqa: E402

LOCAL = {"localhost", "127.0.0.1", "0.0.0.0", "::1", ""}


def main() -> None:
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8502")
    a = ap.parse_args()
    proc = None
    if not wait_up(a.url, 2):
        proc = start_app(int(a.url.rsplit(":", 1)[-1]))
        if not wait_up(a.url):
            sys.exit("app did not start")
    external, total, fonts = [], 0, set()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path=chromium_path())
            ctx = b.new_context(viewport={"width": 1920, "height": 1080})

            def on_request(req):
                nonlocal total
                total += 1
                u = urlparse(req.url)
                if u.scheme in ("data", "blob", "about", "chrome-extension"):
                    return
                if u.hostname not in LOCAL:
                    external.append(req.url)
                if req.url.endswith(".woff2"):
                    fonts.add(req.url.rsplit("/", 1)[-1])

            ctx.on("request", on_request)
            page = ctx.new_page()
            for name, q in SHOTS.items():
                page.goto(f"{a.url}/?{q}", wait_until="networkidle")
                page.wait_for_timeout(2500)
                for fr in page.frames:  # press play in the map iframes
                    btn = fr.query_selector("button.play")
                    if btn:
                        btn.click()
                page.wait_for_timeout(1500)
                print(f"checked {name}")
            b.close()
    finally:
        if proc:
            proc.terminate()
    print(f"{total} requests, {len(external)} external, fonts loaded: {sorted(fonts)}")
    if external:
        for u in sorted(set(external)):
            print("EXTERNAL:", u)
        sys.exit(1)
    print("OFFLINE CHECK PASSED: 0 external requests")


if __name__ == "__main__":
    main()
```

## 75. `scripts/storyboard_facts.py`

```python
"""Write docs/storyboard_facts.md: the real value, from data/demo, behind every fact tag of the storyboard.
The storyboard's own numbers are illustrative; the video must use these."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "data" / "demo"


def main() -> None:
    meta = json.loads((DEMO / "meta.json").read_text())
    ev = json.loads((DEMO / "events.json").read_text())
    me = json.loads((DEMO / "model_eval.json").read_text())
    bt = json.loads((DEMO / "backtest.json").read_text())
    risk = pd.read_parquet(DEMO / "risk_index.parquet")
    risk["date"] = pd.to_datetime(risk["date"])
    today = risk.date.max()
    last = {r.commodity: r for r in risk[risk.date == today].itertuples()}
    oni = pd.read_parquet(DEMO / "oni.parquet")
    o = oni[pd.to_datetime(oni.available_at) <= today].iloc[-1]
    notes = pd.read_parquet(DEMO / "notes.parquet")
    notes["week"] = pd.to_datetime(notes["week"])
    nm = notes[(notes.week == notes.week.max())]
    e12, e21, ecc = ev["us_drought_2012"], ev["brazil_frost_2021"], ev["cocoa_2023_2024"]
    pooled = me["pooled"].get("end", {})
    cm = meta["commodities"]
    maize_contrib = json.loads(last["maize"].contributors)
    pr_c = pd.read_parquet(DEMO / "prices_cocoa.parquet")
    pr_c["date"] = pd.to_datetime(pr_c["date"])

    def close_on(df, d):
        x = df[df.date <= pd.Timestamp(d)].iloc[-1]
        return x.date.strftime("%Y-%m-%d"), float(x.close)

    c0 = close_on(pr_c, "2023-07-03")
    c1 = close_on(pr_c, "2024-12-31")
    rows = [
        ("F1", "2012 price window and peak", f"CBOT corn {e12['price_from']} on {e12['price_from_date']} "
         f"({e12['price_from_kind']}) to {e12['price_to']} on {e12['price_to_date']} ({e12['price_change_pct']:+.1f}%). "
         f"High of the episode {e12.get('price_max')} on {e12.get('price_max_date')}. Say \"by 20 July\", never \"peaked\"."),
        ("F2", "Date the 2012 index first crossed +2", f"{e12['first_above_2'] or 'never'}"
         + (f" ({e12.get('lead_text')})" if e12.get("lead_text") else "")
         + f"; peak {e12['peak_risk_z']:+.2f} on {e12['peak_date']}. The storyboard's 8 June is illustrative."),
        ("F3", "Out of sample", f"The 2012 forecasts come from a model trained on seasons up to "
         f"{e12.get('model_trained_on_seasons_up_to')} (FAOSTAT publishes year Y in December of Y+1). "
         f"Chip text: MODEL TRAINED ON SEASONS UP TO {e12.get('model_trained_on_seasons_up_to')}."),
        ("F4", "Model vs trend only", f"End of season, {me['test_seasons'][0]} to {me['test_seasons'][1]}: "
         f"{pooled.get('rmse_vs_trend_weighted_pct')}% RMSE weighted by world share, "
         f"{pooled.get('rmse_vs_trend_pct')}% with every country counted equally."),
        ("F5", "Share of weeks above +2 since 2001", ", ".join(f"{c['label']} {c['weeks_above_2_pct']}%" for c in cm.values())),
        ("F6", "Crop maps and weather points", f"{sum(c['regions'] for c in cm.values())} regions "
         f"({', '.join(str(c['regions']) + ' ' + c['label'].lower() for c in cm.values())}), each set covering 90% of "
         f"world output (MapSPAM 2020); {meta['cells']:,} NASA POWER grid points, daily since 1981."),
        ("F7", "Maize drivers this week", "; ".join(f"{c['name']} {c['contrib_pct']:+.2f} pp (crop {c['season']}, "
                                                    f"{c['pred_anom_pct']:+.1f}% vs trend)" for c in maize_contrib)),
        ("F8", "Readings today", f"week of {today:%d %b %Y}: " + ", ".join(
            f"{cm[k]['label']} {last[k].risk_z:+.2f} (supply {last[k].delta_prod_pct:+.1f}%)" for k in cm)),
        ("F9", "El Nino wording", f"ONI {o.label}: {o.oni:+.2f} (NOAA CPC, published {pd.Timestamp(o.available_at):%d %b %Y}). "
         "Context only: call it \"Climate driver\" or \"Context\", never \"driving the index\"."),
        ("F10", "Dekad of the stress map", f"latest complete dekad: {cm['maize']['latest_dekad_end']}"),
        ("F11", "Cocoa price definition", f"ICE cocoa front-month continuous (yfinance CC=F), US$ per tonne: "
         f"{c0[1]:,.0f} on {c0[0]} to {c1[1]:,.0f} on {c1[0]} (x{c1[1] / c0[1]:.2f})."),
        ("F12", "Brazil frost 2021", f"{e21['verdict'].upper()}: peak {e21['peak_risk_z']:+.2f} on {e21['peak_date']}"),
        ("F13", "Cocoa 2023-2024", f"{ecc['verdict'].upper()}: peak {ecc['peak_risk_z']:+.2f} on {ecc['peak_date']}"),
        ("F14", "2012", f"{e12['verdict'].upper()}"),
        ("F15", "Trading rule after costs", f"pre-registered rule: best p {bt['best_rule_p']:.2f} "
         f"({bt['best_rule_p_corrected']:.2f} after Bonferroni for 3 crops); best of the 3 x 3 grid "
         f"{bt['best_p_overall']:.3f} ({bt['best_p_overall_corrected']:.2f} corrected for 27 tests): no significant edge"),
        ("F16", "Critical windows (config)", "; ".join(
            f"{c['label']} {c['main_country_name']}: " + ", ".join(f"{w['stage']} {w['start']} to {w['end']}"
                                                                 for w in c['windows'][c['main_country']])
            for c in cm.values())),
        ("F17", "What it means for the price", "; ".join(
            f"{cm[k]['label']}: " + (f"{v['implied_pct']:+.1f}% expected (range {v['low_pct']:+.1f}% to {v['high_pct']:+.1f}%), "
                                    f"{-v['slope_pct_per_pct']:+.1f}% price per 1% of world supply missing, {v['years'][0]}-{v['years'][1]}"
                                    if v["reliable"] else "no reliable link, no estimate")
            for k, v in json.loads((DEMO / "price_impact.json").read_text())["commodities"].items())),
        ("F18", "Daily note labels", "; ".join(f"{r.commodity}: \"{r.title}\" ({r.model}, "
                                               f"{int(r.template_paragraphs)} of 3 paragraphs from the template, "
                                               f"checks {int(r.numbers_ok) + int(r.context_ok) + int(r.claims_ok)}/3)"
                                               for r in nm.itertuples())),
    ]
    out = ["# Storyboard facts, from the data", "",
           f"Generated by `scripts/storyboard_facts.py` from `data/demo` (as of {today:%d %b %Y}). The storyboard v3 "
           "numbers are illustrative; use these in the video.", "", "| Tag | Fact | Value from the data |", "|---|---|---|"]
    out += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    (ROOT / "docs" / "storyboard_facts.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
```

## 76. `tests/conftest.py`

```python
import json

import pandas as pd
import pytest

from harvestradar.config import load_config


@pytest.fixture(scope="session")
def cfg():
    return load_config()


@pytest.fixture()
def payload():
    """A small, self-consistent note payload (synthetic test data)."""
    slots = {
        "RISK": {"kind": "figure", "text": "+2.10", "value": 2.1, "label": "MAIZE harvest-risk index",
                 "source": "risk_index.parquet", "date": "2026-11-13", "detail": ""},
        "RISK_CHANGE": {"kind": "figure", "text": "+0.40", "value": 0.4, "label": "Change", "source": "risk_index.parquet",
                        "date": "2026-11-13", "detail": ""},
        "SUPPLY": {"kind": "figure", "text": "-1.8%", "value": -1.8, "label": "Supply", "source": "model predictions",
                   "date": "2026-11-13", "detail": ""},
        "PRICE": {"kind": "figure", "text": "445.50", "value": 445.5, "label": "CBOT corn close",
                  "source": "prices_maize.parquet", "date": "2026-11-13", "detail": ""},
        "PRICE_CHANGE": {"kind": "figure", "text": "+3.2%", "value": 3.2, "label": "Price change",
                         "source": "prices_maize.parquet", "date": "2026-11-13", "detail": ""},
        "ONI": {"kind": "figure", "text": "+2.46", "value": 2.46, "label": "El Nino", "source": "oni.parquet",
                "date": "2026-11-10", "detail": ""},
        "ONI_PERIOD": {"kind": "label", "text": "ONI AUG-OCT 2026", "label": "ONI season", "source": "oni.parquet",
                       "date": "2026-11-10", "detail": ""},
        "DRIVER1": {"kind": "name", "text": "United States", "label": "c1", "source": "risk_index.parquet",
                    "date": "2026-11-13", "detail": "USA"},
        "DRIVER1_CONTRIB": {"kind": "figure", "text": "-1.20 pp", "value": -1.2, "label": "US", "source": "risk_index.parquet",
                            "date": "2026-11-13", "detail": ""},
        "DRIVER2": {"kind": "name", "text": "China", "label": "c2", "source": "risk_index.parquet",
                    "date": "2026-11-13", "detail": "CHN"},
        "DRIVER2_CONTRIB": {"kind": "figure", "text": "-0.60 pp", "value": -0.6, "label": "CN", "source": "risk_index.parquet",
                            "date": "2026-11-13", "detail": ""},
        "REGION1": {"kind": "name", "text": "Iowa", "label": "r1", "source": "stress_maize.parquet",
                    "date": "2026-11-10", "detail": "USA"},
        "REGION1_STRESS": {"kind": "figure", "text": "+1.9", "value": 1.9, "label": "Iowa stress",
                           "source": "stress_maize.parquet", "date": "2026-11-10", "detail": ""},
    }
    facts = {"risk_z": 2.1, "risk_change_4w": 0.4, "delta_prod_pct": -1.8, "price_change_4w_pct": 3.2, "oni": 2.46,
             "level": "elevated", "windows_open": [], "oni_label": "ONI AUG-OCT 2026",
             "drivers": [{"slot": "DRIVER1", "effect": "lowers supply", "window_open": False},
                         {"slot": "DRIVER2", "effect": "lowers supply", "window_open": False}],
             "region_causes": {"REGION1": "dry soils"}}
    return {"commodity": "maize", "label": "Maize", "display": "MAIZE", "week": "2026-11-13", "slots": slots,
            "facts": facts, "allowed_names": ["United States", "China", "Brazil"], "all_region_names": ["Iowa", "Illinois"],
            "title": "Maize risk elevated: +2.10",
            "readings": {"maize": {"display": "MAIZE", "glyph": "maize", "text": "+2.10", "value": 2.1,
                                   "source": "risk_index.parquet", "date": "2026-11-13"},
                         "coffee": {"display": "ARABICA", "glyph": "arabica", "text": "+0.95", "value": 0.95,
                                    "source": "risk_index.parquet", "date": "2026-11-13"}}}


@pytest.fixture()
def note_row(payload):
    template = ("Maize harvest risk is elevated this week. The index stands at {RISK}, up {RISK_CHANGE} from four "
                "weeks ago. Expected world supply is {SUPPLY} against trend.\n\n"
                "The largest contributions come from {DRIVER1} ({DRIVER1_CONTRIB}) and {DRIVER2} ({DRIVER2_CONTRIB}). "
                "The most stressed producing region is {REGION1} ({REGION1_STRESS}).\n\n"
                "Futures settled at {PRICE}, {PRICE_CHANGE} over four weeks. Climate context: the El Niño reading "
                "is {ONI} ({ONI_PERIOD}), shown as background only.")
    return {"commodity": "maize", "week": pd.Timestamp("2026-11-13"), "title": payload["title"], "template": template,
            "markdown": "", "numbers_ok": True, "context_ok": True, "claims_ok": True, "model": "Qwen/Qwen2.5-1.5B-Instruct",
            "payload": json.dumps(payload), "seconds": 1.0, "attempts": 1, "failures": "[]"}
```

## 77. `tests/test_cli.py`

```python
import re

from typer.testing import CliRunner

from harvestradar.cli import app

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _help(*args: str) -> str:
    """Plain help text: CI terminals get coloured, boxed output, so colour codes are removed before checking."""
    out = CliRunner().invoke(app, [*args, "--help"], env={"NO_COLOR": "1", "TERM": "dumb", "COLUMNS": "200"}).output
    return ANSI.sub("", out)


def test_cli_lists_groups():
    out = _help()
    for g in ["data", "regions", "features", "model", "index", "report", "demo", "all", "update"]:
        assert g in out


def test_report_email_help():
    assert "--week" in _help("report", "email")


def test_update_help():
    out = _help("update")
    assert "--date" in out and "--deterministic" in out  # long option names are cut at narrow widths
```

## 78. `tests/test_config_windows.py`

```python
import datetime as dt

import numpy as np
import pandas as pd

from harvestradar.features.windows import active_season, in_critical_window, season_switch, window_open_on


def test_config_validates(cfg):
    assert set(cfg.commodities) == {"maize", "coffee", "cocoa"}
    for c in cfg.commodities.values():
        assert 0 < c.coverage <= 1
        assert c.main_country in c.windows
        assert c.target in {"yield", "production"}


def test_window_crossing_year_end(cfg):
    w = cfg.commodities["cocoa"].windows["CIV"]
    dates = pd.to_datetime(["2023-12-15", "2024-01-20", "2024-02-28", "2024-03-05", "2023-06-01"])
    got = in_critical_window(dates, w, 2023)
    assert got.tolist() == [True, True, True, False, True]


def test_year_offset(cfg):
    # arabica Brazil: the flowering of September Y-1 belongs to the season (harvest) Y
    s, e = cfg.commodities["coffee"].season_span("BRA", 2022)
    assert s == dt.date(2021, 6, 1) and e == dt.date(2021, 11, 30)


def test_active_season_and_switch(cfg):
    c = cfg.commodities["maize"]
    assert active_season(c, "USA", dt.date(2026, 11, 13), 120) == 2026
    assert active_season(c, "USA", dt.date(2026, 12, 20), 120) == 2027
    assert season_switch(c, "USA", 2026, 120) == dt.date(2026, 12, 13)
    assert window_open_on(dt.date(2026, 7, 10), c.windows["USA"])
    assert not window_open_on(dt.date(2026, 11, 13), c.windows["USA"])
    _ = np
```

## 79. `tests/test_email.py`

```python
import email
import json
import re

from harvestradar.report.email_note import render_note_email, render_text, write_eml


def test_eml_parses_back_with_html_and_text(note_row, tmp_path):
    html = render_note_email(note_row)
    path = write_eml(html, note_row["title"], "2026-11-13", "maize", render_text(note_row), tmp_path)
    msg = email.message_from_bytes(path.read_bytes())
    types = [p.get_content_type() for p in msg.walk()]
    assert "text/plain" in types and "text/html" in types and "image/png" in types
    assert msg["Subject"] == note_row["title"]
    assert (tmp_path / "2026-11-13_maize.html").exists()


def test_every_figure_in_email_comes_from_payload(note_row):
    p = json.loads(note_row["payload"])
    html = render_note_email(note_row)
    figs = re.findall(r'data-fig="([A-Z0-9_]+)"[^>]*>([^<]+)<', html)
    assert figs
    allowed = {s["text"] for s in p["slots"].values()} | {r["text"] for r in p["readings"].values()}
    for slot, text in figs:
        assert text in allowed, (slot, text)
    # plain text: every number is a payload figure or part of the week label / ONI period
    txt = render_text(note_row)
    nums = re.findall(r"(?<![\w.])[-+]?\d[\d,]*(?:\.\d+)?", txt.split("\n", 2)[2])
    payload_nums = set()
    for s in list(p["slots"].values()) + list(p["readings"].values()):
        payload_nums |= set(re.findall(r"[-+]?\d[\d,]*(?:\.\d+)?", s["text"] + " " + s.get("date", "")))
    for n in nums:
        assert n in payload_nums or n.lstrip("+-") in {x.lstrip("+-") for x in payload_nums}, n


def test_email_html_is_offline(note_row):
    html = render_note_email(note_row)
    assert "http://" not in html and "https://" not in html
```

## 80. `tests/test_fair_value.py`

```python
import math

import numpy as np
import pandas as pd
import pytest

from harvestradar.paths import DEMO
from harvestradar.signal.fair_value import comovement, fair_value_series, index_path

FLEX = {"slope_pct_per_pct": -3.0, "se": 1.0, "p_value": 0.01}


def _prices(n=400, level=100.0):
    return pd.DataFrame({"date": pd.bdate_range("2024-01-01", periods=n), "close": np.full(n, level)})


def _path(gap):
    return pd.DataFrame({"date": pd.to_datetime(["2023-12-01"]), "delta_prod_pct": [gap], "delta_prod_lo_pct": [gap - 5],
                         "delta_prod_hi_pct": [gap + 5], "risk_z": [1.0]})


def test_fair_value_moves_with_supply_gap_and_band_brackets_it():
    fv = fair_value_series(_prices(), _path(-1.0), FLEX)
    last = fv.iloc[-1]
    assert last.anchor == pytest.approx(100.0)
    assert last.fair == pytest.approx(100 * math.exp(0.03))  # 1 % missing, 3 % per 1 % -> about +3 %
    assert last.fair_lo < last.fair < last.fair_hi
    assert last.fair_lo == pytest.approx(100 * math.exp((3 - 1.2816) / 100))
    assert last.gap_to_fair_pct == pytest.approx(100 * (100 / last.fair - 1))


def test_no_gap_means_fair_value_is_the_anchor():
    last = fair_value_series(_prices(), _path(0.0), FLEX).iloc[-1]
    assert last.fair == pytest.approx(last.anchor) and last.fair_lo == pytest.approx(last.fair_hi)


def test_anchor_needs_200_days_and_uses_no_future_index():
    p = _prices()
    path = pd.DataFrame({"date": pd.to_datetime(["2024-12-01"]), "delta_prod_pct": [-2.0], "delta_prod_lo_pct": [-3.0],
                         "delta_prod_hi_pct": [-1.0], "risk_z": [2.0]})
    fv = fair_value_series(p, path, FLEX)
    assert fv.date.min() >= pd.Timestamp("2024-12-01")  # no index value known before its date
    assert len(fair_value_series(p.head(150), _path(-1.0), FLEX)) == 0


def test_index_path_switches_from_weekly_to_daily():
    cols = {"delta_prod_lo_pct": 0.0, "delta_prod_hi_pct": 0.0, "risk_z": 0.0}
    w = pd.DataFrame({"commodity": "maize", "date": pd.to_datetime(["2025-07-25", "2025-08-01", "2025-08-08"]),
                      "delta_prod_pct": [1.0, 2.0, 3.0], **cols})
    d = pd.DataFrame({"commodity": "maize", "date": pd.to_datetime(["2025-08-01", "2025-08-04"]),
                      "delta_prod_pct": [20.0, 30.0], **cols})
    p = index_path(w, d, "maize", "2025-08-01")
    assert p.delta_prod_pct.tolist() == [1.0, 20.0, 30.0]


def test_comovement_reports_correlations():
    dates = pd.date_range("2006-01-06", periods=300, freq="W-FRI")
    rng = np.random.default_rng(0)
    z = rng.normal(size=300).cumsum() / 10
    w = pd.DataFrame({"commodity": "maize", "date": dates, "risk_z": z, "major_window_open": np.arange(300) % 4 == 0})
    px = pd.DataFrame({"date": pd.bdate_range("2005-12-01", "2012-01-01")})
    px["close"] = 100 * np.exp(rng.normal(scale=0.01, size=len(px)).cumsum())
    out = comovement(w, {"maize": px})["maize"]
    assert out["weeks"] == 300 and -1 <= out["weekly_changes"] <= 1 and out["weeks_in_windows"] == 75


@pytest.mark.skipif(not (DEMO / "fair_value_daily.parquet").exists(), reason="no demo snapshot")
def test_demo_fair_value_contract():
    df = pd.read_parquet(DEMO / "fair_value_daily.parquet")
    assert {"commodity", "date", "close", "anchor", "fair", "fair_lo", "fair_hi", "gap_to_fair_pct"} <= set(df.columns)
    assert (df.fair_lo <= df.fair + 1e-9).all() and (df.fair <= df.fair_hi + 1e-9).all()
```

## 81. `tests/test_note_checks.py`

```python
from harvestradar.report.checks import check_claims, check_context, check_numbers, fill
from harvestradar.report.weekly_note import run_checks, template_note


def test_good_note_passes(note_row, payload):
    res = run_checks(note_row["template"], payload)
    assert res["numbers_ok"] and res["context_ok"] and res["claims_ok"], res["reasons"]


def test_digit_typed_by_model_fails(payload):
    ok, reasons = check_numbers("The index is 2.5 this week, {RISK}.", payload)
    assert not ok and any("digit" in r for r in reasons)


def test_unknown_number_after_fill_fails(payload):
    payload["slots"]["RISK"]["text"] = "+9.99"  # not equal to the value checked elsewhere is fine; inject a stray one
    ok, _ = check_numbers("Index {RISK}.", payload)
    assert ok
    payload["slots"]["PRICE"]["text"] = "445.50 (was 400)"
    ok, reasons = check_numbers("Price {PRICE}.", payload)
    assert ok  # numbers inside the payload text are, by definition, in the payload


def test_name_outside_payload_fails(payload):
    text = ("Maize harvest risk is elevated. The index is {RISK}. " + "Weather was dry. " * 15 + "Argentina too.")
    ok, reasons = check_context(text, payload)
    assert not ok and any("Argentina" in r for r in reasons)


def test_contradictions_are_caught(payload):
    assert not check_claims("Harvest risk is near normal this week at {RISK}.", payload)[0]
    assert not check_claims("Expected supply is {SUPPLY}, above trend.", payload)[0]
    assert not check_claims("Futures prices fell to {PRICE}.", payload)[0]
    assert not check_claims("El Nino is driving the index this week.", payload)[0]
    assert not check_claims("Buyers should buy now.", payload)[0]
    assert not check_claims("The window opens next month.", payload)[0]


def test_template_always_passes(payload):
    t = template_note(payload)
    res = run_checks(t, payload)
    assert res["numbers_ok"] and res["context_ok"] and res["claims_ok"], res["reasons"]
    assert "{" not in fill(t, payload)


def test_semantic_errors_seen_in_real_notes_are_caught(payload):
    # the change read as a previous level
    assert not check_claims("The index stands at {RISK}, up from {RISK_CHANGE} four weeks ago.", payload)[0]
    # supply direction contradicting a negative SUPPLY figure
    assert not check_claims("This points to a higher-than-trend supply situation.", payload)[0]
    assert not check_claims("World supply is {SUPPLY} against trend, down from a month ago.", payload)[0]
    # a positive contribution presented as a risk
    payload["slots"]["DRIVER2_CONTRIB"]["value"] = 0.95
    assert not check_claims("The largest contributors to this risk are {DRIVER1} at {DRIVER1_CONTRIB} and "
                            "{DRIVER2} at {DRIVER2_CONTRIB}.", payload)[0]


def test_reused_figure_and_bold_heading_fail(payload):
    filler = " The weather was watched closely." * 12
    ok, reasons = check_context("**Maize Harvest Risk: Elevated**\n\nIndex {RISK}." + filler, payload)
    assert not ok and any("headings" in r for r in reasons)
    ok, reasons = check_context("Iowa reads {REGION1_STRESS}, mainly due to {REGION1_STRESS}. Index {RISK}." + filler,
                                payload)
    assert not ok and any("more than once" in r for r in reasons)
    ok, reasons = check_context("Index {RISK}. Strong demand and low stocks." + filler, payload)
    assert not ok


def test_more_real_errors_are_caught(payload):
    assert not check_numbers("Contributions: {DRIVER1} (-{DRIVER1_CONTRIB}).", payload)[0]
    assert not check_claims("The index is {RISK_CHANGE} above the trend line.", payload)[0]
    assert not check_claims("The El Nino reading is {ONI}, indicating low chances of impacts.", payload)[0]
    filler = " The weather was watched closely." * 12
    assert not check_context("Index {RISK}. Stay tuned for developments." + filler, payload)[0]


def test_contribution_direction_both_ways(payload):
    bad = ("{DRIVER1} ({DRIVER1_CONTRIB}) and {DRIVER2} ({DRIVER2_CONTRIB}) contribute negatively to world supply, "
           "lowering the risk.")
    assert not check_claims(bad, payload)[0]
```

## 82. `tests/test_signal.py`

```python
import numpy as np
import pandas as pd

from harvestradar.signal.backtest import permutation_p, perf, positions


def test_positions_rule():
    r = pd.DataFrame({"risk_z": [0, 0, 0, 0, 1.0, 1.2, -1.0, -1.0], "major_window_open": [True] * 4 + [True, False, True, True]})
    p = positions(r, 0.5, 4)
    assert p.tolist()[4] == 1 and p.tolist()[5] == 0 and p.tolist()[6] == -1


def test_permutation_p_bounds():
    rng = np.random.default_rng(1)
    ret = pd.Series(rng.normal(0, 0.02, 300))
    pos = pd.Series(rng.choice([-1, 0, 1], 300))
    p = permutation_p(ret, pos, 5, 200, 42)
    assert 0 < p <= 1
    assert "sharpe" in perf(ret, pos, 5)


def test_standardize_uses_past_only_and_flags_shortfalls():
    from harvestradar.signal.risk_index import standardize

    dates = pd.date_range("2000-01-07", "2012-12-28", freq="W-FRI")
    rng = np.random.default_rng(0)
    d = pd.Series(rng.normal(0, 0.5, len(dates)), index=dates)
    d.loc["2012-07-13":"2012-08-31"] = -3.0  # a large expected shortfall
    st = standardize(d, 15, 3, 4, 0.5)
    assert st.loc["2012-07-20", "risk_z"] > 3
    assert st.loc[:"2003-12-31", "risk_z"].isna().all()  # fewer than 4 years of history
    d2 = d.copy()
    d2.loc["2012-09-01":] = 50.0  # future values must not change earlier z
    st2 = standardize(d2, 15, 3, 4, 0.5)
    assert np.allclose(st.loc[:"2012-08-31", "risk_z"].dropna(), st2.loc[:"2012-08-31", "risk_z"].dropna())
```

## 83. `tests/test_stress_features.py`

```python
import datetime as dt

import numpy as np
import pandas as pd

from harvestradar.features.aggregate import SeasonCube
from harvestradar.features.stress import dekad_end, dekad_of, frost_days, hargreaves_et0, heat_degree_days, to_dekad
from harvestradar.models.targets import yield_anomaly


def synthetic_daily(start="1981-01-01", end="2026-11-10", seed=0):
    rng = np.random.default_rng(seed)
    d = pd.date_range(start, end, freq="D")
    doy = d.day_of_year.to_numpy()
    tmax = 22 + 10 * np.sin(2 * np.pi * (doy - 100) / 365) + rng.normal(0, 3, len(d))
    return pd.DataFrame({"date": d, "tmax_c": tmax, "tmin_c": tmax - 11, "precip_mm": rng.gamma(0.5, 5, len(d)),
                         "sm_root": np.clip(0.5 + rng.normal(0, 0.05, len(d)), 0, 1), "sm_top": 0.5,
                         "et0_mm": 4.0})


def test_basic_stress_functions():
    assert heat_degree_days(pd.Series([25.0, 31.0]), 29).tolist() == [0.0, 2.0]
    assert frost_days(pd.Series([1.0, 3.0]), 2.0).tolist() == [1.0, 0.0]
    et = hargreaves_et0(np.array([30.0]), np.array([18.0]), np.array([42.0]), np.array([196]))
    assert 3 < et[0] < 9
    d = pd.Series(pd.to_datetime(["2026-01-10", "2026-01-11", "2026-02-28"]))
    assert dekad_of(d).tolist() == [0, 1, 5]
    assert dekad_end(pd.Series([2026]), pd.Series([5])).iloc[0] == pd.Timestamp("2026-02-28")


def test_to_dekad_shapes():
    daily = synthetic_daily("2020-01-01", "2020-12-31").assign(region_id="X")
    dek = to_dekad(daily, 29.0)
    assert len(dek) == 36 and dek["n"].between(8, 11).all()


def test_season_features_are_leak_free(cfg):
    """Changing weather AFTER the cutoff must not change a feature computed as of the cutoff."""
    c = cfg.commodities["maize"]
    base = synthetic_daily()
    cut = dt.date(2012, 7, 20)
    a = SeasonCube(c, "USA", base, cfg).features(2012, cut)
    tampered = base.copy()
    after = tampered["date"] > pd.Timestamp(cut)
    tampered.loc[after, ["tmax_c", "precip_mm", "sm_root"]] = [45.0, 0.0, 0.01]
    b = SeasonCube(c, "USA", tampered, cfg).features(2012, cut)
    for k in a:
        assert (np.isnan(a[k]) and np.isnan(b[k])) or abs(a[k] - b[k]) < 1e-12, k
    assert 0 < a["progress"] < 1


def test_season_features_before_window_are_neutral(cfg):
    c = cfg.commodities["maize"]
    f = SeasonCube(c, "USA", synthetic_daily(), cfg).features(2012, dt.date(2012, 5, 1))
    assert f["progress"] == 0 and f["hdd_z"] == 0 and np.isfinite(f["sm_pre_z"])


def test_trend_uses_only_past_years():
    years = np.arange(1990, 2021)
    y = 5 + 0.1 * (years - 1990)
    df = pd.DataFrame({"commodity": "maize", "country_iso3": "USA", "year": years, "yield_t_ha": y})
    a = yield_anomaly(df).set_index("year")["yield_anom"]
    df2 = df.copy()
    df2.loc[df2.year == 2020, "yield_t_ha"] = 1.0  # a crash in the last year
    b = yield_anomaly(df2).set_index("year")["yield_anom"]
    assert np.allclose(a.loc[:2019].dropna(), b.loc[:2019].dropna())
    assert b.loc[2020] < -0.5 and abs(a.loc[2015]) < 1e-9
```

## 84. `tests/test_theme_and_contracts.py`

```python
import re
from pathlib import Path

import pandas as pd
import pytest

from harvestradar.app.theme import RAMP, TOKENS, ramp, ramp_opacity
from harvestradar.paths import DEMO, ROOT

ALLOWED = {v.upper() for v in TOKENS.values()} | {c.upper() for _, c in RAMP} | {"#142030"}


def test_ramp_endpoints_and_opacity():
    assert ramp(-5) == (126, 176, 255) and ramp(0) == (30, 40, 51) and ramp(9) == (255, 90, 54)
    assert ramp_opacity(0) == pytest.approx(0.35) and ramp_opacity(3) == pytest.approx(1.0)


def test_only_design_tokens_are_used():
    """Section 3 of the app guidelines: grep for stray hex colours in the app and the email."""
    files = list((ROOT / "src/harvestradar/app").rglob("*.py")) + list((ROOT / "src/harvestradar/app/static/js").glob("*.js"))
    files += [ROOT / "src/harvestradar/report/email_note.py"]
    stray = {}
    for f in files:
        for h in re.findall(r"#[0-9A-Fa-f]{6}\b", f.read_text()):
            if h.upper() not in ALLOWED:
                stray.setdefault(str(f.relative_to(ROOT)), set()).add(h)
    assert not stray, stray


def test_no_em_dash_on_screen():
    for f in (ROOT / "src/harvestradar/app").rglob("*.py"):
        assert "—" not in f.read_text(), f


CONTRACTS = {
    "risk_index.parquet": ["commodity", "date", "risk_z", "delta_prod_pct", "coverage_share", "major_window_open",
                           "contributors"],
    "predictions.parquet": ["commodity", "country_iso3", "season", "date", "pred_anom", "pred_lo", "pred_hi",
                            "window_open"],
    "shap_latest.parquet": ["commodity", "country_iso3", "season", "as_of", "shap_hdd_z", "shap_oni"],
    "notes.parquet": ["commodity", "week", "markdown", "numbers_ok", "model", "payload", "seconds"],
}


@pytest.mark.skipif(not (DEMO / "meta.json").exists(), reason="no demo snapshot")
@pytest.mark.parametrize("name,cols", CONTRACTS.items())
def test_demo_contracts(name, cols):
    df = pd.read_parquet(DEMO / name)
    assert set(cols) <= set(df.columns)


@pytest.mark.skipif(not (DEMO / "meta.json").exists(), reason="no demo snapshot")
def test_demo_size_under_50mb():
    assert sum(p.stat().st_size for p in Path(DEMO).glob("*")) < 50e6
```

## 85. `tests/test_update.py`

```python
import datetime as dt

import numpy as np
import pandas as pd

from harvestradar.ingest import power
from harvestradar.update import latest_business_day

COLS = ["tmax_c", "tmin_c", "precip_mm", "sm_root", "sm_top"]


def _days(start, end, missing_tail=0):
    d = pd.DataFrame({"date": pd.date_range(start, end)})
    for c in COLS:
        d[c] = 1.0
    if missing_tail:
        d.loc[d.index[-missing_tail:], COLS] = np.nan
    return d


def test_update_cells_appends_new_days_and_drops_unfilled_tail(tmp_path, monkeypatch):
    monkeypatch.setattr(power, "POWER_DIR", tmp_path)
    monkeypatch.setattr(power, "record_group", lambda *a, **k: None)
    _days("2026-01-01", "2026-11-05").to_parquet(tmp_path / "+010.00_+010.000.parquet", index=False)
    calls = []

    def fake(lat, lon, start, end, session):
        calls.append((start, end))
        new = _days(start, end, missing_tail=2)  # NASA has not filled the last two days yet
        new.loc[new.date == pd.Timestamp("2026-11-01"), "tmax_c"] = 9.0  # a revised value
        return new

    monkeypatch.setattr(power, "_fetch_one", fake)
    cells = pd.DataFrame({"cell_id": ["+010.00_+010.000", "+020.00_+020.000"], "lat": [10.0, 20.0], "lon": [10.0, 20.0]})
    n = power.update_cells(cells, "2026-11-13", "1981-01-01", overlap_days=10)
    assert n == 2
    assert ("2026-10-26", "2026-11-13") in calls and ("1981-01-01", "2026-11-13") in calls
    d = pd.read_parquet(tmp_path / "+010.00_+010.000.parquet")
    assert d.date.is_unique and d.date.is_monotonic_increasing
    assert d.date.max() == pd.Timestamp("2026-11-11")  # the unfilled tail is fetched again next run
    assert d.loc[d.date == pd.Timestamp("2026-11-01"), "tmax_c"].item() == 9.0
    assert d.date.min() == pd.Timestamp("2026-01-01")


def test_latest_business_day():
    assert latest_business_day(dt.date(2026, 11, 16)) == dt.date(2026, 11, 16)  # Monday
    assert latest_business_day(dt.date(2026, 11, 15)) == dt.date(2026, 11, 13)  # Sunday -> Friday


def test_prices_keep_only_settled_closes():
    import pandas as pd

    from harvestradar.ingest.prices import settled_until

    assert settled_until(pd.Timestamp("2026-11-16 09:30", tz="UTC")) == pd.Timestamp("2026-11-16")
    assert settled_until(pd.Timestamp("2026-11-16 21:30", tz="UTC")) == pd.Timestamp("2026-11-17")
```
