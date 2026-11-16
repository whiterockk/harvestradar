# Acceptance checklist (app guidelines, section 8)

| Item | Status |
|---|---|
| Branch `app-redesign`, PR | Not applicable: the project was built from scratch, without a GitHub repository. Delivered as a git bundle (branch `main`) and a zip. |
| `make setup`, `make demo`, `make test` from a fresh clone | Passed (setup 81 s, 35 tests). |
| Offline check: zero external requests | Passed: `make offline-check` opens the 8 page states and plays the maps, 0 external requests. |
| Only the tokens of section 3 | Checked by `tests/test_theme_and_contracts.py` (grep for stray hex colours). |
| Fonts: Space Grotesk, Inter, JetBrains Mono | Bundled `.woff2` with OFL licences, also declared as Streamlit theme fonts. |
| No text under 13 px; every data panel has a source line | Done. |
| Stress map: satellite base, ramp with opacity rule, top-5 regions from data, hotspot rings, scrubber | Done (Equal Earth projection on NASA Blue Marble, SVG, animation in the browser). |
| Commodity: hero number, index vs price with windows from config, contributors and SHAP from data | Done. |
| Episode replay: all three episodes play; 2012 date and prices from data | Done. 2012 first above +2 on 2012-07-06 (not 8 June: the storyboard value is illustrative). See `docs/storyboard_facts.md`. |
| Weekly note: figure pills, data panel, fallback tag, Download as email | Done (daily; "Fixed template" or "n of 3 paragraphs from the template"; checks as tags, no symbols). |
| Fair value and pricing tool (round 3) | Done: `signal/fair_value.py`, Fair value page in both editions, `tests/test_fair_value.py`. |
| `harvestradar report email --week latest` writes valid `.eml` and `.html` for 3 commodities; tests | Done (`reports/notes/`, `tests/test_email.py`). |
| Query parameters and `?capture=1` | Done (`page, crop, date, dekad, episode, week, country, capture, play, data`). |
| One screenshot of each page at 1920 x 1080 | `docs/img/` (`make screenshots` for device scale factor 2). |
| `docs/data_sources.md` credits NASA Blue Marble and the fonts; README screenshot | Done. |

Deviation from the guidelines: the map uses an SVG component (Equal Earth, as in the storyboard) instead of
pydeck, so that the animation runs in the browser without re-sending the page, and the rendering stays sharp
when filmed and zoomed 2x.
