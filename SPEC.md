# HarvestRadar – Spécification technique

> Document de référence pour développer HarvestRadar avec Claude Code. Version 0.1 du 13 novembre 2026.
> Statuts utilisés : **Vérifié** (contrôlé le 13/11/2026), **Connu, à revérifier** (à confirmer au démarrage), **À vérifier** (incertain).
> HarvestRadar est un outil d'analyse. Son indice et son signal ne sont pas des recommandations d'investissement.

---

## 1. Objectif et utilisateurs

### 1.1 Problème
Les prix des matières premières agricoles réagissent aux chocs météo dans un petit nombre de zones productrices, pendant des fenêtres de quelques semaines (pollinisation du maïs, floraison du café, saison sèche du cacao…). Suivre ces chocs demande de croiser des données météo, satellite, agronomiques et de marché. Ces données sont dispersées, hétérogènes et souvent lues trop tard.

### 1.2 Ce que fait HarvestRadar
1. Il mesure les écarts à la normale de la météo, de l'humidité du sol et de la végétation (NDVI) dans les zones productrices de chaque commodité. Chaque zone est pondérée par son poids dans la production, et seules les fenêtres critiques de chaque culture comptent.
2. Il prédit l'écart de rendement attendu par pays, puis l'écart de production mondial.
3. Il en tire un **indice de risque récolte** par commodité, exprimé en écarts-types, avec une carte des zones en stress.
4. Il confronte cet indice aux prix des futures : backtest, études d'événements, et test d'anticipation des révisions de l'USDA dans le rapport WASDE.
5. Il produit une note hebdomadaire en langage clair, rédigée par un LLM à partir de chiffres sourcés et contrôlés.

### 1.3 Utilisateurs
| Utilisateur | Besoin | Usage dans HarvestRadar |
|---|---|---|
| Analyste ou trader en commodités agricoles | Repérer tôt un choc d'offre | Indice, carte, contributions par région |
| Acheteur agroalimentaire (achats, couverture) | Anticiper la hausse d'un intrant | Note hebdomadaire, alertes de fenêtre critique |
| Journaliste, ONG, sécurité alimentaire | Comprendre où la récolte souffre | Carte mondiale, rejeu d'épisodes |
| Étudiant ou grand public | Comprendre pourquoi le prix du café ou du chocolat bouge | Démo et note en langage clair |

### 1.4 Hors périmètre
- Exécution d'ordres, gestion de portefeuille, conseil en investissement.
- Données intraday, carnets d'ordres.
- Prévision météo propriétaire : on consomme des données existantes.

### 1.5 Éléments qui vont au-delà du cours (à confronter au syllabus)
- Machine learning géospatial : agrégation de rasters et de points pondérée par la production.
- Validation temporelle sans fuite (rolling origin, disponibilité réelle des données) et baselines explicites.
- Explicabilité par SHAP au niveau pays et région.
- LLM avec contrôle de cohérence des chiffres contre les hallucinations.
- Backtest de futures avec coûts, gestion du roll et tests de permutation.

---

## 2. Périmètre

### 2.1 Prototype (6 commodités)
Fenêtres et zones par défaut, **à valider** avec les calendriers GEOGLAM, SAGE et USDA IPAD. Les tickers yfinance sont **Connus, à revérifier**.

| Commodité | Contrats (ticker yfinance) | Zones suivies | Fenêtres critiques par défaut | Risque principal |
|---|---|---|---|---|
| Maïs | CBOT Corn (`ZC=F`) | États-Unis (Corn Belt), Brésil (safrinha : MT, PR, GO, MS), Argentine, Ukraine, Chine, UE | US : 1/07–15/08 ; Brésil safrinha : 1/03–31/05 ; Argentine : 1/01–28/02 ; Ukraine : 1/07–15/08 | Chaleur et sécheresse à la pollinisation |
| Soja | CBOT Soybeans (`ZS=F`) | États-Unis (Midwest), Brésil (MT, PR, RS, GO), Argentine, Paraguay | US : 15/07–15/09 ; Brésil : 1/12–28/02 ; Argentine : 1/02–31/03 | Sécheresse pendant le remplissage des gousses |
| Blé | CBOT SRW (`ZW=F`), KC HRW (`KE=F`) | Plaines US, Russie (sud, Volga, Sibérie), Ukraine, UE, Canada, Australie, Argentine, Kazakhstan | Blé d'hiver (hémisphère nord) : 1/04–30/06 ; blé de printemps : 15/06–31/07 ; Australie : 1/08–31/10 ; Argentine : 1/09–30/11 | Sécheresse et chaleur à l'épiaison |
| Café | ICE Arabica (`KC=F`) ; robusta ICE Europe (**À vérifier**, probablement absent de yfinance) | Brésil (Minas Gerais, São Paulo, Espírito Santo), Vietnam (Hauts Plateaux), Colombie, Indonésie | Arabica Brésil : floraison 1/09–30/11, gel 1/06–31/08 ; robusta Vietnam : floraison 1/01–31/03 | Gel, sécheresse à la floraison |
| Cacao | ICE US Cocoa (`CC=F`) ; cacao de Londres (**À vérifier**) | Côte d'Ivoire, Ghana, Cameroun, Nigeria, Équateur | Harmattan : 1/12–28/02 ; développement de la récolte principale : 1/05–30/09 | Sécheresse, et maladie quand l'humidité est excessive |
| Sucre | ICE Sugar n°11 (`SB=F`) | Brésil Centre-Sud, Inde (Maharashtra, Uttar Pradesh, Karnataka), Thaïlande, Chine (Guangxi), UE (betterave) | Brésil : croissance 1/10–31/03, gel 1/06–31/08 ; Inde : mousson 1/06–30/09 ; Thaïlande : 1/06–31/10 | Sécheresse, mousson faible, gel |

### 2.2 Extensions (après le prototype)
| Commodité | Contrat | Zones | Fenêtre par défaut | Risque | Statut des données de prix |
|---|---|---|---|---|---|
| Coton | ICE Cotton n°2 (`CT=F`) | Texas, Inde, Xinjiang, Brésil | 1/06–31/08 (Texas) | Sécheresse qui pousse à abandonner les parcelles | Connu, à revérifier |
| Huile de palme | Bursa Malaysia FCPO | Indonésie, Malaisie | Effet décalé de 6 à 12 mois | Sécheresse liée à El Niño | À vérifier (hors yfinance probable) |
| Jus d'orange | ICE FCOJ (`OJ=F`) | São Paulo, Floride | Floraison 1/09–31/10 ; ouragans 1/08–31/10 | Sécheresse, ouragans | Connu, à revérifier |
| Colza / canola | Euronext rapeseed, ICE canola | Canada, UE, Australie | Canada : 1/07–31/07 ; UE : 1/03–31/05 | Chaleur pendant la floraison | À vérifier |

Pour le jus d'orange, MapSPAM ne distingue pas les agrumes. Il faudra un masque régional manuel pour la ceinture d'agrumes de São Paulo et pour la Floride.

---

## 3. Architecture et arborescence

### 3.1 Flux
```
Sources ──> ingest/ ──> data/raw ──> features/ ──> data/processed ──> models/ ──> predictions
                                                                              │
                                    prix, COT ─────────────> signal/ <────────┘
                                                                │
                                         report/ (note LLM) <───┤
                                                                └──> app/ (Streamlit, données précalculées)
```

### 3.2 Pile technique (Python 3.11)
- Données : `pandas`, `pyarrow` (Parquet), `duckdb` (requêtes locales, optionnel), `xarray`, `rioxarray`, `geopandas`, `exactextract` ou `rasterstats` (statistiques par zone).
- Accès : `requests`, `requests-cache`, `openmeteo-requests` (client officiel Open-Meteo), `earthaccess` (NASA Earthdata), `pystac-client` + `planetary-computer` (option), `yfinance`, `cot_reports`.
- ML : `scikit-learn`, `lightgbm`, `shap`, `statsmodels`.
- LLM : client `mistralai` (ou client compatible OpenAI), configurable.
- Application : `streamlit`, `pydeck`, `plotly`.
- Outillage : `pydantic` (configuration), `typer` (ligne de commande), `pytest`, `ruff`, `uv` ou `pip-tools` (verrouillage des versions).

### 3.3 Arborescence du dépôt
```
harvestradar/
├── README.md                  # présentation, installation, démo en 3 commandes
├── SPEC.md                    # ce document
├── pyproject.toml
├── requirements.lock
├── Makefile
├── .env.example               # MISTRAL_API_KEY, EARTHDATA_USERNAME, EARTHDATA_PASSWORD, NASS_API_KEY
├── config/
│   ├── commodities.yaml       # périmètre, contrats, fenêtres, seuils, mode de pondération
│   └── settings.yaml          # chemins, années de base, paramètres de modèle et de backtest
├── data/
│   ├── raw/                   # ignoré par git
│   ├── interim/               # ignoré par git
│   ├── processed/             # ignoré par git, sauf petits extraits
│   ├── demo/                  # instantané précalculé versionné (< 50 Mo) pour la démo
│   └── manifest.json          # provenance : source, URL, date de collecte, licence, empreinte
├── src/harvestradar/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── geo/regions.py
│   ├── ingest/{openmeteo.py, chirps.py, ndvi.py, soil_moisture.py, spam.py, yields.py, wasde.py, prices.py, cot.py, enso.py}
│   ├── features/{climatology.py, stress.py, windows.py, aggregate.py}
│   ├── models/{yield_model.py, baselines.py, validation.py, explain.py}
│   ├── signal/{risk_index.py, backtest.py, events.py, wasde_test.py}
│   ├── report/{weekly_note.py, prompts/weekly_note_system.md}
│   └── app/streamlit_app.py
├── notebooks/                 # exploration uniquement : appellent src/, aucune logique propre
│   ├── 01_regions_et_poids.ipynb
│   ├── 02_donnees_meteo_ndvi.ipynb
│   ├── 03_modele_rendement.ipynb
│   ├── 04_indice_backtest.ipynb
│   └── 05_episodes.ipynb
├── tests/
└── docs/
    ├── user_guide.md
    ├── data_sources.md
    ├── prompts_log.md         # prompts des outils d'IA utilisés (exigence du cours)
    └── video_script.md
```

---

## 4. Sources de données

| Source | Variables | Accès | Licence | Résolution | Historique | Délai de publication | Statut |
|---|---|---|---|---|---|---|---|
| Open-Meteo Historical Weather API (ERA5, ERA5-Land) | tmax, tmin, précipitations, ET0, humidité du sol par couche | API REST sans clé, plusieurs coordonnées par appel | Gratuite pour un usage non commercial ; données CC BY 4.0 | 0,25° (ERA5), 0,1° (ERA5-Land) | 1940 → | Environ 5 jours | Connu, à revérifier (quotas d'appels, variables d'humidité du sol) |
| Copernicus CDS ERA5 / ERA5-Land | Mêmes variables, en masse | `cdsapi` avec compte gratuit | Licence Copernicus | 0,25° / 0,1° | 1940 → / 1950 → | Environ 5 jours (ERA5T) | Connu, à revérifier ; solution de repli si les quotas Open-Meteo bloquent |
| CHIRPS | Précipitations | Téléchargement HTTP (GeoTIFF / NetCDF) | Accès libre | 0,05° | 1981 → (50°S–50°N) | Version préliminaire en quelques jours, finale en quelques semaines | À vérifier (version en vigueur, licence exacte) ; optionnel |
| ESA CCI Soil Moisture | Humidité du sol | Téléchargement, compte gratuit | Licence ESA CCI | 0,25° | 1978 → | Mises à jour espacées (pas de temps réel) | Connu, à revérifier ; sert à l'historique |
| NASA SMAP (L3/L4) | Humidité du sol | `earthaccess`, compte Earthdata gratuit | Données NASA ouvertes | 9 km | 2015 → | Quelques jours | Connu, à revérifier ; optionnel |
| NDVI MODIS (MOD13C1 0,05° ou MOD13Q1 250 m) | NDVI, EVI | `earthaccess`, AppEEARS ou Planetary Computer | Données NASA ouvertes | 0,05° / 250 m, composites de 16 jours | 2000 → | Quelques jours | **Vérifié** : la NASA prévoit de cesser la collecte MODIS début 2027 (Terra) et vers septembre 2027 (Aqua) et recommande VIIRS |
| NDVI VIIRS (VNP13 / VJ113) | NDVI, EVI | `earthaccess`, AppEEARS | Données NASA ouvertes | 500 m – 0,05° | 2012 → | Quelques jours | Connu, à revérifier ; assure la continuité après MODIS |
| Sentinel-2 L2A | Réflectances 10 m (NDVI local) | Copernicus Data Space Ecosystem, compte gratuit | Licence Copernicus | 10 m, tous les 5 jours | 2017 → (L2A global) | 1 à 2 jours | Connu, à revérifier ; réservé aux zooms de la démo |
| MapSPAM 2020 | Production, surface, rendement par culture | Téléchargement (mapspam.info) | **CC-BY-4.0** | 10 km | Vers 2020 (moyennes 2019–2021), 46 cultures | Statique | **Vérifié** |
| MapSPAM 2010 | Idem | Téléchargement | Licence à vérifier | 10 km | Vers 2010 | Statique | À vérifier ; sert aux pondérations historiques |
| USDA Cropland Data Layer | Masque de cultures aux États-Unis | Téléchargement / CropScape | Domaine public (USDA) | 30 m | 2008 → (national) | Annuel | Connu, à revérifier ; optionnel |
| ESA WorldCereal | Masques maïs, céréales d'hiver et de printemps | Téléchargement | À vérifier | 10 m | 2021 | Statique | À vérifier ; optionnel |
| Calendriers culturaux (GEOGLAM, SAGE/Sacks 2010, USDA IPAD) | Semis, floraison, récolte | Téléchargement / pages web | Variable | Pays ou région | — | Statique | À vérifier ; servent à fixer les fenêtres par défaut du YAML |
| geoBoundaries ADM1 | Contours régionaux | Téléchargement / API | CC BY 4.0 | Admin-1 | — | Statique | Connu, à revérifier ; préféré à GADM pour la clarté de la licence |
| USDA FAS PSD | Production, surface, rendement par pays et campagne | Fichiers CSV complets ; API avec clé | Domaine public | Pays | 1960 → | Mensuel | À vérifier (clé API, format) |
| FAOSTAT (QCL) | Production, surface, rendement | API / CSV | CC BY 4.0 (à vérifier) | Pays | 1961 → | 1 à 2 ans | Connu, à revérifier ; solution de repli |
| CONAB | Production brésilienne par État et par campagne | Téléchargement | Données publiques | État | Variable | Mensuel | À vérifier |
| USDA NASS QuickStats | Rendements des États-Unis par État ou comté | API, clé gratuite | Domaine public | État / comté | Long | Annuel / hebdomadaire | Connu, à revérifier ; optionnel |
| WASDE (USDA) | Estimations mensuelles de production | Archives PDF ; fichiers lisibles par machine sur les années récentes | Domaine public | Pays / monde | Archives longues | Mensuel | À vérifier (profondeur des fichiers lisibles par machine) |
| yfinance | Futures en continu (échéance la plus proche) | Bibliothèque Python | Conditions Yahoo, usage personnel ou recherche | Quotidien | Variable selon le ticker | J+1 | Connu, à revérifier ; voir 9.4 sur les limites |
| CFTC COT (désagrégé) | Positionnement par catégorie d'intervenants | `cot_reports` / site CFTC | Domaine public | Hebdomadaire | 2006 → (désagrégé) | Vendredi (données du mardi) | Connu, à revérifier |
| NOAA ONI (ENSO) | Indice El Niño / La Niña | CSV | Domaine public | Mensuel | 1950 → | Mensuel | Connu, à revérifier |

Chaque téléchargement est inscrit dans `data/manifest.json` : source, URL, date de collecte, licence, empreinte SHA-256.

---

## 5. Pipeline détaillé

### 5.0 Conventions
- Pas de temps : la **décade** (périodes de 10 jours : 1–10, 11–20, 21–fin de mois) pour les variables agrégées, le jour pour la météo brute.
- Identifiant régional : `region_id = "<ISO3>-<code ADM1 geoBoundaries>"`.
- Chaque table porte une colonne `available_at` : date à laquelle la donnée était réellement publiée. Elle sert à éviter toute fuite d'information.

### 5.1 Configuration : `config.py`
- `load_config(path: str) -> Settings` : valide `commodities.yaml` et `settings.yaml` avec pydantic.
- Le YAML définit, pour chaque commodité : les codes de cultures MapSPAM, les tickers, la liste des pays, le seuil de couverture de la production (par défaut 0,90), les fenêtres critiques par pays ou région, les seuils de stress et le mode de pondération (`production` ou `exports`).

### 5.2 Régions et pondérations : `geo/regions.py`
- `build_regions(commodity: str, cfg: Settings) -> geopandas.GeoDataFrame`
  - Entrées : contours geoBoundaries ADM1 et raster MapSPAM de production pour la culture.
  - Traitement : somme de la production MapSPAM par ADM1, tri décroissant, conservation des régions jusqu'à couvrir `coverage` de la production mondiale.
  - Pondération : `weight = prod_r / Σ prod_r`. En mode `exports`, la part de chaque pays est remplacée par sa part dans les exportations mondiales (USDA PSD), puis redistribuée entre ses régions selon la production.
  - Sorties : `data/processed/regions_<commodity>.parquet` et `.gpkg`.
- `sample_points(regions, spam_raster, n_max: int = 5) -> DataFrame` : choisit jusqu'à 5 points par région, sur les pixels qui produisent le plus, chacun avec un poids. Ces points servent aux appels Open-Meteo.
- Pondérations historiques : MapSPAM 2010 pour les campagnes jusqu'à 2015, MapSPAM 2020 ensuite (paramètre `weights_switch_year`). Hypothèse à documenter.

### 5.3 Météo : `ingest/openmeteo.py`
- `fetch_daily(points: DataFrame, start: date, end: date, variables: list[str]) -> DataFrame`
  - Variables par défaut : `temperature_2m_max`, `temperature_2m_min`, `precipitation_sum`, `et0_fao_evapotranspiration`. L'humidité du sol (`soil_moisture_0_to_7cm`, `soil_moisture_7_to_28cm`) est à vérifier dans l'API historique.
  - Requêtes regroupées par lots de coordonnées, cache disque (`requests-cache`), reprises avec délai croissant en cas d'erreur.
  - Sortie : `weather_daily.parquet`, agrégé par région (moyenne pondérée par les points).
- Option `ingest/chirps.py` : `zonal_precip(regions, start, end)` pour remplacer les précipitations ERA5 par CHIRPS sous les tropiques (cacao, café).

### 5.4 Végétation : `ingest/ndvi.py`
- `fetch_ndvi(regions, start, end, sensor: Literal["MODIS", "VIIRS"]) -> DataFrame` : statistiques par zone sur les composites de 16 jours, masquées par les pixels cultivés MapSPAM et filtrées par les drapeaux de qualité.
- `harmonize_modis_viirs(df) -> DataFrame` : régression linéaire par région sur la période où les deux capteurs existent, pour obtenir une série continue après l'arrêt de MODIS.
- Sortie : `ndvi_16d.parquet`.
- Limite : sous les tropiques, la couverture nuageuse dégrade le NDVI (cacao, café). Il faut garder `frac_valid` et pondérer en conséquence.

### 5.5 Humidité du sol : `ingest/soil_moisture.py`
- Priorité : humidité du sol ERA5-Land via Open-Meteo si l'API historique la fournit. Sinon ESA CCI pour l'historique et SMAP pour la période récente.
- Sortie : `soil_moisture_daily.parquet`.

### 5.6 Variables de stress : `features/`
- `climatology.py`
  - `compute_climatology(df, base: tuple[int, int] = (2001, 2020), mode: Literal["fixed", "expanding"]) -> DataFrame` : moyenne et écart-type par région et par décade.
  - Le mode `fixed` sert à la carte. Le mode `expanding` (années passées seulement, au moins 10 ans) sert au modèle et au backtest, pour éviter la fuite d'information.
- `stress.py`
  - `spi(precip, window_days: int) -> Series` : indice de précipitations standardisé sur 30 et 90 jours.
  - `heat_degree_days(tmax, threshold_c: float) -> Series` : degrés-jours au-dessus du seuil. Seuils par défaut tirés de Schlenker & Roberts (2009) : maïs 29 °C, soja 30 °C, coton 32 °C. Blé 32 °C, à valider.
  - `frost_days(tmin, threshold_c: float = 2.0) -> Series` : café et sucre au Brésil, seuil à valider.
  - `water_deficit(precip, et0) -> Series` : bilan précipitations − ET0 cumulé.
  - `sm_percentile(sm) -> Series` : rang centile de l'humidité du sol par rapport à la climatologie.
  - `ndvi_anomaly(ndvi) -> Series` : écart à la normale en écarts-types.
- `windows.py`
  - `in_critical_window(dates, window_spec) -> Series[bool]` : gère les fenêtres à cheval sur deux années (par exemple du 1/12 au 28/02).
- `aggregate.py`
  - `to_dekad(daily_df) -> DataFrame`
  - `to_country_season(dekad_df, regions, as_of: date) -> DataFrame` : agrège les variables sur les fenêtres critiques, pondérées par région, en n'utilisant que les données publiées au plus tard à la date `as_of`.
- Sorties : `features_dekad.parquet`, `features_season.parquet`.

### 5.7 Cible : `ingest/yields.py`
- `load_psd(commodity)`, `load_faostat(commodity)`, `load_conab(commodity)`.
- `yield_anomaly(df) -> DataFrame` : `anom = (yield − trend) / trend`, où la tendance est ajustée **uniquement sur les années antérieures** (linéaire ou LOESS, au moins 8 ans).
- Correspondance entre l'année civile et la campagne de commercialisation de chaque pays et culture, déclarée dans le YAML.
- Sortie : `targets.parquet`.

### 5.8 Modèle de rendement : `models/`
- `yield_model.py`
  - `train(features_season, targets, cfg) -> Model` : LightGBM, un modèle commun à toutes les commodités avec la commodité et le pays comme variables. Une variante par commodité est comparée.
  - Paramètres par défaut, à ajuster : `num_leaves = 15`, `min_data_in_leaf = 10`, `learning_rate = 0.05`, `n_estimators = 300`, `feature_fraction = 0.8`, `seed = 42`.
  - Contraintes monotones possibles (plus de degrés-jours de chaleur → rendement plus faible), activables dans le YAML.
  - `predict(model, features, as_of) -> DataFrame` avec un intervalle (régression quantile 10 % / 90 %).
- `baselines.py` : écart nul (la tendance seule), régression linéaire sur 3 variables, persistance (écart de l'an dernier).
- `validation.py` : `rolling_origin_cv(first_test_year = 2012, last_test_year = 2025)`. Pour chaque année t, entraînement sur les années ≤ t − 1 et prédiction de t, à plusieurs dates `as_of` dans la saison (fin de chaque mois de la fenêtre).
  - Métriques : RMSE, MAE, Spearman, exactitude du signe de l'écart, gain de score par rapport à chaque baseline.
- `explain.py` : `shap_by_prediction(model, X) -> DataFrame` pour les contributions par variable, réparties ensuite par région au prorata des poids.
- Sortie : `predictions.parquet`, rapport `reports/model_eval.md`. Les résultats y figurent tels qu'ils sont, y compris si le modèle ne bat pas les baselines.

### 5.9 Indice de risque : `signal/risk_index.py`
- `build_risk_index(predictions, shares, cfg) -> DataFrame`
  - Écart de production mondial attendu : `ΔP_c(t) = Σ_pays part_pays × anom_pred_pays(t)`, où `part_pays` est la part dans la production (ou les exportations) mondiale, connue à la date t (USDA PSD, décalée).
  - `risk_z = −standardize(ΔP_c)`, normalisé par écart de calendrier comparable et avec un historique glissant. Un `risk_z` positif signale un risque d'offre plus élevé.
  - Contributions par pays et par région : JSON des 5 principales contributions.
- Mise à jour hebdomadaire, chaque vendredi, à partir des données publiées au plus tard le jeudi.
- Sortie : `risk_index.parquet`.

---

## 6. Schémas des tables (Parquet)

| Table | Clés | Colonnes (type) |
|---|---|---|
| `regions_<c>` | `region_id` | `commodity` (str), `country_iso3` (str), `adm1_name` (str), `prod_t` (float), `weight` (float), `geometry` (GeoPackage) |
| `sample_points` | `region_id`, `point_id` | `lat` (float), `lon` (float), `point_weight` (float) |
| `weather_daily` | `region_id`, `date` | `tmax_c`, `tmin_c`, `precip_mm`, `et0_mm`, `sm_0_7`, `sm_7_28` (float, nullable), `source` (str), `available_at` (date) |
| `ndvi_16d` | `region_id`, `date` | `ndvi` (float), `frac_valid` (float), `sensor` (str), `available_at` (date) |
| `features_dekad` | `commodity`, `region_id`, `dekad`, `feature` | `value` (float), `z` (float), `in_window` (bool), `available_at` (date) |
| `features_season` | `commodity`, `country_iso3`, `season`, `as_of` | une colonne par variable (float), `coverage` (float) |
| `targets` | `commodity`, `country_iso3`, `season` | `yield_t_ha`, `trend_t_ha`, `yield_anom` (float), `source` (str) |
| `predictions` | `commodity`, `country_iso3`, `season`, `as_of` | `pred_anom`, `pred_lo`, `pred_hi` (float), `model_version` (str) |
| `risk_index` | `commodity`, `date` | `risk_z`, `delta_prod_pct` (float), `contributors` (str JSON) |
| `prices` | `commodity`, `date` | `ticker` (str), `close` (float), `ret_1d` (float), `roll_flag` (bool) |
| `cot` | `commodity`, `date` | `mm_net` (float), `mm_net_z` (float) |
| `backtest_daily` | `commodity`, `date` | `position` (int), `ret_gross`, `cost`, `ret_net` (float) |
| `notes` | `commodity`, `week` | `markdown` (str), `numbers_ok` (bool), `model` (str) |

---

## 7. Configuration par défaut (extrait de `config/commodities.yaml`)

```yaml
# Valeurs par défaut à valider avec GEOGLAM, SAGE et USDA IPAD
maize:
  label: "Maïs"
  spam_crops: ["maiz"]
  tickers: {cbot: "ZC=F"}
  coverage: 0.90
  weight_mode: production        # production | exports
  thresholds: {heat_c: 29.0}
  windows:
    USA: [{start: "07-01", end: "08-15", stage: "pollinisation"}]
    BRA: [{start: "03-01", end: "05-31", stage: "safrinha"}]
    ARG: [{start: "01-01", end: "02-28", stage: "floraison"}]
    UKR: [{start: "07-01", end: "08-15", stage: "pollinisation"}]
coffee:
  label: "Café arabica"
  spam_crops: ["acof"]
  tickers: {ice_us: "KC=F"}
  coverage: 0.90
  weight_mode: exports
  thresholds: {frost_c: 2.0}
  windows:
    BRA: [{start: "09-01", end: "11-30", stage: "floraison"},
          {start: "06-01", end: "08-31", stage: "risque_gel"}]
    COL: [{start: "03-01", end: "05-31", stage: "floraison"}]
```

`config/settings.yaml` contient les années de base de la climatologie (2001, 2020), la première année de test (2012), le paramètre `weights_switch_year` (2016), les paramètres du modèle, et les paramètres de backtest (§ 9.3). Les codes de cultures MapSPAM (`maiz`, `acof`…) sont **À vérifier** dans la documentation de SPAM 2020.

---

## 8. Validation sans fuite d'information

| Risque de fuite | Mesure |
|---|---|
| Tendance de rendement estimée avec des années futures | Tendance ajustée sur les années strictement antérieures |
| Climatologie calculée avec des années futures | Climatologie `expanding` pour le modèle et le backtest |
| Données utilisées avant leur publication | Colonne `available_at` et filtre `as_of` dans toutes les agrégations |
| Pondérations de production postérieures | MapSPAM 2010 jusqu'en 2015, puis MapSPAM 2020 ; hypothèse documentée |
| Hyperparamètres choisis sur la période de test | Hyperparamètres fixés sur 2001–2011, puis gelés |
| Signal exécuté au même cours que son calcul | Position appliquée à la clôture suivante (t + 1) |

Toutes les baselines et métriques sont reportées dans `reports/model_eval.md`, sans sélection a posteriori.

---

## 9. Signal, backtest et tests

### 9.1 Signal : `signal/backtest.py`
- `signal_t = Δ4 semaines(risk_z)`.
- Règle par défaut, pré-enregistrée : `position = +1` si `signal_t > θ` et qu'au moins une fenêtre critique majeure est ouverte ; `−1` si `signal_t < −θ` (variante acheteuse seulement : 0) ; `0` sinon. `θ = 0.5` par défaut.
- Fréquence hebdomadaire : calcul le vendredi, exécution à la clôture du lundi suivant.

### 9.2 Prix et roll : `ingest/prices.py`
- `load_futures(ticker, start, end) -> DataFrame` via yfinance (série continue de l'échéance la plus proche).
- `detect_rolls(df) -> Series[bool]` : repère les sauts aux dates de roll attendues (calendrier des échéances dans le YAML). Le rendement de ces jours est neutralisé (NaN).
- Limite : la série continue ne reflète pas exactement le rendement d'une stratégie qui change d'échéance. **À vérifier** : source gratuite de contrats individuels. Sinon, la limite est documentée.

### 9.3 Protocole de backtest
- Paramètres : `cost_bps_per_trade` (5 par défaut, paramétrable, à justifier), `slippage_bps` (0 par défaut), période 2006 → présent selon la disponibilité des prix.
- Points de comparaison : achat et conservation, position acheteuse pendant toutes les fenêtres critiques, signal aléatoire (1 000 permutations).
- Métriques : rendement annualisé, volatilité, Sharpe, Sortino, perte maximale, taux de réussite, rotation, t-stat Newey-West, p-valeur de permutation.
- Robustesse : grille réduite sur θ ∈ {0,25 ; 0,5 ; 1,0} et Δ ∈ {2, 4, 8} semaines, publiée en entier pour éviter la sélection a posteriori.
- Avertissement dans le rapport et dans l'application : résultat de recherche, pas une recommandation d'investissement.

### 9.4 Études d'événements : `signal/events.py`
- Épisodes : sécheresse américaine 2012 (maïs, soja ; mai–septembre 2012), gel brésilien de juillet 2021 (café ; juin–septembre 2021), cacao 2023–2024 (juillet 2023 – décembre 2024).
- Mesures : trajectoire de `risk_z` et du prix, corrélation croisée avec décalage (−8 à +8 semaines), date du premier franchissement de seuil par rapport au mouvement de prix. Aucun résultat n'est supposé à l'avance.

### 9.5 Test WASDE : `signal/wasde_test.py`
- Champ : maïs, soja, blé, plus le sucre si les données le permettent. Le café et le cacao ne sont pas couverts par le WASDE mensuel.
- Pour chaque publication : révision de la production (mois m contre m − 1), pour les États-Unis et le monde.
- Test : la variation de `risk_z` sur les 30 jours précédant la publication prédit-elle le signe de la révision ? Mesures : taux de réussite comparé à 50 %, régression logistique, test binomial.
- Disponibilité des archives WASDE lisibles par machine : **À vérifier**. À défaut, l'extraction se limite aux années disponibles.

---

## 10. Note hebdomadaire LLM : `report/weekly_note.py`
- `build_payload(commodity, week) -> dict` : niveau et variation de `risk_z`, 5 principales régions contributrices avec leurs écarts à la normale, fenêtres ouvertes, variation du prix sur 4 semaines, positionnement COT (`mm_net_z`), liste des sources et dates.
- `generate_note(payload, llm) -> str` : prompt système dans `prompts/weekly_note_system.md`.
  - Utiliser uniquement les chiffres du payload et citer la source et la date de chaque chiffre.
  - Structure : titre, ce qui a changé, régions en cause, à surveiller.
  - 150 à 250 mots, en français ou en anglais, sans recommandation d'investissement.
- `check_numbers(note, payload) -> bool` : extrait tous les nombres de la note et vérifie qu'ils existent dans le payload (tolérance d'arrondi). En cas d'échec : 2 nouvelles tentatives, puis un modèle de note déterministe.
- Fournisseur : API Mistral (offre gratuite Experiment, à réserver aux données publiques) ou modèle open source via Hugging Face. Fournisseur et modèle sont configurables dans `settings.yaml`.

---

## 11. Application et parcours de démo : `app/streamlit_app.py`
- Déploiement : Hugging Face Spaces, avec uniquement les données précalculées de `data/demo/`. Le mode de déploiement de Streamlit sur Spaces (SDK natif ou modèle Docker) est **À vérifier**.
- Pages :
  1. **Carte mondiale** : carte choroplèthe des régions ADM1 (pydeck) colorées selon le stress, curseur temporel et bouton de lecture, filtre par commodité.
  2. **Commodité** : `risk_z` et prix sur un même graphique, contributions par pays et région (barres SHAP), frise des fenêtres critiques.
  3. **Rejeu d'épisodes** : 2012, 2021 et 2023–2024 avec lecture animée et commentaire automatique.
  4. **Note hebdomadaire** : dernière note et archives.
  5. **Méthode et sources** : rappel du pipeline, des limites, des licences et de l'avertissement.
- Exigences : chargement initial en moins de 10 s sur le CPU de base de Spaces, aucune requête externe en mode démo.
- Parcours de démo vidéo (5 min ± 10 %) : accroche (prix du cacao ou du café), problème, nom et promesse, carte mondiale, zoom sur une commodité, rejeu d'un épisode, note hebdomadaire, valeur si l'outil se répandait, briques utilisées, reproductibilité, limites.

---

## 12. Reproductibilité
- Versions verrouillées (`requirements.lock`), Python 3.11, `seed = 42` partout (numpy, LightGBM, permutations).
- Commandes `make` :
  - `make setup` : installation et pré-commit.
  - `make demo` : lance l'application sur `data/demo/`, sans réseau.
  - `make data` : télécharge toutes les sources (comptes gratuits requis : Earthdata, CDS si utilisé).
  - `make features`, `make train`, `make index`, `make backtest`, `make notes` : étapes du pipeline.
  - `make all` : enchaîne l'ensemble.
  - `make test` : tests unitaires sur données synthétiques.
- Ligne de commande (`typer`) : `harvestradar <groupe> <commande> --commodity maize --start 2000-01-01 --end 2026-11-13`.
- Secrets dans `.env` (jamais versionné). `data/manifest.json` assure la traçabilité.
- Kaggle : publier l'instantané `data/demo` comme Kaggle Dataset et un notebook public qui reproduit les graphiques. GitHub : code. Hugging Face : Space de démo.

---

## 13. Plan de développement et critères d'acceptation

| Jalon | Contenu | Critères d'acceptation testables |
|---|---|---|
| M0 – Socle | Dépôt, configuration, ligne de commande, CI | `make test` passe ; `harvestradar --help` liste les commandes ; la configuration est validée par pydantic |
| M1 – Régions | Régions ADM1 et pondérations pour les 6 commodités | Couverture ≥ 0,90 de la production MapSPAM par commodité ; poids sommant à 1 (± 1e-6) ; carte exportée |
| M2 – Données | Météo quotidienne, NDVI et humidité du sol 2000 → présent | Moins de 2 % de valeurs manquantes par région ; `available_at` renseigné ; manifeste complet |
| M3 – Variables | Variables de stress, fenêtres, agrégations | Tests unitaires (SPI synthétique, fenêtre à cheval sur deux années, poids) ; contrôle visuel : anomalie de chaleur de juillet 2012 sur le Corn Belt nettement positive |
| M4 – Modèle | Rendement, validation rolling origin, SHAP | Rapport `model_eval.md` avec les 3 baselines, toutes les métriques, et une conclusion honnête |
| M5 – Indice et signal | `risk_z`, backtest, études d'événements, test WASDE | Séries 2001 → présent pour les 6 commodités ; rapport de backtest avec coûts et permutations ; graphiques des 3 épisodes |
| M6 – Note LLM | Payload, génération, contrôle des chiffres | `check_numbers` passe sur 10 notes consécutives ; repli déterministe testé |
| M7 – Application | Streamlit et Space publique | Les 5 pages fonctionnent hors ligne ; chargement en moins de 10 s ; guide utilisateur |
| M8 – Livrables | Vidéo, citations, prompts | Checklist du § 15 entièrement cochée |

---

## 14. Risques et limites
- **Efficience du marché** : la météo est une information publique et rapide. Le signal peut être déjà intégré dans les prix. La valeur de l'outil tient aussi à la synthèse et à la transparence.
- **Peu d'observations** : environ 25 campagnes par pays. Risque de surapprentissage, réduit par un modèle commun aux commodités, la régularisation et des variables peu nombreuses.
- **Approximations spatiales** : points d'échantillonnage, niveau ADM1, pondérations quasi statiques (MapSPAM 2010 et 2020).
- **Calendriers variables** : retards de semis, double récolte. Les fenêtres fixes sont une approximation.
- **Continuité satellite** : fin de MODIS en 2027 (vérifié), d'où l'harmonisation avec VIIRS. Nuages sous les tropiques.
- **Prix** : artefacts de la série continue yfinance, robusta, cacao de Londres et FCPO probablement indisponibles (à vérifier).
- **Licences** : certaines sources sont limitées à un usage non commercial (Open-Meteo gratuit, conditions Yahoo). Une exploitation commerciale demanderait une revue des licences.
- **LLM** : risque d'hallucination, encadré par `check_numbers` et le repli déterministe.
- **Usage** : outil d'analyse uniquement, pas de recommandation d'investissement.

---

## 15. Checklist des livrables du cours (Advanced AI Algorithms, ESSEC)
- [ ] Nom accrocheur et objectif expliqués dans la démo (HarvestRadar)
- [ ] Valeur créée si l'outil se répandait, expliquée et illustrée
- [ ] Éléments au-delà du contenu du cours identifiés (§ 1.5) et confrontés au syllabus
- [ ] Application reproductible à partir du code (`make demo`, `make all`)
- [ ] Briques Hugging Face, GitHub et Kaggle utilisées et citées dans le README
- [ ] Données fournies (`data/demo`) ou scripts de téléchargement, avec `manifest.json`
- [ ] Guide utilisateur clair (`docs/user_guide.md`)
- [ ] Packages et données cités, avec leurs licences
- [ ] Prompts des outils d'IA utilisés consignés dans `docs/prompts_log.md`
- [ ] Vidéo de démo de 5 minutes maximum (± 10 %), structurée et professionnelle

---

## 16. Consignes pour Claude Code
1. Avancer jalon par jalon (§ 13). Écrire les tests de chaque jalon et vérifier ses critères d'acceptation avant de passer au suivant.
2. Ne jamais inventer de données ni de résultat. Si une source est inaccessible ou si sa licence est incompatible, s'arrêter, le signaler et proposer une alternative du § 4.
3. Garder toute la logique dans `src/harvestradar/`. Les notebooks ne font qu'appeler ces fonctions.
4. Ne versionner ni secrets ni données brutes volumineuses. Seul `data/demo/` est versionné.
5. Respecter `available_at` et `as_of` dans toute agrégation, et ajouter un test qui échoue en cas de fuite.
6. Consigner dans `docs/prompts_log.md` chaque prompt d'IA utilisé pour produire du code ou du contenu (exigence du cours).
7. Mettre à jour le statut des sources (Vérifié, À vérifier) dans `docs/data_sources.md` à mesure des contrôles.
