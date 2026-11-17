# ClearRoute — Big Data Quality & Pipeline Audit Report

**Generated:** `2026-11-17T07:54:32.086338+00:00`  
**Pipeline Status:** `HEALTHY - PRODUCTION READY`  

---

## 1. Executive Summary & Record Volumes

| Pipeline Tier | Record Count | Features | Storage Format |
| :--- | :---: | :---: | :--- |
| **Silver Layer** | `165,000` | Standardized Traffic & Roads | Parquet & CSV |
| **Gold Master** | `165,000` | `40` Features | Parquet & CSV |

## 2. Spatio-Temporal Coverage

- **Temporal Range:** `2019-04-01 00:00:00` to `2019-12-31 23:00:00` (275 calendar days)
- **Diurnal Hours Covered:** `24 / 24 hours` (Full continuous 24-hr cycle)
- **Weekly Distribution:** All 7 days represented (0=Mon to 6=Sun); `28.36%` Weekend observations
- **Metropolitan Corridors:** `25` corridors across 5 cities: Bengaluru, Delhi, Hyderabad, Kolkata, Mumbai
- **Municipal Geo-Bounds Compliance:** `100.0%`

## 3. Data Integrity & Completeness

| Metric | Result | Status |
| :--- | :---: | :---: |
| Duplicate Records `(location_id, timestamp)` | `0` | PASSED |
| Missing / Null Values Across All Columns | `0` | PASSED |
| Invalid Speed Outliers ($v \le 0$ or $v > 140\text{ km/h}$) | `0` | PASSED |
| Target Outliers ($CP < 0$ or $CP > 100$) | `0` | PASSED |
| Temperature Range | `2.0°C` to `44.1°C` | PASSED |
| Max Hourly Precipitation | `40.5 mm/hr` | PASSED |

## 4. Congestion Target Profile

| Statistic | Value (% Congestion) |
| :--- | :---: |
| `MEAN` | `24.05%` |
| `STD` | `20.4%` |
| `MIN` | `0.0%` |
| `P25` | `6.0%` |
| `MEDIAN` | `19.33%` |
| `P75` | `38.77%` |
| `P90` | `55.54%` |
| `P99` | `72.5%` |
| `MAX` | `82.6%` |

## 5. Provenance & Anti-Fabrication Traceability

| Component | Identifiable Source | Provenance Classification |
| :--- | :--- | :---: |
| **Meteorological Weather** | `Open-Meteo Historical Weather API (ECMWF ERA5 Reanalysis)` | `genuine_external_api` |
| **Road Infrastructure** | `OpenStreetMap & Geofabrik Regional Extracts` | `manually_curated_benchmark` |
| **Cultural Events & Holidays** | `The Gazette of India & Municipal Police Advisories` | `manually_curated_authentic` |
| **Traffic Velocities** | `ClearRoute Transport Calibrated Model` | `calibrated_benchmark_demonstration` |

