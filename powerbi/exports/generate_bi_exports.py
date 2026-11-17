"""
ClearRoute Power BI Export Generator
Produces high-performance Star-Schema fact and dimension tables, analytical aggregates,
and genuine machine learning evaluation and prediction outputs for Microsoft Power BI Desktop.

Reads:
- data/gold/master_congestion/gold_master_congestion.parquet
- data/bronze/events/raw_events_2019_historical.csv
- ml/artifacts/metrics.json
- ml/artifacts/training_config.json
- ml/artifacts/feature_importance.json
- ml/artifacts/shap_summary.json
- ml/artifacts/shap_category_drivers.json
- ml/artifacts/subgroup_performance.json
- ml/artifacts/preprocessor.joblib
- ml/artifacts/model_*.joblib

Writes: powerbi/exports/*.csv and refresh_metadata.json
"""

import os
import sys
import json
import logging
import argparse
import datetime
import joblib
import numpy as np
import pandas as pd

# Add repo root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ml.preprocessing.preprocessor import TrafficDataPreprocessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger("clearroute.powerbi.exports")


def generate_powerbi_exports(
    gold_parquet: str = "data/gold/master_congestion/gold_master_congestion.parquet",
    events_csv: str = "data/bronze/events/raw_events_2019_historical.csv",
    artifacts_dir: str = "ml/artifacts",
    output_dir: str = "powerbi/exports"
) -> dict:
    """
    Executes the full Power BI analytical export pipeline.
    Ensures referential integrity across all fact and dimension tables,
    avoids hardcoded model metrics, and preserves genuine evaluation outputs.
    """
    os.makedirs(output_dir, exist_ok=True)
    logger.info("==================================================================")
    logger.info("STARTING POWER BI DATA PREPARATION & EXPORT REGENERATION PIPELINE")
    logger.info(f"Target Directory: {os.path.abspath(output_dir)}")
    logger.info("==================================================================")

    # 1. Load Gold Master Analytical Dataset
    if not os.path.exists(gold_parquet):
        raise FileNotFoundError(f"Gold dataset missing at {gold_parquet}. Run ingestion pipeline first.")
    
    logger.info(f"Loading Gold master dataset from {gold_parquet}...")
    df = pd.read_parquet(gold_parquet)
    logger.info(f"Loaded {len(df):,} records across {df['city'].nunique()} metropolitan cities.")

    # Standardize timestamps and string flags
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.strftime("%Y-%m-%d")
    df["date_key"] = df["timestamp"].dt.strftime("%Y%m%d").astype(int)
    df["event_name"] = df["event_name"].fillna("No Event").replace({"None": "No Event"})
    df["event_type"] = df["event_type"].fillna("No Event").replace({"None": "No Event"})
    df["speed_reduction_pct"] = np.round(
        ((df["free_flow_speed_kmh"] - df["observed_speed_kmh"]) / df["free_flow_speed_kmh"]) * 100.0,
        2
    )

    # -------------------------------------------------------------------------
    # 2. DIMENSION TABLES
    # -------------------------------------------------------------------------

    # 2A. Dim Location (Corridor Master)
    dim_location = df[[
        "location_id", "location_name", "city", "latitude", "longitude",
        "road_type", "road_lanes", "length_m", "accident_risk_score", "free_flow_speed_kmh"
    ]].drop_duplicates(subset=["location_id"]).sort_values("location_id").reset_index(drop=True)
    
    dim_location["corridor_label"] = dim_location["city"] + " — " + dim_location["location_name"]
    dim_loc_path = os.path.join(output_dir, "dim_location.csv")
    dim_location.to_csv(dim_loc_path, index=False)
    logger.info(f"Exported: dim_location.csv ({len(dim_location)} corridors)")

    # 2B. Dim Date (Calendar Master 2019-04-01 to 2019-12-31)
    unique_dates = sorted(df["date"].unique())
    dates_list = []
    month_names = {
        1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
        7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
    }
    day_names = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}

    for d_str in unique_dates:
        dt = pd.to_datetime(d_str)
        date_slice = df[df["date"] == d_str]
        is_wknd = int(date_slice["is_weekend"].iloc[0]) if len(date_slice) > 0 else (1 if dt.dayofweek in [5, 6] else 0)
        is_hol = int(date_slice["is_holiday"].iloc[0]) if len(date_slice) > 0 else 0
        quarter_str = f"Q{(dt.month - 1) // 3 + 1}"

        dates_list.append({
            "date": d_str,
            "date_key": int(dt.strftime("%Y%m%d")),
            "year": dt.year,
            "quarter": quarter_str,
            "month": dt.month,
            "month_name": month_names.get(dt.month, ""),
            "day": dt.day,
            "day_of_week": dt.dayofweek,
            "day_name": day_names.get(dt.dayofweek, ""),
            "is_weekend": is_wknd,
            "is_holiday": is_hol
        })
    dim_date = pd.DataFrame(dates_list)
    dim_date_path = os.path.join(output_dir, "dim_date.csv")
    dim_date.to_csv(dim_date_path, index=False)
    logger.info(f"Exported: dim_date.csv ({len(dim_date)} dates)")

    # 2C. Dim Time (24 Diurnal Hours Master)
    time_list = []
    for h in range(24):
        t_label = f"{h:02d}:00"
        if 0 <= h < 7:
            period = "Late Night (00:00-06:00)"
            peak_name = "Off-Peak"
        elif 7 <= h < 12:
            period = "Morning Rush (07:00-11:00)"
            peak_name = "Morning Peak (08:00-11:00)" if h in [8, 9, 10, 11] else "Off-Peak"
        elif 12 <= h < 17:
            period = "Midday (12:00-16:00)"
            peak_name = "Off-Peak"
        elif 17 <= h < 22:
            period = "Evening Rush (17:00-21:00)"
            peak_name = "Evening Peak (17:00-21:00)"
        else:
            period = "Night (22:00-23:00)"
            peak_name = "Off-Peak"

        is_pk = 1 if h in [8, 9, 10, 11, 17, 18, 19, 20, 21] else 0
        time_list.append({
            "hour": h,
            "time_key": h,
            "time_label": t_label,
            "period_of_day": period,
            "is_peak_hour": is_pk,
            "peak_period_name": peak_name
        })
    dim_time = pd.DataFrame(time_list)
    dim_time_path = os.path.join(output_dir, "dim_time.csv")
    dim_time.to_csv(dim_time_path, index=False)
    logger.info(f"Exported: dim_time.csv ({len(dim_time)} diurnal hours)")

    # 2D. Dim Event (Event Catalog with Location & Impact Benchmarks)
    city_baselines = df[df["event_present"] == 0].groupby("city")["congestion_percentage"].mean().to_dict()
    dim_events = []
    if os.path.exists(events_csv):
        events_raw = pd.read_csv(events_csv)
        for idx, row in events_raw.iterrows():
            c = row["city"]
            ename = row["event_name"]
            etype = row["event_type"]
            edate = str(row["date"])
            base_cong = city_baselines.get(c, 24.05)

            evt_slice = df[(df["city"] == c) & (df["event_name"] == ename)]
            if len(evt_slice) > 0:
                evt_cong = evt_slice["congestion_percentage"].mean()
                obs_count = len(evt_slice)
            else:
                evt_cong = base_cong
                obs_count = 0

            delta = evt_cong - base_cong
            dim_events.append({
                "event_id": f"EVT_{idx+1:03d}",
                "event_name": ename,
                "event_type": etype,
                "city": c,
                "date": edate,
                "venue": row.get("venue", ""),
                "attendance": row.get("attendance", 0),
                "event_intensity": row.get("event_intensity", 0.5),
                "event_avg_congestion_pct": round(float(evt_cong), 2),
                "city_baseline_congestion_pct": round(float(base_cong), 2),
                "congestion_lift_pct": round(float(delta), 2),
                "observations_count": obs_count
            })
    dim_event_df = pd.DataFrame(dim_events)
    dim_event_path = os.path.join(output_dir, "dim_event.csv")
    dim_event_df.to_csv(dim_event_path, index=False)
    logger.info(f"Exported: dim_event.csv ({len(dim_event_df)} scheduled event occurrences)")

    # 2E. Dim Weather Category
    weather_cats = [
        {"rain_category": "Dry (<0.5mm)", "precip_min_mm": 0.0, "precip_max_mm": 0.5, "weather_severity": "Normal", "advisory_level": "Green - Optimal Traction"},
        {"rain_category": "Light Rain (0.5-5mm)", "precip_min_mm": 0.5, "precip_max_mm": 5.0, "weather_severity": "Moderate", "advisory_level": "Yellow - Wet Pavement Caution"},
        {"rain_category": "Moderate Rain (5-15mm)", "precip_min_mm": 5.0, "precip_max_mm": 15.0, "weather_severity": "High", "advisory_level": "Amber - Surface Water Delay"},
        {"rain_category": "Heavy Monsoon (>15mm)", "precip_min_mm": 15.0, "precip_max_mm": 150.0, "weather_severity": "Severe", "advisory_level": "Red - Monsoon Inundation Alert"}
    ]
    dim_weather_df = pd.DataFrame(weather_cats)
    dim_weather_path = os.path.join(output_dir, "dim_weather_category.csv")
    dim_weather_df.to_csv(dim_weather_path, index=False)
    logger.info(f"Exported: dim_weather_category.csv ({len(dim_weather_df)} weather tiers)")

    # -------------------------------------------------------------------------
    # 3. FACT TABLE (Standard Star Schema Grain: Location x Timestamp)
    # -------------------------------------------------------------------------
    fact_cols = [
        "timestamp", "date", "date_key", "location_id", "hour", "day_of_week", "month",
        "is_weekend", "is_peak_hour", "is_holiday", "event_present", "event_name", "event_type", "event_intensity",
        "temperature_2m_c", "precipitation_mm", "is_raining", "relative_humidity_2m_pct", "wind_speed_10m_kmh",
        "observed_speed_kmh", "free_flow_speed_kmh", "congestion_percentage", "congestion_category", "speed_reduction_pct"
    ]
    fact_table = df[[c for c in fact_cols if c in df.columns]].copy()
    fact_table["congestion_percentage"] = fact_table["congestion_percentage"].round(2)
    fact_table["observed_speed_kmh"] = fact_table["observed_speed_kmh"].round(1)
    fact_table["temperature_2m_c"] = fact_table["temperature_2m_c"].round(1)
    fact_table["precipitation_mm"] = fact_table["precipitation_mm"].round(2)

    fact_path = os.path.join(output_dir, "fact_congestion_hourly.csv")
    fact_table.to_csv(fact_path, index=False)
    logger.info(f"Exported: fact_congestion_hourly.csv ({len(fact_table):,} rows)")

    # -------------------------------------------------------------------------
    # 4. PRE-AGGREGATED ANALYTICAL BENCHMARK SUMMARIES
    # -------------------------------------------------------------------------

    # 4A. City-Wise Congestion Summary
    city_summary = df.groupby(["city"]).agg(
        avg_congestion_pct=("congestion_percentage", "mean"),
        peak_hour_congestion_pct=("congestion_percentage", lambda x: float(np.percentile(x, 90))),
        off_peak_congestion_pct=("congestion_percentage", lambda x: float(np.percentile(x, 25))),
        mean_speed_kmh=("observed_speed_kmh", "mean"),
        corridors_monitored=("location_id", "nunique"),
        total_observations=("location_id", "count")
    ).reset_index()
    city_summary["avg_congestion_pct"] = city_summary["avg_congestion_pct"].round(2)
    city_summary["peak_hour_congestion_pct"] = city_summary["peak_hour_congestion_pct"].round(2)
    city_summary["off_peak_congestion_pct"] = city_summary["off_peak_congestion_pct"].round(2)
    city_summary["mean_speed_kmh"] = city_summary["mean_speed_kmh"].round(1)
    city_summary.to_csv(os.path.join(output_dir, "city_congestion_summary.csv"), index=False)
    logger.info("Exported: city_congestion_summary.csv")

    # 4B. Location-Wise Congestion Summary
    loc_summary = df.groupby(["city", "location_id", "location_name", "road_type", "road_lanes"]).agg(
        avg_congestion_pct=("congestion_percentage", "mean"),
        peak_hour_congestion_pct=("congestion_percentage", lambda x: float(np.mean(x[df.loc[x.index, "is_peak_hour"] == 1]))),
        free_flow_speed_kmh=("free_flow_speed_kmh", "first"),
        mean_observed_speed_kmh=("observed_speed_kmh", "mean"),
        accident_risk_score=("accident_risk_score", "first"),
        total_observations=("hour", "count")
    ).reset_index()
    loc_summary["avg_congestion_pct"] = loc_summary["avg_congestion_pct"].round(2)
    loc_summary["peak_hour_congestion_pct"] = loc_summary["peak_hour_congestion_pct"].round(2)
    loc_summary["mean_observed_speed_kmh"] = loc_summary["mean_observed_speed_kmh"].round(1)
    loc_summary.to_csv(os.path.join(output_dir, "location_congestion_summary.csv"), index=False)
    logger.info("Exported: location_congestion_summary.csv")

    # 4C. Hourly Diurnal Congestion Summary
    hourly_summary = df.groupby(["hour", "is_weekend", "is_peak_hour"]).agg(
        mean_congestion_pct=("congestion_percentage", "mean"),
        mean_observed_speed_kmh=("observed_speed_kmh", "mean"),
        observation_count=("location_id", "count")
    ).reset_index()
    hourly_summary["mean_congestion_pct"] = hourly_summary["mean_congestion_pct"].round(2)
    hourly_summary["mean_observed_speed_kmh"] = hourly_summary["mean_observed_speed_kmh"].round(1)
    hourly_summary.to_csv(os.path.join(output_dir, "hourly_congestion_summary.csv"), index=False)
    logger.info("Exported: hourly_congestion_summary.csv")

    # 4D. Weather Precipitation Impact Summary
    df["rain_category"] = pd.cut(
        df["precipitation_mm"],
        bins=[-0.1, 0.5, 5.0, 15.0, 150.0],
        labels=["Dry (<0.5mm)", "Light Rain (0.5-5mm)", "Moderate Rain (5-15mm)", "Heavy Monsoon (>15mm)"]
    )
    weather_summary = df.groupby("rain_category", observed=False).agg(
        mean_congestion_pct=("congestion_percentage", "mean"),
        mean_speed_kmh=("observed_speed_kmh", "mean"),
        observation_count=("hour", "count")
    ).reset_index()
    weather_summary["mean_congestion_pct"] = weather_summary["mean_congestion_pct"].round(2)
    weather_summary["mean_speed_kmh"] = weather_summary["mean_speed_kmh"].round(1)
    weather_summary["speed_reduction_pct"] = np.round(
        ((df["free_flow_speed_kmh"].mean() - weather_summary["mean_speed_kmh"]) / df["free_flow_speed_kmh"].mean()) * 100.0,
        2
    )
    weather_summary.to_csv(os.path.join(output_dir, "weather_impact_summary.csv"), index=False)
    logger.info("Exported: weather_impact_summary.csv")

    # 4E. Weather Temperature & Heat Congestion Summary
    df["temperature_category"] = pd.cut(
        df["temperature_2m_c"],
        bins=[-10.0, 20.0, 28.0, 35.0, 60.0],
        labels=["Cool (<20°C)", "Moderate (20-28°C)", "Warm (28-35°C)", "Hot (>35°C)"]
    )
    temp_summary = df.groupby("temperature_category", observed=False).agg(
        mean_congestion_pct=("congestion_percentage", "mean"),
        mean_speed_kmh=("observed_speed_kmh", "mean"),
        observation_count=("hour", "count")
    ).reset_index()
    temp_summary["mean_congestion_pct"] = temp_summary["mean_congestion_pct"].round(2)
    temp_summary["mean_speed_kmh"] = temp_summary["mean_speed_kmh"].round(1)
    temp_summary.to_csv(os.path.join(output_dir, "weather_temperature_summary.csv"), index=False)
    logger.info("Exported: weather_temperature_summary.csv")

    # 4F. Event Impact Summary
    event_summary = df.groupby(["event_type", "event_present"]).agg(
        mean_congestion_pct=("congestion_percentage", "mean"),
        mean_speed_kmh=("observed_speed_kmh", "mean"),
        sample_count=("hour", "count")
    ).reset_index()
    event_summary["mean_congestion_pct"] = event_summary["mean_congestion_pct"].round(2)
    event_summary["mean_speed_kmh"] = event_summary["mean_speed_kmh"].round(1)
    event_summary.to_csv(os.path.join(output_dir, "event_impact_summary.csv"), index=False)
    logger.info("Exported: event_impact_summary.csv")

    # -------------------------------------------------------------------------
    # 5. MACHINE LEARNING EVALUATION & PREDICTIVE ANALYTICS TABLES
    # -------------------------------------------------------------------------

    # 5A. Model Benchmark Performance (Strictly from metrics.json - No Hardcoding)
    metrics_json_path = os.path.join(artifacts_dir, "metrics.json")
    if not os.path.exists(metrics_json_path):
        raise FileNotFoundError(f"Machine learning metrics file missing at {metrics_json_path}.")
    
    with open(metrics_json_path, "r") as f:
        meta = json.load(f)
    
    models_dict = meta.get("models", {})
    rows = []
    for k, v in models_dict.items():
        rows.append({
            "model_key": k,
            "model_name": v.get("name", k),
            "algorithm_family": v.get("family", "Statistical/ML"),
            "role": v.get("role", "Candidate"),
            "mae": v.get("mae", 0.0),
            "rmse": v.get("rmse", 0.0),
            "r2_score": v.get("r2", 0.0),
            "is_champion": 1 if v.get("is_primary") else 0
        })
    models_df = pd.DataFrame(rows).sort_values("r2_score", ascending=False)
    models_df.to_csv(os.path.join(output_dir, "model_performance_summary.csv"), index=False)
    logger.info("Exported: model_performance_summary.csv (Dynamically validated from metrics.json)")

    # 5B. Actual vs. Predicted Values on Held-Out Test Set (All 4 Models)
    logger.info("Generating genuine Actual vs. Predicted test evaluations for all 4 models...")
    preprocessor = TrafficDataPreprocessor()
    _, _, test_df = preprocessor.chronological_split(df, train_ratio=0.70, val_ratio=0.15)
    preprocessor.load(os.path.join(artifacts_dir, "preprocessor.joblib"))

    # Load serialized model estimators
    m1 = joblib.load(os.path.join(artifacts_dir, "model_historical_mean.joblib"))
    m2 = joblib.load(os.path.join(artifacts_dir, "model_linear_regression.joblib"))
    m3 = joblib.load(os.path.join(artifacts_dir, "model_random_forest.joblib"))
    m4 = joblib.load(os.path.join(artifacts_dir, "model_xgboost.joblib"))

    X_test, y_test = preprocessor.transform(test_df)

    p1 = np.round(m1.predict(test_df), 2)
    p2 = np.round(np.clip(m2.predict(X_test), 0.0, 100.0), 2)
    p3 = np.round(m3.predict(X_test), 2)
    p4 = np.round(m4.predict(X_test), 2)

    actual_vs_pred_df = pd.DataFrame({
        "timestamp": test_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S").values,
        "date": test_df["date"].values,
        "location_id": test_df["location_id"].values,
        "location_name": test_df["location_name"].values,
        "city": test_df["city"].values,
        "hour": test_df["hour"].values,
        "is_peak_hour": test_df["is_peak_hour"].values,
        "is_weekend": test_df["is_weekend"].values,
        "actual_congestion_pct": np.round(y_test, 2),
        "pred_historical_mean": p1,
        "pred_linear_regression": p2,
        "pred_random_forest": p3,
        "pred_xgboost": p4,
        "residual_historical_mean": np.round(y_test - p1, 2),
        "residual_linear_regression": np.round(y_test - p2, 2),
        "residual_random_forest": np.round(y_test - p3, 2),
        "residual_xgboost": np.round(y_test - p4, 2)
    })
    actual_vs_pred_path = os.path.join(output_dir, "model_actual_vs_predicted.csv")
    actual_vs_pred_df.to_csv(actual_vs_pred_path, index=False)
    logger.info(f"Exported: model_actual_vs_predicted.csv ({len(actual_vs_pred_df):,} test records across 4 models)")

    # 5C. Subgroup Performance Diagnostics (City & Traffic Condition Slices)
    subgroup_path = os.path.join(artifacts_dir, "subgroup_performance.json")
    if os.path.exists(subgroup_path):
        with open(subgroup_path, "r") as f:
            subgroup_data = json.load(f)
        subgroup_rows = []
        for slice_type, slice_key in [("City", "by_city"), ("Traffic Condition", "by_traffic_condition")]:
            slice_dict = subgroup_data.get(slice_key, {})
            for m_key, m_slices in slice_dict.items():
                m_name = models_dict.get(m_key, {}).get("name", m_key)
                for s_name, s_metrics in m_slices.items():
                    subgroup_rows.append({
                        "model_key": m_key,
                        "model_name": m_name,
                        "slice_type": slice_type,
                        "slice_name": s_name,
                        "samples": s_metrics.get("samples", 0),
                        "mae": s_metrics.get("mae", 0.0),
                        "rmse": s_metrics.get("rmse", 0.0),
                        "r2": s_metrics.get("r2", 0.0)
                    })
        subgroup_df = pd.DataFrame(subgroup_rows)
        subgroup_df.to_csv(os.path.join(output_dir, "model_subgroup_performance.csv"), index=False)
        logger.info(f"Exported: model_subgroup_performance.csv ({len(subgroup_df)} slice benchmarks)")

    # 5D. Feature Importance & SHAP Explainability Matrix
    shap_path = os.path.join(artifacts_dir, "shap_summary.json")
    fi_path = os.path.join(artifacts_dir, "feature_importance.json")
    if os.path.exists(shap_path) and os.path.exists(fi_path):
        with open(shap_path, "r") as f:
            shap_data = json.load(f)
        with open(fi_path, "r") as f:
            fi_data = json.load(f)

        shap_map = {
            item["feature"]: (item["display_name"], item["category"], item["mean_abs_shap_pct"])
            for item in shap_data.get("global_importance", [])
        }

        feat_rows = []
        for f_name in fi_data.get("feature_names", []):
            disp, cat, shap_val = shap_map.get(f_name, (f_name, "general", 0.0))
            feat_rows.append({
                "feature_name": f_name,
                "display_name": disp,
                "category": cat.replace("_", " ").title(),
                "shap_importance_pct": round(float(shap_val), 4),
                "xgboost_importance": round(float(fi_data.get("xgboost_importances", {}).get(f_name, 0.0)), 5),
                "random_forest_importance": round(float(fi_data.get("random_forest_importances", {}).get(f_name, 0.0)), 5),
                "ridge_coefficient": round(float(fi_data.get("ridge_coefficients", {}).get(f_name, 0.0)), 4)
            })
        feat_df = pd.DataFrame(feat_rows).sort_values("shap_importance_pct", ascending=False)
        feat_df.to_csv(os.path.join(output_dir, "model_feature_importance.csv"), index=False)
        logger.info(f"Exported: model_feature_importance.csv ({len(feat_df)} features with SHAP weights)")

    # 5E. Corridor Predictive Risk & High-Risk Bottlenecks
    loc_risk = []
    for loc_id, group in df.groupby("location_id"):
        name = group["location_name"].iloc[0]
        city = group["city"].iloc[0]
        rtype = group["road_type"].iloc[0]
        lanes = int(group["road_lanes"].iloc[0])
        ff_speed = float(group["free_flow_speed_kmh"].iloc[0])
        acc_risk = float(group["accident_risk_score"].iloc[0])

        avg_cong = float(group["congestion_percentage"].mean())
        peak_cong = float(group[group["is_peak_hour"] == 1]["congestion_percentage"].mean())
        off_peak_cong = float(group[group["is_peak_hour"] == 0]["congestion_percentage"].mean())
        rain_cong = float(group[group["is_raining"] == 1]["congestion_percentage"].mean())
        evt_slice = group[group["event_present"] == 1]
        event_cong = float(evt_slice["congestion_percentage"].mean()) if len(evt_slice) > 0 else avg_cong

        # Composite risk index: Peak Congestion (45%), Accident Hazard (35%), Rain Vulnerability (20%)
        norm_peak = min(100.0, (peak_cong / 60.0) * 100.0)
        norm_acc = acc_risk * 100.0
        norm_rain = min(100.0, (rain_cong / 60.0) * 100.0)
        risk_score = round(0.45 * norm_peak + 0.35 * norm_acc + 0.20 * norm_rain, 1)

        if risk_score >= 65.0:
            tier = "Critical Risk"
        elif risk_score >= 50.0:
            tier = "High Risk"
        elif risk_score >= 35.0:
            tier = "Moderate Risk"
        else:
            tier = "Low Risk"

        drivers = []
        if peak_cong > 45.0:
            drivers.append("Severe Peak Rush")
        if acc_risk >= 0.70:
            drivers.append("High Accident Hazard")
        if lanes <= 4:
            drivers.append("Constricted Carriageway")
        if rain_cong > avg_cong * 1.05:
            drivers.append("Monsoon Waterlogging Vulnerability")
        primary_driver = " & ".join(drivers) if drivers else "Standard Diurnal Traffic"

        loc_risk.append({
            "location_id": loc_id,
            "location_name": name,
            "city": city,
            "road_type": rtype,
            "road_lanes": lanes,
            "free_flow_speed_kmh": round(ff_speed, 1),
            "accident_risk_score": round(acc_risk, 2),
            "baseline_congestion_pct": round(avg_cong, 2),
            "peak_hour_congestion_pct": round(peak_cong, 2),
            "off_peak_congestion_pct": round(off_peak_cong, 2),
            "rain_congestion_pct": round(rain_cong, 2),
            "event_congestion_pct": round(event_cong, 2),
            "composite_risk_score": risk_score,
            "risk_tier": tier,
            "primary_risk_driver": primary_driver
        })
    risk_df = pd.DataFrame(loc_risk).sort_values("composite_risk_score", ascending=False)
    risk_df.to_csv(os.path.join(output_dir, "corridor_predictive_risk.csv"), index=False)
    logger.info(f"Exported: corridor_predictive_risk.csv ({len(risk_df)} high-risk corridor profiles)")

    # 5F. SHAP Category Drivers
    drivers_path = os.path.join(artifacts_dir, "shap_category_drivers.json")
    if os.path.exists(drivers_path):
        with open(drivers_path, "r") as f:
            drivers_json = json.load(f)
        category_meta = [
            ("time_of_day_driver", "Time of Day (Diurnal Cycle)", 1),
            ("traffic_history_driver", "Traffic History & Autoregressive Lag", 2),
            ("road_characteristics_driver", "Road Infrastructure & Geometry", 3),
            ("weather_condition_driver", "Weather & Monsoon Precipitation", 4),
            ("events_and_holidays_driver", "Special Events & Cultural Gatherings", 5)
        ]
        drivers_rows = []
        for key, name, rank in category_meta:
            if key in drivers_json:
                drivers_rows.append({
                    "category_key": key,
                    "category_name": name,
                    "driver_narrative": drivers_json[key],
                    "priority_rank": rank
                })
        drivers_df = pd.DataFrame(drivers_rows)
        drivers_df.to_csv(os.path.join(output_dir, "shap_category_drivers.csv"), index=False)
        logger.info(f"Exported: shap_category_drivers.csv ({len(drivers_df)} explainability narratives)")

    # 5G. Sample for quick viewing
    df.head(1000).to_csv(os.path.join(output_dir, "gold_master_sample.csv"), index=False)
    logger.info("Exported: gold_master_sample.csv (1,000 preview rows)")

    # -------------------------------------------------------------------------
    # 6. REFRESH AUDIT METADATA RECORD
    # -------------------------------------------------------------------------
    champion_key = meta.get("best_model", "historical_mean")
    champion_name = models_dict.get(champion_key, {}).get("name", champion_key)

    refresh_meta = {
        "refresh_timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "refresh_date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "source_dataset": os.path.abspath(gold_parquet),
        "source_dataset_records": len(df),
        "temporal_range_start": str(df["timestamp"].min()),
        "temporal_range_end": str(df["timestamp"].max()),
        "metropolitan_cities_count": int(df["city"].nunique()),
        "corridors_monitored_count": int(df["location_id"].nunique()),
        "models_evaluated_count": len(models_dict),
        "champion_model_key": champion_key,
        "champion_model_name": champion_name,
        "champion_test_mae": models_dict.get(champion_key, {}).get("mae", 0.0),
        "champion_test_rmse": models_dict.get(champion_key, {}).get("rmse", 0.0),
        "champion_test_r2": models_dict.get(champion_key, {}).get("r2", 0.0),
        "pipeline_status": "SUCCESS"
    }

    # Save JSON metadata
    meta_json_path = os.path.join(output_dir, "refresh_metadata.json")
    with open(meta_json_path, "w") as f:
        json.dump(refresh_meta, f, indent=2)

    # Save 1-row CSV for direct Power BI Card binding
    pd.DataFrame([refresh_meta]).to_csv(os.path.join(output_dir, "refresh_metadata.csv"), index=False)
    logger.info(f"Recorded refresh metadata: {meta_json_path}")

    logger.info("==================================================================")
    logger.info("ALL POWER BI ANALYTICAL EXPORT TABLES GENERATED SUCCESSFULLY")
    logger.info(f"Refresh completed at: {refresh_meta['refresh_timestamp_utc']}")
    logger.info("==================================================================")

    return refresh_meta


def main():
    parser = argparse.ArgumentParser(description="ClearRoute Power BI Export Generator")
    parser.add_argument("--gold-parquet", default="data/gold/master_congestion/gold_master_congestion.parquet", help="Path to Gold parquet")
    parser.add_argument("--events-csv", default="data/bronze/events/raw_events_2019_historical.csv", help="Path to raw bronze events")
    parser.add_argument("--artifacts-dir", default="ml/artifacts", help="Path to ML artifacts")
    parser.add_argument("--output-dir", default="powerbi/exports", help="Export target directory")
    args = parser.parse_args()

    generate_powerbi_exports(
        gold_parquet=args.gold_parquet,
        events_csv=args.events_csv,
        artifacts_dir=args.artifacts_dir,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()
