import joblib
import pandas as pd
import numpy as np

class HistoricalMeanBaseline:
    """
    Model 1: Historical Mean Baseline.
    Computes segment-specific hour-of-day and day-of-week average congestion
    from the chronological training partition.
    """
    def __init__(self):
        self.lookup_table = {}
        self.corridor_means = {}
        self.global_mean = 45.0

    def fit(self, train_df: pd.DataFrame):
        self.global_mean = float(train_df["congestion_percentage"].mean())
        
        # Corridor level means
        self.corridor_means = (
            train_df.groupby("location_id")["congestion_percentage"]
            .mean()
            .to_dict()
        )

        # Spatio-temporal lookup: (location_id, day_of_week, hour) -> mean congestion
        grouped = (
            train_df.groupby(["location_id", "day_of_week", "hour"])["congestion_percentage"]
            .mean()
            .to_dict()
        )
        self.lookup_table = grouped

    def predict_instance(self, location_id: str, day_of_week: int, hour: int) -> float:
        key = (location_id, day_of_week, hour)
        if key in self.lookup_table:
            return float(self.lookup_table[key])
        elif location_id in self.corridor_means:
            return float(self.corridor_means[location_id])
        return self.global_mean

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        preds = []
        for _, row in df.iterrows():
            loc = row.get("location_id", "")
            dow = int(row.get("day_of_week", 0))
            h = int(row.get("hour", 0))
            preds.append(self.predict_instance(loc, dow, h))
        return np.array(preds)

    def save(self, filepath: str = "ml/artifacts/model_historical_mean.joblib"):
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str = "ml/artifacts/model_historical_mean.joblib"):
        return joblib.load(filepath)
