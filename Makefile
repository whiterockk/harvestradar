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
