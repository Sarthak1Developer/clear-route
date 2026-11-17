import os
import joblib
import json
import numpy as np
import pandas as pd
from ml.preprocessing.preprocessor import TrafficDataPreprocessor
from ml.explainability.shap_explainer import TrafficShapExplainer

class TrafficInferenceEngine:
    """
    Unified Inference & Real-Time Explainability Engine.
    Executes model predictions and generates standardized SHAP attributions.
    """
    def __init__(self, artifacts_dir: str = "ml/artifacts"):
        self.artifacts_dir = artifacts_dir
        self.preprocessor_wrapper = TrafficDataPreprocessor()
        self.preprocessor = None
        self.models = {}
        self.shap_summary = {}
        self.explainers = {}
        self.load_artifacts()

    def load_artifacts(self):
        prep_path = os.path.join(self.artifacts_dir, "preprocessor.joblib")
        if os.path.exists(prep_path):
            self.preprocessor = joblib.load(prep_path)

        for m_key in ["historical_mean", "linear_regression", "random_forest", "xgboost"]:
            p = os.path.join(self.artifacts_dir, f"model_{m_key}.joblib")
            if os.path.exists(p):
                self.models[m_key] = joblib.load(p)

        shap_path = os.path.join(self.artifacts_dir, "shap_summary.json")
        if os.path.exists(shap_path):
            with open(shap_path, "r") as f:
                self.shap_summary = json.load(f)

        # Build an explainer per supported tree model. Never reuse XGBoost
        # attributions for a prediction produced by a different estimator.
        feat_names = self.preprocessor.get("feature_names", []) if self.preprocessor else []
        for model_key in ("xgboost", "random_forest"):
            if model_key not in self.models or self.preprocessor is None:
                continue
            try:
                self.explainers[model_key] = TrafficShapExplainer(
                    model=self.models[model_key],
                    feature_names=feat_names,
                    model_id=model_key,
                    artifacts_dir=self.artifacts_dir
                )
            except Exception:
                self.explainers.pop(model_key, None)

    def _prepare_input_matrix(self, input_features: dict) -> np.ndarray:
        df_input = pd.DataFrame([input_features])
        df_imputed = self.preprocessor_wrapper._impute_inference_defaults(df_input)
        return self.preprocessor["preprocessor"].transform(df_imputed)

    def predict(self, model_key: str, input_features: dict) -> float:
        """Executes fast scalar prediction."""
        if model_key == "historical_mean":
            m = self.models.get("historical_mean")
            if m:
                return float(m.predict_instance(
                    input_features.get("location_id", ""),
                    int(input_features.get("day_of_week", 0)),
                    int(input_features.get("hour", 0))
                ))
            raise RuntimeError("Historical Mean model artifact is missing; prediction was not generated.")

        model = self.models.get(model_key)
        if not model:
            raise RuntimeError(f"Model artifact '{model_key}' is missing; prediction was not generated.")
        if not self.preprocessor:
            raise RuntimeError("Preprocessor artifact is missing; prediction was not generated.")

        X = self._prepare_input_matrix(input_features)
        pred = model.predict(X)[0]
        if pred is None or not np.isfinite(pred):
            raise ValueError(f"Model '{model_key}' produced an invalid prediction: {pred}")
        return float(np.clip(pred, 0.0, 100.0))

    def predict_with_explanation(self, model_key: str, input_features: dict, prediction_id: str = None) -> dict:
        """
        Executes prediction and generates a full standardized SHAP explanation payload.
        """
        predicted_val = self.predict(model_key, input_features)

        if model_key not in self.explainers or not self.preprocessor:
            return {
                "prediction_id": prediction_id,
                "model_id": model_key,
                "predicted_congestion": round(predicted_val, 2),
                "base_value": None,
                "feature_contributions": [],
                "explanation_status": "unavailable",
                "explanation_summary": (
                    f"Congestion predicted at {predicted_val:.1f}%. "
                    "A model-specific explainer is not available; no other model's explanation was substituted."
                ),
                "feature_values": input_features,
            }

        X = self._prepare_input_matrix(input_features)
        x_inst = X[0]

        explanation = self.explainers[model_key].explain_instance(
            x_instance=x_inst,
            raw_features_dict=input_features,
            prediction_id=prediction_id
        )
        return explanation

engine = TrafficInferenceEngine()
