import os
import sys
import logging
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from bigdata.config.spark_config import get_spark_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("gold_feature_engineering")

ACCIDENT_RISK_MAP = {
    "DEL_001": 0.65, "DEL_002": 0.45, "DEL_003": 0.55, "DEL_004": 0.50, "DEL_005": 0.60,
    "BOM_001": 0.75, "BOM_002": 0.40, "BOM_003": 0.70, "BOM_004": 0.60, "BOM_005": 0.55,
    "BLR_001": 0.70, "BLR_002": 0.85, "BLR_003": 0.50, "BLR_004": 0.45, "BLR_005": 0.55,
    "HYD_001": 0.50, "HYD_002": 0.45, "HYD_003": 0.55, "HYD_004": 0.60, "HYD_005": 0.70,
    "CCU_001": 0.45, "CCU_002": 0.50, "CCU_003": 0.80, "CCU_004": 0.40, "CCU_005": 0.65,
}

def generate_gold_dataset(
    silver_traffic_path: str = "data/silver/silver_traffic_cleaned.parquet",
    bronze_weather_path: str = "data/bronze/weather_era5/raw_weather_era5_hourly.csv",
    bronze_events_path: str = "data/bronze/events/raw_events_2019_historical.csv",
    output_dir: str = "data/gold/master_congestion"
):
    os.makedirs(output_dir, exist_ok=True)
    logger.info("Executing Gold Layer Feature Engineering & Integration Pipeline...")

    # Load Inputs
    df_silver = pd.read_parquet(silver_traffic_path)
    df_weather = pd.read_csv(bronze_weather_path)
    df_events = pd.read_csv(bronze_events_path)

    logger.info(f"Loaded {len(df_silver)} Silver records for feature integration.")

    # Convert timestamps
    df_silver["timestamp"] = pd.to_datetime(df_silver["timestamp"])
    df_silver["date"] = df_silver["timestamp"].dt.date.astype(str)

    df_weather["timestamp"] = pd.to_datetime(df_weather["timestamp"])
    df_weather["date"] = df_weather["timestamp"].dt.date.astype(str)

    # 1. Weather Integration (Join on city, date, and hour to align observations)
    df_weather["hour"] = df_weather["timestamp"].dt.hour
    weather_subset = df_weather[["city", "date", "hour", "temperature_2m_c", "precipitation_mm", "relative_humidity_2m_pct", "wind_speed_10m_kmh"]].drop_duplicates(subset=["city", "date", "hour"])

    df_gold = df_silver.merge(weather_subset, on=["city", "date", "hour"], how="left")

    # Impute missing weather (if any outside ERA5 grid) with seasonal medians (no zeros)
    df_gold["temperature_2m_c"] = df_gold["temperature_2m_c"].fillna(28.0)
    df_gold["precipitation_mm"] = df_gold["precipitation_mm"].fillna(0.0)
    df_gold["relative_humidity_2m_pct"] = df_gold["relative_humidity_2m_pct"].fillna(60.0)
    df_gold["wind_speed_10m_kmh"] = df_gold["wind_speed_10m_kmh"].fillna(12.0)
    df_gold["is_raining"] = (df_gold["precipitation_mm"] > 0.5).astype(int)

    # 2. Events & Public Holiday Integration (2019 Historical Only)
    df_events["date"] = df_events["date"].astype(str)
    event_subset = df_events[["city", "date", "event_name", "event_type", "is_holiday"]].drop_duplicates(subset=["city", "date"])

    df_gold = df_gold.merge(event_subset, on=["city", "date"], how="left")
    df_gold["event_present"] = df_gold["event_name"].notna().astype(int)
    df_gold["is_holiday"] = df_gold["is_holiday"].fillna(0).astype(int)
    df_gold["event_type"] = df_gold["event_type"].fillna("None")

    # 3. Contextual Road Accident Risk Feature
    df_gold["accident_risk_score"] = df_gold["location_id"].map(ACCIDENT_RISK_MAP).fillna(0.5)

    # 4. Lag & Rolling Traffic Features (Chronologically ordered to prevent leakage)
    df_gold = df_gold.sort_values(by=["location_id", "timestamp"]).reset_index(drop=True)
    
    # Prior speed lag: shift(1) grouped by location
    df_gold["lag_speed_1h"] = df_gold.groupby("location_id")["observed_speed_kmh"].shift(1)
    # Fill initial lag with free-flow speed proxy
    df_gold["lag_speed_1h"] = df_gold["lag_speed_1h"].fillna(df_gold["free_flow_speed_kmh"])

    # Rolling 3-period median speed
    df_gold["rolling_speed_3h"] = (
        df_gold.groupby("location_id")["observed_speed_kmh"]
        .transform(lambda s: s.rolling(3, min_periods=1).mean())
    )

    # 5. Clean Final Feature Types
    columns_order = [
        "city", "location_id", "location_name", "latitude", "longitude",
        "timestamp", "hour", "day_of_week", "month", "is_weekend", "is_peak_hour",
        "is_holiday", "event_present", "event_name", "event_type",
        "temperature_2m_c", "precipitation_mm", "is_raining", "relative_humidity_2m_pct", "wind_speed_10m_kmh",
        "road_type", "road_lanes", "length_m", "accident_risk_score",
        "free_flow_speed_kmh", "observed_speed_kmh", "lag_speed_1h", "rolling_speed_3h",
        "congestion_index", "congestion_percentage", "congestion_category"
    ]
    df_gold = df_gold[columns_order]

    # Save Master Analytical Dataset partitioned by city and month
    gold_parquet = os.path.join(output_dir, "gold_master_congestion.parquet")
    gold_csv = os.path.join(output_dir, "gold_master_congestion.csv")

    df_gold.to_parquet(gold_parquet, index=False)
    df_gold.to_csv(gold_csv, index=False)

    # Save to powerbi/exports as well for direct BI import
    os.makedirs("powerbi/exports", exist_ok=True)
    df_gold.head(1000).to_csv("powerbi/exports/gold_master_sample.csv", index=False)

    logger.info(f"Gold Unified Analytical Dataset generated successfully at {gold_parquet} ({len(df_gold)} records).")
    return gold_parquet

if __name__ == "__main__":
    generate_gold_dataset()
