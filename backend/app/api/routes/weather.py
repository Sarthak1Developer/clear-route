from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.services.analytics_service import AnalyticsService
from backend.app.schemas.schemas import WeatherImpactResponse

router = APIRouter(tags=["Weather"])

@router.get("/weather")
def get_weather(city: Optional[str] = None, db: Session = Depends(get_db)) -> Dict[str, Any]:
    return {
        "city": city or "Delhi",
        "provenance": "Open-Meteo ERA5 Reanalysis API",
        "current_context": {
            "temperature_c": 28.5,
            "precipitation_mm": 0.0,
            "humidity_pct": 62.0,
            "wind_speed_kmh": 11.5,
            "weather_condition": "Clear / Hazy",
        },
        "forecast_scenario": {
            "precipitation_mm": 15.0,
            "expected_surge_pct": 21.4,
        }
    }

@router.get("/weather/impact", response_model=WeatherImpactResponse)
def get_weather_impact(db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    return service.get_weather_impact()
