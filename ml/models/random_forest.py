import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

class RandomForestModel:
    """
    Model 3: Random Forest Regressor.
    Ensemble of bagging decision trees capturing non-linear interactions
    with constrained tree depth for low RAM consumption and fast serialization.
    """
    def __init__(self, n_estimators: int = 50, max_depth: int = 10, min_samples_split: int = 6, min_samples_leaf: int = 4, random_state: int = 42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.random_state = random_state
        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            max_features="sqrt",
            random_state=self.random_state,
            n_jobs=-1
        )

    def fit(self, X_train: np.ndarray, y_train: np.ndarray):
        self.model.fit(X_train, y_train)

    def tune_and_fit(self, X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray):
        best_depth = self.max_depth
        best_r2 = -float("inf")
        # Validate depth candidates keeping memory footprint low
        for d in [8, 10, 12]:
            rf = RandomForestRegressor(
                n_estimators=self.n_estimators,
                max_depth=d,
                min_samples_split=self.min_samples_split,
                min_samples_leaf=self.min_samples_leaf,
                max_features="sqrt",
                random_state=self.random_state,
                n_jobs=-1
            )
            rf.fit(X_train, y_train)
            val_r2 = float(r2_score(y_val, rf.predict(X_val)))
            if val_r2 > best_r2:
                best_r2 = val_r2
                best_depth = d

        self.max_depth = best_depth
        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            max_features="sqrt",
            random_state=self.random_state,
            n_jobs=-1
        )
        self.model.fit(X_train, y_train)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.clip(self.model.predict(X), 0.0, 100.0)

    def get_feature_importances(self) -> np.ndarray:
        return self.model.feature_importances_

    def save(self, filepath: str = "ml/artifacts/model_random_forest.joblib"):
        joblib.dump(self.model, filepath, compress=3)

    def load(self, filepath: str = "ml/artifacts/model_random_forest.joblib"):
        self.model = joblib.load(filepath)
