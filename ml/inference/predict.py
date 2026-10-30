import os
import joblib
import json
import numpy as np
import pandas as pd

class TrafficInferenceEngine:
    def __init__(self, artifacts_dir: str = "ml/artifacts"):
        self.artifacts_dir = artifacts_dir
        self.preprocessor = None
        self.models = {}
        self.shap_summary = {}
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

    def predict(self, model_key: str, input_features: dict) -> float:
        if model_key == "historical_mean":
            m = self.models.get("historical_mean")
            if m:
                return float(m.predict_instance(
                    input_features.get("location_id", ""),
                    int(input_features.get("day_of_week", 0)),
                    int(input_features.get("hour", 0))
                ))
            return 45.0

        model = self.models.get(model_key)
        if not model or not self.preprocessor:
            return 45.0

        df_input = pd.DataFrame([input_features])
        X = self.preprocessor["preprocessor"].transform(df_input)
        pred = model.predict(X)[0]
        return float(np.clip(pred, 0.0, 100.0))

engine = TrafficInferenceEngine()
