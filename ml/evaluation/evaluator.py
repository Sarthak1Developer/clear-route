"""
ClearRoute Model Evaluation Engine
Computes genuine held-out test set metrics, residual diagnostics,
and subgroup slices across cities, corridors, and traffic conditions.
"""

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

class ModelEvaluator:
    @staticmethod
    def evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)

        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        r2 = float(r2_score(y_true, y_pred))

        residuals = y_true - y_pred
        skewness = float(stats.skew(residuals)) if len(residuals) > 2 else 0.0

        p5, p25, p50, p75, p95 = np.percentile(residuals, [5, 25, 50, 75, 95])
        iqr = p75 - p25

        return {
            "mae": round(mae, 3),
            "rmse": round(rmse, 3),
            "r2": round(r2, 4),
            "residuals": {
                "mean": round(float(np.mean(residuals)), 3),
                "std": round(float(np.std(residuals)), 3),
                "median": round(float(p50), 3),
                "skewness": round(skewness, 3),
                "p5": round(float(p5), 3),
                "p25": round(float(p25), 3),
                "p75": round(float(p75), 3),
                "p95": round(float(p95), 3),
                "iqr": round(float(iqr), 3),
            }
        }

    @staticmethod
    def evaluate_by_city(df_test: pd.DataFrame, y_true: np.ndarray, y_pred: np.ndarray) -> dict:
        results = {}
        for city in sorted(df_test["city"].unique()):
            mask = (df_test["city"] == city).values
            if np.sum(mask) > 0:
                y_t = y_true[mask]
                y_p = y_pred[mask]
                results[city] = {
                    "samples": int(np.sum(mask)),
                    "mae": round(float(mean_absolute_error(y_t, y_p)), 3),
                    "rmse": round(float(np.sqrt(mean_squared_error(y_t, y_p))), 3),
                    "r2": round(float(r2_score(y_t, y_p)), 4),
                }
        return results

    @staticmethod
    def evaluate_by_condition(df_test: pd.DataFrame, y_true: np.ndarray, y_pred: np.ndarray) -> dict:
        conditions = {
            "Peak Hours (08-11 & 17-21)": df_test["is_peak_hour"] == 1,
            "Off-Peak Hours": df_test["is_peak_hour"] == 0,
            "Weekdays (Mon-Fri)": df_test["is_weekend"] == 0,
            "Weekends (Sat-Sun)": df_test["is_weekend"] == 1,
            "Rainy Weather (>0.5mm)": df_test["precipitation_mm"] > 0.5,
            "Dry Weather (<=0.5mm)": df_test["precipitation_mm"] <= 0.5,
            "Low Congestion (0-25%)": df_test["congestion_percentage"] <= 25.0,
            "Moderate Congestion (26-50%)": (df_test["congestion_percentage"] > 25.0) & (df_test["congestion_percentage"] <= 50.0),
            "High Congestion (51-75%)": (df_test["congestion_percentage"] > 50.0) & (df_test["congestion_percentage"] <= 75.0),
            "Severe Congestion (>75%)": df_test["congestion_percentage"] > 75.0,
        }

        results = {}
        for cond_name, mask_series in conditions.items():
            mask = mask_series.values
            if np.sum(mask) > 5:
                y_t = y_true[mask]
                y_p = y_pred[mask]
                results[cond_name] = {
                    "samples": int(np.sum(mask)),
                    "mae": round(float(mean_absolute_error(y_t, y_p)), 3),
                    "rmse": round(float(np.sqrt(mean_squared_error(y_t, y_p))), 3),
                    "r2": round(float(r2_score(y_t, y_p)), 4) if len(np.unique(y_t)) > 1 else 0.0,
                }
        return results
