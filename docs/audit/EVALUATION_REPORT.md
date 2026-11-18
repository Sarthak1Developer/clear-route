# ClearRoute evaluation report — 18 November 2026

## A. Executive result

VERIFIED WORKING: reconciled Gold-backed application database; independent statistics for five cities and 25 corridors; automatic four-model scenario comparison; missing-data null handling; backend contracts and frontend build; regenerated Power BI exports. FAILED: local raw-data provenance validation (missing weather metadata). DATA UNAVAILABLE: required infrastructure/event context for raw-pipeline regeneration. NOT VERIFIED: real-world forecasting, causal weather/event effects, external deployment and Power BI Desktop rendering.

## B. Changes, branch reconciliation and root cause

The legacy application database held 6,000 sparse samples while Gold held 165,000 hourly records. Existing seeding stopped once traffic rows existed, leaving stale, almost-identical city/corridor means around 36.5%. A new database builder clones dimension metadata into a separate database, imports Gold traffic and city-hour weather, preserves event annotations, validates keys/targets and records source hashes. Existing database files are never overwritten. The launcher selects this reconciled database. Missing datasets and model failures remain explicit.

PR #4 already merged CI work into main at 22ac084. This branch starts there and preserves the previous audit commits through merge a8792b3. Thus validation and audit fixes are consolidated without duplicating or cherry-picking the already-merged CI changes. No existing branch was deleted; main was not modified.

Gold -> validated new SQLite database -> repository/statistics services -> API -> React pages and CSV exports. Gold -> existing preprocessing/model artifacts -> chronological evaluation and scenario inference. Gold + evaluation artifacts -> Power BI exports. Raw Bronze -> Silver -> Gold regeneration is a separate blocked path.

## C. Dataset audit

31 local CSV/Parquet datasets were read. The companion JSON contains actual schemas, types, units, missing counts, duplicates, coverage and SHA-256 hashes. Source attribution is not independent proof of provenance. Gold has 165,000 rows, 40 columns, 25 corridors in five cities, 24 hours per day, 1 April–31 December 2019. Traffic target is clip((free-flow speed − observed speed)/free-flow speed, 0, 1) × 100. Weather joins use city + timestamp, not arbitrary current values.

| File | Rows | Columns | Missing cells | Duplicates | Status |
|---|---:|---:|---:|---:|---|
| data/bronze/events/raw_events_2019_historical.csv | 15 | 7 | 0 | 0 | Read verified; source NOT VERIFIED |
| data/bronze/events/raw_events_2026_future.csv | 5 | 7 | 0 | 0 | Read verified; source NOT VERIFIED |
| data/bronze/osm_infrastructure/raw_osm_road_segments.csv | 25 | 12 | 0 | 0 | Read verified; source NOT VERIFIED |
| data/bronze/uber_movement/raw_uber_movement_traffic.csv | 6000 | 8 | 0 | 0 | Read verified; source NOT VERIFIED |
| data/bronze/weather_era5/raw_weather_era5_hourly.csv | 1200 | 9 | 0 | 0 | Read verified; source NOT VERIFIED |
| data/clearroute_analytics.db | ? | ? | 0 | ? | Read verified; source NOT VERIFIED |
| data/clearroute_app.db | ? | ? | 0 | ? | Read verified; source NOT VERIFIED |
| data/gold/master_congestion/gold_master_congestion.csv | 165000 | 40 | 324960 | 0 | Read verified; source NOT VERIFIED |
| data/gold/master_congestion/gold_master_congestion.parquet | 165000 | 40 | 0 | 0 | Read verified; source NOT VERIFIED |
| data/silver/silver_traffic_cleaned.csv | 6000 | 23 | 0 | 0 | Read verified; source NOT VERIFIED |
| data/silver/silver_traffic_cleaned.parquet | 6000 | 23 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/city_congestion_summary.csv | 5 | 7 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/corridor_predictive_risk.csv | 25 | 15 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/dim_date.csv | 275 | 11 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/dim_event.csv | 21 | 12 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/dim_location.csv | 25 | 11 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/dim_time.csv | 24 | 6 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/dim_weather_category.csv | 4 | 5 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/event_impact_summary.csv | 5 | 5 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/fact_congestion_hourly.csv | 165000 | 24 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/gold_master_sample.csv | 1000 | 45 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/hourly_congestion_summary.csv | 48 | 6 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/location_congestion_summary.csv | 25 | 11 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/model_actual_vs_predicted.csv | 24750 | 17 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/model_feature_importance.csv | 31 | 7 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/model_performance_summary.csv | 4 | 8 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/model_subgroup_performance.csv | 60 | 8 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/refresh_metadata.csv | 1 | 15 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/shap_category_drivers.csv | 5 | 4 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/weather_impact_summary.csv | 4 | 5 | 0 | 0 | Read verified; source NOT VERIFIED |
| powerbi/exports/weather_temperature_summary.csv | 4 | 4 | 0 | 0 | Read verified; source NOT VERIFIED |

The legacy Bronze/Silver samples and current Gold differ in coverage. Silver execution rejects missing accident_risk_score. Gold execution after that fails because no new Silver output exists. Event context also lacks intensity/confidence fields required for a reproducible rebuild. Weather provenance_metadata.json is absent. No fields or observations were fabricated to pass these gates.

## D. Model audit

VERIFIED WORKING: loaded all four repository artifacts and preprocessor.joblib, transformed the actual chronological test partition and recomputed metrics on 24,750 rows. Split uses existing preprocessing code (70/15/15). Categorical encoding/scaling and feature selection use the saved preprocessor; Historical Mean uses its own city/corridor/hour lookup. Source feature groups include city, corridor, time, physical road context, weather and event scenario fields; exact feature keys are in inference API evidence. Gold lag-feature/training provenance and independent sensor validity remain NOT VERIFIED. No retraining was claimed.

| Artifact | MAE | RMSE | R² | First held-out prediction |
|---|---:|---:|---:|---:|
| model_historical_mean.joblib | 2.674682 | 3.404825 | 0.972220 | 70.785714 |
| model_linear_regression.joblib | 8.645899 | 11.117879 | 0.703801 | 58.276565 |
| model_random_forest.joblib | 4.687900 | 6.153633 | 0.909259 | 62.078573 |
| model_xgboost.joblib | 2.726790 | 3.464450 | 0.971239 | 72.478302 |

Historical Mean has no feature attribution and reports explanation unavailable. Ridge reports actual linear contributions when unclipped; RF and XGBoost use model-specific TreeExplainers. Additivity was checked. Pickled XGBoost emits a cross-version portability warning; current inference is tested but future dependency compatibility is not guaranteed.

## E. Actual prediction comparison

The browser scenario Delhi / DEL_001 / 2026-11-18 18:00 IST, hypothetical 0 mm rainfall, 28°C, 65% humidity, 12 km/h wind and no event produced XGBoost 54.6%, RF 46.5%, Ridge 38.1%, Historical Mean 66.6%; 4/4 succeeded. These are benchmark model outputs, not verified forecasts. A separate HTTP scenario with full input features/results is in ClearRoute-evaluation-http.json. The regression suite checks identical four-model input payloads, real partial failure when an artifact is absent, and 404 for an invalid corridor.

## F. Backend and API

VERIFIED WORKING: 60 real HTTP requests covered health, overview, cities, locations/history/trends, models/performance/explainability, weather/history/impact, events/impact, records/governance, six report CSVs, all four prediction/persisted explanation paths and comparison. Expected unknown-resource/validation errors were checked. New database regression checks independently reconcile every city and all 25 corridor means/counts/min/max to Gold; date filters are inclusive; empty groups return null; event windows contain actual observations and matched weekday baselines.

Final local automated suite: 89 passed, 1 failed. Failure: test_bronze_layer_outputs, absent weather provenance metadata in partially present local raw inputs. The entire optional raw dataset may be absent in clean CI; partial datasets never silently skip. Production frontend build passed.

## G. Frontend

VERIFIED WORKING: Overview and five city views show distinct Gold-derived means: Delhi 24.68%, Mumbai 21.76%, Bengaluru 25.29%, Hyderabad 24.83%, Kolkata 23.69%. Location Analytics shows 6,600 observations per corridor with daily/hourly/weekly/monthly and descriptive statistics. Prediction defaults to one action for four model cards and comparison. Weather and Event pages had a filter mount/reset loading loop; fixed and retested. Data Explorer retrieves 165,000 records, supports dates/sort/pagination/current-page export. Reports uses response-checked CSV downloads. Model Performance shows actual stored benchmark metrics. Settings reports the active queried database count and no unused single-model selector. Browser evidence and screenshots accompany this report. Corridor layout checks at 390px and 768px showed no document horizontal overflow. Date filtering was verified through backend tests; browser date-input automation did not reliably update the field, so the date control itself remains NOT VERIFIED.

Unexpected horizontal colored line: investigation in the current DOM/screenshots found intentional panel/header/chart borders and the amber provenance notice. The original unexplained artifact was not reproduced; its specific cause/fix is NOT VERIFIED. Do not claim it was fixed.

## H. Power BI

VERIFIED WORKING: regenerated exports into an isolated output directory from current Gold and artifacts. All six checks passed: completeness, star-schema primary/foreign keys, Gold fact/mean reconciliation, metrics reconciliation, actual-vs-predicted integrity, refresh metadata. Export covers 165,000 facts and 24,750 held-out predictions. Power BI Desktop report opening/refresh/rendering is NOT VERIFIED.

## I. Remaining limitations and security

External observational provenance, full raw-data regeneration, future forecast validity and event causation are NOT VERIFIED or DATA UNAVAILABLE as described above. Event records lack independently verified venue/duration/attendance, so city/day annotations are not precise within-event measurements. Live weather provider was disabled during deterministic verification; current live connectivity is NOT VERIFIED. Deployment configuration for Render/Vercel is supplied; no external deployment was performed. Docker Compose references missing Dockerfiles.

Python installed dependency audit after upgrading pip/setuptools: no known vulnerabilities found. npm audit reports 11 high development dependency advisories (picomatch transitive chain); no clean npm security claim. Review before production. The user database matches its backup SHA-256 161b8fd08e57db027c209ec0043b95b3e77f2e8a78c9dba6ff551c91b9705318. Credentials, derived databases, generated raw inputs and node_modules are excluded from commits.

## J. GitHub delivery

Branch: fix/clearroute-evaluation-ready. Delivery commit, PR URL and final CI status will be recorded in the companion GitHub delivery file after publication. main will not be merged.
