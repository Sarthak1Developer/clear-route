import os
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

class TrafficDataPreprocessor:
    def __init__(self):
        self.num_features = [
            "hour", "day_of_week", "month", "temperature_2m_c",
            "precipitation_mm", "relative_humidity_2m_pct", "wind_speed_10m_kmh",
            "road_lanes", "length_m", "accident_risk_score",
            "free_flow_speed_kmh", "lag_speed_1h", "rolling_speed_3h"
        ]
        self.cat_features = ["road_type", "event_type"]
        self.binary_features = ["is_weekend", "is_peak_hour", "is_holiday", "event_present", "is_raining"]
        self.target_col = "congestion_percentage"
        
        self.preprocessor = None
        self.feature_names = []

    def chronological_split(self, df: pd.DataFrame, train_ratio: float = 0.70, val_ratio: float = 0.15):
        """
        Performs strict chronological splitting (70% train, 15% val, 15% test)
        to prevent temporal data leakage and preserve time-series ordering.
        """
        df = df.sort_values(by="timestamp").reset_index(drop=True)
        n = len(df)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        train_df = df.iloc[:train_end].copy()
        val_df = df.iloc[train_end:val_end].copy()
        test_df = df.iloc[val_end:].copy()

        return train_df, val_df, test_df

    def fit_transform(self, train_df: pd.DataFrame):
        self.preprocessor = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), self.num_features),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), self.cat_features),
                ("bin", "passthrough", self.binary_features),
            ]
        )
        
        X_train = self.preprocessor.fit_transform(train_df)
        y_train = train_df[self.target_col].values

        # Build feature names list
        cat_names = self.preprocessor.named_transformers_["cat"].get_feature_names_out(self.cat_features).tolist()
        self.feature_names = self.num_features + cat_names + self.binary_features

        return X_train, y_train

    def transform(self, df: pd.DataFrame):
        X = self.preprocessor.transform(df)
        y = df[self.target_col].values if self.target_col in df.columns else None
        return X, y

    def save(self, filepath: str = "ml/artifacts/preprocessor.joblib"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({"preprocessor": self.preprocessor, "feature_names": self.feature_names}, filepath)

    def load(self, filepath: str = "ml/artifacts/preprocessor.joblib"):
        data = joblib.load(filepath)
        self.preprocessor = data["preprocessor"]
        self.feature_names = data["feature_names"]
