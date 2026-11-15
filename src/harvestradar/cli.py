"""HarvestRadar command line: `harvestradar <group> <command>`."""

from __future__ import annotations

import typer

app = typer.Typer(help="HarvestRadar: harvest-risk index for agricultural commodities.", no_args_is_help=True)
data_app = typer.Typer(help="Download sources (network).", no_args_is_help=True)
regions_app = typer.Typer(help="Producing regions and weights.", no_args_is_help=True)
features_app = typer.Typer(help="Stress variables and model features.", no_args_is_help=True)
model_app = typer.Typer(help="Yield model, validation, SHAP.", no_args_is_help=True)
index_app = typer.Typer(help="Risk index, episodes, backtest.", no_args_is_help=True)
report_app = typer.Typer(help="Weekly notes and email export.", no_args_is_help=True)
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


@report_app.command("notes")
def report_notes(weeks: int = typer.Option(None, help="Number of latest weeks"),
                 deterministic: bool = typer.Option(False, help="Skip the LLM, use the template")) -> None:
    """Weekly notes (local Hugging Face model, guarded by number and claim checks)."""
    from harvestradar.report.weekly_note import build_notes

    build_notes(_cfg(), weeks=weeks, deterministic=deterministic)


@report_app.command("email")
def report_email(week: str = typer.Option("latest", help="'latest' or a date YYYY-MM-DD"),
                 out_dir: str = typer.Option("reports/notes", help="Output directory")) -> None:
    """Write the weekly notes as .eml and .html (offline: nothing is sent)."""
    from pathlib import Path

    from harvestradar.report.email_note import export_week

    for p in export_week(week, Path(out_dir)):
        typer.echo(str(p))


@demo_app.command("export")
def demo_export() -> None:
    """Write the offline snapshot used by the app to data/demo/."""
    from harvestradar.demo.export import export_demo

    export_demo(_cfg())


@app.command("all")
def run_all(skip_download: bool = False, deterministic_notes: bool = False) -> None:
    """Run the full pipeline."""
    from harvestradar.pipeline import run_all as _run

    _run(_cfg(), skip_download=skip_download, deterministic_notes=deterministic_notes)


if __name__ == "__main__":
    app()
