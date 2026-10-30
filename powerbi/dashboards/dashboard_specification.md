# ClearRoute — Power BI Dashboard Specifications

This document defines the layout specifications, visualization parameters, and color palettes for the 5 Power BI report pages.

---

## 1. Visual Styling & Color Theme (ClearRoute Dark Architecture)

- **Canvas Background**: Dark Charcoal / Deep Navy (`#0A0F1D`)
- **Card / Visual Container Fill**: Slate Dark (`#111827`)
- **Primary Accent**: Electric Cyan (`#06B6D4`)
- **Secondary Accent**: Royal Blue (`#3B82F6`)
- **Warning Accent**: Amber (`#F59E0B`)
- **Critical / Severe Congestion**: Rose Red (`#EF4444`)
- **Optimal / Low Congestion**: Emerald Green (`#10B981`)
- **Font Family**: Segoe UI / Inter (Clean Modern Sans)

---

## 2. Page-by-Page Specifications

### Page 1: Executive Overview
| Visual Container | Visual Type | Data Fields | Formatting Notes |
| :--- | :--- | :--- | :--- |
| **Top Left Card 1** | Multi-row KPI Card | `[Avg Congestion Pct]`, `[Peak Hour Congestion]` | Callout size 28pt, Cyan font |
| **Top Mid Card 2** | Card | Total Observations (COUNTROWS) | Format: `184.5K` |
| **Top Right Card 3** | Card | Most Congested Metro (`Bengaluru`) | Highlighted Amber border |
| **Center Left** | Clustered Column Chart | X: `city`, Y: `avg_congestion_pct` | Data labels on, conditional formatting by severity |
| **Center Right** | Line & Clustered Column | X: `hour`, Column: `avg_congestion_pct`, Line: `mean_speed_kmh` | Dual axis, secondary axis inverted for speed |
| **Bottom** | Decomposition Tree | Metric: `[Avg Congestion Pct]`, Explain by: `city`, `road_type`, `is_peak_hour` | Interactive root analysis |

### Page 2: City-Wise Traffic Analytics
| Visual Container | Visual Type | Data Fields | Formatting Notes |
| :--- | :--- | :--- | :--- |
| **Left Half** | Azure Maps / Shape Map | Location: `latitude`, `longitude`, Size: `avg_congestion_pct` | Dark map style, circle zoom |
| **Top Right** | Bar Chart | Y: `location_name`, X: `avg_congestion_pct` | Filter top 10 corridors in city |
| **Bottom Right** | Stacked Area Chart | X: `hour`, Values: `weekday_congestion`, `weekend_congestion` | Semi-transparent area fill |

### Page 3: Location-Wise Congestion Analysis
| Visual Container | Visual Type | Data Fields | Formatting Notes |
| :--- | :--- | :--- | :--- |
| **Top Bar** | Slicer Dropdowns | `city`, `location_name`, `road_type` | Multi-select enabled |
| **Center** | Matrix Table | Rows: `location_name`, Columns: `hour`, Values: `congestion_percentage` | Conditional background color scale (Green to Red) |
| **Bottom Left** | Scatter Chart | X: `free_flow_speed_kmh`, Y: `observed_speed_kmh`, Size: `road_lanes` | 45-degree reference line representing zero delay |
| **Bottom Right** | Donut Chart | Legend: `congestion_category`, Values: Count of observations | Emerald, Amber, Orange, Red slices |

### Page 4: Weather & Event Impact Dynamics
| Visual Container | Visual Type | Data Fields | Formatting Notes |
| :--- | :--- | :--- | :--- |
| **Top Left** | Clustered Column Chart | X: `rain_category`, Y: `mean_congestion_pct` | Step-up bar progression |
| **Top Right** | Line Chart | X: `precipitation_mm`, Y: `speed_reduction_pct` | Fitted polynomial trend line |
| **Bottom Left** | Grouped Bar Chart | Y: `event_type`, X: `mean_congestion_pct` | Compared against non-event baseline |
| **Bottom Right** | Card Matrix | `[Monsoon Rain Delta]`, `[Festival Congestion Delta]` | Callout indicators |

### Page 5: Predictive Model Performance
| Visual Container | Visual Type | Data Fields | Formatting Notes |
| :--- | :--- | :--- | :--- |
| **Top Left** | Benchmark Table | `model_name`, `family`, `mae`, `rmse`, `r2_score` | Champion highlighted with green check badge |
| **Top Right** | Clustered Bar Chart | Y: `model_name`, X: `r2_score` | Target threshold reference line at $R^2 = 0.85$ |
| **Bottom** | Waterfall Chart | Category: `Feature`, Y: `SHAP Impact %` | Positive impacts in Red, Dampeners in Green |
