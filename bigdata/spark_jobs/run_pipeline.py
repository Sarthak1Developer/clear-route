"""
ClearRoute Master Big Data Pipeline Orchestrator
Executes Bronze -> Silver -> Gold ETL & Data Quality Audit

Ensures end-to-end reproducibility across local and distributed environments.
"""

import os
import sys
import time
import logging

# Ensure project root in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from bigdata.ingestion.ingest_weather_openmeteo import ingest_weather_era5
from bigdata.ingestion.ingest_osm_infrastructure import ingest_osm_infrastructure
from bigdata.ingestion.ingest_events_holidays import ingest_events_holidays
from bigdata.ingestion.ingest_uber_movement import ingest_uber_movement
from bigdata.spark_jobs.silver_cleaning import clean_silver_layer
from bigdata.spark_jobs.gold_feature_engineering import generate_gold_dataset
from bigdata.reports.data_quality_report import generate_data_quality_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger("clearroute.bigdata.pipeline")

def run_complete_pipeline():
    import json
    traffic_path = "data/bronze/uber_movement/raw_uber_movement_traffic.csv"
    metadata_path = "data/bronze/uber_movement/provenance_metadata.json"
    if not os.path.exists(traffic_path) or not os.path.exists(metadata_path):
        raise FileNotFoundError("Genuine traffic CSV and provenance_metadata.json are required before production ETL.")
    with open(metadata_path, encoding="utf-8") as stream:
        metadata = json.load(stream)
    if metadata.get("is_genuine_sensor_data") is not True:
        raise RuntimeError("Production ETL blocked: existing traffic is generated demonstration data, not genuine observations. Files preserved.")
    start_time = time.time()
    logger.info("================================================================")
    logger.info("STARTING CLEARROUTE BIG DATA PIPELINE (BRONZE -> SILVER -> GOLD)")
    logger.info("================================================================")

    # 1. Bronze Layer Ingestion
    logger.info(">>> Stage 1: Ingesting Raw Data to Bronze Layer...")
    w_csv = ingest_weather_era5()
    osm_csv = ingest_osm_infrastructure()
    ev_2019, ev_2026 = ingest_events_holidays()
    t_csv = traffic_path
    logger.info("Bronze Stage Completed Successfully.")

    # 2. Silver Layer Cleaning & Standardization
    logger.info(">>> Stage 2: Transforming Bronze to Cleaned Silver Parquet...")
    silver_parquet = clean_silver_layer(bronze_traffic_path=t_csv, bronze_osm_path=osm_csv)
    logger.info(f"Silver Stage Completed Successfully: {silver_parquet}")

    # 3. Gold Layer Feature Engineering & Analytical Integration
    logger.info(">>> Stage 3: Engineering Features & Generating Master Gold Analytical Dataset...")
    gold_parquet = generate_gold_dataset(
        silver_traffic_path=silver_parquet,
        bronze_weather_path=w_csv,
        bronze_events_path=ev_2019
    )
    logger.info(f"Gold Stage Completed Successfully: {gold_parquet}")

    # 4. Automated Data Quality Audit
    logger.info(">>> Stage 4: Executing Automated Data Quality & Integrity Audit...")
    report = generate_data_quality_report(
        gold_parquet_path=gold_parquet,
        silver_parquet_path=silver_parquet
    )
    logger.info("Stage 4 Data Quality Audit Completed.")

    elapsed = round(time.time() - start_time, 2)
    logger.info("================================================================")
    logger.info(f"BIG DATA PIPELINE COMPLETED SUCCESSFULLY IN {elapsed} SECONDS")
    logger.info(f"Gold Analytical Dataset: {gold_parquet} ({report['layer_record_counts']['gold_master']:,} rows)")
    logger.info("================================================================")

if __name__ == "__main__":
    run_complete_pipeline()
