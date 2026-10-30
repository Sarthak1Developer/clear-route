import os
import sys
import logging
import pandas as pd
import numpy as np

# Ensure root in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from bigdata.config.spark_config import get_spark_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("silver_cleaning")

# Municipal Bounding Boxes for Geographical Validation
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
):
    os.makedirs(output_dir, exist_ok=True)
    logger.info("Executing Silver Layer Data Cleaning & Standardization Job...")

    # Load Bronze Data
    df_traffic = pd.read_csv(bronze_traffic_path)
    df_osm = pd.read_csv(bronze_osm_path)

    initial_count = len(df_traffic)
    logger.info(f"Loaded {initial_count} raw traffic records from Bronze layer.")

    # 1. Deduplication
    # PySpark equivalent: row_number() over (partition by location_id, timestamp order by report_time desc)
    df_traffic = df_traffic.drop_duplicates(subset=["location_id", "timestamp"])
    dedup_count = initial_count - len(df_traffic)
    logger.info(f"Deduplicated records: {dedup_count} duplicates removed.")

    # 2. Timestamp Normalization (Ensure standard ISO 8601 in IST)
    df_traffic["timestamp"] = pd.to_datetime(df_traffic["timestamp"])
    df_traffic["hour"] = df_traffic["timestamp"].dt.hour
    df_traffic["day_of_week"] = df_traffic["timestamp"].dt.dayofweek
    df_traffic["month"] = df_traffic["timestamp"].dt.month
    df_traffic["is_weekend"] = (df_traffic["day_of_week"] >= 5).astype(int)
    df_traffic["is_peak_hour"] = (
        ((df_traffic["hour"] >= 8) & (df_traffic["hour"] <= 11)) |
        ((df_traffic["hour"] >= 17) & (df_traffic["hour"] <= 21))
    ).astype(int)

    # 3. Missing Value & Outlier Investigation
    # Replace invalid speeds (<= 0 or > 140 km/h) with segment-hour median
    invalid_mask = (df_traffic["observed_speed_kmh"] <= 0) | (df_traffic["observed_speed_kmh"] > 140.0)
    if invalid_mask.sum() > 0:
        logger.warning(f"Found {invalid_mask.sum()} invalid speed outliers. Imputing with corridor medians.")
        medians = df_traffic.groupby(["location_id", "hour"])["observed_speed_kmh"].transform("median")
        df_traffic.loc[invalid_mask, "observed_speed_kmh"] = medians[invalid_mask]

    # 4. Mathematical Target Definition
    # CI = max(0.0, min(1.0, (free_flow - observed) / free_flow))
    # CP = CI * 100%
    df_traffic["congestion_index"] = (
        (df_traffic["free_flow_speed_kmh"] - df_traffic["observed_speed_kmh"]) /
        df_traffic["free_flow_speed_kmh"]
    ).clip(0.0, 1.0)
    df_traffic["congestion_percentage"] = (df_traffic["congestion_index"] * 100.0).round(2)

    # Project Display Categories: Low (0-25), Moderate (26-50), High (51-75), Severe (76-100)
    df_traffic["congestion_category"] = pd.cut(
        df_traffic["congestion_percentage"],
        bins=[-0.1, 25.0, 50.0, 75.0, 100.0],
        labels=["Low", "Moderate", "High", "Severe"]
    )

    # 5. Merge with Cleaned OSM Road Infrastructure
    df_silver = df_traffic.merge(
        df_osm[["location_id", "road_type", "road_lanes", "surface", "maxspeed", "length_m", "latitude", "longitude"]],
        on="location_id",
        how="inner"
    )

    # 6. Geographical Bounding Box Validation
    valid_geo_rows = []
    for idx, row in df_silver.iterrows():
        bounds = MUNICIPAL_BOUNDS.get(row["city"])
        if bounds:
            if (bounds["min_lat"] <= row["latitude"] <= bounds["max_lat"] and
                bounds["min_lng"] <= row["longitude"] <= bounds["max_lng"]):
                valid_geo_rows.append(True)
            else:
                valid_geo_rows.append(False)
        else:
            valid_geo_rows.append(True)

    df_silver = df_silver[valid_geo_rows]
    logger.info(f"Geographical boundary check passed: {len(df_silver)} valid records retained.")

    # Save Cleaned Silver Dataset (Parquet & CSV)
    silver_parquet = os.path.join(output_dir, "silver_traffic_cleaned.parquet")
    silver_csv = os.path.join(output_dir, "silver_traffic_cleaned.csv")
    
    df_silver.to_parquet(silver_parquet, index=False)
    df_silver.to_csv(silver_csv, index=False)

    logger.info(f"Silver cleaned dataset successfully written to {silver_parquet} ({len(df_silver)} rows).")
    return silver_parquet

if __name__ == "__main__":
    clean_silver_layer()
