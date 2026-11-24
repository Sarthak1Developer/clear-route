# ClearRoute final engineering audit

Audit executed 17–18 November 2026, Asia/Kolkata. Repository: `D:\Sarthak Projects\Clear-Route`. Branch: `fix/clearroute-full-audit`.

**Outcome: substantial verified corrections, with explicit data and authentication blockers. This is not a production-readiness certification.** Real congestion validity cannot be established from generated traffic. Missing provenance and incompatible historical pipeline inputs prevent a successful full ingestion run. The original database and model artifacts were preserved.

Status vocabulary: **Verified** = executed successfully; **Inspected** = source/configuration examined without complete runtime validation; **Blocked** = an identified dependency/data/access failure; **Not verified** = not executed or insufficient evidence. Passing tests do not establish real-world predictive validity.

## A. Project architecture inspected

React 18 + Vite + Tailwind + Recharts + Leaflet frontend with ten tab-based views. Requests use the existing fetch service and Vite `/api` proxy. FastAPI provides analytics, prediction, weather, event, governance, and CSV endpoints. SQLAlchemy supports SQLite and PostgreSQL. The tested database is SQLite; PostgreSQL was not exercised. ML uses a saved ColumnTransformer, Ridge, Random Forest, XGBoost, and a corridor/day/hour historical lookup. Models load once into the inference service. Power BI uses CSV dimensions/facts, Power Query, DAX, and refresh metadata.

The executable Silver and Gold jobs use **Pandas/PyArrow**. Spark configuration exists, but these jobs do not establish a distributed Spark execution path. README/project status claims of verified Uber observations, zero leakage, and production readiness were unsupported. Correction notices now identify those historical claims.

Starting local branch was main at `f72518c`; the sole pre-existing uncommitted file was `data/clearroute_app.db`. Latest remote main (`e8dcb5d`) was fetched and merged into the audit branch, preserving the new four-model comparison API/UI and recent missing-data fixes. Main was not edited, reset, or overwritten.

## B. Application startup results

| Component | Result | Evidence / limit |
|---|---|---|
| Python environment | Verified | Python 3.11.0; existing venv; `pip check` passed |
| Node/npm/Git | Verified | Node 24.13.0, npm 11.6.2, Git 2.53.0 |
| Backend | Verified | Uvicorn on `127.0.0.1:8001`; HTTP health, OpenAPI and endpoints exercised |
| Frontend | Verified | Vite on `127.0.0.1:5174`; rendered in Edge; production build passed |
| Configured default ports | Verified reachable | Existing services on 8000 and 5173 responded; separate audit ports avoided interfering with them |
| SQLite | Verified | Snapshot made using SQLite backup API; tests and audit server use copied database |
| PostgreSQL | Not verified | No PostgreSQL execution performed |
| Four model artifacts | Verified | All loaded, produced finite bounded values and reproduced benchmark metrics |
| Open-Meteo live weather | Verified | Actual live HTTP response; no credentials invented; offline fallback also tested |
| Full production ingestion | Blocked | Existing traffic source provenance is not authenticated; safe preflight rejects it |
| Docker deployment | Inspected / blocked | Compose references missing backend/frontend Dockerfiles; container deployment not verified |

Windows sandbox reload mode failed during multiprocessing socket handoff; a normal single-process Uvicorn run succeeded. Normal startup commands below omit reload. `.env` and secret values were not changed or committed.

## C. Frontend testing

All existing pages opened in Edge at desktop, 768px tablet, and 390px mobile widths:

| Existing page | Executed checks |
|---|---|
| Overview | KPIs, charts, corridor table, coverage and governance panels rendered |
| City Analytics | Delhi and Mumbai selection; city-specific headings, corridor lists and charts |
| Location Analytics | Mumbai corridor selector changed Andheri to BKC; corridor details/chart navigation; overflow reproduced and fixed |
| Congestion Prediction | XGBoost scenario displayed; historical lookup displayed explicit explanation-unavailable state; merged Compare All 4 Models returned four results |
| Event Impact | Catalog/table/chart rendered; fabricated -12% fallback replaced with zero or Not observed as appropriate |
| Weather Impact | Live weather rendered; selected city passed to impact API; tablet overflow reproduced and fixed |
| Model Performance | Four-model metrics, real held-out sample chart, SHAP summary rendered |
| Data Explorer | Table, impossible corridor search, empty result message, clearing search and governance view |
| Reports & Power BI | Page and export controls rendered; six export APIs verified by HTTP; browser download completion not verified |
| Settings | System status and preferences page opened; persisted-setting combinations not exhaustively tested |

The fresh verification tab had no console errors/warnings at the recorded check. Earlier HMR errors occurred while merge-conflicted files were temporarily present; they were resolved and a fresh tab was tested. Desktop and mobile screenshots were inspected during the audit. Two document-level overflows were reproduced: Location Analytics (446px at 390px viewport) and Weather Impact (770px at 768px); retests were 385/390 and 762/768 respectively. Temporary viewport overrides were reset.

The report-download browser wait failed when the automation session expired. This does **not** prove download success or failure. The app was reopened successfully afterward. Not every possible filter, settings combination, map interaction, and browser-download behavior was tested.

Frontend fixes: lazy-loaded pages; responsive sidebar/content, shrinkable corridor selector and metric cards; readable validation errors; refresh interval zero honored; null-safe prediction deltas; actual weather city filtering; explicit benchmark/mismatched-dataset notice; removed invented map congestion/speed, event impacts, coverage claims and unsupported weather narratives.

## D. Backend testing

**Verified:** 60 real HTTP requests with no unexpected status codes, plus API/TestClient regression checks. Covered health/OpenAPI/root, overview, all five cities' summaries and locations, corridor search/history/trends, four-model predictions and explanations, stored prediction retrieval, model comparison, model performance/global explainability, events/impacts, live and historical weather, governance/coverage/pagination, and all six CSV export types. Invalid city/location/export, bad date/page, empty-database, missing-artifact and unavailable-explainer paths were exercised.

Corrections:

- Public ML entry point shares the validated inference service; missing artifacts raise errors instead of returning 25%.
- Historical lookup no longer invents 60/25/15 attribution ratios. Missing tree explainers do not substitute historical or another model's values.
- Performance chart reads actual exported held-out observations, and absent evaluation artifacts produce an unavailable response rather than perfect default metrics.
- Strict temporal parsing, city/corridor checks, conflicting date/hour/day/month rejection, date-filter validation and inclusive end-of-day history filters.
- Stored prediction IDs are retrievable; new records retain exact explanation inputs/results in the existing JSON column. Legacy records without full inputs return an explicit 409 rather than a recomputed, potentially different explanation.
- Database-save failures roll back and return an error instead of silently reporting persistence success.
- Uncalibrated 95% RMSE intervals were removed; clipped linear outputs do not claim additive explanations for the clipped score.
- Unknown impact-city/corridor filters return 404 instead of silently returning national aggregates. Location rainfall summaries use that corridor.
- Unknown exports return 404; location CSV free-flow column uses free-flow speed rather than speed limit.
- Weather no longer invents a rainfall × 1.45 congestion surge, substitutes Delhi for unknown cities, returns invented empty weather values, or substitutes current weather for an absent requested historical date.
- Health reports degradation and avoids exposing raw database exceptions. Inference timestamps identify execution time in IST.

This was representative endpoint and boundary coverage, not every invalid-input permutation for every endpoint.

## E. Database audit

**Verified:** five cities, 25 locations, 25 events, four model metadata rows, five catalog sources, 6,000 traffic records and 1,200 weather records. SQLite integrity check passed; foreign-key consistency check found no violations; no duplicate traffic natural keys or out-of-range congestion percentages were found. Keys/relationships were inspected. Empty-database API checks ran against a separate temporary database.

**Critical unresolved data mismatch:** joining application records to Gold on corridor + timestamp matches 6,000 keys, but **5,969 congestion values differ by more than 0.01 percentage points**. Bronze traffic and the existing Silver file also contain 6,000 rows, while Gold/model/BI artifacts use 165,000. Similar displayed location averages are present in the stored sample; they are not evidence that the models ignored location. No unsupported real-world explanation was assigned to these patterns.

The catalog contained seeded counts such as 184,500 traffic rows and labels claiming verified telemetry. API counts now reflect application tables where available; unknown contextual counts are unavailable. Nonempty source text no longer proves independent event-source verification. Duplicate count is queried instead of hardcoded, and empty coverage no longer invents dates.

Original database SHA-256 before and after: `4bd5bd44c54602632a52167291b9d22926be0fba874a1135c62f251f61fb78f1`. It remains the user's pre-existing uncommitted change and is excluded from audit commits. No original records were repaired, reseeded, deleted, or migrated. Schema consistency checks are not a certification of source truth; PostgreSQL behavior and production migrations remain unverified.

## F. Machine learning audit

**Executed independently:** all four artifacts evaluated on the same 24,750-row chronological held-out benchmark partition. No retraining or artifact replacement occurred.

| Model | MAE | RMSE | R² | First evaluated input prediction |
|---|---:|---:|---:|---:|
| historical_mean | 2.6747 | 3.4048 | 0.9722 | 70.7857% |
| linear_regression | 8.6459 | 11.1179 | 0.7038 | 58.2766% |
| random_forest | 4.6879 | 6.1536 | 0.9093 | 62.0786% |
| xgboost | 2.7268 | 3.4645 | 0.9712 | 72.4783% |

All predictions were finite, clipped to [0,100], and reproducible for repeated inputs. Metrics reproduce the stored benchmark to its reported precision. They quantify **generated traffic**, not real sensor traffic or future forecasting accuracy. Full precision and output ranges are in `ClearRoute-model-data-validation.json`.

XGBoost and Random Forest use their own TreeExplainer objects; sampled additive reconstruction checks passed for each. Ridge coefficient decomposition was checked separately and is not described as TreeExplainer SHAP. Historical lookup has no fabricated feature decomposition. Missing explainer/artifact behavior and clipped-linear explanation absence have regression tests. Global SHAP remains explicitly associated with XGBoost; absolute global magnitude does not establish causal direction.

Training inspection found a shared boundary timestamp: original train ended and validation began at 2019-10-10 11:00. New chronological splitting keeps all records at a timestamp together; executed split test yielded 115,500 / 24,750 / 24,750 rows with strictly disjoint timestamp ranges. Existing fitted artifacts retain their original training history. The old trainer also chose its champion using test metrics; future training now ranks validation scores and reserves test scores for reporting. No claim of an unbiased historical champion selection is made.

Training uses fitted numeric scaling, one-hot categorical encoding and binary flags. Inference uses that saved transform; derived peak/weekend/rain/event flags now match the documented feature contract. Missing lag speeds are explicitly defaulted to free-flow values, limiting future scenario realism. Gold lag construction uses shifted prior observations; availability assumes observed recent speeds and is not a validated multi-step future forecasting backtest. Real-world weather/event effects cannot be established because generated traffic does not demonstrate their causal influence.

XGBoost emitted an older-serialization warning (artifact training environment records newer XGBoost than the local serving version). Numeric evaluation succeeded; portable artifact re-export in the training-compatible environment remains recommended before deployment. Other warnings: Starlette TestClient httpx deprecation and unset pytest-asyncio fixture-loop scope.

## G. Big Data pipeline

| Layer / action | Actual result |
|---|---|
| Bronze existing files | Traffic, weather, OSM and event CSVs exist; weather provenance JSON is missing |
| Traffic provenance | Ingestion implementation explicitly generates benchmarks and writes `is_genuine_sensor_data: false`; the older local metadata only asserts Uber Movement provenance without an authenticated sensor-data flag or reproducible archive lineage |
| Production orchestrator | Now fails preflight before ingestion overwrites when traffic is demonstration data |
| Weather ingestion failure | No longer silently generates simulated weather on an external download failure |
| Silver execution in scratch directory | Blocked: existing OSM CSV lacks required `accident_risk_score`; error now identifies missing contextual fields |
| Gold execution after Silver attempt | Blocked by absent newly generated Silver output |
| Gold isolated execution using existing Silver | Blocked: existing event CSV lacks `event_intensity` and `confidence_score` |
| Existing Gold integrity tests | Passed: schema, five cities, hours/weekdays, 165,000 records, no nulls/duplicate corridor timestamps |
| Distributed Spark | Not verified; executable transformation jobs use Pandas/PyArrow |

No fake observations, missing provenance, risk scores, event intensities or confidence scores were generated to make the pipeline pass. A pre-existing Gold artifact passing schema checks does not establish a reproducible Bronze-to-Gold run.

Required recovery: acquire licensed genuine corridor observations with timestamps, units and source metadata; reconcile corridor mapping and IST time alignment; supply independently supported infrastructure/risk context and event metadata or redesign those features to be explicitly optional; recover genuine weather download provenance; run cleaning and feature stages into a new directory; reconcile keys/counts/targets; only then train and benchmark in a separate approved data/artifact version. Do not run the legacy demonstration generator as a production ingestion substitute. Existing files were preserved.

## H. Power BI integration

**Verified:** export generator executed into a scratch directory from the existing 165,000-row Gold benchmark and all four artifacts. It generated dimensions, hourly facts, summaries, model actual/predicted rows and refresh metadata with SUCCESS. Existing Power BI tests passed primary-key and foreign-key checks, fact-vs-Gold means/counts, 24,750 test predictions, residual arithmetic, metrics agreement and refresh metadata.

This is artifact/export verification. Power BI Desktop refresh, rendered dashboard behavior, and live report publishing were **not verified**. BI data follows Gold; browser database CSV exports follow the inconsistent application sample. Those outputs must not be presented as reconciled versions of one dataset. Existing DAX, M queries and dashboard specifications were inspected as integration assets, not executed in Power BI Desktop.

## I. Security and performance

CORS now uses configured origins rather than wildcard origins with credentials. Search/history limits and date/temporal validation were strengthened. Errors avoid raw database/inference details where changed. No `.env`, new secrets, user database changes, heavy datasets, or binary model artifacts were staged.

`npm audit`: before **11 high + 1 moderate**; after compatible Vite 7.3.8 / React-plugin update, **11 high, 0 moderate**. No forced audit upgrade was run. Remaining findings trace to picomatch and dependent development tooling. The reviewed advisory lists no patched release; replacing the CSS/tooling stack would be a separate compatibility migration. See [GHSA-fc5q-39xc-vjpf](https://github.com/advisories/GHSA-fc5q-39xc-vjpf) and [Vite migration guidance](https://vite.dev/guide/migration.html). Restrict development-server exposure; default host is now loopback. Production runtime dependency exploitability was not independently established by this audit. Python dependency CVE scanning was not executed.

Initial eager JavaScript entry: 838.64 KB (gzip 232.52 KB). With lazy page imports, entry is approximately 163.6 KB (gzip 53.3 KB); largest shared chart chunk approximately 383.3 KB. This reduces initial entry loading, not necessarily total downloaded assets after visiting every page. Production build passes without the previous >500KB chunk warning.

Inspected remaining deployment limitations: Compose includes development database credentials and references absent Dockerfiles; dependencies use broad version ranges; SQLite connection-level FK enforcement and production migration behavior were not changed/certified. Do not deploy this checkout under the original unsupported production-ready claim.

## J. Test summary

Final pytest: **81 total; 80 passed; 1 failed; 0 skipped**. The remaining failing test is `bigdata/tests/test_data_pipeline.py::test_bronze_layer_outputs`, because `data/bronze/weather_era5/provenance_metadata.json` is absent. It was deliberately not fabricated or skipped.

Additional executed checks: frontend production build passed; pip dependency consistency passed; 60 live HTTP requests matched expected statuses; independent four-model evaluation passed; Power BI export execution passed; browser ten-page/responsive checks completed with the limitations in C. One intermediate combined suite hit a transient allocation failure reading a wide CSV while extra audit processes existed; unused audit processes were stopped and the final full suite completed with only the provenance failure.

Evidence: `ClearRoute-tests.xml`, `ClearRoute-http-verification.json`, `ClearRoute-model-data-validation.json`, `ClearRoute-pipeline-execution.json`, dependency audit JSON, and build log. Counts do not include browser clicks as automated unit tests. Two warning categories remain in pytest, plus the pytest-asyncio configuration warning before test execution.

## K. GitHub changes

Branch: `fix/clearroute-full-audit`; latest main merged as `949b860`. Logical task commits currently recorded:

```text
5a6cb86 fix: verify provenance, missing explanations, and responsive data states
949b860 merge: preserve latest main and all-model comparison feature
5d426ee docs: correct unverified production and data provenance claims
1965529 fix: reject synthetic production ingestion and simulated weather fallbacks
4a4da8a fix: expose benchmark limitations and verify responsive analytics UI
93948d9 fix: remove fabricated inference outputs and validate analytics contracts
```

The existing modified database is excluded. Final audit/evidence documentation is committed separately after this report is prepared. Complete commit ledger is provided with the deliverables.

**Push / PR blocked by Windows credential access.** `git push -u origin fix/clearroute-full-audit` failed because the Git helper's MSYS subprocess could not create its sandbox named object. Native Git Credential Manager was tried directly without printing secrets and reported `Failed to enumerate credentials. [0x5]` / `Access is denied`. No credential was retrieved or changed. GitHub CLI is absent. No branch push or pull request is claimed; no merge occurred.

Changed source files relative to fetched main (excluding the unchanged user database):

```text
PROJECT_STATUS.md
README.md
backend/app/api/routes/data.py
backend/app/api/routes/events.py
backend/app/api/routes/health.py
backend/app/api/routes/locations.py
backend/app/api/routes/models.py
backend/app/api/routes/predictions.py
backend/app/api/routes/reports.py
backend/app/main.py
backend/app/repositories/data_repository.py
backend/app/schemas/schemas.py
backend/app/services/analytics_service.py
backend/app/services/inference_service.py
backend/app/services/weather_service.py
backend/requirements.txt
backend/tests/test_api.py
backend/tests/test_audit_regressions.py
bigdata/ingestion/ingest_uber_movement.py
bigdata/ingestion/ingest_weather_openmeteo.py
bigdata/spark_jobs/run_pipeline.py
bigdata/spark_jobs/silver_cleaning.py
conftest.py
docs/ML_INTEGRATION_CONTRACT.md
frontend/package-lock.json
frontend/package.json
frontend/src/App.jsx
frontend/src/components/common/Card.jsx
frontend/src/components/layout/Header.jsx
frontend/src/components/layout/Sidebar.jsx
frontend/src/components/maps/TrafficMap.jsx
frontend/src/context/AppContext.jsx
frontend/src/pages/CongestionPrediction.jsx
frontend/src/pages/DataExplorer.jsx
frontend/src/pages/EventImpact.jsx
frontend/src/pages/LocationAnalytics.jsx
frontend/src/pages/ModelPerformance.jsx
frontend/src/pages/Overview.jsx
frontend/src/pages/WeatherImpact.jsx
frontend/src/services/api.js
frontend/vite.config.js
ml/inference/predict.py
ml/preprocessing/preprocessor.py
ml/training/train_all_models.py
```

A binary-capable patch relative to fetched main is provided as `ClearRoute-audit.patch`; it excludes the local database change. To publish from an ordinary authorized terminal after credential access is available:

```powershell
cd 'D:\Sarthak Projects\Clear-Route'
git switch fix/clearroute-full-audit
git push -u origin fix/clearroute-full-audit
```

Then open a pull request targeting main using the supplied PR description. Do not merge automatically. If remote main advances further, review/merge that work before publishing.

## L. Remaining issues and manual requirements

1. **Data blocker:** genuine historical traffic unavailable; generated benchmark metrics do not certify a traffic analytics product.
2. **Data reconciliation blocker:** 5,969/6,000 application values differ from Gold. Original database preserved; agree on an authoritative dataset and migrate a backed-up/new database rather than overwriting these records.
3. **Pipeline blockers:** missing weather provenance; missing OSM risk field; missing event intensity/confidence fields; Bronze/Silver and Gold artifacts have different row counts. Rebuild only from supported source data.
4. **Security blocker:** 11 high npm development dependency findings remain without a published upstream patch in the inspected advisory. Python CVE scanning and production exposure analysis remain undone.
5. **Deployment blocker:** missing Dockerfiles, development credential defaults, unverified PostgreSQL and distributed Spark execution. Production deployment is not validated.
6. **Missing local dependencies:** `matplotlib` and `pyspark` are absent from the existing venv (checked with module discovery). Matplotlib is now declared in backend requirements because training imports it; distributed Spark additionally requires the Spark-specific requirements/runtime. Neither was installed just to conceal the data blockers.
7. **ML limitations:** original train/validation timestamp overlap and test-based champion selection remain properties of existing artifacts; future code corrected but not retrained. Model serialization compatibility warning; lag-based future forecasting not backtested.
8. **QA limits:** browser export completion, all settings combinations, all filter permutations, Power BI Desktop refresh, production load/concurrency and every external failure mode are not verified.
9. **GitHub blocker:** sandbox cannot read Windows-stored Git credentials; push and PR need an authorized normal terminal or a connected GitHub service.

## M. Run the corrected project locally

Preserve the existing `.env` and database. From the repository root, in a normal PowerShell terminal:

```powershell
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal (Node 24 was tested):

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open `http://127.0.0.1:5173`; API health is `http://127.0.0.1:8000/api/health`. Existing models, preprocessor and datasets are local ignored files and are not supplied by a plain clone. Missing artifacts return explicit unavailable errors. Do not reseed a populated database or retrain merely to eliminate an error message.

For an isolated audit server using the preserved backup already created in this session:

```powershell
$env:DATABASE_URL='sqlite:///C:/Users/sarth/Documents/Codex/2026-11-17/files-pasted-by-the-user-role/work/audit/audit.db'
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001
```

Frontend audit terminal:

```powershell
cd frontend
$env:CLEARROUTE_BACKEND_URL='http://127.0.0.1:8001'
npm run dev -- --host 127.0.0.1 --port 5174 --strictPort
```

Tests:

```powershell
.venv\Scripts\python.exe -m pytest backend/tests bigdata/tests powerbi/tests -q
npm --prefix frontend run build
npm --prefix frontend audit
```

The root pytest configuration copies the developer SQLite database when no database override is supplied. Use an explicitly disposable database URL when overriding it. Expect the provenance test to fail until authentic metadata is restored. The production orchestrator will reject the current generated traffic rather than overwrite data and declare success.
