# ClearRoute corrections — 20 November 2026

## Implemented and verified
- Event timeline inputs now keep draft values until Apply. Native date input events are handled consistently, so entering a date no longer triggers a load that destroys the field. Invalid/reversed ranges receive clear errors. Controls remain visible during requests.
- City/corridor changes clear stale trends, use scoped API requests and remount the hourly chart for the new scope. Added 24-hour numeric values, scope labels and sample counts. The benchmark genuinely has similar daily shapes: Delhi 00:00/09:00/19:00 = 5.27/48.88/60.68%; Mumbai = 3.10/45.49/57.20%. Values were checked against Gold for all five cities and 25 corridors. No artificial variation was added.
- Corridor weekday/month selectors now filter actual query results, including speeds, descriptive statistics, hourly/weekly/monthly series and rain comparisons. Empty bins stay null.
- Replaced the huge event provenance metric with a compact label and explanatory text. Reset event windows when filters/city change. Corrected percentage-point units and removed missing-weather zero substitutes.
- Retrieved 33,000 hourly ERA5 reanalysis records for five cities, April–December 2019, directly from Open-Meteo. Committed the compressed response, normalized Parquet and request/checksum manifest under data/external/era5_2019. Source: https://open-meteo.com/en/docs/historical-weather-api . Reanalysis is modeled historical weather, not a road sensor observation.
- The launcher now builds data/clearroute_analytics_v2.db without overwriting the legacy application or earlier analytical stores. It uses the pinned traffic Gold plus timestamp-matched retrieved weather. Checksums are checked before import/startup. Windows database publication now uses a no-overwrite rename because hard-link publication was denied by the filesystem.
- Added /api/data/readiness and a compact expandable source-status panel showing actual required file availability, database counts and all four loaded models.

## Executed validation
- Backend + Power BI suite: 89 passed.
- Full backend/bigdata/Power BI suite: 93 passed, 1 failed. The preserved, partially present legacy Bronze weather CSV has no provenance_metadata.json; the stricter legacy raw-input test still correctly fails. No fake provenance was created to pass it.
- Production Vite build passed.
- Four-model comparison succeeded with identical features in all five cities using real loaded artifacts. Independent evaluation of all four artifacts on 24,750 held-out benchmark rows reproduced stored metrics. Historical Mean MAE/RMSE/R2: 2.674682/3.404825/0.972220; Ridge: 8.645899/11.117879/0.703801; RF: 4.687900/6.153633/0.909259; XGBoost: 2.726790/3.464450/0.971239.
- Browser verified Delhi/Mumbai overview values and the event date range: Mumbai October 2019 filters four catalog entries to the single October event, preserving both date fields. Combined corridor weekday/month filtering was also checked.
- Active new database: 165,000 traffic rows, 33,000 retrieved weather rows, 25 corridors, 21 event annotations. Required runtime datasets/model artifacts are present.
- Original data/clearroute_app.db SHA-256 remains 9b3661f8b430f26f5ab6c20b2debf25db39d14bf502a0f63597752062607a642.

## What cannot honestly be declared verified
The repository traffic is a generated benchmark, not genuine Uber Movement observations. Downloading actual weather cannot make the traffic real or establish forecasting accuracy. Existing trained-model metrics still describe their original Gold training/test benchmark; models were not retrained on the new weather archive. Scenario inference remains functional and user inputs remain hypothetical.

Event city-day annotations exist, but exact duration, independently sourced venue/attendance and causal impacts are unavailable. These are not invented. The old raw production pipeline still requires authentic traffic provenance and complete risk/event source fields. The application can run from pinned Gold and the new weather archive; a fully genuine production rebuild remains blocked by those external source gaps.

Delhi's retrieved archive has no rainfall >=15 mm/hour (maximum 9.7). A heavy-rain surge cannot be computed there; the interface now gives the reason and sample coverage. Missing groups must not be turned into fabricated zero/effect values.

## Delivery
Changes remain on fix/clearroute-evaluation-ready; no new branch or main merge. Live corrected test app: http://127.0.0.1:5181/ (backend 8011). Final commit and CI results are in the accompanying delivery JSON.
