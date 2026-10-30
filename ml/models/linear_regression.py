import joblib
import numpy as np
from sklearn.linear_model import Ridge

class LinearRegressionModel:
    """
    Model 2: Linear Regression (Ridge Regularized).
    Provides an interpretable statistical baseline with sensitivity coefficients.
    """
    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.model = Ridge(alpha=self.alpha)

    def fit(self, X_train: np.ndarray, y_train: np.ndarray):
        self.model.fit(X_train, y_train)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.clip(self.model.predict(X), 0.0, 100.0)

    def get_coefficients(self, feature_names: list) -> dict:
        return dict(zip(feature_names, self.model.coef_))

    def save(self, filepath: str = "ml/artifacts/model_linear_regression.joblib"):
        joblib.dump(self.model, filepath)

    def load(self, filepath: str = "ml/artifacts/model_linear_regression.joblib"):
        self.model = joblib.load(filepath)
