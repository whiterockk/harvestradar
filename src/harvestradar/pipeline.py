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

    first = min(cfg.index_start.year, int(cfg.model["first_test_year"]))
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


def build_index(cfg: Settings) -> None:
    from harvestradar.signal.backtest import run_backtest
    from harvestradar.signal.events import build_events
    from harvestradar.signal.risk_index import build_risk_index

    preds = pd.read_parquet(PROCESSED / "predictions_weekly.parquet")
    preds = preds[preds.as_of >= pd.Timestamp(cfg.index_start)]
    targets = pd.read_parquet(PROCESSED / "targets.parquet")
    fao = pd.read_parquet(PROCESSED / "fao_qcl.parquet")
    risk = build_risk_index(cfg, preds, targets, fao)
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
    build_notes(cfg, deterministic=deterministic_notes)
    export_demo(cfg)
    export_week("latest", REPORTS / "notes")
