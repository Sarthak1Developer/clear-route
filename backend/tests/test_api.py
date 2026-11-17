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
    assert p_data["best_model"]["key"] == "xgboost"
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
