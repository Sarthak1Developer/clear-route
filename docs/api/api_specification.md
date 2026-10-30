# ClearRoute — REST API Specification

ClearRoute exposes a modern RESTful API powered by **FastAPI** with automatic OpenAPI/Swagger documentation, strict Pydantic schemas, and structured error responses.

Base URL: `http://127.0.0.1:8000/api`  
Swagger UI: `http://127.0.0.1:8000/docs`  
ReDoc: `http://127.0.0.1:8000/redoc`

---

## 1. System & Health

### `GET /api/health`
Returns system status, active database dialect, and ML artifact availability.
- **Response**:
  ```json
  {
    "status": "online",
    "version": "1.0.0",
    "database": "connected (sqlite / postgresql)",
    "models_loaded": ["historical_mean", "linear_regression", "random_forest", "xgboost"],
    "timestamp": "2026-10-30T12:00:00+05:30"
  }
  ```

### `GET /api/overview`
High-level analytical KPIs for the Executive Dashboard.
- **Response**:
  ```json
  {
    "total_cities": 5,
    "total_locations": 25,
    "avg_congestion_pct": 46.2,
    "most_congested_city": "Bengaluru",
    "total_records_processed": 184500,
    "historical_coverage": "April 2019 - December 2019",
    "city_comparison": [...],
    "hourly_trend": [...],
    "weekly_trend": [...],
    "weather_correlation": [...]
  }
  ```

---

## 2. Cities & Geography

### `GET /api/cities`
List all 5 supported metropolitan cities with their coordinates and baseline metrics.

### `GET /api/cities/{city}/summary`
Detailed congestion profile, peak congestion hours, and weather impact for a specific city.

### `GET /api/cities/{city}/locations`
List of supported locations/road segments within the specified city.

---

## 3. Locations & Road Segments

### `GET /api/locations/search?q={query}&city={city}`
Search supported locations by name or corridor.

### `GET /api/locations/{location_id}/history`
Historical traffic records for a location with optional date filtering (`start_date`, `end_date`, `limit`).

### `GET /api/locations/{location_id}/trends`
Aggregated hourly, day-of-week, and monthly congestion patterns for a selected location.

---

## 4. Congestion Prediction

### `POST /api/predict`
Calculates predicted traffic congestion and returns SHAP attribution.
- **Request Body**:
  ```json
  {
    "city": "Delhi",
    "location_id": "DEL_001",
    "prediction_date": "2026-11-05",
    "prediction_time": "18:00",
    "model_type": "xgboost",
    "temperature_c": 26.5,
    "precipitation_mm": 12.0,
    "humidity_pct": 78.0,
    "wind_speed_kmh": 14.2,
    "event_present": true,
    "event_name": "Major Trade Expo"
  }
  ```
- **Response**:
  ```json
  {
    "prediction_id": "pred_9847123",
    "predicted_congestion_pct": 74.8,
    "congestion_category": "High",
    "historical_baseline_pct": 52.3,
    "difference_pct": 22.5,
    "selected_model": "xgboost",
    "confidence_interval": {"lower": 70.1, "upper": 79.5},
    "shap_attributions": [
      {"feature": "precipitation_mm", "value": 12.0, "impact_pct": 11.2},
      {"feature": "hour_of_day (18:00)", "value": 18, "impact_pct": 8.5},
      {"feature": "event_present", "value": 1, "impact_pct": 3.8}
    ]
  }
  ```

### `GET /api/models`
Returns metadata, architecture, and hyperparameter descriptions for all 4 models.

---

## 5. Events & Weather Impact

### `GET /api/events`
Returns historical 2019 events and separate 2026 forward-looking events categorized by city.

### `GET /api/events/impact`
Statistical comparison of congestion levels on event days vs non-event days.

### `GET /api/weather`
Overview of historical weather observations across cities.

### `GET /api/weather/impact`
Empirical analysis of rainfall intensity, temperature, and wind speed vs. congestion percentage.

---

## 6. Model Performance & Explainability

### `GET /api/models/performance`
Strict benchmark evaluation metrics (MAE, RMSE, $R^2$) computed on the held-out 15% test set across all 4 models.

### `GET /api/models/feature-importance`
Global feature importance rankings across models.

### `GET /api/models/explainability`
Summary of SHAP values, feature beeswarm data, and variable sensitivity curves.

---

## 7. Data Quality & Coverage

### `GET /api/data/sources`
Metadata, provenance, license, and download origin for all raw input sources.

### `GET /api/data/quality`
Data completeness, missing value rates, outlier statistics, and deduplication audit logs.

### `GET /api/data/coverage`
Temporal and spatial coverage boundaries across the 5 Indian metropolitan cities.
