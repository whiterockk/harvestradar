# HarvestRadar user guide

## 1. Install and start

Requirements: Python 3.11, `make`. Mobile is not supported; the app is designed for 1440 x 900 and 1920 x 1080.

```bash
make setup
make demo
```

Open http://localhost:8501. The app reads only `data/demo/` and makes no external request.

## 2. Reading the index

`risk_z` is the expected world production gap of a commodity, in units of a typical year-to-year supply
surprise, with the sign flipped so that **positive means more supply risk**. Zero is a normal season; above +2
is rare (the share of weeks above +2 since 2001 is in `data/demo/meta.json`). Before a critical window opens
the model knows little and the index stays near zero; it moves when the window weather comes in.

Colour only ever means risk: the amber signal and the blue-to-red ramp. Crops are told apart by their glyph
and name. Maps read "lower stress / higher stress": a region's stress compares its heat, 30-day rain and
root-zone soil moisture with the same dekad in 2001-2020.

## 3. Pages

- **Stress map**: click a ticker card to change crop. Press play (or Space) to run the dekads of the year,
  arrows step one dekad, `x1 / x2.5` changes speed. Rings mark the three regions with the highest
  stress x share of world supply. The right column ranks the top five for the latest dekad, shows El Nino as
  context only, and links to the Friday note.
- **Commodity**: the index (amber) against the futures price (white), the main producer's critical windows
  shaded and named from `config/commodities.yaml`. "Who drives this week" gives each country's contribution
  in percentage points of world supply (amber raises risk, blue lowers it). Pick a country to see the four
  largest SHAP contributions of its forecast.
- **Replay**: pick an episode. The chip says which seasons the model had seen. The film strip shows six
  dekads; the event card gives the first week with `risk_z` at or above +2, or the peak if it never got there.
- **Weekly note**: notes for the latest two weeks. Figures are amber pills; hover one to see its source.
  "Data given to the model" lists every figure with its source and date. A note tagged
  `DETERMINISTIC-TEMPLATE` means the model failed the checks after two retries (or was not run).
- **Method**: pipeline, out-of-sample evaluation, the honest record (what the index caught and missed, the
  trading-rule test), credits.

## 4. Exporting the weekly note as an email

On the Weekly note page, **Download as email** saves a `.eml` file (open it with any mail client). From the
command line, for the three commodities of the latest week:

```bash
harvestradar report email --week latest
```

This writes `reports/notes/<week>_<crop>.eml` and `.html`. The email is self-contained (inline CSS, logo
embedded), so it renders offline. Nothing is sent: there is no SMTP and no stored credential.

## 5. Opening an exact state (for the video)

| Parameter | Values |
|---|---|
| `page` | `stress`, `commodity`, `replay`, `note`, `method` |
| `crop` | `maize`, `coffee`, `cocoa` |
| `date` | as-of date `YYYY-MM-DD` (defaults to the latest date in `data/demo`) |
| `dekad` | dekad shown first on the maps, `YYYY-MM-DD` |
| `episode` | `us_drought_2012`, `brazil_frost_2021`, `cocoa_2023_2024` |
| `week`, `country` | note week; country for the SHAP panel (ISO3) |
| `capture=1`, `play=1`, `data=1` | freeze animations and hovers; autoplay the map; open the note data panel |

`make screenshots` captures all pages with Playwright at 1920 x 1080, device scale factor 2.

## 6. Refreshing the data

See the README ("Rebuild everything"). The date of the weekly update is `dates.as_of_end` in
`config/settings.yaml`; set it to the latest Friday and run `make all`.

## 7. Limits

The index is an analysis tool: weather is public and fast, so part of the signal can already be in prices.
Windows are fixed calendar approximations, weights are static (MapSPAM 2020), and NASA POWER is coarse
(about 50 km). See the honest record on the Method page and `reports/model_eval.md`.
