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
        self.explainer = None
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

        # Initialize TreeExplainer on primary model if available
        try:
            if "xgboost" in self.models and self.preprocessor:
                feat_names = self.preprocessor.get("feature_names", [])
                self.explainer = TrafficShapExplainer(
                    model=self.models["xgboost"],
                    feature_names=feat_names,
                    model_id="xgboost",
                    artifacts_dir=self.artifacts_dir
                )
        except Exception:
            self.explainer = None

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
            return 25.0

        model = self.models.get(model_key)
        if not model or not self.preprocessor:
            return 25.0

        X = self._prepare_input_matrix(input_features)
        pred = model.predict(X)[0]
        return float(np.clip(pred, 0.0, 100.0))

    def predict_with_explanation(self, model_key: str, input_features: dict, prediction_id: str = None) -> dict:
        """
        Executes prediction and generates a full standardized SHAP explanation payload.
        """
        predicted_val = self.predict(model_key, input_features)

        if not self.explainer or not self.preprocessor:
            return {
                "prediction_id": prediction_id,
                "model_id": model_key,
                "predicted_congestion": round(predicted_val, 2),
                "base_value": 24.05,
                "feature_contributions": [],
                "explanation_summary": f"Congestion predicted at {predicted_val:.1f}%. SHAP explainer uninitialized.",
                "feature_values": input_features,
            }

        X = self._prepare_input_matrix(input_features)
        x_inst = X[0]

        explanation = self.explainer.explain_instance(
            x_instance=x_inst,
            raw_features_dict=input_features,
            prediction_id=prediction_id
        )
        return explanation

engine = TrafficInferenceEngine()
