import os
import json
import logging
import numpy as np
import shap

logger = logging.getLogger("shap_explainer")

class TrafficShapExplainer:
    def __init__(self, model, feature_names: list):
        self.model = model
        self.feature_names = feature_names
        self.explainer = None

    def initialize_tree_explainer(self):
        try:
            self.explainer = shap.TreeExplainer(self.model)
            logger.info("SHAP TreeExplainer initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not initialize TreeExplainer directly: {e}")

    def compute_global_importance(self, X_sample: np.ndarray) -> list:
        if not self.explainer:
            self.initialize_tree_explainer()

        shap_values = self.explainer.shap_values(X_sample)
        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)

        importance_list = []
        for name, imp in zip(self.feature_names, mean_abs_shap):
            importance_list.append({
                "feature": name,
                "importance": round(float(imp), 4),
            })

        importance_list.sort(key=lambda x: x["importance"], reverse=True)
        return importance_list

    def explain_instance(self, x_instance: np.ndarray) -> list:
        if not self.explainer:
            self.initialize_tree_explainer()

        shap_values = self.explainer.shap_values(x_instance.reshape(1, -1))[0]
        attributions = []
        for name, val, impact in zip(self.feature_names, x_instance, shap_values):
            attributions.append({
                "feature": name,
                "value": round(float(val), 2),
                "impact_pct": round(float(impact), 2),
            })

        attributions.sort(key=lambda x: abs(x["impact_pct"]), reverse=True)
        return attributions

    def save_summary(self, importance_list: list, filepath: str = "ml/artifacts/shap_summary.json"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump({"global_importance": importance_list}, f, indent=2)
        logger.info(f"SHAP global feature importance saved to {filepath}")
