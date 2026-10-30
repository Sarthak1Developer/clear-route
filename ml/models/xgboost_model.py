import joblib
import numpy as np
from xgboost import XGBRegressor

class XGBoostModel:
    """
    Model 4: XGBoost Regressor (Primary Prediction Model).
    State-of-the-art gradient boosted decision tree framework.
    """
    def __init__(
        self,
        n_estimators: int = 150,
        learning_rate: float = 0.05,
        max_depth: int = 6,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        random_state: int = 42
    ):
        self.model = XGBRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            objective="reg:squarederror",
            random_state=random_state,
            n_jobs=-1
        )

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, eval_set: list = None):
        if eval_set:
            self.model.fit(X_train, y_train, eval_set=eval_set, verbose=False)
        else:
            self.model.fit(X_train, y_train, verbose=False)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.clip(self.model.predict(X), 0.0, 100.0)

    def get_feature_importances(self) -> np.ndarray:
        return self.model.feature_importances_

    def save(self, filepath: str = "ml/artifacts/model_xgboost.joblib"):
        joblib.dump(self.model, filepath)

    def load(self, filepath: str = "ml/artifacts/model_xgboost.joblib"):
        self.model = joblib.load(filepath)
