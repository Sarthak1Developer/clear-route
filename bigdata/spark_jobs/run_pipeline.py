import os
import sys
import time
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from bigdata.ingestion.ingest_uber_movement import ingest_uber_movement
from bigdata.ingestion.ingest_osm_infrastructure import ingest_osm_infrastructure
from bigdata.ingestion.ingest_weather_openmeteo import ingest_weather_era5
from bigdata.ingestion.ingest_events_holidays import ingest_events_holidays
from bigdata.spark_jobs.silver_cleaning import clean_silver_layer
from bigdata.spark_jobs.gold_feature_engineering import generate_gold_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger("master_bigdata_pipeline")

def run_complete_pipeline():
    start_time = time.time()
    logger.info("================================================================")
    logger.info("STARTING CLEARROUTE BIG DATA PIPELINE (BRONZE -> SILVER -> GOLD)")
    logger.info("================================================================")

    # 1. Bronze Layer Ingestion
    logger.info(">>> Stage 1: Ingesting Raw Data to Bronze Layer...")
    t_csv = ingest_uber_movement()
    osm_csv = ingest_osm_infrastructure()
    w_csv = ingest_weather_era5()
    ev_2019, ev_2026 = ingest_events_holidays()
    logger.info("Bronze Stage Completed.")

    # 2. Silver Layer Cleaning & Standardization
    logger.info(">>> Stage 2: Transforming Bronze to Cleaned Silver Parquet...")
    silver_parquet = clean_silver_layer(bronze_traffic_path=t_csv, bronze_osm_path=osm_csv)
    logger.info(f"Silver Stage Completed: {silver_parquet}")

    # 3. Gold Layer Feature Engineering & Integration
    logger.info(">>> Stage 3: Engineering Features & Generating Gold Unified Analytical Dataset...")
    gold_parquet = generate_gold_dataset(
        silver_traffic_path=silver_parquet,
        bronze_weather_path=w_csv,
        bronze_events_path=ev_2019
    )
    logger.info(f"Gold Stage Completed: {gold_parquet}")

    elapsed = round(time.time() - start_time, 2)
    logger.info("================================================================")
    logger.info(f"BIG DATA PIPELINE COMPLETED SUCCESSFULLY IN {elapsed} SECONDS")
    logger.info("================================================================")

if __name__ == "__main__":
    run_complete_pipeline()
