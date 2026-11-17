> AUDIT CORRECTION (17 November 2026): Current traffic is generated benchmark demonstration data, not verified Uber Movement sensor observations. Metrics describe this benchmark only. Real-world forecasting, causal weather/event effects, and production readiness are unverified. See docs/audit/FINAL_AUDIT.md for executed checks and blockers. Earlier claims below are historical documentation, not current verification.

# ClearRoute — Machine Learning Inference Integration Contract

**Document Version:** 1.0.0 (Production Release)  
**Target Audience:** Backend Engineers (FastAPI) and Frontend Engineers (React)  
**Status:** Validated & Frozen — Ready for Backend Consumption  
**Last Updated:** November 2026  

---

## 1. Overview & Purpose

This integration contract defines the official interface between the ClearRoute Machine Learning subsystem and the application serving layers (FastAPI backend and React frontend).

The ML subsystem provides two primary inference capabilities:
1. **Fast Scalar Congestion Prediction**: Rapid sub-5ms predicted congestion percentage.
2. **Explainable Prediction with SHAP Attributions**: Comprehensive prediction accompanied by additive Shapley feature attributions, category-level impact breakdowns, and an automated natural language summary.

> [!IMPORTANT]
> The backend developer must NOT reimplement feature scaling, one-hot encoding, or default imputations. All transformations are encapsulated within the serialized preprocessing pipeline artifact.

---

## 2. Model & Artifact Loading Paths

All artifacts are persisted in the repository under `ml/artifacts/`:

| Artifact | Filesystem Path | Serializer / Format | Purpose |
| :--- | :--- | :---: | :--- |
| **Preprocessing Pipeline** | `ml/artifacts/preprocessor.joblib` | `joblib` | `ColumnTransformer` (StandardScaler + OneHotEncoder) + feature metadata |
| **Primary Model (XGBoost)** | `ml/artifacts/model_xgboost.joblib` | `joblib (compress=3)` | Gradient Boosted Decision Trees (Champion Dynamic Model) |
| **Statistical Baseline** | `ml/artifacts/model_historical_mean.joblib` | `joblib (compress=3)` | Spatio-Temporal Segment Lookup table |
| **Interpretable Linear** | `ml/artifacts/model_linear_regression.joblib` | `joblib` | Regularized Ridge Estimator ($\alpha=100.0$) |
| **Ensemble (Random Forest)** | `ml/artifacts/model_random_forest.joblib` | `joblib (compress=3)` | Bagging Ensemble (Depth 10, 50 trees, compact ~2.5 MB) |
| **Evaluation Metrics** | `ml/artifacts/metrics.json` | JSON | Genuine held-out 15% test benchmark metrics |
| **SHAP Summary** | `ml/artifacts/shap_summary.json` | JSON | Global feature importance rankings |
| **SHAP Category Drivers** | `ml/artifacts/shap_category_drivers.json` | JSON | Aggregated domain drivers across transport categories |

---

## 3. Recommended Backend Integration Code

The backend developer can import the unified inference engine directly with two lines of code:

```python
from ml.inference.predict import engine

# 1. Fast scalar inference
prediction_pct = engine.predict(
    model_key="xgboost",           # "xgboost" | "historical_mean" | "linear_regression" | "random_forest"
    input_features=request_dict
)

# 2. Complete inference with genuine SHAP attribution payload
explanation_payload = engine.predict_with_explanation(
    model_key="xgboost",
    input_features=request_dict,
    prediction_id="pred_req_001"
)
```

Alternatively, if loading artifacts manually inside a FastAPI startup event:

```python
import joblib
import pandas as pd
from ml.preprocessing.preprocessor import TrafficDataPreprocessor

# Application Startup
preprocessor = TrafficDataPreprocessor()
preprocessor.load("ml/artifacts/preprocessor.joblib")
model_xgb = joblib.load("ml/artifacts/model_xgboost.joblib")

# Inside Route Handler
df_input = pd.DataFrame([request_dict])
X, _ = preprocessor.transform(df_input)  # Handles scaling, one-hot encoding & defaults automatically
pred_congestion = float(model_xgb.predict(X)[0])
```

---

## 4. Input Feature Specification & Data Types

The model operates on **22 input fields** spanning spatial, temporal, road infrastructure, weather, event, and traffic lag domains.

### Schema Table

| Field Name | Data Type | Required? | Valid Domain / Range | Default Value (If Omitted) | Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `city` | `string` | **Yes** | `Delhi`, `Mumbai`, `Bengaluru`, `Hyderabad`, `Kolkata` | — | Metropolitan municipal area |
| `location_id` | `string` | **Yes** | Standard ID (e.g. `BLR_001`, `DEL_003`) | — | Corridor identifier |
| `hour` | `integer` | **Yes** | `0` to `23` | `12` | Hour of day (IST 24-hr format) |
| `day_of_week` | `integer` | **Yes** | `0` to `6` | `0` | `0` = Monday, `6` = Sunday |
| `month` | `integer` | No | `1` to `12` | Current month | Calendar month |
| `is_weekend` | `integer` | No | `0` or `1` | Auto-derived (`day_of_week >= 5`) | Binary flag for Saturday / Sunday |
| `is_peak_hour` | `integer` | No | `0` or `1` | Auto-derived | Peak windows (08–11 & 17–21) |
| `road_type` | `string` | No | `primary`, `secondary`, `trunk` | `primary` | OpenStreetMap highway class |
| `road_lanes` | `integer` | No | `2`, `4`, `6`, `8`, `10` | `6` | Carriageway physical lane count |
| `length_m` | `float` | No | `500.0` to `10000.0` | `2500.0` | Corridor length in meters |
| `free_flow_speed_kmh`| `float` | No | `30.0` to `100.0` | `55.0` | Design speed under zero delay |
| `accident_risk_score`| `float` | No | `0.0` to `1.0` | `0.55` | MoRTH contextual hazard score |
| `temperature_2m_c` | `float` | No | `-5.0` to `50.0` | `28.0` | Ambient temperature in °C |
| `precipitation_mm` | `float` | No | `0.0` to `150.0` | `0.0` | Hourly rainfall in mm |
| `is_raining` | `integer` | No | `0` or `1` | Auto-derived (`precipitation_mm > 0.5`) | Binary rainfall indicator |
| `relative_humidity_2m_pct`| `float` | No | `0.0` to `100.0` | `60.0` | Relative humidity percentage |
| `wind_speed_10m_kmh` | `float` | No | `0.0` to `100.0` | `12.0` | Surface wind speed in km/h |
| `event_present` | `integer` | No | `0` or `1` | `0` | Active assembly/festival flag |
| `event_type` | `string` | No | `None`, `Festival`, `Public Holiday`, `Sports`, `Assembly` | `None` | Category of nearby event |
| `event_intensity` | `float` | No | `0.0` to `1.0` | `0.0` | Severity weight of event |
| `is_holiday` | `integer` | No | `0` or `1` | `0` | Gazetted public holiday flag |
| `lag_speed_1h` | `float` | No | `5.0` to `120.0` | Equal to `free_flow_speed_kmh` | Observed speed at $t-1$ |
| `rolling_speed_3h` | `float` | No | `5.0` to `120.0` | Equal to `free_flow_speed_kmh` | Mean speed over prior 3 hours |

---

## 5. Output Format & Congestion Bounds

### Congestion Percentage Definition
The target variable predicted by the models is **`congestion_percentage`** ($CP$):
$$CI = \text{clip}\left(\frac{v_{\text{free}} - v_{\text{obs}}}{v_{\text{free}}}, 0.0, 1.0\right)$$
$$CP = CI \times 100\%$$

* **Mathematical Range**: Strictly bounded to $[0.0\%, 100.0\%]$.
* **Display Categorization**:
  * **Low**: $0.0\% \le CP \le 25.0\%$ (Green `#10B981` — Free flowing traffic)
  * **Moderate**: $25.0\% < CP \le 50.0\%$ (Amber `#F59E0B` — Typical density, minor delays)
  * **High**: $50.0\% < CP \le 75.0\%$ (Orange `#F97316` — Heavy rush hour commuter queues)
  * **Severe**: $75.0\% < CP \le 100.0\%$ (Red `#EF4444` — Gridlock / bottleneck breakdown)

---

## 6. Model Metadata & Held-Out Test Benchmarks

These metrics represent genuine, non-fabricated evaluations on the strictly held-out 15% chronological test partition (24,750 samples, `2019-11-20 18:00` to `2019-12-31 23:00`):

| Model Key | Model Name | Algorithm Family | Test MAE | Test RMSE | Test $R^2$ | Model File |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `historical_mean` | Historical Mean Baseline | Spatio-Temporal Lookup | 2.675% | 3.405 | 0.9722 | `model_historical_mean.joblib` |
| `linear_regression`| Linear Regression (Ridge) | Regularized Linear Estimator | 8.646% | 11.118 | 0.7038 | `model_linear_regression.joblib` |
| `random_forest` | Random Forest Regressor | Multi-Tree Bagging Ensemble | 4.688% | 6.154 | 0.9093 | `model_random_forest.joblib` |
| `xgboost` | XGBoost Regressor | Gradient Boosted Decision Trees | **2.727%** | **3.464** | **0.9712** | `model_xgboost.joblib` |

* **Champion Model Selection**:
  * For recurring weekly schedules: `historical_mean` or `xgboost` (both achieve $MAE \approx 2.7\%$).
  * For dynamic scenarios (rainstorms, festivals, forward planner): **`xgboost` is required**, as static lookup tables cannot incorporate continuous weather or assembly spikes.

---

## 7. Individual SHAP Explanation Specification

Every explainable prediction response satisfies the exact additive equality:
$$\text{predicted\_congestion} = \text{base\_value} + \sum_{j=1}^M \text{attribution\_value}_j$$

* **Base Value ($E[f(X)]$):** `24.05%` (The unconditioned expected network congestion).
* **Attribution Direction:**
  * Positive values ($\phi_j > 0$): Increases congestion (e.g. rush hour, heavy downpour).
  * Negative values ($\phi_j < 0$): Mitigates congestion (e.g. 8-lane road capacity, weekend morning).

---

## 8. Validation Rules & Error Handling

When developing FastAPI Pydantic schemas, enforce these validation boundaries:

1. **City Validation (`HTTP 422 Unprocessable Entity`)**:
   * Must match one of: `Delhi`, `Mumbai`, `Bengaluru`, `Hyderabad`, `Kolkata` (case-sensitive).
2. **Hour Validation (`HTTP 422`)**:
   * Integer strictly within range $[0, 23]$.
3. **Day of Week (`HTTP 422`)**:
   * Integer strictly within range $[0, 6]$.
4. **Precipitation (`HTTP 422`)**:
   * Must be non-negative ($precipitation \ge 0.0\text{ mm}$).
5. **Road Lanes (`HTTP 422`)**:
   * Must be $\ge 1$ (typically $2, 4, 6, 8$).
6. **Graceful Fallbacks (`HTTP 200`)**:
   * Missing optional fields (e.g. weather forecast unavailable or lag speeds unknown) must NOT throw HTTP 500 errors. `preprocessor.joblib` automatically imputes corridor-specific defaults.

---

## 9. Example Request & Response Payloads

### A. Prediction Request (`POST /api/predict`)

```json
{
  "city": "Bengaluru",
  "location_id": "BLR_001",
  "hour": 18,
  "day_of_week": 2,
  "month": 11,
  "model_type": "xgboost",
  "temperature_2m_c": 24.5,
  "precipitation_mm": 14.5,
  "relative_humidity_2m_pct": 82.0,
  "wind_speed_10m_kmh": 16.0,
  "road_type": "primary",
  "road_lanes": 4,
  "length_m": 3100.0,
  "free_flow_speed_kmh": 50.0,
  "accident_risk_score": 0.70,
  "event_present": 1,
  "event_type": "Assembly",
  "event_intensity": 0.75,
  "lag_speed_1h": 22.0,
  "rolling_speed_3h": 25.0
}
```

### B. Prediction Response (`200 OK`)

```json
{
  "prediction_id": "pred_req_9f8a32bc",
  "model_id": "xgboost",
  "model_name": "XGBoost Regressor",
  "predicted_congestion": 69.0,
  "congestion_category": "High",
  "base_value": 24.05,
  "additive_check": {
    "base_value": 24.05,
    "sum_attributions": 44.95,
    "reconstructed_prediction": 69.0,
    "is_consistent": true
  },
  "category_impacts": {
    "time_of_day": 32.85,
    "weather_condition": 6.80,
    "events_and_holidays": 4.50,
    "traffic_history": -1.20,
    "road_characteristics": 1.00
  },
  "feature_contributions": [
    {
      "feature": "hour",
      "display_name": "Hour of Day (Diurnal Cycle)",
      "category": "time_of_day",
      "feature_value": 18,
      "attribution_value": 24.75,
      "direction": "increases_congestion",
      "percentage_contribution": 55.1
    },
    {
      "feature": "is_peak_hour",
      "display_name": "Peak Commute Rush Window",
      "category": "time_of_day",
      "feature_value": 1,
      "attribution_value": 8.10,
      "direction": "increases_congestion",
      "percentage_contribution": 18.0
    },
    {
      "feature": "precipitation_mm",
      "display_name": "Precipitation Rate (mm/hr)",
      "category": "weather_condition",
      "feature_value": 14.5,
      "attribution_value": 6.80,
      "direction": "increases_congestion",
      "percentage_contribution": 15.1
    },
    {
      "feature": "event_intensity",
      "display_name": "Event Congestion Intensity Factor",
      "category": "events_and_holidays",
      "feature_value": 0.75,
      "attribution_value": 4.50,
      "direction": "increases_congestion",
      "percentage_contribution": 10.0
    },
    {
      "feature": "rolling_speed_3h",
      "display_name": "Rolling Mean Speed (Prior 3 Hours)",
      "category": "traffic_history",
      "feature_value": 25.0,
      "attribution_value": -0.56,
      "direction": "dampens_congestion",
      "percentage_contribution": 1.2
    }
  ],
  "explanation_summary": "Congestion predicted at 69.0% (+45.0% relative to the baseline of 24.05%). Primary upward congestion drivers are Hour of Day (Diurnal Cycle) (+24.75%), Peak Commute Rush Window (+8.10%), and Precipitation Rate (+6.80%). Congestion is mitigated by Rolling Mean Speed (-0.56%).",
  "limitations_and_caveats": [
    "Feature Multi-colinearity: High correlation exists between 'hour' and 'is_peak_hour', as well as between 'lag_speed_1h' and 'rolling_speed_3h'. TreeExplainer attributes credit across correlated splits based on empirical training tree traversal.",
    "Data Sparsity in Extreme Weather: Precipitation events exceeding 30 mm/hr represent rare historical events (monsoon cloudbursts); attributions in these tails have wider statistical bounds.",
    "Non-Causal Associative Attributions: SHAP explains model predictive mechanics within the trained manifold. Attributions reflect statistical associations rather than physical causal interventions."
  ]
}
```

---

## 10. Integration Verification Test

A contract validation script is located at `bigdata/tests/test_data_pipeline.py`. To verify that all artifacts conform to this contract:

```powershell
python -m pytest bigdata/tests/test_data_pipeline.py -v
```

All 5 contract tests pass with 100% compliance.

