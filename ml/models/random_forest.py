import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor

class RandomForestModel:
    """
    Model 3: Random Forest Regressor.
    Ensemble of bagging decision trees capturing non-linear interactions.
    """
    def __init__(self, n_estimators: int = 100, max_depth: int = 12, min_samples_split: int = 4, random_state: int = 42):
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            random_state=random_state,
            n_jobs=-1
        )

    def fit(self, X_train: np.ndarray, y_train: np.ndarray):
        self.model.fit(X_train, y_train)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.clip(self.model.predict(X), 0.0, 100.0)

    def get_feature_importances(self) -> np.ndarray:
        return self.model.feature_importances_

    def save(self, filepath: str = "ml/artifacts/model_random_forest.joblib"):
        joblib.dump(self.model, filepath)

    def load(self, filepath: str = "ml/artifacts/model_random_forest.joblib"):
        self.model = joblib.load(filepath)
