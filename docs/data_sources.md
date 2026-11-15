# Data sources, licences and status

Every download is recorded in `data/manifest.json` (source, URL, collection date, licence, SHA-256).
Status: **Verified** (checked during the build), **Not used** (with the reason).

| Source | Used for | Access | Licence | Status |
|---|---|---|---|---|
| NASA POWER daily point API (MERRA-2, 0.5 x 0.625 deg) | Daily tmax, tmin, rain, root-zone and surface soil wetness, 1981 to present, one request per grid cell | `https://power.larc.nasa.gov/api/temporal/daily/point`, no key | NASA open data | Verified. Chosen instead of Open-Meteo, whose free tier answered HTTP 429 (rate limit) from the build environment and counts a 45-year request as about 680 calls. |
| MapSPAM 2020 V2r2 (IFPRI), global production rasters `*_P_MAIZ_A`, `*_P_ACOF_A`, `*_P_COCO_A` | Production weights of regions and grid cells; arabica country shares | Harvard Dataverse `doi:10.7910/DVN/SWPENT`. A guestbook (name, e-mail, institution) must be filled in by a person before download: put the three `.tif` files in `data/raw/spam/` | CC BY 4.0 | Verified. Manual step, see README. |
| geoBoundaries gbOpen ADM1 (simplified) | Region polygons, names, ids | `https://www.geoboundaries.org/api/current/gbOpen/<ISO3>/ADM1/`. Files are stored with Git LFS and fetched from `media.githubusercontent.com` | Per country, mostly CC BY 4.0 or public domain (recorded per file in the manifest) | Verified |
| FAOSTAT QCL (crops and livestock products), bulk normalized file | Yield (maize) and production (arabica, cocoa) anomalies used as model targets; country shares of world production | `https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_All_Data_(Normalized).zip` | CC BY 4.0 | Verified, data to 2024 (release of December 2025). Year Y is treated as published on 31 December of Y+1. |
| NOAA CPC Oceanic Nino Index | El Nino context card, model feature `oni` | `https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt` | Public domain | Verified |
| Yahoo Finance via `yfinance` | Front-month continuous futures: CBOT corn `ZC=F`, ICE arabica `KC=F`, ICE cocoa `CC=F` | `yfinance` library | Yahoo terms: personal or research use | Verified, closes to the as-of date. Roll days neutralised in returns. |
| Natural Earth 1:110m admin 0 | Faint country borders on the map | `https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip` | Public domain | Verified |
| NASA Blue Marble Next Generation | Satellite base of the maps (graded and projected offline) | Image shipped in the `three-globe` npm package (`example/img/earth-blue-marble.jpg`, MIT package, NASA public-domain image) | Public domain | Verified. Graded by `scripts/grade_blue_marble.py`, projected to Equal Earth by `scripts/build_map_base.py`. |
| Qwen2.5-1.5B-Instruct (Hugging Face) | Weekly note text, run locally on CPU | `Qwen/Qwen2.5-1.5B-Instruct` | Apache 2.0 | Verified |
| Fonts: Space Grotesk, Inter, JetBrains Mono | App typography (bundled `.woff2`, with their licence files) | Google Fonts families, files from the Fontsource npm packages | SIL Open Font License 1.1 | Verified |

## Not used in this version

| Source in the spec | Reason |
|---|---|
| NDVI (MODIS, VIIRS), SMAP, Sentinel-2 | Need a NASA Earthdata or Copernicus account. Soil moisture comes from NASA POWER (MERRA-2 root-zone wetness) instead. |
| CFTC COT | `www.cftc.gov` answered HTTP 403 from the build environment. Positioning is not in the weekly payload. |
| USDA PSD, WASDE | Not needed for the three crops of the prototype (FAOSTAT covers yields and shares). The WASDE revision test is not implemented. |
| Soybeans, wheat, sugar | The prototype covers the three crops of the demo (maize, arabica, cocoa). The configuration accepts more commodities. |

## Main assumptions (documented, not hidden)

- Regions: ADM1 polygons ranked by MapSPAM 2020 production until they cover 90 % of world production (per crop); weights are static (MapSPAM 2020 used for all years).
- Weather: up to 5 NASA POWER cells per region, on the most productive pixels; the region series is the production-weighted mean of its cells.
- Targets: maize uses the yield anomaly; arabica and cocoa use the production anomaly (FAOSTAT harvested area is often imputed for tree crops). Trend: linear on the previous 15 years (at least 8), never using the year itself or later years.
- Arabica shares: MapSPAM 2020 arabica (ACOF) country totals, because FAOSTAT does not split arabica from robusta. The target for arabica countries is FAOSTAT green coffee production (both species).
- Critical windows are defaults from the spec, to validate with GEOGLAM, SAGE and USDA IPAD.
