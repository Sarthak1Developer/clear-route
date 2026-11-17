# ClearRoute — Power BI Dashboard Specifications & Architecture

This document defines the comprehensive visual architecture, canvas layouts, visual containers, field mappings, color theming, and DAX measure bindings for all **6 Power BI Report Pages**.

---

## 1. Global Visual Theme & Styling (ClearRoute Dark Architecture)

The dashboard utilizes the `clearroute_theme.json` styling specification optimized for transportation intelligence and executive command centers:

- **Canvas Background**: Deep Navy Charcoal (`#0A0F1D`)
- **Card / Visual Container Fill**: Slate Dark (`#111827`)
- **Container Borders**: Subtle Charcoal Border (`#1F2937`), 8px border radius
- **Primary Data Accent**: Electric Cyan (`#06B6D4`)
- **Secondary Data Accent**: Royal Blue (`#3B82F6`)
- **Optimal / Low Congestion**: Emerald Green (`#10B981`)
- **Moderate Congestion**: Amber Gold (`#F59E0B`)
- **Severe / High Congestion**: Rose Red (`#EF4444`)
- **Typography**: Segoe UI / Inter (Clean Modern Sans-Serif), Primary Title `#F9FAFB`, Data Labels `#9CA3AF`

---

## 2. Page-by-Page Visual Architecture

### Page 1: Executive Overview
**Objective**: High-level executive pulse across 5 major Indian metropolitan areas (Delhi, Mumbai, Bengaluru, Hyderabad, Kolkata), traffic volume, peak congestion severity, and diurnal speed profiles.

| Container | Visual Type | Data Source & Fields | Visual Configuration & DAX Bindings |
| :--- | :--- | :--- | :--- |
| **KPI Card 1** | Multi-row KPI Card | `_Measures[Avg Congestion Pct]`, `_Measures[Peak Hour Congestion]` | Callout size 28pt; Electric Cyan font; subtitle "Network Baseline vs Peak" |
| **KPI Card 2** | Card Visual | `_Measures[Total Observations]` | Callout size 28pt; Format: `#,##0` (`165,000` observations) |
| **KPI Card 3** | Card Visual | `_Measures[Most Congested City]` | Callout size 28pt; Amber Gold border; displays "Bengaluru" (25.29%) |
| **KPI Card 4** | Card Visual | `_Measures[Mean Network Speed kmh]` | Callout size 28pt; Emerald Green font; displays `42.2 km/h` |
| **Visual 1 (Top Left)** | Clustered Column Chart | X: `dim_location[city]`<br>Y: `_Measures[Avg Congestion Pct]` | Sorted descending by Congestion. Data labels enabled. Conditional bar color (Red > 25%, Amber 22-25%, Green < 22%). |
| **Visual 2 (Top Right)** | Line & Clustered Column | X: `dim_time[time_label]`<br>Column: `_Measures[Avg Congestion Pct]`<br>Line: `_Measures[Mean Network Speed kmh]` | Dual Y-axes. Column fill Electric Cyan, Line Royal Blue. Illustrates inverse velocity decay during 09:00 and 19:00 peaks. |
| **Visual 3 (Bottom Left)** | Horizontal Bar Chart | Y: `dim_location[location_name]`<br>X: `_Measures[Avg Congestion Pct]` | Top 10 Congested Corridors. Tooltip: `dim_location[city]`, `dim_location[road_lanes]`, `dim_location[road_type]`. |
| **Visual 4 (Bottom Right)** | Decomposition Tree | Metric: `_Measures[Avg Congestion Pct]`<br>Explain by: `dim_location[city]`, `dim_location[road_type]`, `dim_time[period_of_day]` | Interactive root-cause explorer allowing drill-down from network average into city and geometry. |
| **Header Slicer Bar** | Slicer Dropdowns | `dim_location[city]`, `dim_date[month_name]`, `dim_time[period_of_day]` | Multi-select with "Select All" option. |

---

### Page 2: Location Analytics
**Objective**: Deep spatial, geometric, and diurnal comparative analytics across individual road corridors, day-of-week commute patterns, and weekend relief.

| Container | Visual Type | Data Source & Fields | Visual Configuration & DAX Bindings |
| :--- | :--- | :--- | :--- |
| **KPI Card 1** | Card Visual | `_Measures[Weekday Congestion]` | Callout size 24pt; displays `25.60%` |
| **KPI Card 2** | Card Visual | `_Measures[Weekend Congestion]` | Callout size 24pt; displays `20.14%` |
| **KPI Card 3** | Card Visual | `_Measures[Weekend Relief Delta]` | Callout size 24pt; displays `+5.46%` weekday commute premium |
| **Visual 1 (Left Half)** | Bubble / Map Visual | Latitude: `dim_location[latitude]`<br>Longitude: `dim_location[longitude]`<br>Size: `_Measures[Avg Congestion Pct]`<br>Color: `dim_location[road_type]` | Azure Maps / Mapbox dark style. Centered over Indian subcontinent with auto-zoom on slicer selection. |
| **Visual 2 (Top Right)** | Stacked Area Chart | X: `dim_time[hour]`<br>Values: `_Measures[Weekday Congestion]`, `_Measures[Weekend Congestion]` | Semi-transparent area fill (Cyan for Weekday, Amber for Weekend). Highlights dual weekday commuter spikes. |
| **Visual 3 (Center)** | Matrix Table | Rows: `dim_location[city]`, `dim_location[location_name]`<br>Columns: `dim_time[time_label]`<br>Values: `_Measures[Avg Congestion Pct]` | Conditional background color heatmap: Green (0%) $\rightarrow$ Amber (30%) $\rightarrow$ Crimson (60%+). |
| **Visual 4 (Bottom Right)** | Scatter Plot | X: `dim_location[free_flow_speed_kmh]`<br>Y: `_Measures[Mean Network Speed kmh]`<br>Size: `dim_location[road_lanes]`<br>Color: `dim_location[city]` | 45-degree reference line ($y = x$) representing theoretical zero-congestion capacity. Distance below line indicates delay magnitude. |
| **Corridor Slicer** | Slicer Dropdowns | `dim_location[city]`, `dim_location[road_type]`, `dim_location[road_lanes]` | Searchable corridor dropdown. |

---

### Page 3: Weather Impact
**Objective**: Detailed meteorological sensitivity analysis evaluating the impact of ERA5 precipitation rates, monsoon rain tiers, and ambient temperatures on vehicular congestion and velocity degradation.

| Container | Visual Type | Data Source & Fields | Visual Configuration & DAX Bindings |
| :--- | :--- | :--- | :--- |
| **KPI Card 1** | Card Visual | `_Measures[Dry Weather Congestion]` | Callout size 26pt; displays `24.07%` |
| **KPI Card 2** | Card Visual | `_Measures[Moderate Rain Congestion]` | Callout size 26pt; displays `25.31%` |
| **KPI Card 3** | Card Visual | `_Measures[Heavy Monsoon Congestion]` | Callout size 26pt; displays `13.30%` (monsoon curfew/off-peak clustering) |
| **KPI Card 4** | Card Visual | `_Measures[Thermal Impact Delta]` | Callout size 26pt; displays `+18.35%` (Hot >35°C vs Cool <20°C) |
| **Visual 1 (Top Left)** | Clustered Column Chart | X: `dim_weather_category[rain_category]`<br>Y: `weather_impact_summary[mean_congestion_pct]`<br>Tooltip: `weather_impact_summary[speed_reduction_pct]` | Color gradient from Teal (`Dry`) to Deep Navy (`Heavy Monsoon`). Data labels on. |
| **Visual 2 (Top Right)** | Line Chart | X: `fact_congestion_hourly[precipitation_mm]` (binned 1mm)<br>Y: `_Measures[Speed Degradation Pct]` | Fitted polynomial trend line demonstrating progressive speed degradation as rainfall intensifies. |
| **Visual 3 (Bottom Left)** | Clustered Column Chart | X: `weather_temperature_summary[temperature_category]`<br>Y: `weather_temperature_summary[mean_congestion_pct]`<br>Line: `weather_temperature_summary[mean_speed_kmh]` | Dual axis showing increase in daytime congestion as temperatures exceed 30°C in conjunction with traffic volume. |
| **Visual 4 (Bottom Right)** | Table Visual | Columns: `dim_weather_category[rain_category]`, `dim_weather_category[weather_severity]`, `dim_weather_category[advisory_level]`, `weather_impact_summary[observation_count]` | Actionable municipal traffic authority advisory matrix. |
| **Weather Slicer** | Slicer | `dim_weather_category[rain_category]`, `dim_location[city]` | Filter by city and rain intensity. |

---

### Page 4: Event & Holiday Impact
**Objective**: Impact of 21 major cultural festivals (Diwali, Ganesh Visarjan, Durga Puja), sporting events (IPL Qualifiers, Pink Ball Test), and public holidays against non-event baseline traffic.

| Container | Visual Type | Data Source & Fields | Visual Configuration & DAX Bindings |
| :--- | :--- | :--- | :--- |
| **KPI Card 1** | Card Visual | `_Measures[Total Events Cataloged]` | Callout size 26pt; displays `21` events |
| **KPI Card 2** | Card Visual | `_Measures[Assembly Congestion]` | Callout size 26pt; displays `26.70%` (+2.65% over baseline) |
| **KPI Card 3** | Card Visual | `_Measures[Festival Congestion]` | Callout size 26pt; displays `23.07%` (reflects holiday commercial shift) |
| **Visual 1 (Top Left)** | Grouped Bar Chart | Y: `event_impact_summary[event_type]`<br>X: `event_impact_summary[mean_congestion_pct]` | Compares Assembly (26.7%), Public Holiday (25.2%), Sports (24.3%), Non-Event Baseline (24.05%), and Festival (23.1%). |
| **Visual 2 (Top Right)** | Scatter Plot | X: `dim_event[attendance]`<br>Y: `dim_event[congestion_lift_pct]`<br>Size: `dim_event[event_intensity]`<br>Color: `dim_event[city]` | Examines correlation between crowd assembly attendance and local corridor congestion lift. |
| **Visual 3 (Bottom Half)** | Detailed Grid Table | Columns: `dim_event[date]`, `dim_event[city]`, `dim_event[event_name]`, `dim_event[event_type]`, `dim_event[venue]`, `dim_event[attendance]`, `dim_event[event_avg_congestion_pct]`, `dim_event[city_baseline_congestion_pct]`, `dim_event[congestion_lift_pct]` | Conditional formatting on `congestion_lift_pct`: Green for negative (holiday clearance), Red for positive (congestion surge). |
| **Event Slicers** | Dropdown Slicers | `dim_event[city]`, `dim_event[event_type]`, `dim_date[month_name]` | Multi-select filters. |

---

### Page 5: Model Performance & Validation
**Objective**: Comprehensive statistical validation across all 4 machine learning models evaluated on the strictly held-out chronological 15% test partition ($N = 24,750$). Avoids hardcoded values and enables actual vs. predicted verification.

| Container | Visual Type | Data Source & Fields | Visual Configuration & DAX Bindings |
| :--- | :--- | :--- | :--- |
| **KPI Card 1** | Card Visual | `_Measures[Champion Model Name]` | Callout size 22pt; displays champion title (e.g. `Historical Mean Baseline` / `XGBoost`) |
| **KPI Card 2** | Card Visual | `_Measures[Champion Model R2]` | Callout size 26pt; Cyan font; displays `0.972` |
| **KPI Card 3** | Card Visual | `_Measures[MAE Historical Mean]` | Callout size 24pt; Amber font; displays `2.68%` |
| **KPI Card 4** | Card Visual | `_Measures[MAE XGBoost]` | Callout size 24pt; Cyan font; displays `2.73%` |
| **Visual 1 (Top Left)** | Benchmark Table | Columns: `model_performance_summary[model_name]`, `model_performance_summary[algorithm_family]`, `model_performance_summary[mae]`, `model_performance_summary[rmse]`, `model_performance_summary[r2_score]`, `model_performance_summary[is_champion]` | Highlighting Champion with green check icon. Sorted by $R^2$ descending. |
| **Visual 2 (Top Right)** | Bar Chart | Y: `model_performance_summary[model_name]`<br>X: `model_performance_summary[r2_score]` | Reference line at $R^2 = 0.85$ acceptance threshold. |
| **Visual 3 (Bottom Left)** | Scatter Plot (Actual vs Pred) | X: `model_actual_vs_predicted[actual_congestion_pct]`<br>Y: `model_actual_vs_predicted[pred_xgboost]` (or `pred_historical_mean`) | 1:1 Identity reference line ($y = x$) in Rose Red. Demonstrates tight alignment across all 24,750 test observations. |
| **Visual 4 (Bottom Right)** | Clustered Column Chart | X: `model_subgroup_performance[slice_name]`<br>Y: `model_subgroup_performance[mae]`<br>Legend: `model_subgroup_performance[model_name]` | Subgroup validation slices across Bengaluru, Delhi, Hyderabad, Kolkata, Mumbai, and traffic regimes. |
| **Partition Slicer** | Slicer / Text Card | Filter: `model_subgroup_performance[slice_type]` | Slices between "City" and "Traffic Condition" performance. |

---

### Page 6: Predictive Analytics & Bottleneck Risk
**Objective**: Forward-looking risk classification, predictive congestion under stress scenarios (rush hour, monsoon precipitation, events), and global SHAP feature importance explainability.

| Container | Visual Type | Data Source & Fields | Visual Configuration & DAX Bindings |
| :--- | :--- | :--- | :--- |
| **KPI Card 1** | Card Visual | `_Measures[Critical Corridors Count]` | Callout size 28pt; Rose Red font; displays count of High/Critical bottlenecks |
| **KPI Card 2** | Card Visual | `_Measures[Top Risk Bottleneck Corridor]` | Callout size 24pt; Amber font; displays `Whitefield` / `Secunderabad` |
| **KPI Card 3** | Card Visual | `_Measures[Max Predicted Peak Congestion]` | Callout size 28pt; displays `48.0%` peak congestion |
| **KPI Card 4** | Card Visual | `_Measures[Top SHAP Feature]` | Callout size 20pt; displays `Hour of Day (Diurnal Cycle)` |
| **Visual 1 (Top Left)** | Ranked Risk Table | Columns: `corridor_predictive_risk[city]`, `corridor_predictive_risk[location_name]`, `corridor_predictive_risk[risk_tier]`, `corridor_predictive_risk[composite_risk_score]`, `corridor_predictive_risk[baseline_congestion_pct]`, `corridor_predictive_risk[peak_hour_congestion_pct]`, `corridor_predictive_risk[primary_risk_driver]` | Sorted by `composite_risk_score` descending. Critical tiers highlighted with red data bars. |
| **Visual 2 (Top Right)** | Donut Chart | Legend: `corridor_predictive_risk[risk_tier]`<br>Values: `COUNTROWS(corridor_predictive_risk)` | Slices: Critical Risk (Crimson), High Risk (Amber), Moderate Risk (Blue), Low Risk (Emerald). |
| **Visual 3 (Bottom Left)** | Horizontal Bar Chart | Y: `model_feature_importance[display_name]`<br>X: `model_feature_importance[shap_importance_pct]`<br>Color: `model_feature_importance[category]` | Displays top 15 global SHAP feature attributions, explaining diurnal cycle, autoregressive lag, carriageway width, and rain drivers. |
| **Visual 4 (Bottom Right)** | Multi-Card Narrative | Title: `shap_category_drivers[category_name]`<br>Body: `shap_category_drivers[driver_narrative]` | Clear text narrative explaining the physical mechanism of traffic bottlenecks. |
| **Risk Slicer** | Dropdown Slicers | `corridor_predictive_risk[city]`, `corridor_predictive_risk[risk_tier]` | Interactive risk filtering. |

---

## 3. Data Refresh & Audit Footer

Every report page features an unobtrusive footer card binding to `refresh_metadata`:
- **Last Refreshed**: `_Measures[Data Last Refreshed UTC]`
- **Dataset Version**: `165,000 Gold Records (April–December 2019)`
- **Evaluation Engine**: `Strict Held-Out 15% Test Split (24,750 Samples)`
- **Pipeline Status**: `_Measures[Pipeline Health Status]` (`SUCCESS`)
