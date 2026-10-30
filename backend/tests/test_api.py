import pytest
from backend.app.database.session import SessionLocal
from backend.app.api.routes import (
    health, overview, cities, locations,
    predictions, events, weather, models,
    data, reports
)
from backend.app.schemas.schemas import PredictionRequest

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_health_route(db_session):
    res = health.health_check(db_session)
    assert res["status"] == "online"
    assert len(res["models_loaded"]) == 4
    assert "historical_mean" in res["models_loaded"]
    assert "xgboost" in res["models_loaded"]

def test_overview_route(db_session):
    res = overview.get_overview(db_session)
    assert res["total_cities"] == 5
    assert res["total_locations"] >= 20
    assert len(res["city_comparison"]) == 5
    assert len(res["hourly_trend"]) == 24

def test_cities_routes(db_session):
    all_cities = cities.get_all_cities(db_session)
    assert len(all_cities) == 5
    delhi = cities.get_city_summary("Delhi", db_session)
    assert delhi["city"] == "Delhi"
    assert len(delhi["top_congested_corridors"]) > 0

    locs = cities.get_city_locations("Delhi", db_session)
    assert len(locs["locations"]) >= 5

def test_locations_routes(db_session):
    search_res = locations.search_locations(q="Laxmi", city="Delhi", db=db_session)
    assert len(search_res) >= 1
    assert "Laxmi Nagar" in search_res[0]["location_name"]

    trends = locations.get_location_trends("DEL_001", db_session)
    assert trends["location_code"] == "DEL_001"
    assert len(trends["hourly"]) == 24
    assert len(trends["weekly"]) == 7

def test_predictions_all_four_models(db_session):
    for m in ["historical_mean", "linear_regression", "random_forest", "xgboost"]:
        req = PredictionRequest(
            city="Delhi",
            location_id="DEL_001",
            prediction_date="2026-11-05",
            prediction_time="18:00",
            model_type=m,
            temperature_c=28.0,
            precipitation_mm=12.5,
            event_present=True,
            event_name="Major Expo",
        )
        res = predictions.predict_congestion(req, db_session)
        assert res["selected_model"] == m
        assert 0.0 <= res["predicted_congestion_pct"] <= 100.0
        assert res["congestion_category"] in ["Low", "Moderate", "High", "Severe"]
        assert len(res["shap_attributions"]) > 0

def test_events_routes(db_session):
    all_events = events.get_all_events(city="Delhi", db=db_session)
    assert len(all_events["events"]) > 0
    impact = events.get_event_impact(db_session)
    assert "festival_delta" in impact

def test_weather_routes(db_session):
    cur_weather = weather.get_weather("Delhi", db_session)
    assert "current_context" in cur_weather
    impact = weather.get_weather_impact(db_session)
    assert len(impact["rain_bands"]) == 4

def test_models_performance_route(db_session):
    perf = models.get_model_performance(db_session)
    assert len(perf["models"]) == 4
    assert perf["best_model"]["key"] == "xgboost"

    feat_imp = models.get_feature_importance()
    assert len(feat_imp["features"]) > 0

def test_data_governance_routes(db_session):
    sources = data.get_data_sources(db_session)
    assert len(sources["sources"]) >= 5
    quality = data.get_data_quality()
    assert quality["completeness_rate"] >= 99.0

def test_reports_export_route():
    res = reports.export_dataset("city_summary")
    assert res.status_code == 200
    assert "text/csv" in res.media_type
    assert b"city_code,city_name" in res.body
