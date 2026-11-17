import joblib
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score

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

    def tune_and_fit(self, X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray):
        best_alpha = self.alpha
        best_r2 = -float("inf")
        for a in [0.01, 0.1, 1.0, 10.0, 50.0, 100.0]:
            r = Ridge(alpha=a)
            r.fit(X_train, y_train)
            val_r2 = float(r2_score(y_val, r.predict(X_val)))
            if val_r2 > best_r2:
                best_r2 = val_r2
                best_alpha = a
        self.alpha = best_alpha
        self.model = Ridge(alpha=self.alpha)
        self.model.fit(X_train, y_train)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.clip(self.model.predict(X), 0.0, 100.0)

    def get_coefficients(self, feature_names: list) -> dict:
        return dict(zip(feature_names, self.model.coef_))

    def save(self, filepath: str = "ml/artifacts/model_linear_regression.joblib"):
        joblib.dump(self.model, filepath)

    def load(self, filepath: str = "ml/artifacts/model_linear_regression.joblib"):
        self.model = joblib.load(filepath)
