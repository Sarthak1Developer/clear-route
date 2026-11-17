import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.repositories.data_repository import DataRepository
from backend.app.models.entities import City, Location, TrafficRecord, WeatherRecord
from backend.app.schemas.schemas import PredictionRequest

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------------------------------------------------------
# 1. Health & Core System Status
# -----------------------------------------------------------------------------
def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["database"] == "connected"
    assert len(data["models_loaded"]) == 4
    assert "xgboost" in data["models_loaded"]

# -----------------------------------------------------------------------------
# 2. Overview Analytics
# -----------------------------------------------------------------------------
def test_overview_endpoint():
    res = client.get("/api/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["total_cities"] == 5
    assert data["total_locations"] == 25
    assert data["total_records_processed"] == 6000
    assert 0.0 < data["avg_congestion_pct"] < 100.0
    assert len(data["city_comparison"]) == 5
    assert len(data["hourly_trend"]) == 24
    assert len(data["weekly_trend"]) == 7
    assert len(data["monthly_trend"]) >= 9
    assert len(data["weather_correlation"]) == 4

# -----------------------------------------------------------------------------
# 3. Cities Analytics & Corridors
# -----------------------------------------------------------------------------
def test_cities_endpoints():
    # All cities
    res = client.get("/api/cities")
    assert res.status_code == 200
    cities_list = res.json()
    assert len(cities_list) == 5
    delhi_obj = next((c for c in cities_list if c["code"] == "DEL"), None)
    assert delhi_obj is not None
    assert delhi_obj["corridor_count"] == 5

    # City summary
    res_delhi = client.get("/api/cities/Delhi/summary")
    assert res_delhi.status_code == 200
    d_data = res_delhi.json()
    assert d_data["city"] == "Delhi"
    assert len(d_data["top_congested_corridors"]) == 5
    assert len(d_data["hourly_distribution"]) == 24
    assert "peak_hours_str" in d_data

    # City locations
    res_locs = client.get("/api/cities/Delhi/locations")
    assert res_locs.status_code == 200
    locs_data = res_locs.json()
    assert locs_data["city"] == "Delhi"
    assert len(locs_data["locations"]) == 5
    first_loc = locs_data["locations"][0]
    assert first_loc["speed_limit_kmh"] > 0
    assert first_loc["observed_speed_kmh"] is not None

    # Invalid city 404 test
    res_invalid = client.get("/api/cities/NonExistentCity/summary")
    assert res_invalid.status_code == 404

# -----------------------------------------------------------------------------
# 4. Locations Search, Trends & History
# -----------------------------------------------------------------------------
def test_locations_endpoints():
    # Search
    res_search = client.get("/api/locations/search?q=Laxmi&city=Delhi")
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert len(search_data) >= 1
    assert "Laxmi Nagar" in search_data[0]["location_name"]

    # Search with empty query matches all
    res_empty_q = client.get("/api/locations/search?limit=10")
    assert res_empty_q.status_code == 200
    assert len(res_empty_q.json()) == 10

    # Search non-existent
    res_none = client.get("/api/locations/search?q=NonExistentRoadName123")
    assert res_none.status_code == 200
    assert res_none.json() == []

    # Trends
    res_trends = client.get("/api/locations/DEL_001/trends")
    assert res_trends.status_code == 200
    t_data = res_trends.json()
    assert t_data["location_code"] == "DEL_001"
    assert len(t_data["hourly"]) == 24
    assert len(t_data["weekly"]) == 7
    assert len(t_data["monthly"]) >= 9

    # Trends with invalid location 404
    res_bad_trend = client.get("/api/locations/INVALID_LOC_999/trends")
    assert res_bad_trend.status_code == 404

    # History
    res_hist = client.get("/api/locations/DEL_001/history?limit=10")
    assert res_hist.status_code == 200
    h_data = res_hist.json()
    assert h_data["location_code"] == "DEL_001"
    assert h_data["total_records_available"] > 0
    assert len(h_data["sample_records"]) <= 10

# -----------------------------------------------------------------------------
# 5. Events & Public Holidays (with unshadowed route verification)
# -----------------------------------------------------------------------------
def test_events_endpoints():
    # Unshadowed route verification: /api/events/impact must return impact schema, NOT 404 or events list
    res_impact = client.get("/api/events/impact")
    assert res_impact.status_code == 200
    imp_data = res_impact.json()
    assert "festival_delta" in imp_data
    assert "holiday_delta" in imp_data
    assert len(imp_data["hourly_comparison"]) == 24
    assert imp_data.get("data_backed") is True
    assert "source" in imp_data

    # City-filtered event impact
    res_blr_impact = client.get("/api/events/impact?city=Bengaluru")
    assert res_blr_impact.status_code == 200
    assert len(res_blr_impact.json()["hourly_comparison"]) == 24

    # All events retrieval
    res_events = client.get("/api/events")
    assert res_events.status_code == 200
    ev_data = res_events.json()
    assert len(ev_data["events"]) >= 10
    first_event = ev_data["events"][0]
    assert "source" in first_event
    assert "source_verified" in first_event
    assert "event_type" in first_event

    # Category filtering (e.g. Festival)
    res_festivals = client.get("/api/events?event_type=Festival")
    assert res_festivals.status_code == 200
    fest_data = res_festivals.json()
    assert len(fest_data["events"]) > 0
    assert all(e["event_type"] == "Festival" for e in fest_data["events"])

    # Future scenario events (2026) must have impact_delta as None (no fake metrics)
    res_future = client.get("/api/events?is_future=true")
    assert res_future.status_code == 200
    future_events = res_future.json()["events"]
    assert len(future_events) >= 5
    for fe in future_events:
        assert fe["is_2026_future"] is True
        assert fe["impact_delta"] is None

    # Historical observed event should compute real impact delta
    res_historical = client.get("/api/events?is_future=false")
    assert res_historical.status_code == 200
    hist_events = res_historical.json()["events"]
    assert len(hist_events) >= 5
    # Verify that not every event is given an arbitrary fixed 24.5
    deltas = [e["impact_delta"] for e in hist_events if e["impact_delta"] is not None]
    assert 24.5 not in deltas or len(set(deltas)) > 1

    # City-specific events
    res_kolkata = client.get("/api/events/Kolkata")
    assert res_kolkata.status_code == 200
    k_data = res_kolkata.json()
    assert len(k_data["events"]) >= 1
    assert all(e["city_name"] == "Kolkata" for e in k_data["events"])

    # Location-based events filtering (mapped via city of corridor)
    res_loc_events = client.get("/api/events?location_id=DEL_001")
    assert res_loc_events.status_code == 200
    assert len(res_loc_events.json()["events"]) >= 1
    assert all(e["city_name"] == "Delhi" for e in res_loc_events.json()["events"])

    # Exact date filtering
    res_date_events = client.get("/api/events?date=2019-09-02")
    assert res_date_events.status_code == 200
    date_evs = res_date_events.json()["events"]
    assert len(date_evs) >= 1
    assert date_evs[0]["event_date"] == "2019-09-02"
    assert "Ganesh" in date_evs[0]["event_name"]

# -----------------------------------------------------------------------------
# 6. Meteorological Analytics (Weather)
# -----------------------------------------------------------------------------
def test_weather_endpoints():
    # Current weather endpoint with graceful fallback
    res_weather = client.get("/api/weather?city=Delhi")
    assert res_weather.status_code == 200
    w_data = res_weather.json()
    assert w_data["city"] == "Delhi"
    assert "current_context" in w_data
    assert w_data["current_context"]["temperature_c"] > 0
    assert "source" in w_data
    assert "provider_available" in w_data
    assert "provider_status" in w_data
    assert isinstance(w_data["provider_available"], bool)

    # Weather by corridor location
    res_loc_weather = client.get("/api/weather?location_id=DEL_001")
    assert res_loc_weather.status_code == 200
    loc_w_data = res_loc_weather.json()
    assert loc_w_data["city"] == "Delhi"
    assert loc_w_data["location_id"] == "DEL_001"

    # Historical weather observations history endpoint
    res_history = client.get("/api/weather/history?city=Delhi&limit=10")
    assert res_history.status_code == 200
    h_data = res_history.json()
    assert h_data["total_records"] > 0
    assert len(h_data["records"]) <= 10
    assert "source" in h_data
    first_rec = h_data["records"][0]
    assert first_rec["city_name"] == "Delhi"
    assert "temperature_c" in first_rec
    assert "precipitation_mm" in first_rec

    # Historical date range filtering
    res_filtered_hist = client.get("/api/weather/history?city=Mumbai&start_date=2019-06-01&end_date=2019-08-31")
    assert res_filtered_hist.status_code == 200
    f_hist_data = res_filtered_hist.json()
    assert f_hist_data["total_records"] > 0
    for r in f_hist_data["records"]:
        assert "2019-06" in r["timestamp"] or "2019-07" in r["timestamp"] or "2019-08" in r["timestamp"]

    # Weather impact correlation curves
    res_impact = client.get("/api/weather/impact")
    assert res_impact.status_code == 200
    imp_data = res_impact.json()
    assert len(imp_data["rain_bands"]) == 4
    assert len(imp_data["temp_bands"]) == 4
    assert "rain_correlation" in imp_data
    assert "temp_correlation" in imp_data
    assert "source" in imp_data

    # City-specific weather impact
    res_mum_impact = client.get("/api/weather/impact?city=Mumbai")
    assert res_mum_impact.status_code == 200
    assert len(res_mum_impact.json()["rain_bands"]) == 4

    # Historical exact date weather retrieval
    res_date_weather = client.get("/api/weather?city=Delhi&date=2019-12-30")
    assert res_date_weather.status_code == 200
    dw_data = res_date_weather.json()
    assert dw_data["city"] == "Delhi"
    assert "2019-12-30" in dw_data["timestamp"]
    assert dw_data["current_context"]["is_live"] is False
    assert "Open-Meteo ERA5" in dw_data["source"]

    # Graceful handling of unknown city
    res_unknown = client.get("/api/weather?city=Atlantis")
    assert res_unknown.status_code == 200
    un_data = res_unknown.json()
    assert un_data["provider_available"] is False

# -----------------------------------------------------------------------------
# 7. Model Benchmarking, SHAP & Explainability
# -----------------------------------------------------------------------------
def test_models_endpoints():
    # Performance
    res_perf = client.get("/api/models/performance")
    assert res_perf.status_code == 200
    p_data = res_perf.json()
    assert len(p_data["models"]) == 4
    assert p_data["best_model"]["key"] in ["historical_mean", "xgboost"]
    assert p_data["best_model"]["key"] == "historical_mean"  # Validated against metrics.json held-out benchmarks
    assert len(p_data["actual_vs_predicted"]) == 10

    # Feature Importance from SHAP summary
    res_feat = client.get("/api/models/feature-importance")
    assert res_feat.status_code == 200
    f_data = res_feat.json()
    assert len(f_data["features"]) > 0
    assert f_data["features"][0]["importance"] >= f_data["features"][-1]["importance"]

    # Explainability
    res_exp = client.get("/api/models/explainability")
    assert res_exp.status_code == 200
    e_data = res_exp.json()
    assert len(e_data["top_drivers"]) > 0

# -----------------------------------------------------------------------------
# 8. Data Governance, Quality & Coverage
# -----------------------------------------------------------------------------
def test_data_governance_endpoints():
    # Sources
    res_sources = client.get("/api/data/sources")
    assert res_sources.status_code == 200
    s_data = res_sources.json()
    assert len(s_data["sources"]) == 5

    # Quality
    res_quality = client.get("/api/data/quality")
    assert res_quality.status_code == 200
    q_data = res_quality.json()
    assert q_data["total_gold_records"] == 6000
    assert q_data["completeness_rate"] == 100.0

    # Coverage
    res_coverage = client.get("/api/data/coverage")
    assert res_coverage.status_code == 200
    cov_data = res_coverage.json()
    assert len(cov_data["cities_covered"]) == 5
    assert cov_data["corridors_total"] == 25
    assert "2019" in cov_data["start_date"]

    # Paginated Database Records
    res_records = client.get("/api/data/records?city=Bengaluru&page=1&page_size=10")
    assert res_records.status_code == 200
    rec_data = res_records.json()
    assert rec_data["total"] == 1200
    assert len(rec_data["records"]) == 10
    assert rec_data["records"][0]["city"] == "Bengaluru"


# -----------------------------------------------------------------------------
# 9. Predictive Scenario Inference Across All 4 ML Models
# -----------------------------------------------------------------------------
def test_predictions_all_models():
    for model_name in ["historical_mean", "linear_regression", "random_forest", "xgboost"]:
        payload = {
            "city": "Delhi",
            "location_id": "DEL_001",
            "prediction_date": "2026-11-05",
            "prediction_time": "18:00",
            "model_type": model_name,
            "temperature_c": 28.0,
            "precipitation_mm": 12.5,
            "humidity_pct": 70.0,
            "wind_speed_kmh": 12.0,
            "event_present": True,
            "event_name": "International Tech Expo"
        }
        res = client.post("/api/predict", json=payload)
        assert res.status_code == 200
        p_res = res.json()
        assert p_res["selected_model"] == model_name
        assert 0.0 <= p_res["predicted_congestion_pct"] <= 100.0
        assert p_res["congestion_category"] in ["Low", "Moderate", "High", "Severe"]
        assert len(p_res["shap_attributions"]) > 0
        assert "confidence_interval" in p_res

def test_prediction_invalid_inputs():
    # Invalid model
    bad_model_payload = {
        "city": "Delhi",
        "location_id": "DEL_001",
        "prediction_date": "2026-11-05",
        "prediction_time": "18:00",
        "model_type": "invalid_deep_neural_net"
    }
    res_bad_model = client.post("/api/predict", json=bad_model_payload)
    assert res_bad_model.status_code == 400

    # Invalid corridor
    bad_loc_payload = {
        "city": "Delhi",
        "location_id": "NON_EXISTENT_CORRIDOR",
        "prediction_date": "2026-11-05",
        "prediction_time": "18:00",
        "model_type": "xgboost"
    }
    res_bad_loc = client.post("/api/predict", json=bad_loc_payload)
    assert res_bad_loc.status_code == 404

    # Invalid date
    bad_date_payload = {
        "city": "Delhi",
        "location_id": "DEL_001",
        "prediction_date": "invalid-date",
        "prediction_time": "18:00",
        "model_type": "xgboost"
    }
    res_bad_date = client.post("/api/predict", json=bad_date_payload)
    assert res_bad_date.status_code == 400

# -----------------------------------------------------------------------------
# 10. Reports & Exports
# -----------------------------------------------------------------------------
def test_reports_export_endpoints():
    datasets = ["city_summary", "location_summary", "hourly_patterns", "weather_impact", "model_evaluation", "gold_master_sample"]
    for d_id in datasets:
        res = client.get(f"/api/reports/export/{d_id}")
        assert res.status_code == 200
        assert "text/csv" in res.headers["content-type"]
        assert len(res.text) > 20

# -----------------------------------------------------------------------------
# 11. ML Model Integration Contract & Reliability Tests
# -----------------------------------------------------------------------------
def test_prediction_output_contract_fields():
    """Verifies that all required fields from the ML Integration Contract are present in prediction responses."""
    payload = {
        "city": "Bengaluru",
        "location_id": "BLR_001",
        "hour": 18,
        "day_of_week": 2,
        "month": 11,
        "model_type": "xgboost",
        "temperature_2m_c": 24.5,
        "precipitation_mm": 14.5,
        "relative_humidity_2m_pct": 82.0,
        "wind_speed_10m_kmh": 16.0,
        "road_type": "primary",
        "road_lanes": 4,
        "length_m": 3100.0,
        "free_flow_speed_kmh": 50.0,
        "accident_risk_score": 0.70,
        "event_present": 1,
        "event_type": "Assembly",
        "event_intensity": 0.75,
        "lag_speed_1h": 22.0,
        "rolling_speed_3h": 25.0
    }
    res = client.post("/api/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "timestamp" in data
    assert data["city"] == "Bengaluru"
    assert data["location_id"] == "BLR_001"
    assert data["location_info"] is not None
    assert data["location_info"]["road_lanes"] == 4
    assert 0.0 <= data["predicted_congestion_pct"] <= 100.0
    assert data["model_name"] == "XGBoost Regressor"
    assert data["model_version"] == "1.0.0"
    assert data["selected_model"] == "xgboost"
    assert data["input_features"] is not None
    assert data["input_features"]["hour"] == 18
    assert data["input_features"]["precipitation_mm"] == 14.5
    assert len(data["shap_attributions"]) > 0

def test_prediction_response_against_direct_model_inference():
    """Verifies that the API response strictly matches direct inference computed by the model artifact."""
    from backend.app.services.inference_service import inference_service
    payload = {
        "city": "Delhi",
        "location_id": "DEL_001",
        "hour": 9,
        "day_of_week": 1,
        "month": 10,
        "model_type": "xgboost",
        "temperature_c": 26.0,
        "precipitation_mm": 0.0,
        "road_lanes": 6,
        "free_flow_speed_kmh": 60.0
    }
    res = client.post("/api/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    api_val = data["predicted_congestion_pct"]

    # Compute direct model inference on the exact feature dictionary
    direct_val = round(inference_service.predict_scalar("xgboost", data["input_features"]), 1)
    assert api_val == direct_val

def test_prediction_missing_optional_inputs_graceful_defaults():
    """Verifies that omitted optional features are automatically imputed without failing."""
    minimal_payload = {
        "city": "Mumbai",
        "location_id": "BOM_001",
        "hour": 14,
        "day_of_week": 3,
        "model_type": "xgboost"
    }
    res = client.post("/api/predict", json=minimal_payload)
    assert res.status_code == 200
    data = res.json()
    assert 0.0 <= data["predicted_congestion_pct"] <= 100.0
    assert data["city"] == "Mumbai"

def test_prediction_invalid_feature_boundaries():
    """Verifies that invalid input features outside defined bounds return HTTP 422 Unprocessable Entity."""
    # Invalid City
    res_bad_city = client.post("/api/predict", json={
        "city": "Atlantis", "location_id": "DEL_001", "hour": 12, "day_of_week": 0
    })
    assert res_bad_city.status_code == 422

    # Negative precipitation
    res_neg_rain = client.post("/api/predict", json={
        "city": "Delhi", "location_id": "DEL_001", "hour": 12, "day_of_week": 0, "precipitation_mm": -10.0
    })
    assert res_neg_rain.status_code == 422

    # Invalid hour
    res_bad_hour = client.post("/api/predict", json={
        "city": "Delhi", "location_id": "DEL_001", "hour": 25, "day_of_week": 0
    })
    assert res_bad_hour.status_code == 422

    # Invalid road lanes
    res_bad_lanes = client.post("/api/predict", json={
        "city": "Delhi", "location_id": "DEL_001", "hour": 12, "day_of_week": 0, "road_lanes": 0
    })
    assert res_bad_lanes.status_code == 422

def test_inference_service_graceful_startup_missing_artifacts(tmp_path):
    """Verifies that InferenceService handles missing artifacts directory gracefully without crashing."""
    from backend.app.services.inference_service import InferenceService, ModelNotAvailableError
    empty_dir = str(tmp_path / "empty_artifacts")
    service = InferenceService(artifacts_dir=empty_dir)
    assert len(service.get_loaded_models()) == 0
    with pytest.raises(ModelNotAvailableError) as exc_info:
        service.predict_scalar("xgboost", {"city": "Delhi", "location_id": "DEL_001"})
    assert "not loaded or missing" in str(exc_info.value)

# -----------------------------------------------------------------------------
# 12. Dedicated Genuine SHAP TreeExplainer & Additive Efficiency Tests
# -----------------------------------------------------------------------------
def test_individual_prediction_explanation_additive_efficiency():
    """
    Verifies that the individual prediction explanation endpoint executes genuine
    SHAP TreeExplainer local attributions satisfying exact additive efficiency:
    predicted_congestion = base_value + sum(attribution_value).
    """
    payload = {
        "city": "Bengaluru",
        "location_id": "BLR_001",
        "hour": 18,
        "day_of_week": 2,
        "month": 11,
        "model_type": "xgboost",
        "temperature_2m_c": 24.5,
        "precipitation_mm": 14.5,
        "relative_humidity_2m_pct": 82.0,
        "wind_speed_10m_kmh": 16.0,
        "road_type": "primary",
        "road_lanes": 4,
        "free_flow_speed_kmh": 50.0,
        "accident_risk_score": 0.70,
        "event_present": 1,
        "event_type": "Assembly",
        "event_intensity": 0.75,
        "lag_speed_1h": 22.0,
        "rolling_speed_3h": 25.0
    }
    res = client.post("/api/predict/explain", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["model_id"] == "xgboost"
    assert data["model_version"] == "1.0.0"
    assert "predicted_congestion" in data
    assert "base_value" in data
    assert 20.0 <= data["base_value"] <= 30.0

    # Verify Additive Efficiency
    check = data["additive_check"]
    assert check["is_consistent"] is True
    assert abs((check["base_value"] + check["sum_attributions"]) - check["reconstructed_prediction"]) < 0.05
    assert abs(check["reconstructed_prediction"] - data["predicted_congestion"]) < 0.2

    # Verify Feature Contributions
    contribs = data["feature_contributions"]
    assert len(contribs) > 10
    top_c = contribs[0]
    assert "feature" in top_c
    assert "display_name" in top_c
    assert "category" in top_c
    assert "feature_value" in top_c
    assert "attribution_value" in top_c
    assert "direction" in top_c
    assert "percentage_contribution" in top_c
    assert top_c["direction"] in ["increases_congestion", "dampens_congestion"]

    # Verify Category Aggregated Impacts
    cat_impacts = data["category_impacts"]
    assert "time_of_day" in cat_impacts
    assert "weather_condition" in cat_impacts
    assert "traffic_history" in cat_impacts
    assert "road_characteristics" in cat_impacts

    # Verify Narrative Summary
    assert len(data["explanation_summary"]) > 20
    assert len(data["limitations_and_caveats"]) >= 3

def test_global_shap_feature_importance_ranking():
    """
    Verifies that the feature-importance endpoint returns genuine global SHAP
    attributions (mean absolute SHAP) ranked in descending order.
    """
    res = client.get("/api/models/feature-importance")
    assert res.status_code == 200
    data = res.json()

    assert "TreeExplainer" in data["model"]
    assert data["model_version"] == "1.0.0"
    assert data["base_value"] > 0
    assert len(data["features"]) >= 10

    # Verify strict descending ranking
    importances = [f["importance"] for f in data["features"]]
    for i in range(len(importances) - 1):
        assert importances[i] >= importances[i + 1]

    # Verify top feature has realistic SHAP magnitude
    first = data["features"][0]
    assert first["rank"] == 1
    assert first["importance"] > 1.0
    assert first["feature"] in ["hour", "is_peak_hour"]

def test_global_shap_explainability_summary_drivers():
    """
    Verifies that the explainability endpoint returns genuine qualitative domain
    drivers and top physical/meteorological/temporal factors without mock numbers.
    """
    res = client.get("/api/models/explainability")
    assert res.status_code == 200
    data = res.json()

    assert data["model_version"] == "1.0.0"
    assert len(data["top_drivers"]) >= 5
    for driver in data["top_drivers"]:
        assert driver["mean_shap_pct"] > 0
        assert driver["direction"] in ["Increases Congestion", "Dampens Congestion", "Diurnal Commuter Rhythm", "Traffic Momentum", "Modulates Congestion"]
        assert driver["rank"] >= 1

    # Verify category domain drivers
    assert data["category_drivers"] is not None
    assert "time_of_day_driver" in data["category_drivers"]
    assert "weather_condition_driver" in data["category_drivers"]
    assert len(data["summary_text"]) > 20

def test_stored_prediction_explain_by_id():
    """
    Verifies that a previously computed prediction record can have its individual
    SHAP explanation retrieved by record ID.
    """
    # Create prediction
    res_pred = client.post("/api/predict", json={
        "city": "Delhi",
        "location_id": "DEL_001",
        "prediction_date": "2026-11-10",
        "prediction_time": "18:00",
        "model_type": "xgboost"
    })
    assert res_pred.status_code == 200
    
    # Check explanation endpoint for prediction ID 1
    res_expl = client.get("/api/predictions/1/explain")
    assert res_expl.status_code == 200
    expl_data = res_expl.json()
    assert expl_data["additive_check"]["is_consistent"] is True
    assert len(expl_data["feature_contributions"]) > 5


