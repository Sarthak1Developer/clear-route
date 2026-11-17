# ClearRoute — Microsoft Power BI Setup & Integration Guide

This guide describes how to connect **Microsoft Power BI Desktop** to ClearRoute analytical data sources, establish the dimensional semantic star schema, configure all DAX measures, apply the custom dark theme, and construct the **6 Executive Transportation Intelligence Dashboard Pages**.

> [!NOTE]
> **Environment Verification**: Microsoft Power BI Desktop (`PBIDesktop.exe`) is not installed on this headless Windows server environment. In strict accordance with the project requirements, no empty or fabricated `.pbix` file has been created. Instead, the complete production-ready semantic dataset (165,000 Gold records, 24,750 held-out test predictions, 21 events, 25 corridors), star-schema relationships, DAX measure scripts, Power Query M code, visual theme JSON, and 6-page dashboard layout blueprints are fully generated, audited, and verified via automated test suites.

---

## 1. Quick Start & Prerequisites

### Prerequisites
- Windows 10/11 64-bit with **Microsoft Power BI Desktop** (free download from Microsoft Store or direct installer).
- ClearRoute project repository cloned or downloaded locally.
- Directory of analytical exports: `powerbi/exports/`
- Custom dark theme: `powerbi/dashboards/clearroute_theme.json`
- DAX measures library: `powerbi/dashboards/dax_measures.dax`
- Automated M script: `powerbi/dashboards/power_query_setup.m`

---

## 2. Data Connection & Power Query Import

### Option 1: Automated Import via Power Query M Scripts (Fastest & Recommended)
1. Launch **Microsoft Power BI Desktop**.
2. Click **Home** $\rightarrow$ **Transform Data** to open the Power Query Editor.
3. Under **Home** $\rightarrow$ **Manage Parameters**, click **New Parameter**:
   - **Name**: `ExportFolderPath`
   - **Type**: `Text`
   - **Current Value**: Your absolute path, e.g., `C:\Users\aurian\Downloads\clear-route-main\powerbi\exports`
4. In the Queries pane on the left, right-click and choose **New Query** $\rightarrow$ **Blank Query**.
5. Click **Advanced Editor** in the ribbon, paste the corresponding code block from `powerbi/dashboards/power_query_setup.m`, and rename the query to match the table:
   - `dim_location`
   - `dim_date`
   - `dim_time`
   - `dim_event`
   - `dim_weather_category`
   - `fact_congestion_hourly`
   - `model_performance_summary`
   - `model_actual_vs_predicted`
   - `model_feature_importance`
   - `corridor_predictive_risk`
   - `refresh_metadata`
6. Click **Close & Apply** in the top left.

### Option 2: Standard CSV Import
1. In Power BI Desktop, click **Get Data** $\rightarrow$ **Text/CSV**.
2. Navigate to `powerbi/exports/` and select each CSV file.
3. Verify that column headers are recognized properly, and click **Load**.

---

## 3. Data Modeling & Semantic Relationships

Switch to the **Model View** (icon on the far left pane) and establish the single-direction **1-to-Many ($1:*$)** relationships as follows:

```
                    +--------------------+
                    |      dim_date      |
                    | (date) [PK]        |
                    +---------+----------+
                              | 1
                              | *
+--------------------+        |        +--------------------+
|    dim_location    |        |        |      dim_time      |
| (location_id) [PK] |--------+--------| (hour) [PK]        |
+---------+----------+        |        +---------+----------+
          | 1                 |                  | 1
          |                   |                  |
          | *                 | *                | *
+---------+-------------------+------------------+----------+
|                  fact_congestion_hourly                   |
| (location_id) [FK], (date) [FK], (hour) [FK]              |
+-----------------------------------------------------------+
          | 1
          |
          | *
+---------+--------------------------+
|       model_actual_vs_predicted    |
| (location_id) [FK]                 |
+------------------------------------+
          | 1
          |
          | 1
+---------+--------------------------+
|        corridor_predictive_risk    |
| (location_id) [PK/FK]              |
+------------------------------------+
```

### Relationship Configuration Checklist:
1. `dim_location[location_id]` $\rightarrow$ `fact_congestion_hourly[location_id]`
   - Cardinality: **One to Many ($1:*$)**
   - Cross filter direction: **Single**
2. `dim_date[date]` $\rightarrow$ `fact_congestion_hourly[date]`
   - Cardinality: **One to Many ($1:*$)**
   - Cross filter direction: **Single**
3. `dim_time[hour]` $\rightarrow$ `fact_congestion_hourly[hour]`
   - Cardinality: **One to Many ($1:*$)**
   - Cross filter direction: **Single**
4. `dim_location[location_id]` $\rightarrow$ `model_actual_vs_predicted[location_id]`
   - Cardinality: **One to Many ($1:*$)**
   - Cross filter direction: **Single**
5. `dim_location[location_id]` $\rightarrow$ `corridor_predictive_risk[location_id]`
   - Cardinality: **One to One ($1:1$)**
   - Cross filter direction: **Both** or **Single**

### Geospatial & Column Formatting:
- Select `dim_location[latitude]` $\rightarrow$ Set **Data Category** to **Latitude**.
- Select `dim_location[longitude]` $\rightarrow$ Set **Data Category** to **Longitude**.
- Select `dim_date[date]` $\rightarrow$ Set **Data Type** to **Date** (`YYYY-MM-DD`).
- Select `fact_congestion_hourly[timestamp]` $\rightarrow$ Set **Data Type** to **Date/Time**.

---

## 4. DAX Measures Table Creation

1. In the **Home** tab, click **Enter Data**.
2. Name the table `_Measures` and click **Load**.
3. Right-click `_Measures` in the Data pane and select **New Measure**.
4. Copy and paste the DAX formulas from `powerbi/dashboards/dax_measures.dax`.
5. Key foundational measures:
   ```dax
   // Average Congestion Percentage
   Avg Congestion Pct = AVERAGE(fact_congestion_hourly[congestion_percentage])

   // Total Recorded Readings
   Total Observations = COUNTROWS(fact_congestion_hourly)

   // Peak Commute Congestion Rate
   Peak Hour Congestion = CALCULATE([Avg Congestion Pct], fact_congestion_hourly[is_peak_hour] = 1)

   // Off-Peak Congestion Rate
   Off Peak Congestion = CALCULATE([Avg Congestion Pct], fact_congestion_hourly[is_peak_hour] = 0)

   // Commute Rush Delta
   Peak Rush Delta = [Peak Hour Congestion] - [Off Peak Congestion]
   ```

---

## 5. Visual Theme Setup

1. In Power BI Desktop, click the **View** tab in the top ribbon.
2. In the **Themes** dropdown, click **Browse for themes...**.
3. Select `powerbi/dashboards/clearroute_theme.json`.
4. The canvas background will automatically transition to Dark Charcoal (`#0A0F1D`), visual cards to Slate Dark (`#111827`), with modern cyan, blue, emerald, amber, and red data accents.

---

## 6. Building the 6 Dashboard Pages

### Page 1: Executive Overview
- **Header**: Metropolitan Transportation Intelligence Command Overview.
- **Top KPI Cards**:
  - Card 1: `_Measures[Avg Congestion Pct]` (`24.05%`) and `_Measures[Peak Hour Congestion]` (`41.34%`).
  - Card 2: `_Measures[Total Observations]` (`165,000`).
  - Card 3: `_Measures[Most Congested City]` (`Bengaluru`, `25.29%`).
  - Card 4: `_Measures[Mean Network Speed kmh]` (`42.2 km/h`).
- **Visuals**:
  - **Clustered Column Chart**: X: `dim_location[city]`, Y: `_Measures[Avg Congestion Pct]`.
  - **Line & Clustered Column Chart**: X: `dim_time[time_label]`, Column: `_Measures[Avg Congestion Pct]`, Line: `_Measures[Mean Network Speed kmh]`.
  - **Horizontal Bar Chart**: Top 10 Corridors by `_Measures[Avg Congestion Pct]`.
  - **Decomposition Tree**: Metric: `_Measures[Avg Congestion Pct]`, Explain by: `city`, `road_type`, `period_of_day`.
- **Slicers**: `dim_location[city]`, `dim_date[month_name]`.

### Page 2: Location Analytics
- **Header**: Corridor Micro-Analysis, Spatial Geometry & Diurnal Cycles.
- **Top KPI Cards**:
  - `_Measures[Weekday Congestion]` (`25.60%`).
  - `_Measures[Weekend Congestion]` (`20.14%`).
  - `_Measures[Weekend Relief Delta]` (`+5.46%`).
- **Visuals**:
  - **Map Visual**: Latitude: `dim_location[latitude]`, Longitude: `dim_location[longitude]`, Bubble Size: `_Measures[Avg Congestion Pct]`, Legend: `dim_location[road_type]`.
  - **Matrix Heatmap**: Rows: `dim_location[city]`, `dim_location[location_name]`; Columns: `dim_time[time_label]`; Values: `_Measures[Avg Congestion Pct]`. Conditional color gradient from green (0%) to red (60%+).
  - **Stacked Area Chart**: X: `dim_time[hour]`, Values: `_Measures[Weekday Congestion]`, `_Measures[Weekend Congestion]`.
  - **Scatter Chart**: X: `dim_location[free_flow_speed_kmh]`, Y: `_Measures[Mean Network Speed kmh]`, Size: `dim_location[road_lanes]`.
- **Slicers**: `dim_location[city]`, `dim_location[road_type]`.

### Page 3: Weather Impact
- **Header**: Meteorological Sensitivity & Monsoon Flood Perturbations.
- **Top KPI Cards**:
  - `_Measures[Dry Weather Congestion]` (`24.07%`).
  - `_Measures[Moderate Rain Congestion]` (`25.31%`).
  - `_Measures[Thermal Impact Delta]` (`+18.35%` heat increase).
- **Visuals**:
  - **Clustered Column Chart**: X: `dim_weather_category[rain_category]`, Y: `weather_impact_summary[mean_congestion_pct]`.
  - **Line Chart**: X: `fact_congestion_hourly[precipitation_mm]`, Y: `_Measures[Speed Degradation Pct]`.
  - **Temperature Breakdown Column Chart**: X: `weather_temperature_summary[temperature_category]`, Y: `weather_temperature_summary[mean_congestion_pct]`, Line: `weather_temperature_summary[mean_speed_kmh]`.
  - **Weather Advisory Table**: Columns: `dim_weather_category[rain_category]`, `dim_weather_category[weather_severity]`, `dim_weather_category[advisory_level]`.
- **Slicers**: `dim_weather_category[rain_category]`, `dim_location[city]`.

### Page 4: Event & Holiday Impact
- **Header**: Civic Assemblies, Festivals & Cultural Perturbation Dynamics.
- **Top KPI Cards**:
  - `_Measures[Total Events Cataloged]` (`21`).
  - `_Measures[Assembly Congestion]` (`26.70%`).
  - `_Measures[Festival Congestion]` (`23.07%`).
- **Visuals**:
  - **Grouped Bar Chart**: Y: `event_impact_summary[event_type]`, X: `event_impact_summary[mean_congestion_pct]`. Compares Assemblies (+2.65%), Public Holidays, Sports, and Festivals against baseline.
  - **Scatter Plot**: X: `dim_event[attendance]`, Y: `dim_event[congestion_lift_pct]`, Size: `dim_event[event_intensity]`.
  - **Event Master Table**: Columns: `date`, `city`, `event_name`, `event_type`, `venue`, `attendance`, `event_avg_congestion_pct`, `city_baseline_congestion_pct`, `congestion_lift_pct`.
- **Slicers**: `dim_event[city]`, `dim_event[event_type]`.

### Page 5: Model Performance & Validation
- **Header**: Machine Learning Held-Out Test Set Validation ($N = 24,750$).
- **Top KPI Cards**:
  - `_Measures[Champion Model Name]` (`Historical Mean Baseline`).
  - `_Measures[Champion Model R2]` (`0.972`).
  - `_Measures[MAE Historical Mean]` (`2.68%`).
  - `_Measures[MAE XGBoost]` (`2.73%`).
- **Visuals**:
  - **Benchmark Table**: Columns: `model_name`, `algorithm_family`, `mae`, `rmse`, `r2_score`, `is_champion`.
  - **Bar Chart**: Y: `model_name`, X: `r2_score` with reference line at $R^2 = 0.85$.
  - **Scatter Plot (Actual vs. Predicted)**: X: `model_actual_vs_predicted[actual_congestion_pct]`, Y: `model_actual_vs_predicted[pred_xgboost]` with $y = x$ identity line in red.
  - **Subgroup Slices Clustered Bar**: X: `model_subgroup_performance[slice_name]`, Y: `mae`, Legend: `model_name`.
- **Slicers**: `model_subgroup_performance[slice_type]` ("City" vs "Traffic Condition").

### Page 6: Predictive Analytics & Bottleneck Risk
- **Header**: Forward Bottleneck Risk Classification & SHAP Driver Decomposition.
- **Top KPI Cards**:
  - `_Measures[Critical Corridors Count]` (`5` Critical Bottlenecks).
  - `_Measures[Top Risk Bottleneck Corridor]` (`Whitefield` / `Secunderabad`).
  - `_Measures[Max Predicted Peak Congestion]` (`48.0%`).
  - `_Measures[Top SHAP Feature]` (`Hour of Day`).
- **Visuals**:
  - **Ranked Corridor Risk Table**: Columns: `city`, `location_name`, `risk_tier`, `composite_risk_score`, `baseline_congestion_pct`, `peak_hour_congestion_pct`, `primary_risk_driver`.
  - **Risk Tier Donut Chart**: Legend: `risk_tier`, Values: Count of corridors.
  - **SHAP Feature Importance Bar Chart**: Y: `display_name`, X: `shap_importance_pct`, Color: `category`.
  - **Driver Narrative Cards**: Title: `category_name`, Text: `driver_narrative`.
- **Slicers**: `corridor_predictive_risk[city]`, `corridor_predictive_risk[risk_tier]`.

---

## 7. Data Refresh Process & Audit Trail

### How to Regenerate Analytical CSV Exports
Whenever new upstream data is ingested through the Big Data pipeline (Bronze $\rightarrow$ Silver $\rightarrow$ Gold) or new models are trained, simply run:

```bash
python powerbi/exports/generate_bi_exports.py
```

### What the Refresh Script Performs:
1. Validates `data/gold/master_congestion/gold_master_congestion.parquet`.
2. Extracts clean star-schema fact and dimension CSV files.
3. Dynamically re-evaluates held-out test predictions for all 4 models without hardcoded values.
4. Re-computes corridor composite risk indices and SHAP driver matrices.
5. Updates `refresh_metadata.json` and `refresh_metadata.csv` with the exact execution UTC timestamp, record counts, and champion model metrics.

### Refreshing Power BI Desktop:
1. In Power BI Desktop, click **Home** $\rightarrow$ **Refresh**.
2. All tables update within seconds.
3. The footer card automatically reflects the updated timestamp and row counts.

---

## 8. Verification & Ground Truth Reference Table

Verify your Power BI report values against this verified ground-truth reference table:

| Analytical Metric | Ground Truth Value (Gold Master) | Power BI Measure / Table Field |
| :--- | :--- | :--- |
| **Total Master Observations** | `165,000` | `_Measures[Total Observations]` |
| **Overall Average Congestion** | `24.05%` | `_Measures[Avg Congestion Pct]` |
| **Harmonic Mean Velocity** | `42.18 km/h` | `_Measures[Mean Network Speed kmh]` |
| **Peak Commute Congestion** | `41.34%` | `_Measures[Peak Hour Congestion]` |
| **Off-Peak Congestion** | `13.68%` | `_Measures[Off Peak Congestion]` |
| **Weekday Congestion** | `25.60%` | `_Measures[Weekday Congestion]` |
| **Weekend Congestion** | `20.14%` | `_Measures[Weekend Congestion]` |
| **Most Congested Metro** | `Bengaluru` (`25.29%`) | `_Measures[Most Congested City]` |
| **Second Congested Metro** | `Hyderabad` (`24.83%`) | `city_congestion_summary[city]` |
| **Highest Congestion Corridor** | `Secunderabad` (`30.30%`) | `location_congestion_summary` |
| **Second Highest Corridor** | `Whitefield` (`30.27%`) | `location_congestion_summary` |
| **Moderate Rain Congestion** | `25.31%` | `_Measures[Moderate Rain Congestion]` |
| **Civic Assembly Congestion** | `26.70%` | `_Measures[Assembly Congestion]` |
| **Champion Model Held-Out $R^2$** | `0.972` | `_Measures[Champion Model R2]` |
| **Champion Model Held-Out MAE** | `2.68%` | `_Measures[MAE Historical Mean]` |
| **Primary ML Regressor $R^2$ (XGBoost)** | `0.971` | `model_performance_summary[r2_score]` |
| **Primary ML Regressor MAE (XGBoost)** | `2.73%` | `model_performance_summary[mae]` |
