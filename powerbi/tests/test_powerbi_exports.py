"""
ClearRoute Power BI Component Validation Test Suite
Tests:
1. Export file completeness & existence
2. Star schema referential integrity & primary key uniqueness
3. Genuine ML evaluation metrics reconciliation (no hardcoding)
4. Dashboard measures & aggregation correctness against Gold master
5. Refresh audit metadata validity
"""

import os
import sys
import json
import pytest
import pandas as pd
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

EXPORTS_DIR = os.path.join(ROOT_DIR, "powerbi/exports")
GOLD_PARQUET = os.path.join(ROOT_DIR, "data/gold/master_congestion/gold_master_congestion.parquet")
METRICS_JSON = os.path.join(ROOT_DIR, "ml/artifacts/metrics.json")


def test_export_files_completeness():
    required_files = [
        "dim_location.csv",
        "dim_date.csv",
        "dim_time.csv",
        "dim_event.csv",
        "dim_weather_category.csv",
        "fact_congestion_hourly.csv",
        "city_congestion_summary.csv",
        "location_congestion_summary.csv",
        "hourly_congestion_summary.csv",
        "weather_impact_summary.csv",
        "weather_temperature_summary.csv",
        "event_impact_summary.csv",
        "model_performance_summary.csv",
        "model_actual_vs_predicted.csv",
        "model_subgroup_performance.csv",
        "model_feature_importance.csv",
        "corridor_predictive_risk.csv",
        "shap_category_drivers.csv",
        "refresh_metadata.csv",
        "refresh_metadata.json"
    ]
    for fname in required_files:
        fpath = os.path.join(EXPORTS_DIR, fname)
        assert os.path.exists(fpath), f"Missing Power BI export artifact: {fname}"
        assert os.path.getsize(fpath) > 0, f"Export artifact {fname} is empty"


def test_star_schema_primary_and_foreign_keys():
    dim_loc = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_location.csv"))
    dim_date = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_date.csv"))
    dim_time = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_time.csv"))
    dim_event = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_event.csv"))
    fact = pd.read_csv(os.path.join(EXPORTS_DIR, "fact_congestion_hourly.csv"))
    act_pred = pd.read_csv(os.path.join(EXPORTS_DIR, "model_actual_vs_predicted.csv"))
    risk = pd.read_csv(os.path.join(EXPORTS_DIR, "corridor_predictive_risk.csv"))

    # Primary key uniqueness
    assert dim_loc["location_id"].is_unique, "dim_location.location_id must be unique PK"
    assert dim_date["date"].is_unique, "dim_date.date must be unique PK"
    assert dim_time["hour"].is_unique, "dim_time.hour must be unique PK"
    assert dim_event["event_id"].is_unique, "dim_event.event_id must be unique PK"
    assert risk["location_id"].is_unique, "corridor_predictive_risk.location_id must be unique PK"

    # Referential integrity
    assert set(fact["location_id"]).issubset(set(dim_loc["location_id"])), "Foreign key violation: fact -> dim_location"
    assert set(fact["date"]).issubset(set(dim_date["date"])), "Foreign key violation: fact -> dim_date"
    assert set(fact["hour"]).issubset(set(dim_time["hour"])), "Foreign key violation: fact -> dim_time"
    assert set(act_pred["location_id"]).issubset(set(dim_loc["location_id"])), "Foreign key violation: act_pred -> dim_location"
    assert set(risk["location_id"]).issubset(set(dim_loc["location_id"])), "Foreign key violation: risk -> dim_location"


def test_reconciliation_against_gold_master():
    df_gold = pd.read_parquet(GOLD_PARQUET)
    fact = pd.read_csv(os.path.join(EXPORTS_DIR, "fact_congestion_hourly.csv"))

    assert len(fact) == len(df_gold), "Fact row count must exactly match Gold dataset row count (165,000)"
    gold_mean = df_gold["congestion_percentage"].mean()
    fact_mean = fact["congestion_percentage"].mean()
    assert abs(gold_mean - fact_mean) < 0.05, f"Mean congestion mismatch: Gold={gold_mean:.2f}, Fact={fact_mean:.2f}"

    gold_speed_mean = df_gold["observed_speed_kmh"].mean()
    fact_speed_mean = fact["observed_speed_kmh"].mean()
    assert abs(gold_speed_mean - fact_speed_mean) < 0.1, f"Mean speed mismatch: Gold={gold_speed_mean:.1f}, Fact={fact_speed_mean:.1f}"


def test_ml_evaluation_metrics_not_hardcoded():
    with open(METRICS_JSON, "r") as f:
        meta = json.load(f)
    
    perf_df = pd.read_csv(os.path.join(EXPORTS_DIR, "model_performance_summary.csv"))
    assert len(perf_df) == 4, "Must evaluate exactly 4 finalized models"
    
    models = meta["models"]
    for _, row in perf_df.iterrows():
        m_key = row["model_key"]
        assert m_key in models, f"Model key {m_key} not in metrics.json"
        assert abs(row["mae"] - models[m_key]["mae"]) < 0.001, f"MAE mismatch for {m_key}"
        assert abs(row["rmse"] - models[m_key]["rmse"]) < 0.001, f"RMSE mismatch for {m_key}"
        assert abs(row["r2_score"] - models[m_key]["r2"]) < 0.001, f"R2 mismatch for {m_key}"

    # Champion model verification
    champion_row = perf_df[perf_df["is_champion"] == 1]
    assert len(champion_row) == 1, "Exactly one champion model must be flagged"
    assert champion_row.iloc[0]["model_key"] == meta["best_model"]


def test_model_actual_vs_predicted_integrity():
    act_pred = pd.read_csv(os.path.join(EXPORTS_DIR, "model_actual_vs_predicted.csv"))
    assert len(act_pred) == 24750, "Test set size must be exactly 24,750 (15% chronological split)"

    # Check bounds
    assert ((act_pred["actual_congestion_pct"] < 0) | (act_pred["actual_congestion_pct"] > 100)).sum() == 0
    assert ((act_pred["pred_xgboost"] < 0) | (act_pred["pred_xgboost"] > 100)).sum() == 0
    assert ((act_pred["pred_historical_mean"] < 0) | (act_pred["pred_historical_mean"] > 100)).sum() == 0

    # Residual calculation check
    diff_xgb = np.abs((act_pred["actual_congestion_pct"] - act_pred["pred_xgboost"]) - act_pred["residual_xgboost"])
    assert (diff_xgb > 0.02).sum() == 0, "Residual math mismatch in XGBoost"


def test_refresh_audit_metadata():
    with open(os.path.join(EXPORTS_DIR, "refresh_metadata.json"), "r") as f:
        meta = json.load(f)
    assert meta["pipeline_status"] == "SUCCESS"
    assert meta["source_dataset_records"] == 165000
    assert meta["metropolitan_cities_count"] == 5
    assert meta["corridors_monitored_count"] == 25
    assert meta["models_evaluated_count"] == 4
    assert "refresh_timestamp_utc" in meta
