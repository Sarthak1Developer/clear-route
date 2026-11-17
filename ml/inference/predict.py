"""Public ML API backed by the same validated service used by FastAPI."""
from pathlib import Path
from backend.app.services.inference_service import InferenceService, inference_service

class TrafficInferenceEngine:
    def __init__(self, artifacts_dir=None):
        self.service = (InferenceService(str(Path(artifacts_dir).resolve()))
                        if artifacts_dir is not None else inference_service)

    @property
    def models(self):
        return self.service.models

    def predict(self, model_key, input_features):
        return self.service.predict_scalar(model_key, input_features)

    def predict_with_explanation(self, model_key, input_features, prediction_id=None):
        return self.service.explain_prediction(input_features, model_key, prediction_id)

engine = TrafficInferenceEngine()
