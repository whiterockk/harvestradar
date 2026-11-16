# Method notes: decisions, checks and the honest record

This file lists every modelling decision taken while building HarvestRadar, with the reason and the data
used to take it. Rule followed throughout: decisions are taken on data before 2012; the test period
(2012-2024) is only used to report.

## 1. Regions and weather

- MapSPAM 2020 V2r2 production rasters: maize `MAIZ`, arabica `COFF` (the 2020 release names arabica `COFF`
  and robusta `RCOF`; checked: Minas Gerais 498 kt, Colombia 220 kt, Vietnam Central Highlands 3.5 kt of
  `COFF`), cocoa `COCO`.
- geoBoundaries ADM1 for the 96 countries that produce 99.5 % of each crop; regions ranked by MapSPAM
  production until they cover 90 % of world output: 312 maize, 93 arabica, 65 cocoa regions.
- Up to 5 NASA POWER cells per region on the most productive pixels: 2,016 cells, daily 1981 to 12 Nov 2026.

## 2. Model

- Target: maize yield anomaly; arabica and cocoa production anomaly (FAOSTAT harvested area is imputed for
  many tree-crop countries). Trend: linear on the 15 previous years only.
- Features as of each Friday, data used 5 days after the fact; anomalies against the same calendar span in
  strictly earlier years. A leak test (`tests/test_stress_features.py`) tampers with future weather and checks
  that past features do not move.
- Rolling origin with real publication dates: vintage V uses seasons published before 1 January of V
  (FAOSTAT year Y is published in December of Y+1). So the 2012 forecasts come from a model trained on
  seasons up to 2010.
- Hyperparameters chosen on vintages 2003-2011 only, end-of-season RMSE weighted by world share, among
  three tree sizes and three sample weightings, then frozen (`data/processed/hyperparameter_selection.json`).
  A first selection had been run on a dry run with provisional region weights; it was redone on the final
  features with the same grid and criterion, and gave the same choice (5 leaves, 80 samples per leaf,
  sqrt-share weights).
- Headline metric fixed before reading the test period: end-of-season RMSE weighted by share of world
  output, against the trend-only baseline. The unweighted value is always shown next to it.

## 3. The index

- First version: `risk_z = -dP / sd(realised world anomalies)`. Rejected: a regularised model gives shrunk
  forecasts, so the index almost never moved (2012 peak +0.15). It was not the SPEC definition either.
- Second version (SPEC 5.9): standardise dP against the history of past forecasts at the same time of year.
  Rejected on calibration: the spread of `risk_z` over 2006-2026 was 0.91, 6 % of weeks above +2 and none
  below -2, because forecasts drift between vintages.
- Adopted: model climatology, as in seasonal forecasting. Each vintage re-forecasts the same weeks
  (+/- 3) of the previous 15 years; mean and sd of those hindcasts standardise this week's dP; sd floored at
  half the all-weeks sd. Calibration over 2006-2026: sd 0.96. The choice was made on calibration (sd close to
  1), not on the episodes.

## 4. Honest record (as of 13 Nov 2026)

See `data/demo/events.json`, `model_eval.json`, `backtest.json` and `docs/storyboard_facts.md` for the exact
values. Verdict rule fixed in code: an episode is "caught" only if `risk_z` crossed +2 before the futures
price peaked, "late" if it crossed after, "missed" otherwise.

## 5. Daily index

The weekly history (Fridays since 2001) is complemented by an index for every working day since 1 August 2025:
features as of each day, the vintage model of that year, the same model climatology. On Fridays both series are
identical (checked).

## 6. What it means for the price

`signal/price_impact.py`: for each crop, the change of the average front-month futures price over a marketing
year (maize from September, arabica from July, cocoa from October) is regressed on the realised world supply gap
of that year (FAOSTAT, modelled countries, share-weighted), 2002-2024, 23 years, robust standard errors. The
slope is applied to the model's expected supply gap; the 80 % range uses the slope +/- 1.28 standard errors.
Results: maize -3.1 % of price per 1 % of supply (p = 0.01, R2 0.15), cocoa -1.9 (p = 0.03, R2 0.26),
arabica no reliable link (p = 0.90), so the app shows no estimate for arabica. It is a rough guide, not a price
forecast.

## 6b. Climate fair value and the pricing tool

`signal/fair_value.py`, re-run by `harvestradar index price` (and by `harvestradar all`) on every data update.
For each crop and trading day t: anchor A = average close of the last 252 trading days; G = expected world
supply vs normal, latest index value known on day t (weekly index before 1 August 2025, daily after);
fair value F = A x exp(b x G / 100) with b the price reaction of section 6; 80 % range with b +/- 1.28 se.
The index's own 80 % range of world supply is not used for the band: it sums country ranges (a worst case)
and would give a range of +/- 20 % that says nothing. Values before 2025 are in-sample for b.

Today (2026-11-13): maize fair value 466.31 (range 459.57 to 473.15),
close 445.5 (-4.5 %); cocoa 4,944, close 5,119
(+3.5 %); arabica 316.93 but no reliable reaction (p = 0.90), so the fair value is
the 12-month average in practice and the page says so.

What it is: the climate component of a fair value. What it is not: a full valuation model. Demand, stocks,
the dollar, fund positioning and the other origins move prices too; the distance between price and fair value
is what they explain.

## 6c. Why the index and the price do not move together

Correlations, weekly, 2006 to 2026 (1089 weeks), computed by `comovement()` and shown in the app:

| | Weekly changes | Weekly changes, critical windows | Index vs price change over next 13 weeks |
|---|---|---|---|
| Maize | +0.08 | +0.15 | -0.16 |
| Arabica | -0.01 | -0.01 | +0.11 |
| Cocoa | -0.01 | +0.00 | +0.03 |

The index measures the expected harvest against normal for the time of year; it is not a price model. The link
is weak and shows up mainly in the critical windows of maize. The negative 13-week figure for maize says that
by the time the index is high the market has usually moved already. This is why the app turns the supply gap
into a fair value instead of drawing the index as a price signal, and why the trading rule of section 7 is not
significant.

## 7. Trading rule

Pre-registered rule (SPEC 9.1), 5 bps per trade, 1,000 permutations. Three commodities are tested, so the
smallest p-value is reported with a Bonferroni correction; the 3 x 3 robustness grid is reported in full and
its best p is corrected for the 27 tests.
