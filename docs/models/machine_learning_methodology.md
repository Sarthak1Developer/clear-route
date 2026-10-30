# ClearRoute — Machine Learning Methodology & Evaluation

## 1. Experimental Integrity & Chronological Splitting

In traffic and spatio-temporal modeling, random data splitting (e.g. standard K-Fold) introduces severe **temporal data leakage**: adjacent hours share strong auto-correlation and weather states, leading to overly optimistic test metrics that fail in deployment.

### Temporal Partitioning (April 1 – December 31, 2019):
- **Training Set (70%)**: April 1, 2019 00:00 $\rightarrow$ October 11, 2019 23:59 IST.
- **Validation Set (15%)**: October 12, 2019 00:00 $\rightarrow$ November 20, 2019 23:59 IST (hyperparameter tuning).
- **Test Set (15%)**: November 21, 2019 00:00 $\rightarrow$ December 31, 2019 23:59 IST (strictly held-out benchmark).

---

## 2. Four Finalized Model Implementations

### Model 1: Historical Mean Baseline
- **Role**: Statistical benchmark to quantify whether machine learning adds genuine predictive power over naive lookup tables.
- **Formulation**:
  $$\hat{y}(s, h, d) = \frac{1}{|T(s, h, d)|} \sum_{t \in T(s, h, d)} y(s, t)$$
  Where $s$ is the location, $h \in [0, 23]$ is hour of day, and $d \in [0, 6]$ is day of week in the training split.
- **Fallback**: Global location mean if specific hour-day slot is sparse.

### Model 2: Linear Regression (Ridge Regularized)
- **Role**: High-interpretability parametric baseline.
- **Formulation**:
  $$\hat{y} = \mathbf{w}^T \mathbf{x} + b + \alpha \|\mathbf{w}\|_2^2$$
- **Insights Provided**: Direct linear sensitivity coefficients (e.g. percentage increase in congestion per 1 mm/hr rainfall).

### Model 3: Random Forest Regressor
- **Role**: Non-linear ensemble model capturing non-linear interactions without strong parametric assumptions.
- **Configuration**:
  - `n_estimators`: 100
  - `max_depth`: 15
  - `min_samples_split`: 5
  - `n_jobs`: -1

### Model 4: XGBoost Regressor (Primary Model)
- **Role**: State-of-the-art gradient boosted decision tree framework designed for structured tabular and spatio-temporal data.
- **Configuration**:
  - `objective`: `reg:squarederror`
  - `n_estimators`: 200
  - `learning_rate`: 0.05
  - `max_depth`: 6
  - `subsample`: 0.8
  - `colsample_bytree`: 0.8

---

## 3. Evaluation Metrics

Every model is evaluated strictly on the unobserved 15% Test partition across three criteria:
1. **Mean Absolute Error (MAE)**:
   $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |y_i - \hat{y}_i|$$
2. **Root Mean Squared Error (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (y_i - \hat{y}_i)^2}$$
3. **Coefficient of Determination ($R^2$)**:
   $$R^2 = 1 - \frac{\sum_{i=1}^N (y_i - \hat{y}_i)^2}{\sum_{i=1}^N (y_i - \bar{y})^2}$$

---

## 4. Model Explainability via SHAP (SHapley Additive exPlanations)

To ensure ClearRoute does not act as a black-box, SHAP TreeExplainer calculates exact local and global feature attributions:
- **Global Importance**: Mean absolute SHAP values across test instances identify key urban congestion drivers (e.g., peak hour, precipitation, road lanes).
- **Local Attribution**: For any individual prediction $\hat{y}$, SHAP decomposes the output into the baseline expected value $E[y]$ plus individual positive/negative contributions:
  $$\hat{y} = E[y] + \sum_{j=1}^M \phi_j$$
  - $\phi_{\text{rain}}$: Effect of current rainfall.
  - $\phi_{\text{hour}}$: Effect of evening commute rush.
  - $\phi_{\text{event}}$: Marginal impact of nearby sports match or festival.

---

## 5. Artifact Serialization & Serving

All preprocessing pipelines (standard scalers, one-hot encoders, category indices) and trained estimators are serialized using `joblib` into `ml/artifacts/`:
- `ml/artifacts/preprocessor.joblib`
- `ml/artifacts/model_historical_mean.joblib`
- `ml/artifacts/model_linear_regression.joblib`
- `ml/artifacts/model_random_forest.joblib`
- `ml/artifacts/model_xgboost.joblib`
- `ml/artifacts/model_metrics.json`
- `ml/artifacts/shap_summary.json`

The FastAPI inference service loads these artifacts into memory on startup, ensuring instantaneous sub-20ms prediction times without retraining.
