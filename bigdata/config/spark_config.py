import os
import logging

logger = logging.getLogger("clearroute.bigdata.config")

def get_spark_session(app_name: str = "ClearRoute-BigData-Pipeline"):
    """
    Initializes and returns an Apache Spark session.
    If PySpark / Java runtime is absent on local developer laptop, returns None
    so jobs can execute high-performance vectorized PyArrow fallbacks gracefully.
    """
    try:
        from pyspark.sql import SparkSession
        builder = (
            SparkSession.builder
            .appName(app_name)
            .master("local[*]")
            .config("spark.driver.memory", "4g")
            .config("spark.sql.session.timeZone", "Asia/Kolkata")
            .config("spark.sql.parquet.compression.codec", "snappy")
            .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        )
        spark = builder.getOrCreate()
        spark.sparkContext.setLogLevel("WARN")
        logger.info(f"Apache Spark Session '{app_name}' initialized successfully.")
        return spark
    except Exception as e:
        logger.warning(
            f"PySpark runtime initialization unavailable on this machine ({e}). "
            "Pipeline will utilize vectorized PyArrow / Pandas engines."
        )
        return None
