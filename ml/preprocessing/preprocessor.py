"""
ClearRoute Machine Learning Preprocessing Pipeline
Standardizes continuous numerical features, one-hot encodes categoricals,
and preserves binary flags. Preprocessing is strictly fit on the training split only.
"""

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
            "free_flow_speed_kmh", "event_intensity", "lag_speed_1h", "rolling_speed_3h"
        ]
        self.cat_features = ["road_type", "event_type", "city"]
        self.binary_features = ["is_weekend", "is_peak_hour", "is_holiday", "event_present", "is_raining"]
        self.target_col = "congestion_percentage"
        
        self.preprocessor = None
        self.feature_names = []

    def chronological_split(self, df: pd.DataFrame, train_ratio: float = 0.70, val_ratio: float = 0.15):
        """
        Performs strict chronological splitting (70% train, 15% val, 15% test)
        to prevent temporal data leakage and preserve real time-series causality.
        """
        if not 0 < train_ratio < 1 or not 0 < val_ratio < 1 or train_ratio + val_ratio >= 1:
            raise ValueError("Split ratios must leave nonempty train, validation and test partitions")
        df = df.sort_values(by="timestamp", kind="stable").reset_index(drop=True)
        times = df["timestamp"].drop_duplicates().tolist()
        train_end = int(len(times) * train_ratio)
        val_end = int(len(times) * (train_ratio + val_ratio))
        if not 0 < train_end < val_end < len(times):
            raise ValueError("Insufficient distinct timestamps for chronological partitions")
        train_df = df[df["timestamp"] < times[train_end]].copy()
        val_df = df[(df["timestamp"] >= times[train_end]) & (df["timestamp"] < times[val_end])].copy()
        test_df = df[df["timestamp"] >= times[val_end]].copy()

        return train_df, val_df, test_df

    def _impute_inference_defaults(self, df: pd.DataFrame) -> pd.DataFrame:
        """Safely imputes expected feature defaults if called with incomplete inference payloads."""
        df = df.copy()
        defaults_num = {
            "hour": 12, "day_of_week": 0, "month": 6,
            "temperature_2m_c": 28.0, "precipitation_mm": 0.0,
            "relative_humidity_2m_pct": 60.0, "wind_speed_10m_kmh": 12.0,
            "road_lanes": 6, "length_m": 2500.0, "accident_risk_score": 0.55,
            "free_flow_speed_kmh": 55.0, "event_intensity": 0.0,
        }
        for col, val in defaults_num.items():
            if col not in df.columns:
                df[col] = val
            else:
                df[col] = df[col].fillna(val)

        # Lags default to free-flow baseline if not supplied during forward inference
        if "lag_speed_1h" not in df.columns:
            df["lag_speed_1h"] = df["free_flow_speed_kmh"]
        else:
            df["lag_speed_1h"] = df["lag_speed_1h"].fillna(df["free_flow_speed_kmh"])

        if "rolling_speed_3h" not in df.columns:
            df["rolling_speed_3h"] = df["free_flow_speed_kmh"]
        else:
            df["rolling_speed_3h"] = df["rolling_speed_3h"].fillna(df["free_flow_speed_kmh"])

        defaults_cat = {"road_type": "primary", "event_type": "None", "city": "Delhi"}
        for col, val in defaults_cat.items():
            if col not in df.columns:
                df[col] = val
            else:
                df[col] = df[col].fillna(val)

        derived = {
            "is_weekend": (df["day_of_week"] >= 5).astype(int),
            "is_peak_hour": (df["hour"].between(8, 11) | df["hour"].between(17, 21)).astype(int),
            "is_raining": (df["precipitation_mm"] > 0.5).astype(int),
            "event_present": (~df["event_type"].isin(["None", "No Event"])).astype(int),
            "is_holiday": 0,
        }
        for col, default in derived.items():
            df[col] = df[col].fillna(default).astype(int) if col in df else default

        return df

    def fit_transform(self, train_df: pd.DataFrame):
        train_df = self._impute_inference_defaults(train_df)
        
        self.preprocessor = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), self.num_features),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), self.cat_features),
                ("bin", "passthrough", self.binary_features),
            ]
        )
        
        X_train = self.preprocessor.fit_transform(train_df)
        y_train = train_df[self.target_col].values

        # Build human-readable feature names list
        cat_names = self.preprocessor.named_transformers_["cat"].get_feature_names_out(self.cat_features).tolist()
        self.feature_names = self.num_features + cat_names + self.binary_features

        return X_train, y_train

    def transform(self, df: pd.DataFrame):
        df_imputed = self._impute_inference_defaults(df)
        X = self.preprocessor.transform(df_imputed)
        y = df[self.target_col].values if self.target_col in df.columns else None
        return X, y

    def save(self, filepath: str = "ml/artifacts/preprocessor.joblib"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({
            "preprocessor": self.preprocessor,
            "feature_names": self.feature_names,
            "num_features": self.num_features,
            "cat_features": self.cat_features,
            "binary_features": self.binary_features,
            "target_col": self.target_col
        }, filepath)

    def load(self, filepath: str = "ml/artifacts/preprocessor.joblib"):
        data = joblib.load(filepath)
        self.preprocessor = data["preprocessor"]
        self.feature_names = data["feature_names"]
        self.num_features = data.get("num_features", self.num_features)
        self.cat_features = data.get("cat_features", self.cat_features)
        self.binary_features = data.get("binary_features", self.binary_features)
        self.target_col = data.get("target_col", self.target_col)
