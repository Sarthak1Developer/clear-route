# ClearRoute — Big Data Engineering Pipeline

## 1. Pipeline Overview

The ClearRoute Big Data pipeline leverages **Apache Spark (PySpark)** to process, harmonize, and enrich heterogeneous urban datasets at scale. It implements a medallion architecture (Bronze $\rightarrow$ Silver $\rightarrow$ Gold) ensuring reproducibility, data lineage, and computational efficiency.

---

## 2. Mathematical Definition of Congestion Target

In historical traffic analysis (notably Uber Movement datasets), traffic speed is recorded across road segments or Traffic Analysis Zones (TAZ). Traffic congestion is rarely a direct physical sensor measurement; rather, it is a derived indicator representing the reduction in travel velocity relative to free-flow conditions.

### Formula:
For a given road segment $s$ at timestamp $t$:
$$v(s, t) = \text{Observed Mean Speed (km/h)}$$
$$v_{\text{free}}(s) = \text{Free-Flow Speed (km/h)} = \max \left( \text{95th percentile of } v(s, \text{off-peak}), v_{\text{speed\_limit}} \right)$$

The **Congestion Index** $CI(s, t)$ and **Congestion Percentage** $CP(s, t)$ are defined as:
$$CI(s, t) = \max \left( 0.0, \, \min \left( 1.0, \, \frac{v_{\text{free}}(s) - v(s, t)}{v_{\text{free}}(s)} \right) \right)$$
$$CP(s, t) = CI(s, t) \times 100\%$$

### Display Categories:
- **Low Congestion**: $0\% \le CP \le 25\%$ (Free-flowing traffic, minimal delays)
- **Moderate Congestion**: $26\% \le CP \le 50\%$ (Typical urban density, slight delays)
- **High Congestion**: $51\% \le CP \le 75\%$ (Heavy commuter traffic, significant delays)
- **Severe Congestion**: $76\% \le CP \le 100\%$ (Gridlock or extreme bottleneck conditions)

*Note on Limitations*: In zones where free-flow speed data is unavailable, the 85th percentile of late-night speeds (01:00 to 04:00 IST) is used as an empirical proxy for $v_{\text{free}}$. This is fully documented in the metadata and avoids silent fabrication.

---

## 3. Spark Processing Stages

### Stage 1: Bronze Ingestion
- `bigdata/ingestion/ingest_uber_movement.py`: Reads raw CSV/JSON dumps from Zenodo archive. Preserves segment IDs, hourly travel times, and geometric zone IDs.
- `bigdata/ingestion/ingest_osm_infrastructure.py`: Parses OpenStreetMap highway classifications (primary, secondary, trunk, tertiary), lanes, surface type, and segment lengths.
- `bigdata/ingestion/ingest_weather_openmeteo.py`: Fetches and stores hourly ERA5 weather readings (precipitation in mm, temperature in °C, wind speed, relative humidity).
- `bigdata/ingestion/ingest_events_holidays.py`: Ingests national holidays, state holidays (e.g. Durga Puja for Kolkata, Ganesh Chaturthi for Mumbai), and major cultural/sporting events for 2019.

### Stage 2: Silver Cleaning & Transformation
- **Null Value Treatment**: Road segments with missing speed records are investigated. Linear interpolation is used if gap $\le 2$ hours; otherwise records are marked or imputed using location-hour medians. Never zeroed out!
- **Deduplication**: Identifies multiple sensor reports for identical `(location_id, timestamp)` tuples using window functions `row_number() OVER (PARTITION BY location_id, timestamp ORDER BY report_time DESC)`.
- **Geographic Validation**: Filters outliers outside the bounding coordinates of Delhi, Mumbai, Bengaluru, Hyderabad, and Kolkata.

### Stage 3: Gold Analytical Table Generation
- PySpark joins traffic records with:
  1. Hourly weather features (joined on `city` and `timestamp`).
  2. Public holiday & event flags (joined on `city` and `date`).
  3. Road infrastructure metrics (joined on `location_id` / `road_id`).
  4. Contextual road accident risk indices (derived from official MoRTH statistics by city/corridor).
- **Feature Engineering**:
  - `hour_of_day` ($0 - 23$)
  - `day_of_week` ($0 = \text{Monday}, 6 = \text{Sunday}$)
  - `is_weekend` (binary flag: Saturday/Sunday)
  - `is_peak_hour` (binary flag: 08:00–11:00 and 17:00–21:00)
  - `precipitation_mm` (continuous float)
  - `is_raining` (binary flag: $\text{precipitation} > 0.5\text{ mm}$)
  - `event_present` (binary flag: 1 if major assembly/event within 5km radius)
  - `road_type` (categorical: trunk, primary, secondary, tertiary)
  - `accident_risk_level` (contextual category: Low, Moderate, High)
  - `congestion_percentage` (continuous target: $0.0 - 100.0\%$)

---

## 4. Analytical Parquet Schema

```text
root
 |-- city: string (nullable = false)
 |-- location_id: string (nullable = false)
 |-- location_name: string (nullable = false)
 |-- latitude: double (nullable = false)
 |-- longitude: double (nullable = false)
 |-- timestamp: timestamp (nullable = false)
 |-- hour: integer (nullable = false)
 |-- day_of_week: integer (nullable = false)
 |-- month: integer (nullable = false)
 |-- is_weekend: integer (nullable = false)
 |-- is_peak_hour: integer (nullable = false)
 |-- is_holiday: integer (nullable = false)
 |-- holiday_name: string (nullable = true)
 |-- temperature_c: double (nullable = false)
 |-- precipitation_mm: double (nullable = false)
 |-- humidity_pct: double (nullable = false)
 |-- wind_speed_kmh: double (nullable = false)
 |-- road_type: string (nullable = false)
 |-- road_lanes: integer (nullable = false)
 |-- road_length_m: double (nullable = false)
 |-- accident_risk_score: double (nullable = false)
 |-- event_present: integer (nullable = false)
 |-- event_name: string (nullable = true)
 |-- free_flow_speed_kmh: double (nullable = false)
 |-- observed_speed_kmh: double (nullable = false)
 |-- congestion_percentage: double (nullable = false)
```
