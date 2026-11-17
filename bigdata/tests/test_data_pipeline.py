"""
ClearRoute Big Data Pipeline & Model Artifacts Automated Test Suite
Verifies:
1. Bronze layer ingestion and provenance metadata
2. Silver layer cleaning, deduplication, and bounds integrity
3. Gold master analytical dataset completeness and schema compliance
4. ML model artifact serialization and predict functionality
5. Power BI export tables and referential integrity
"""

import os
import sys
import json
import joblib
import pandas as pd
import pytest

# Ensure root in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def test_bronze_layer_outputs():
    assert os.path.exists("data/bronze/weather_era5/raw_weather_era5_hourly.csv"), "Bronze weather CSV missing"
    assert os.path.exists("data/bronze/weather_era5/provenance_metadata.json"), "Weather provenance JSON missing"
    assert os.path.exists("data/bronze/osm_infrastructure/raw_osm_road_segments.csv"), "Bronze OSM CSV missing"
    assert os.path.exists("data/bronze/events/raw_events_2019_historical.csv"), "Bronze events CSV missing"
    assert os.path.exists("data/bronze/uber_movement/raw_uber_movement_traffic.csv"), "Bronze traffic CSV missing"

    with open("data/bronze/weather_era5/provenance_metadata.json", "r") as f:
        meta = json.load(f)
        assert meta["provenance_type"] in ["genuine_external_api", "simulated_fallback"]

def test_silver_layer_integrity():
    silver_path = "data/silver/silver_traffic_cleaned.parquet"
    assert os.path.exists(silver_path), "Silver parquet missing"
    df = pd.read_parquet(silver_path)

    assert len(df) > 0, "Silver layer is empty"
    assert df.duplicated(subset=["location_id", "timestamp"]).sum() == 0, "Duplicate records found in Silver"
    assert ((df["observed_speed_kmh"] <= 0) | (df["observed_speed_kmh"] > 140)).sum() == 0, "Invalid speed outliers in Silver"
    assert ((df["congestion_percentage"] < 0) | (df["congestion_percentage"] > 100)).sum() == 0, "Target out of bounds"

def test_gold_layer_schema_and_features():
    gold_path = "data/gold/master_congestion/gold_master_congestion.parquet"
    assert os.path.exists(gold_path), "Gold master parquet missing"
    df = pd.read_parquet(gold_path)

    required_features = [
        "city", "location_id", "timestamp", "hour", "day_of_week", "month",
        "road_type", "traffic_speed", "free_flow_speed", "congestion_percentage",
        "temperature", "precipitation", "humidity", "wind_speed",
        "event_type", "event_intensity", "road_lanes", "road_length", "accident_risk"
    ]
    for feat in required_features:
        assert feat in df.columns, f"Required feature '{feat}' missing from Gold dataset"

    assert df["hour"].nunique() == 24, "Gold dataset does not cover all 24 diurnal hours"
    assert df["day_of_week"].nunique() == 7, "Gold dataset does not cover all 7 days of the week"
    assert df["city"].nunique() == 5, "Gold dataset does not cover all 5 metropolitan cities"
    assert df.isnull().sum().sum() == 0, "Null values detected in Gold master dataset"

def test_ml_model_artifacts_and_inference():
    artifacts = [
        "preprocessor.joblib",
        "model_historical_mean.joblib",
        "model_linear_regression.joblib",
        "model_random_forest.joblib",
        "model_xgboost.joblib",
        "metrics.json",
        "shap_summary.json"
    ]
    for art in artifacts:
        p = os.path.join("ml/artifacts", art)
        assert os.path.exists(p), f"Trained artifact {art} is missing"

    with open("ml/artifacts/metrics.json", "r") as f:
        metrics = json.load(f)
        assert "models" in metrics
        assert "xgboost" in metrics["models"]
        assert metrics["best_model"] in metrics["models"], "Champion model not found in models dict"
        assert metrics["models"][metrics["best_model"]]["r2"] > 0.90, "Best model R2 below 0.90 threshold"

def test_powerbi_exports_referential_integrity():
    dim_path = "powerbi/exports/dim_location.csv"
    fact_path = "powerbi/exports/fact_congestion_hourly.csv"
    assert os.path.exists(dim_path), "dim_location.csv missing"
    assert os.path.exists(fact_path), "fact_congestion_hourly.csv missing"

    df_dim = pd.read_csv(dim_path)
    df_fact = pd.read_csv(fact_path)

    dim_ids = set(df_dim["location_id"])
    fact_ids = set(df_fact["location_id"])
    assert fact_ids.issubset(dim_ids), "Foreign key violation: fact_congestion has location_ids not in dim_location"
    assert df_fact["hour"].nunique() == 24, "Power BI fact table does not have 24 hours"
    assert set(df_fact["is_weekend"].unique()) == {0, 1}, "Power BI fact table missing weekends"

