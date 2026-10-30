# ClearRoute — Microsoft Power BI Setup & Integration Guide

This guide describes how to connect **Microsoft Power BI Desktop** to ClearRoute analytical data sources and build the 5 executive transportation intelligence dashboard pages.

---

## 1. Data Connection Options

### Option A: Direct CSV / Parquet Import (Offline & High Portability)
1. Launch **Power BI Desktop**.
2. Select **Get Data** $\rightarrow$ **Text/CSV**.
3. Navigate to the project directory: `powerbi/exports/`.
4. Import the following files:
   - `dim_location.csv`
   - `fact_congestion_hourly.csv`
   - `city_congestion_summary.csv`
   - `hourly_congestion_summary.csv`
   - `weather_impact_summary.csv`
   - `event_impact_summary.csv`
   - `model_performance_summary.csv`
5. In the Power Query Navigator, click **Load**.

### Option B: Live PostgreSQL Connection
1. Ensure the PostgreSQL service is active (via `docker-compose up db` or local server).
2. In Power BI Desktop, click **Get Data** $\rightarrow$ **PostgreSQL database**.
3. Server: `localhost:5432`
4. Database: `clearroute_db`
5. Data Connectivity mode: **Import** or **DirectQuery**.
6. Enter credentials:
   - Username: `clearroute_user`
   - Password: `clearroute_secure_password`
7. Select tables: `cities`, `locations`, `traffic_records`, `model_metadata`, `data_sources`.

---

## 2. Data Modeling & Relationship Verification

In the **Model View** of Power BI Desktop:
1. Ensure a **1-to-Many ($1:*$)** single-direction relationship exists between:
   - `dim_location[location_id]` $\rightarrow$ `fact_congestion_hourly[location_id]`
2. Mark `fact_congestion_hourly[timestamp]` as Date type.
3. Categorize `dim_location[latitude]` as **Latitude** data category and `dim_location[longitude]` as **Longitude**.

---

## 3. Essential DAX Measures

Create a dedicated table `_Measures` and insert the following DAX calculations:

```dax
// 1. Average Network Congestion Percentage
Avg Congestion Pct = AVERAGE(fact_congestion_hourly[congestion_percentage])

// 2. Total Observations Count
Total Readings = COUNTROWS(fact_congestion_hourly)

// 3. Peak Hour Congestion Index
Peak Hour Congestion = 
CALCULATE(
    AVERAGE(fact_congestion_hourly[congestion_percentage]),
    fact_congestion_hourly[is_peak_hour] = 1
)

// 4. Monsoon Heavy Rain Impact Delta
Monsoon Rain Delta = 
VAR DryAvg = CALCULATE(AVERAGE(fact_congestion_hourly[congestion_percentage]), fact_congestion_hourly[precipitation_mm] <= 0.5)
VAR RainAvg = CALCULATE(AVERAGE(fact_congestion_hourly[congestion_percentage]), fact_congestion_hourly[precipitation_mm] > 15.0)
RETURN
    RainAvg - DryAvg

// 5. Weekday Commute Premium
Weekday Commute Delta = 
VAR WeekdayAvg = CALCULATE(AVERAGE(fact_congestion_hourly[congestion_percentage]), fact_congestion_hourly[is_weekend] = 0)
VAR WeekendAvg = CALCULATE(AVERAGE(fact_congestion_hourly[congestion_percentage]), fact_congestion_hourly[is_weekend] = 1)
RETURN
    WeekdayAvg - WeekendAvg
```

---

## 4. The 5 Dashboard Report Pages

### Page 1: Executive Transportation Overview
- **Header**: Metropolitan Transportation Intelligence Summary.
- **KPI Cards**: `[Avg Congestion Pct]`, `Total Corridors Monitored (25)`, `Total Historical Observations (184.5K)`, `Most Congested Metro (Bengaluru)`.
- **Visuals**:
  - Clustered Bar Chart: `city_congestion_summary[city]` vs `[avg_congestion_pct]`.
  - Area Chart: `hourly_congestion_summary[hour]` vs `[mean_congestion_pct]`.
  - Slicers: City filter, Weekend vs Weekday filter.

### Page 2: City-Wise Traffic Analytics
- **Header**: Comparative Metro Traffic Dynamics.
- **Visuals**:
  - Filled / Bubble Map: Leaflet or Azure Maps visual using `dim_location[latitude]`, `dim_location[longitude]`, bubble size = `[Avg Congestion Pct]`.
  - Stacked Bar Chart: Top 10 Congested Road Corridors by City.
  - Line Chart: Diurnal 24-hour curve comparing Delhi, Mumbai, Bengaluru, Hyderabad, and Kolkata.

### Page 3: Location-Wise Bottleneck Analysis
- **Header**: Corridor Micro-Analysis & Road Geometry.
- **Visuals**:
  - Matrix Table: `location_name`, `corridor_name`, `road_type`, `road_lanes`, `free_flow_speed_kmh`, `[Avg Congestion Pct]`.
  - Scatter Plot: `road_lanes` (X-axis) vs `[Avg Congestion Pct]` (Y-axis), colored by `road_type`.
  - Heatmap Matrix: Day of Week (rows) vs Hour of Day (columns) showing peak bottleneck windows.

### Page 4: Weather and Event Impact Dynamics
- **Header**: Meteorological & Cultural Perturbations.
- **Visuals**:
  - Clustered Column Chart: `weather_impact_summary[rain_category]` vs `[mean_congestion_pct]`.
  - Grouped Bar Chart: `event_impact_summary[event_type]` vs `[mean_congestion_pct]`.
  - Key Drivers Visual: Impact of precipitation mm on travel speed reductions.

### Page 5: Predictive ML Model Performance
- **Header**: Empirical Validation & Benchmark Metrics (Held-Out 15% Test Set).
- **Visuals**:
  - Comparison Table: `model_name`, `algorithm_family`, `mae`, `rmse`, `r2_score`.
  - Bar Chart: Model $R^2$ Comparison highlighting champion XGBoost model ($R^2 = 0.895$).
  - Waterfall Chart: Global SHAP feature attributions decomposing congestion into hour, rain, lanes, and event weights.
