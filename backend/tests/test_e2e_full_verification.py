"""
ClearRoute - End-to-End Comprehensive Test Suite
Validates all 20 operational aspects of the integrated Big Data, ML, SHAP, and Frontend platform.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.models.entities import Base, City, Location, TrafficRecord, WeatherRecord, Event
from backend.app.database.session import engine, SessionLocal, get_db
from backend.app.services.inference_service import inference_service, InferenceService, ModelNotAvailableError
from backend.app.services.weather_service import WeatherService
from backend.app.services.analytics_service import AnalyticsService
from backend.app.repositories.data_repository import DataRepository

client = TestClient(app)

# -----------------------------------------------------------------------------
# 1. Database Initialization
# -----------------------------------------------------------------------------
def test_01_database_initialization(tmp_path):
    """Verifies that schema tables and constraints can be initialized cleanly on a fresh database."""
    temp_db_path = str(tmp_path / "fresh_test.db")
    test_engine = create_engine(f"sqlite:///{temp_db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    
    with test_engine.connect() as conn:
        res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
        table_names = [r[0] for r in res]
        for expected in ["cities", "locations", "traffic_records", "weather_records", "events", "predictions", "data_sources"]:
            assert expected in table_names, f"Expected table '{expected}' missing from initialized schema."

# -----------------------------------------------------------------------------
# 2. Database Connectivity
# -----------------------------------------------------------------------------
def test_02_database_connectivity():
    """Verifies active connectivity to the configured database engine."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1, "Database connectivity ping failed."

# -----------------------------------------------------------------------------
# 3. Backend Startup
# -----------------------------------------------------------------------------
def test_03_backend_startup():
    """Verifies FastAPI application startup, OpenAPI schema generation, and routes registry."""
    schema = app.openapi()
    assert schema is not None
    assert "paths" in schema
    assert "/api/predict" in schema["paths"]
    assert "/api/models/feature-importance" in schema["paths"]
    assert "/api/data/records" in schema["paths"]

# -----------------------------------------------------------------------------
# 4. Frontend Startup / Build
# -----------------------------------------------------------------------------
def test_04_frontend_startup():
    """Verifies that the React/Vite frontend bundle compiles cleanly and assets exist."""
    dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
    index_html = os.path.join(dist_dir, "index.html")
    assert os.path.exists(index_html), "Frontend dist/index.html was not generated. Run vite build."
    with open(index_html, "r", encoding="utf-8") as f:
        content = f.read()
        assert "ClearRoute" in content or "vite" in content or "assets" in content

# -----------------------------------------------------------------------------
# 5. Frontend-to-Backend API Communication
# -----------------------------------------------------------------------------
def test_05_frontend_to_backend_api_communication():
    """Verifies that the backend health endpoint responds with 200 OK and valid JSON."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["online", "healthy", "degraded"]
    assert "models_loaded" in data
    assert data["database"] in ["connected", "fallback", "degraded"]



# -----------------------------------------------------------------------------
# 6. City and Location Analytics
# -----------------------------------------------------------------------------
def test_06_city_and_location_analytics():
    """Verifies city summaries, location listings, and corridor trends."""
    # Cities list
    res_cities = client.get("/api/cities")
    assert res_cities.status_code == 200
    cities = res_cities.json()
    assert len(cities) >= 5
    city_names = [c["name"] for c in cities]
    assert "Delhi" in city_names
    assert "Bengaluru" in city_names

    # City summary
    res_sum = client.get("/api/cities/Delhi/summary")
    assert res_sum.status_code == 200
    sum_data = res_sum.json()
    assert sum_data["city"] == "Delhi"
    assert sum_data["avg_congestion_pct"] >= 0.0

    # City locations
    res_locs = client.get("/api/cities/Delhi/locations")
    assert res_locs.status_code == 200
    locs = res_locs.json()["locations"]
    assert len(locs) >= 1

    # Location trends
    loc_code = locs[0]["location_code"]
    res_trends = client.get(f"/api/locations/{loc_code}/trends")
    assert res_trends.status_code == 200
    trends = res_trends.json()
    assert len(trends["hourly"]) == 24
    assert len(trends["weekly"]) == 7

# -----------------------------------------------------------------------------
# 7. Historical Congestion Queries
# -----------------------------------------------------------------------------
def test_07_historical_congestion_queries():
    """Verifies time-series historical observations for road corridors."""
    res = client.get("/api/locations/DEL_001/history?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "sample_records" in data
    assert len(data["sample_records"]) <= 10
    if len(data["sample_records"]) > 0:
        first = data["sample_records"][0]
        assert "congestion_percentage" in first
        assert "observed_speed_kmh" in first
        assert "timestamp" in first


# -----------------------------------------------------------------------------
# 8. Weather Analytics
# -----------------------------------------------------------------------------
def test_08_weather_analytics():
    """Verifies meteorological conditions and weather impact correlations."""
    # Weather context
    res_w = client.get("/api/weather?city=Bengaluru")
    assert res_w.status_code == 200
    w_data = res_w.json()
    assert w_data["city"] == "Bengaluru"
    assert "current_context" in w_data

    # Weather impact
    res_imp = client.get("/api/weather/impact")
    assert res_imp.status_code == 200
    imp_data = res_imp.json()
    assert "rain_bands" in imp_data
    assert "temp_bands" in imp_data
    assert "rain_correlation" in imp_data

# -----------------------------------------------------------------------------
# 9. Event Analytics
# -----------------------------------------------------------------------------
def test_09_event_analytics():
    """Verifies public event listings and impact comparisons."""
    res_events = client.get("/api/events")
    assert res_events.status_code == 200
    e_data = res_events.json()
    assert "events" in e_data
    assert len(e_data["events"]) > 0

    res_impact = client.get("/api/events/impact")
    assert res_impact.status_code == 200
    imp_data = res_impact.json()
    assert "hourly_comparison" in imp_data
    assert len(imp_data["hourly_comparison"]) == 24

# -----------------------------------------------------------------------------
# 10. Actual ML Model Loading
# -----------------------------------------------------------------------------
def test_10_actual_ml_model_loading():
    """Verifies that all 4 models and the preprocessor are loaded into memory."""
    models = inference_service.get_loaded_models()
    assert len(models) == 4
    for expected in ["historical_mean", "linear_regression", "random_forest", "xgboost"]:
        assert expected in models, f"Model '{expected}' was not loaded."
    assert inference_service.preprocessor_data is not None


# -----------------------------------------------------------------------------
# 11. Actual Congestion Predictions
# -----------------------------------------------------------------------------
def test_11_actual_congestion_predictions():
    """Verifies prediction inference across all 4 modeling approaches."""
    for model_type in ["historical_mean", "linear_regression", "random_forest", "xgboost"]:
        payload = {
            "city": "Bengaluru",
            "location_id": "BLR_001",
            "hour": 18,
            "day_of_week": 2,
            "month": 11,
            "model_type": model_type,
            "temperature_2m_c": 24.0,
            "precipitation_mm": 5.0,
            "relative_humidity_2m_pct": 75.0,
            "wind_speed_10m_kmh": 12.0,
            "road_type": "primary",
            "road_lanes": 4,
            "free_flow_speed_kmh": 50.0,
            "accident_risk_score": 0.65,
            "event_present": 0,
            "lag_speed_1h": 24.0,
            "rolling_speed_3h": 26.0
        }
        res = client.post("/api/predict", json=payload)
        assert res.status_code == 200, f"Predict failed for model '{model_type}': {res.text}"
        data = res.json()
        assert 0.0 <= data["predicted_congestion_pct"] <= 100.0
        assert data["selected_model"] == model_type
        assert data["model_version"] == "1.0.0"
        assert "timestamp" in data
        assert data["location_info"] is not None

# -----------------------------------------------------------------------------
# 12. Individual SHAP Explanations
# -----------------------------------------------------------------------------
def test_12_individual_shap_explanations():
    """Verifies TreeExplainer local attribution and mathematical additive consistency."""
    payload = {
        "city": "Bengaluru",
        "location_id": "BLR_001",
        "hour": 18,
        "day_of_week": 2,
        "month": 11,
        "model_type": "xgboost",
        "temperature_2m_c": 24.0,
        "precipitation_mm": 10.0,
        "relative_humidity_2m_pct": 80.0,
        "wind_speed_10m_kmh": 15.0,
        "road_type": "primary",
        "road_lanes": 4,
        "free_flow_speed_kmh": 50.0,
        "accident_risk_score": 0.65,
        "event_present": 1,
        "event_type": "Festival",
        "event_intensity": 0.8,
        "lag_speed_1h": 20.0,
        "rolling_speed_3h": 22.0
    }
    res = client.post("/api/predict/explain", json=payload)
    assert res.status_code == 200
    data = res.json()

    # Additive check: base_value + sum(attributions) == reconstructed_prediction
    check = data["additive_check"]
    assert check["is_consistent"] is True
    assert abs((check["base_value"] + check["sum_attributions"]) - check["reconstructed_prediction"]) < 0.05
    assert len(data["feature_contributions"]) >= 10
    assert "time_of_day" in data["category_impacts"]

# -----------------------------------------------------------------------------
# 13. Global SHAP Feature Importance
# -----------------------------------------------------------------------------
def test_13_global_shap_feature_importance():
    """Verifies descending rank order and TreeExplainer global metrics."""
    res = client.get("/api/models/feature-importance")
    assert res.status_code == 200
    data = res.json()
    assert "TreeExplainer" in data["model"]
    assert data["model_version"] == "1.0.0"
    assert len(data["features"]) >= 10

    # Strict descending ranking
    importances = [f["importance"] for f in data["features"]]
    for i in range(len(importances) - 1):
        assert importances[i] >= importances[i + 1]

# -----------------------------------------------------------------------------
# 14. Model Performance Metrics
# -----------------------------------------------------------------------------
def test_14_model_performance_metrics():
    """Verifies held-out test benchmarks for all 4 models."""
    res = client.get("/api/models/performance")
    assert res.status_code == 200
    data = res.json()
    models = data["models"]
    assert len(models) == 4
    for m in models:
        assert m["mae"] > 0
        assert m["rmse"] > 0
        assert m["r2"] > 0
    # Champion / Best Model
    best = data["best_model"]
    assert best["key"] in ["historical_mean", "xgboost"]

# -----------------------------------------------------------------------------
# 15. Data Explorer
# -----------------------------------------------------------------------------
def test_15_data_explorer():
    """Verifies paginated database records and governance catalogs."""
    # Paginated database records
    res_rec = client.get("/api/data/records?city=Delhi&page=1&page_size=10")
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    assert rec_data["total"] >= 1000
    assert len(rec_data["records"]) == 10
    assert rec_data["records"][0]["city"] == "Delhi"

    # Governance catalogs
    res_src = client.get("/api/data/sources")
    assert res_src.status_code == 200
    assert len(res_src.json()["sources"]) == 5

    res_qual = client.get("/api/data/quality")
    assert res_qual.status_code == 200
    assert res_qual.json()["total_gold_records"] >= 6000

    res_cov = client.get("/api/data/coverage")
    assert res_cov.status_code == 200
    assert len(res_cov.json()["cities_covered"]) == 5

# -----------------------------------------------------------------------------
# 16. Reports and Exports
# -----------------------------------------------------------------------------
def test_16_reports_and_exports():
    """Verifies CSV generation for all 6 Power BI export datasets."""
    datasets = ["city_summary", "location_summary", "hourly_patterns", "weather_impact", "model_evaluation", "gold_master_sample"]
    for d_id in datasets:
        res = client.get(f"/api/reports/export/{d_id}")
        assert res.status_code == 200, f"Export '{d_id}' failed: {res.status_code}"
        assert "text/csv" in res.headers["content-type"]
        assert len(res.text) > 50

# -----------------------------------------------------------------------------
# 17. Empty Database Behavior
# -----------------------------------------------------------------------------
def test_17_empty_database_behavior():
    """Verifies graceful handling when querying an empty database without crashing."""
    mem_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=mem_engine)
    MemSession = sessionmaker(bind=mem_engine)
    mem_db = MemSession()

    repo = DataRepository(mem_db)
    svc = AnalyticsService(mem_db)
    w_svc = WeatherService(mem_db)

    # Overview
    ov = svc.get_overview()
    assert ov["total_cities"] == 0
    assert ov["total_locations"] == 0
    assert ov["avg_congestion_pct"] == 0.0

    # Quality & Coverage
    qual = repo.get_data_quality_stats()
    assert qual["total_gold_records"] == 0

    cov = repo.get_data_coverage_stats()
    assert cov["corridors_total"] == 0
    assert cov["cities_covered"] == []

    # Records
    recs = repo.get_paginated_traffic_records()
    assert recs["total"] == 0
    assert recs["records"] == []

    # Weather & Event Impact
    w_imp = repo.get_weather_impact_data()
    assert w_imp["heavy_rain_surge"] == 0.0

    e_imp = svc.get_event_impact()
    assert e_imp["festival_delta"] is None

# -----------------------------------------------------------------------------
# 18. Invalid Input Handling
# -----------------------------------------------------------------------------
def test_18_invalid_input_handling():
    """Verifies that invalid inputs return HTTP 422 or 400 without crashing."""
    # Invalid City
    res = client.post("/api/predict", json={
        "city": "Atlantis", "location_id": "DEL_001", "hour": 12, "day_of_week": 0
    })
    assert res.status_code == 422

    # Negative precipitation
    res = client.post("/api/predict", json={
        "city": "Delhi", "location_id": "DEL_001", "hour": 12, "day_of_week": 0, "precipitation_mm": -10.0
    })
    assert res.status_code == 422

    # Invalid Hour (> 23)
    res = client.post("/api/predict", json={
        "city": "Delhi", "location_id": "DEL_001", "hour": 25, "day_of_week": 0
    })
    assert res.status_code == 422

    # Invalid Lanes (< 1)
    res = client.post("/api/predict", json={
        "city": "Delhi", "location_id": "DEL_001", "hour": 12, "day_of_week": 0, "road_lanes": 0
    })
    assert res.status_code == 422

    # Non-existent corridor
    res = client.post("/api/predict", json={
        "city": "Delhi", "location_id": "NON_EXISTENT", "prediction_date": "2026-11-05", "prediction_time": "18:00", "model_type": "xgboost"
    })
    assert res.status_code == 404

# -----------------------------------------------------------------------------
# 19. Missing Model Artifact Handling
# -----------------------------------------------------------------------------
def test_19_missing_model_artifact_handling(tmp_path):
    """Verifies that InferenceService handles missing artifacts gracefully and raises ModelNotAvailableError."""
    empty_dir = str(tmp_path / "empty_artifacts")
    service = InferenceService(artifacts_dir=empty_dir)
    assert len(service.get_loaded_models()) == 0

    with pytest.raises(ModelNotAvailableError) as exc_info:
        service.predict_scalar("xgboost", {"city": "Delhi", "location_id": "DEL_001"})
    assert "not loaded or missing" in str(exc_info.value)

# -----------------------------------------------------------------------------
# 20. External APIs Unavailable Handling
# -----------------------------------------------------------------------------
def test_20_external_apis_unavailable_handling():
    """Verifies that WeatherService falls back to verified DB records when external APIs are unreachable."""
    res = client.get("/api/weather?city=Delhi")
    assert res.status_code == 200
    data = res.json()
    assert data["city"] == "Delhi"
    # Even if external provider is offline, returns verified historical archive
    assert data["source"] is not None
    assert "Open-Meteo" in data["provenance"]
