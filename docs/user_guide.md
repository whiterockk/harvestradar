# HarvestRadar user guide

## 1. Install and start

Requirements: Python 3.11, `make`. Mobile is not supported; the app is designed for 1440 x 900 and 1920 x 1080.

```bash
make setup
make demo
```

Open http://localhost:8501. The app reads only `data/demo/` and makes no external request.

## 2. Reading the index

`risk_z` says how unusual this week's expected world production gap is, for this time of year, compared
with what the same model says at the same weeks of the previous 15 years; the sign is flipped so that
**positive means more supply risk**. Zero is a normal season; above +2
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
- **Commodity**: "From weather to price" shows the four steps behind today's reading: the weather in the
  producing regions, the expected world harvest vs normal, the risk index and the price (expected move and
  climate fair value). Below it, the index (amber, left scale) against the futures price (white, right scale), the main
  producer's critical windows shaded and named from `config/commodities.yaml`. "What it means for the price"
  turns the expected world supply gap into the move of the futures price that such a gap has come with since
  2002 (a rough guide with an 80 % range; for arabica no reliable link was found, so none is shown). "Who drives this week" gives each country's contribution
  in percentage points of world supply (amber raises risk, blue lowers it). Pick a country to see the four
  largest SHAP contributions of its forecast.
- **Fair value**: the futures price against its climate fair value: the average close of the last 12 months,
  moved by the price reaction that today's expected world supply implies (same measured slope as "What it means
  for the price"). The 80 % range covers the uncertainty of that slope. The pricing tool recomputes the fair
  value for a scenario: pick "Index +2" or "Index +3" (the supply gap that would give that index today), move
  the supply gap, the price reaction or the anchor price. "Why the index and the price do not move together"
  gives the measured correlations since 2006. For arabica no reliable price reaction was found, which the page
  says: the fair value then stays close to the 12-month average.
- **Replay**: pick an episode. The chip says which seasons the model had seen. The film strip shows six
  dekads; the event card gives the first week with `risk_z` at or above +2, or the peak if it never got there.
- **Daily note**: one note per commodity for each of the last five working days. Figures are amber pills;
  hover one to see its source. "Data given to the model" lists every figure with its source and date. A note
  tagged "Fixed template" means the model failed the checks for every paragraph; "n of 3 paragraphs from the
  template" means that n paragraphs were replaced by the fixed template after failing the checks. The three
  checks show as tags (blue: passed, red: failed).
- **Method**: pipeline, out-of-sample evaluation, the honest record as a table with a verdict for each test
  (clear or small gain, caught, too late, missed, significant or not), credits.
- **Assistant**: a button on every page ("Ask the assistant") opens a side panel with suggested questions for
  that page and a chat box; the Commodity page has "Ask about <crop>" and the pricing tool "Ask the assistant
  about this scenario". The answer appears in the panel. It comes from a small open model (Qwen 2.5,
  0.5 billion parameters, GGUF) run by wllama (llama.cpp compiled to WebAssembly) on the computer's processor:
  no graphics card needed, free, no account, and the questions stay on the computer. The first question
  downloads the model (about 400 MB, once; the browser keeps it); each answer then takes about 30 to 60
  seconds. Where the model cannot load (for example in the page published inside Claude), a link offers to
  ask ChatGPT in a new tab instead. In the Streamlit app, the Commodity page answers with the local model of
  the daily notes. "What the assistant receives" shows the exact text given to the model. The model is small
  and can be wrong: check the figures on the page. Not investment advice.

## 4. Opening an exact state (for the video)

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

## 5. Refreshing the data

See the README ("Rebuild everything"). The date of the weekly update is `dates.as_of_end` in
`config/settings.yaml`; set it to the latest working day and run `make all`.

## 6. Limits

The index is an analysis tool: weather is public and fast, so part of the signal can already be in prices.
Windows are fixed calendar approximations, weights are static (MapSPAM 2020), and NASA POWER is coarse
(about 50 km). See the honest record on the Method page and `reports/model_eval.md`.
