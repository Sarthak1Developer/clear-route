"""
ClearRoute Big Data Pipeline - Silver Layer
Transformation: Cleaning, Standardization, Outlier Treatment & Geometric Integrity

Transforms raw Bronze traffic velocity records and OpenStreetMap road infrastructure:
1. Deduplication by (location_id, timestamp)
2. ISO 8601 Indian Standard Time timestamp parsing and calendar attribute normalization
3. Physical speed bounds validation (0 < speed <= 140 km/h)
4. Standard mathematical Congestion Index (CI) and Percentage (CP) derivation
5. Safe 1-to-1 join with road infrastructure without record duplication
6. Geographic bounding box spatial validation for all 5 metropolitan municipal areas
7. Parquet and CSV output serialization

Provenance: ClearRoute Silver Cleaned Tier
"""

import os
import sys
import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger("silver_cleaning")

# Official Municipal Bounding Boxes for Spatial Validation
MUNICIPAL_BOUNDS = {
    "Delhi": {"min_lat": 28.40, "max_lat": 28.88, "min_lng": 76.84, "max_lng": 77.40},
    "Mumbai": {"min_lat": 18.89, "max_lat": 19.30, "min_lng": 72.75, "max_lng": 73.05},
    "Bengaluru": {"min_lat": 12.80, "max_lat": 13.15, "min_lng": 77.45, "max_lng": 77.80},
    "Hyderabad": {"min_lat": 17.20, "max_lat": 17.60, "min_lng": 78.20, "max_lng": 78.65},
    "Kolkata": {"min_lat": 22.40, "max_lat": 22.75, "min_lng": 88.25, "max_lng": 88.55},
}

def clean_silver_layer(
    bronze_traffic_path: str = "data/bronze/uber_movement/raw_uber_movement_traffic.csv",
    bronze_osm_path: str = "data/bronze/osm_infrastructure/raw_osm_road_segments.csv",
    output_dir: str = "data/silver"
) -> str:
    """Executes Silver layer cleaning, standardization, and target derivation."""
    os.makedirs(output_dir, exist_ok=True)
    logger.info("Executing Silver Layer Data Cleaning & Standardization Job...")

    # 1. Load Bronze Datasets
    df_traffic = pd.read_csv(bronze_traffic_path)
    df_osm = pd.read_csv(bronze_osm_path)
    initial_count = len(df_traffic)
    logger.info(f"Loaded {initial_count} raw traffic records from Bronze.")

    # 2. Deduplication on Unique Natural Key
    df_traffic = df_traffic.drop_duplicates(subset=["location_id", "timestamp"], keep="last")
    dedup_count = initial_count - len(df_traffic)
    if dedup_count > 0:
        logger.info(f"Deduplication complete: {dedup_count} duplicates removed.")

    # 3. Timestamp Normalization & Calendar Parsing (IST UTC+05:30)
    df_traffic["timestamp"] = pd.to_datetime(df_traffic["timestamp"])
    df_traffic["date"] = df_traffic["timestamp"].dt.date.astype(str)
    df_traffic["hour"] = df_traffic["timestamp"].dt.hour
    df_traffic["day_of_week"] = df_traffic["timestamp"].dt.dayofweek
    df_traffic["month"] = df_traffic["timestamp"].dt.month
    df_traffic["is_weekend"] = (df_traffic["day_of_week"] >= 5).astype(int)
    
    # Peak Commute Windows: 08:00 - 11:00 and 17:00 - 21:00 IST
    df_traffic["is_peak_hour"] = (
        ((df_traffic["hour"] >= 8) & (df_traffic["hour"] <= 11)) |
        ((df_traffic["hour"] >= 17) & (df_traffic["hour"] <= 21))
    ).astype(int)

    # 4. Outlier Investigation & Imputation
    # Flag impossible negative speeds or speeds exceeding 140 km/h in urban corridors
    invalid_mask = (df_traffic["observed_speed_kmh"] <= 0) | (df_traffic["observed_speed_kmh"] > 140.0)
    if invalid_mask.sum() > 0:
        logger.warning(f"Found {invalid_mask.sum()} invalid speed readings. Imputing with corridor-hour median.")
        corridor_medians = df_traffic.groupby(["location_id", "hour"])["observed_speed_kmh"].transform("median")
        df_traffic.loc[invalid_mask, "observed_speed_kmh"] = corridor_medians[invalid_mask]

    # Standardize observed speed precision
    df_traffic["observed_speed_kmh"] = df_traffic["observed_speed_kmh"].round(1)

    # 5. Standard Mathematical Target Derivation
    # CI = clip((v_free - v_obs) / v_free, 0.0, 1.0)
    # CP = CI * 100%
    df_traffic["congestion_index"] = (
        (df_traffic["free_flow_speed_kmh"] - df_traffic["observed_speed_kmh"]) /
        df_traffic["free_flow_speed_kmh"]
    ).clip(0.0, 1.0)
    df_traffic["congestion_percentage"] = (df_traffic["congestion_index"] * 100.0).round(2)

    # Display Categories: Low (0-25%), Moderate (26-50%), High (51-75%), Severe (76-100%)
    df_traffic["congestion_category"] = pd.cut(
        df_traffic["congestion_percentage"],
        bins=[-0.1, 25.0, 50.0, 75.0, 100.0],
        labels=["Low", "Moderate", "High", "Severe"]
    ).astype(str)

    # 6. Safe 1-to-1 Join with Road Infrastructure (No Cartesian Explosion)
    osm_cols = ["location_id", "road_type", "road_lanes", "surface", "maxspeed", "length_m", "latitude", "longitude", "accident_risk_score"]
    df_osm_subset = df_osm[osm_cols].drop_duplicates(subset=["location_id"])
    
    pre_join_len = len(df_traffic)
    df_silver = df_traffic.merge(df_osm_subset, on="location_id", how="inner")
    if len(df_silver) != pre_join_len:
        raise ValueError(f"Join integrity violation! Pre-join: {pre_join_len}, Post-join: {len(df_silver)}")

    # 7. Geographic Municipal Bounding Box Spatial Validation
    valid_mask = pd.Series(True, index=df_silver.index)
    for city, bounds in MUNICIPAL_BOUNDS.items():
        city_mask = (df_silver["city"] == city)
        in_bounds = (
            (df_silver["latitude"] >= bounds["min_lat"]) &
            (df_silver["latitude"] <= bounds["max_lat"]) &
            (df_silver["longitude"] >= bounds["min_lng"]) &
            (df_silver["longitude"] <= bounds["max_lng"])
        )
        valid_mask = valid_mask & (~city_mask | in_bounds)

    df_silver = df_silver[valid_mask].copy()
    logger.info(f"Geographical boundary check passed: {len(df_silver)} valid records retained.")

    # 8. Save Cleaned Silver Artifacts (Parquet & CSV)
    silver_parquet = os.path.join(output_dir, "silver_traffic_cleaned.parquet")
    silver_csv = os.path.join(output_dir, "silver_traffic_cleaned.csv")
    
    df_silver.to_parquet(silver_parquet, index=False)
    df_silver.to_csv(silver_csv, index=False)

    logger.info(f"Silver cleaned dataset successfully written to {silver_parquet} ({len(df_silver)} rows).")
    return silver_parquet

if __name__ == "__main__":
    clean_silver_layer()
