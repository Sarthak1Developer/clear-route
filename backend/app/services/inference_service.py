import os
import json
import uuid
import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import joblib

from backend.app.core.config import settings
from ml.preprocessing.preprocessor import TrafficDataPreprocessor
from ml.explainability.shap_explainer import (
    TrafficShapExplainer,
    FEATURE_CATEGORIES,
    HUMAN_READABLE_NAMES,
    LIMITATIONS_AND_CAVEATS
)

logger = logging.getLogger("clearroute.inference")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

class ModelNotAvailableError(Exception):
    """Raised when a requested model is not loaded or its artifact is missing."""
    pass

class PreprocessingArtifactMissingError(Exception):
    """Raised when the preprocessor pipeline artifact is missing."""
    pass

class PredictionOutputValidationError(Exception):
    """Raised when the predicted output value is invalid (e.g. NaN, infinite, or physically invalid)."""
    pass

MODEL_METADATA_FALLBACK = {
    "historical_mean": {
        "name": "Historical Mean Baseline",
        "family": "Spatio-Temporal Segment Lookup",
        "version": "1.0.0",
        "role": "Statistical Baseline",
    },
    "linear_regression": {
        "name": "Linear Regression (Ridge)",
        "family": "Regularized Parametric Estimator",
        "version": "1.0.0",
        "role": "Interpretable Baseline",
    },
    "random_forest": {
        "name": "Random Forest Regressor",
        "family": "Multi-Tree Bagging Ensemble",
        "version": "1.0.0",
        "role": "Non-linear Ensemble",
    },
    "xgboost": {
        "name": "XGBoost Regressor",
        "family": "Gradient Boosted Decision Trees",
        "version": "1.0.0",
        "role": "Primary Forecasting Model",
    },
}

class InferenceService:
    """
    Dedicated Inference Service for ClearRoute Machine Learning Models.
    Safely loads serialized models and preprocessors from ml/artifacts/.
    Executes actual model predictions with genuine SHAP TreeExplainer local and global explainability.
    """
    def __init__(self, artifacts_dir: Optional[str] = None):
        if not artifacts_dir:
            artifacts_dir = os.path.join(PROJECT_ROOT, settings.ML_ARTIFACTS_DIR)
        self.artifacts_dir = artifacts_dir
        self.preprocessor_wrapper = TrafficDataPreprocessor()
        self.preprocessor_data: Optional[Dict[str, Any]] = None
        self.models: Dict[str, Any] = {}
        self.metrics: Dict[str, Any] = {}
        self.shap_summary: Dict[str, Any] = {}
        self.shap_category_drivers: Dict[str, str] = {}
        self.shap_explainers: Dict[str, TrafficShapExplainer] = {}
        self.load_artifacts()

    def load_artifacts(self):
        """
        Loads serialized model artifacts, preprocessing pipeline, and SHAP explainability assets.
        Gracefully handles missing files without crashing during startup.
        """
        self.models.clear()
        self.shap_explainers.clear()
        self.preprocessor_data = None
        self.metrics = {}
        self.shap_summary = {}
        self.shap_category_drivers = {}

        if not os.path.isdir(self.artifacts_dir):
            logger.warning(f"ML artifacts directory does not exist: {self.artifacts_dir}")
            return

        # 1. Load Preprocessor Pipeline
        prep_path = os.path.join(self.artifacts_dir, "preprocessor.joblib")
        if os.path.exists(prep_path):
            try:
                self.preprocessor_data = joblib.load(prep_path)
                logger.info(f"Loaded preprocessor pipeline from {prep_path}")
            except Exception as e:
                logger.error(f"Failed to load preprocessor artifact: {e}")
        else:
            logger.warning(f"Preprocessor artifact not found at {prep_path}")

        # 2. Load the 4 Model Artifacts
        for model_key in ["historical_mean", "linear_regression", "random_forest", "xgboost"]:
            model_path = os.path.join(self.artifacts_dir, f"model_{model_key}.joblib")
            if os.path.exists(model_path):
                try:
                    self.models[model_key] = joblib.load(model_path)
                    logger.info(f"Loaded trained model '{model_key}' from {model_path}")
                except Exception as e:
                    logger.error(f"Failed to load model artifact '{model_key}': {e}")
            else:
                logger.warning(f"Model artifact not found for '{model_key}' at {model_path}")

        # 3. Load Held-Out Benchmark Metrics
        metrics_path = os.path.join(self.artifacts_dir, "metrics.json")
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, "r", encoding="utf-8") as f:
                    self.metrics = json.load(f)
                logger.info(f"Loaded evaluation metrics from {metrics_path}")
            except Exception as e:
                logger.warning(f"Could not load metrics artifact: {e}")

        # 4. Load SHAP Summary & Category Drivers
        shap_path = os.path.join(self.artifacts_dir, "shap_summary.json")
        if os.path.exists(shap_path):
            try:
                with open(shap_path, "r", encoding="utf-8") as f:
                    self.shap_summary = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load shap_summary artifact: {e}")

        cat_path = os.path.join(self.artifacts_dir, "shap_category_drivers.json")
        if os.path.exists(cat_path):
            try:
                with open(cat_path, "r", encoding="utf-8") as f:
                    self.shap_category_drivers = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load shap_category_drivers artifact: {e}")

        # 5. Initialize TreeExplainers for ensemble & tree models
        try:
            if self.preprocessor_data and "feature_names" in self.preprocessor_data:
                feat_names = self.preprocessor_data["feature_names"]
                for mk in ["xgboost", "random_forest"]:
                    if mk in self.models:
                        self.shap_explainers[mk] = TrafficShapExplainer(
                            model=self.models[mk],
                            feature_names=feat_names,
                            model_id=mk,
                            artifacts_dir=self.artifacts_dir
                        )
                        logger.info(f"Initialized SHAP TreeExplainer for {mk}")
        except Exception as e:
            logger.warning(f"Could not initialize TreeExplainers: {e}")

    def is_model_available(self, model_key: str) -> bool:
        """Checks if the requested model and its dependencies are loaded."""
        if model_key == "historical_mean":
            return "historical_mean" in self.models
        return model_key in self.models and self.preprocessor_data is not None

    def get_loaded_models(self) -> List[str]:
        """Returns list of currently available model keys."""
        return [k for k in ["historical_mean", "linear_regression", "random_forest", "xgboost"] if self.is_model_available(k)]

    def get_best_model_key(self) -> str:
        """Returns the best model key based on genuine held-out test metrics."""
        return self.metrics.get("best_model", "historical_mean")

    def get_model_info(self, model_key: str) -> Dict[str, Any]:
        """Returns descriptive metadata for a model."""
        meta = self.metrics.get("models", {}).get(model_key, {})
        fallback = MODEL_METADATA_FALLBACK.get(model_key, {})
        return {
            "key": model_key,
            "name": meta.get("name", fallback.get("name", model_key)),
            "family": meta.get("family", fallback.get("family", "Predictive Estimator")),
            "version": "1.0.0",
            "role": meta.get("role", fallback.get("role", "Model")),
            "mae": meta.get("mae"),
            "rmse": meta.get("rmse"),
            "r2": meta.get("r2"),
            "is_primary": meta.get("is_primary", False)
        }

    def _prepare_feature_dataframe(self, input_features: Dict[str, Any]) -> pd.DataFrame:
        """Uses ML developer's impute logic to format features without duplicating code."""
        df_raw = pd.DataFrame([input_features])
        return self.preprocessor_wrapper._impute_inference_defaults(df_raw)

    def _transform_features(self, df_imputed: pd.DataFrame) -> np.ndarray:
        """Transforms input DataFrame using the fitted preprocessor pipeline artifact."""
        if not self.preprocessor_data or "preprocessor" not in self.preprocessor_data:
            raise PreprocessingArtifactMissingError(
                "Preprocessing pipeline artifact ('preprocessor.joblib') is missing or not loaded."
            )
        return self.preprocessor_data["preprocessor"].transform(df_imputed)

    def predict_scalar(self, model_key: str, input_features: Dict[str, Any]) -> float:
        """
        Executes genuine scalar prediction.
        Raises ModelNotAvailableError or PreprocessingArtifactMissingError if artifacts are absent.
        Validates output to prevent NaNs or infinite values.
        """
        valid_keys = ["historical_mean", "linear_regression", "random_forest", "xgboost"]
        if model_key not in valid_keys:
            raise ValueError(f"Unknown model_key '{model_key}'. Allowed: {valid_keys}")

        if model_key not in self.models:
            raise ModelNotAvailableError(
                f"Model artifact for '{model_key}' is not loaded or missing from artifacts directory."
            )

        if model_key == "historical_mean":
            loc_id = str(input_features.get("location_id", "")).strip()
            dow = int(input_features.get("day_of_week", 0))
            hr = int(input_features.get("hour", 0))
            raw_pred = self.models["historical_mean"].predict_instance(loc_id, dow, hr)
        else:
            df_imputed = self._prepare_feature_dataframe(input_features)
            X = self._transform_features(df_imputed)
            model = self.models[model_key]
            raw_pred = model.predict(X)[0]

        # Reliability check: validate output
        if raw_pred is None or np.isnan(raw_pred) or np.isinf(raw_pred):
            raise PredictionOutputValidationError(
                f"Model '{model_key}' produced invalid prediction value: {raw_pred}"
            )

        return float(np.clip(raw_pred, 0.0, 100.0))

    def explain_prediction(
        self,
        features: Dict[str, Any],
        model_key: str = "xgboost",
        prediction_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates individual prediction explanation with genuine additive efficiency:
        predicted_congestion = base_value + sum(attribution_value)
        Supports genuine TreeExplainer for XGBoost and Random Forest, and exact linear / segment attributions for baselines.
        """
        valid_keys = ["historical_mean", "linear_regression", "random_forest", "xgboost"]
        if model_key not in valid_keys:
            raise ValueError(f"Unknown model_key '{model_key}'. Allowed: {valid_keys}")

        if not self.is_model_available(model_key):
            raise ModelNotAvailableError(f"Model artifact for '{model_key}' is not loaded or unavailable.")

        pred_id = prediction_id or f"pred_{uuid.uuid4().hex[:10]}"
        raw_pred = self.predict_scalar(model_key, features)
        pred_congestion = round(raw_pred, 1)

        # Categorization according to contract
        if pred_congestion <= 25.0:
            category = "Low"
        elif pred_congestion <= 50.0:
            category = "Moderate"
        elif pred_congestion <= 75.0:
            category = "High"
        else:
            category = "Severe"

        model_info = self.get_model_info(model_key)

        # 1. Tree Models with genuine TreeExplainer (XGBoost, Random Forest)
        if model_key in self.shap_explainers and self.preprocessor_data:
            df_imp = self._prepare_feature_dataframe(features)
            X_trans = self._transform_features(df_imp)
            expl = self.shap_explainers[model_key]
            explanation = expl.explain_instance(
                x_instance=X_trans[0],
                raw_features_dict=features,
                prediction_id=pred_id
            )
            explanation["model_version"] = "1.0.0"
            explanation["congestion_category"] = category
            return explanation

        # 2. Linear Regression (Ridge) Exact Linear Attributions
        if model_key == "linear_regression" and self.preprocessor_data:
            df_imp = self._prepare_feature_dataframe(features)
            X_trans = self._transform_features(df_imp)[0]
            model = self.models["linear_regression"]
            feat_names = self.preprocessor_data.get("feature_names", [])
            unbounded_score = float(model.predict(X_trans.reshape(1, -1))[0])
            if not 0.0 <= unbounded_score <= 100.0:
                return {
                    "prediction_id": pred_id, "model_id": model_key, "model_name": model_info["name"],
                    "model_version": "1.0.0", "predicted_congestion": pred_congestion,
                    "congestion_category": category, "base_value": None, "additive_check": None,
                    "category_impacts": {}, "feature_contributions": [], "feature_values": features,
                    "explanation_summary": "Linear score was clipped to physical bounds. Additive feature explanation unavailable for the clipped output.",
                    "limitations_and_caveats": LIMITATIONS_AND_CAVEATS,
                }
            coefs = model.coef_
            intercept = float(model.intercept_)

            base_val = round(intercept, 2)
            contributions = []
            category_impacts = {
                "time_of_day": 0.0,
                "weather_condition": 0.0,
                "traffic_history": 0.0,
                "events_and_holidays": 0.0,
                "road_characteristics": 0.0,
                "spatial_location": 0.0,
            }

            raw_attributions = coefs * X_trans
            total_abs = float(np.sum(np.abs(raw_attributions))) or 1.0

            for name, val, impact in zip(feat_names, X_trans, raw_attributions):
                imp_val = round(float(impact), 2)
                cat_found = "other"
                for cat_name, cat_feats in FEATURE_CATEGORIES.items():
                    if name in cat_feats:
                        cat_found = cat_name
                        category_impacts[cat_name] += imp_val
                        break

                raw_val = features.get(name, round(float(val), 2))
                direction = "increases_congestion" if imp_val >= 0 else "dampens_congestion"
                contributions.append({
                    "feature": name,
                    "display_name": HUMAN_READABLE_NAMES.get(name, name.replace("_", " ").title()),
                    "category": cat_found,
                    "feature_value": raw_val,
                    "attribution_value": imp_val,
                    "direction": direction,
                    "percentage_contribution": round(abs(imp_val) / total_abs * 100.0, 1),
                })

            contributions.sort(key=lambda x: abs(x["attribution_value"]), reverse=True)
            sum_attr = round(float(np.sum([c["attribution_value"] for c in contributions])), 2)
            reconstructed = round(base_val + sum_attr, 2)

            for k in category_impacts:
                category_impacts[k] = round(category_impacts[k], 2)

            top_pos = [c for c in contributions if c["attribution_value"] > 0][:2]
            top_neg = [c for c in contributions if c["attribution_value"] < 0][:2]
            narrative = [f"Linear regression predicted congestion at {pred_congestion}% relative to base intercept of {base_val}%."]
            if top_pos:
                narrative.append("Upward drivers: " + ", ".join([f"{c['display_name']} (+{c['attribution_value']}%)" for c in top_pos]) + ".")
            if top_neg:
                narrative.append("Mitigating drivers: " + ", ".join([f"{c['display_name']} ({c['attribution_value']}%)" for c in top_neg]) + ".")

            return {
                "prediction_id": pred_id,
                "model_id": model_key,
                "model_name": model_info["name"],
                "model_version": "1.0.0",
                "predicted_congestion": pred_congestion,
                "congestion_category": category,
                "base_value": base_val,
                "additive_check": {
                    "base_value": base_val,
                    "sum_attributions": sum_attr,
                    "reconstructed_prediction": reconstructed,
                    "is_consistent": abs(reconstructed - pred_congestion) < 0.2
                },
                "category_impacts": category_impacts,
                "feature_contributions": contributions,
                "feature_values": features,
                "explanation_summary": " ".join(narrative),
                "limitations_and_caveats": LIMITATIONS_AND_CAVEATS
            }

        # Neither a lookup table nor a failed TreeExplainer supports feature SHAP values.
        return {
            "prediction_id": pred_id, "model_id": model_key,
            "model_name": model_info["name"], "model_version": "1.0.0",
            "predicted_congestion": pred_congestion, "congestion_category": category,
            "base_value": None, "additive_check": None, "category_impacts": {},
            "feature_contributions": [], "feature_values": features,
            "explanation_summary": "Feature explanation unavailable for this model. No substitute attributions were generated.",
            "limitations_and_caveats": LIMITATIONS_AND_CAVEATS,
        }

    def predict(
        self,
        city: str,
        location_code: str,
        hour: int,
        day_of_week: int,
        month: int = 11,
        model_type: str = "xgboost",
        temperature_c: float = 28.0,
        precipitation_mm: float = 0.0,
        humidity_pct: float = 65.0,
        wind_speed_kmh: float = 12.0,
        event_present: bool = False,
        event_name: str = "",
        event_type: Optional[str] = None,
        event_intensity: Optional[float] = None,
        road_lanes: int = 4,
        road_type: str = "primary",
        free_flow_speed: float = 60.0,
        accident_risk_score: float = 0.5,
        length_m: float = 3000.0,
        lag_speed_1h: Optional[float] = None,
        rolling_speed_3h: Optional[float] = None,
        location_name: Optional[str] = None,
        corridor_name: Optional[str] = None,
        prediction_date: Optional[str] = None,
        prediction_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full prediction pipeline returning standardized prediction and genuine SHAP explainability details.
        """
        is_peak = (8 <= hour <= 11) or (17 <= hour <= 21)
        is_weekend = (day_of_week >= 5)
        is_raining = (precipitation_mm > 0.5)

        resolved_event_type = event_type if event_type else ("Festival" if event_present else "None")
        resolved_event_intensity = float(event_intensity) if event_intensity is not None else (0.5 if event_present else 0.0)

        # Build clean input feature dictionary adhering to ML Integration Contract
        features: Dict[str, Any] = {
            "city": city,
            "location_id": str(location_code).strip(),
            "hour": int(hour),
            "day_of_week": int(day_of_week),
            "month": int(month),
            "temperature_2m_c": float(temperature_c),
            "precipitation_mm": float(precipitation_mm),
            "relative_humidity_2m_pct": float(humidity_pct),
            "wind_speed_10m_kmh": float(wind_speed_kmh),
            "road_lanes": int(road_lanes),
            "length_m": float(length_m),
            "accident_risk_score": float(accident_risk_score),
            "free_flow_speed_kmh": float(free_flow_speed),
            "road_type": str(road_type).lower(),
            "event_type": resolved_event_type,
            "event_intensity": resolved_event_intensity,
            "is_weekend": int(is_weekend),
            "is_peak_hour": int(is_peak),
            "is_holiday": 0,
            "event_present": 1 if event_present else 0,
            "is_raining": 1 if is_raining else 0,
        }
        if lag_speed_1h is not None:
            features["lag_speed_1h"] = float(lag_speed_1h)
        if rolling_speed_3h is not None:
            features["rolling_speed_3h"] = float(rolling_speed_3h)

        pred_id = f"pred_{uuid.uuid4().hex[:10]}"

        # 1. Genuine ML Prediction & Explanation
        explanation = self.explain_prediction(features, model_key=model_type, prediction_id=pred_id)
        predicted_pct = round(explanation["predicted_congestion"], 1)

        # 2. Genuine Historical Baseline
        if self.is_model_available("historical_mean"):
            baseline_val = self.predict_scalar("historical_mean", features)
            baseline_pct = round(baseline_val, 1)
        else:
            baseline_pct = None
        
        difference_pct = round(predicted_pct - baseline_pct, 1) if baseline_pct is not None else None
        category = explanation.get("congestion_category") or ("Low" if predicted_pct <= 25.0 else "Moderate" if predicted_pct <= 50.0 else "High" if predicted_pct <= 75.0 else "Severe")

        # 3. Model Metadata
        model_info = self.get_model_info(model_type)

        # 4. Map contributions to frontend shap_attributions list
        feature_contributions = explanation.get("feature_contributions", [])
        shap_attributions = [
            {
                "feature": c["feature"],
                "value": c.get("feature_value"),
                "impact_pct": round(float(c.get("attribution_value", 0.0)), 2)
            }
            for c in feature_contributions[:10]
        ]

        # RMSE alone does not establish a calibrated 95% interval.
        # 6. Formatted Timestamp
        p_date = prediction_date or pd.Timestamp.now(tz="Asia/Kolkata").date().isoformat()
        p_time = prediction_time or f"{hour:02d}:00"
        timestamp_str = pd.Timestamp.now(tz="Asia/Kolkata").isoformat()

        return {
            "prediction_id": pred_id,
            "status": "success",
            "timestamp": timestamp_str,
            "city": city,
            "location_id": location_code,
            "location_name": location_name or location_code,
            "corridor_name": corridor_name or location_code,
            "location_info": {
                "location_id": location_code,
                "city": city,
                "location_name": location_name or location_code,
                "corridor_name": corridor_name or location_code,
                "road_type": road_type,
                "road_lanes": road_lanes,
                "length_m": length_m,
                "free_flow_speed_kmh": free_flow_speed,
                "accident_risk_score": accident_risk_score,
            },
            "prediction_date": p_date,
            "prediction_time": p_time,
            "predicted_congestion_pct": predicted_pct,
            "congestion_category": category,
            "model_name": model_info["name"],
            "model_version": model_info["version"],
            "selected_model": model_type,
            "historical_baseline_pct": baseline_pct,
            "difference_pct": difference_pct,
            "confidence_interval": None,
            "input_features": features,
            "base_value": explanation.get("base_value"),
            "additive_check": explanation.get("additive_check"),
            "category_impacts": explanation.get("category_impacts"),
            "feature_contributions": feature_contributions,
            "explanation_summary": explanation.get("explanation_summary"),
            "limitations_and_caveats": (explanation.get("limitations_and_caveats") or []) + ["Traffic artifacts were trained on generated demonstration data. Real-world predictive validity is unverified.", "Missing lag speeds are imputed to free-flow speed; future scenarios are not live forecasts."],
            "shap_attributions": shap_attributions,
        }

    def get_global_feature_importance(self, model_key: str = "xgboost", limit: int = 15) -> Dict[str, Any]:
        """
        Retrieves genuine global SHAP feature importance computed from TreeExplainer.
        Does NOT use ordinary model feature importances (e.g. split counts) or fixed mock values.
        """
        if not self.shap_summary or "global_importance" not in self.shap_summary:
            raise ModelNotAvailableError("Global SHAP summary artifact ('shap_summary.json') is missing or not loaded.")

        global_imp = self.shap_summary["global_importance"]
        base_val = float(self.shap_summary.get("base_value", 24.05))

        descriptions = {
            "is_peak_hour": "Binary peak commute rush hour indicator (08:00-11:00, 17:00-21:00 IST)",
            "hour": "Continuous diurnal hour of day (0-23)",
            "lag_speed_1h": "Autoregressive lag speed reading from previous hour (t-1)",
            "day_of_week": "Weekly day index (weekday commuter traffic vs weekend leisure)",
            "road_lanes": "Carriageway physical lane width and throughput capacity",
            "rolling_speed_3h": "Trailing 3-hour localized corridor moving average speed",
            "accident_risk_score": "MoRTH arterial road safety and collision hazard index",
            "is_weekend": "Weekend indicator capturing Saturday/Sunday volume reductions",
            "free_flow_speed_kmh": "Uncongested baseline corridor free-flow design speed",
            "relative_humidity_2m_pct": "Relative atmospheric humidity percentage",
            "temperature_2m_c": "ERA5 ambient surface temperature in degrees Celsius",
            "length_m": "OpenStreetMap corridor segment length in meters",
            "city_Kolkata": "Kolkata municipal arterial network fixed effect",
            "precipitation_mm": "Hourly rainfall rate in millimeters per hour",
            "city_Hyderabad": "Hyderabad Cyberabad IT corridor spatial fixed effect",
            "month": "Seasonal month index (monsoon vs winter/dry periods)",
        }

        feature_items = []
        for idx, item in enumerate(global_imp[:limit]):
            f_name = item["feature"]
            disp_name = item.get("display_name", f_name.replace("_", " ").title())
            mean_shap = float(item["mean_abs_shap_pct"])
            feature_items.append({
                "name": f_name,
                "feature": f_name,
                "display_name": disp_name,
                "importance": round(mean_shap, 4),
                "mean_abs_shap_pct": round(mean_shap, 4),
                "category": item.get("category", "other"),
                "rank": idx + 1,
                "description": descriptions.get(f_name, disp_name)
            })

        return {
            "model": "XGBoost Regressor (TreeExplainer)",
            "model_version": "1.0.0",
            "base_value": round(base_val, 2),
            "features": feature_items,
            "total_features_evaluated": len(global_imp)
        }

    def get_explainability_summary(self) -> Dict[str, Any]:
        """
        Retrieves global explainability insights and domain drivers derived from TreeExplainer.
        Does NOT use hardcoded driver lists or fake impact values.
        """
        if not self.shap_summary or "global_importance" not in self.shap_summary:
            raise ModelNotAvailableError("SHAP summary artifact ('shap_summary.json') is missing or not loaded.")

        global_imp = self.shap_summary["global_importance"]
        base_val = float(self.shap_summary.get("base_value", 24.05))

        # Qualitative domain drivers from shap_category_drivers.json
        cat_drivers = self.shap_category_drivers
        if not cat_drivers:
            cat_drivers_path = os.path.join(self.artifacts_dir, "shap_category_drivers.json")
            if os.path.exists(cat_drivers_path):
                try:
                    with open(cat_drivers_path, "r", encoding="utf-8") as f:
                        cat_drivers = json.load(f)
                except Exception as e:
                    logger.warning(f"Could not load category drivers: {e}")

        driver_directions = {
            "is_peak_hour": "Increases Congestion",
            "hour": "Diurnal Commuter Rhythm",
            "lag_speed_1h": "Traffic Momentum",
            "day_of_week": "Modulates Congestion",
            "road_lanes": "Dampens Congestion",
            "rolling_speed_3h": "Traffic Momentum",
            "accident_risk_score": "Increases Congestion",
            "is_weekend": "Dampens Congestion",
            "free_flow_speed_kmh": "Dampens Congestion",
            "precipitation_mm": "Increases Congestion",
        }

        top_drivers = []
        for idx, item in enumerate(global_imp[:6]):
            f_name = item["feature"]
            disp = item.get("display_name", f_name)
            mean_shap = float(item["mean_abs_shap_pct"])
            top_drivers.append({
                "driver": disp,
                "feature": f_name,
                "mean_shap_pct": round(mean_shap, 2),
                "direction": "Magnitude only; direction varies by observation",
                "category": item.get("category", "other"),
                "rank": idx + 1
            })

        summary_text = "Global mean absolute SHAP values describe model associations on benchmark data; they do not establish causal direction or real-world forecast validity."

        return {
            "model": "XGBoost Regressor (TreeExplainer)",
            "model_version": "1.0.0",
            "base_value": round(base_val, 2),
            "top_drivers": top_drivers,
            "category_drivers": cat_drivers,
            "summary_text": summary_text,
            "limitations_and_caveats": LIMITATIONS_AND_CAVEATS
        }

inference_service = InferenceService()
