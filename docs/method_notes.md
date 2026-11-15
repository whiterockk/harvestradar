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

## 5. Trading rule

Pre-registered rule (SPEC 9.1), 5 bps per trade, 1,000 permutations. Three commodities are tested, so the
smallest p-value is reported with a Bonferroni correction; the 3 x 3 robustness grid is reported in full and
its best p is corrected for the 27 tests.
