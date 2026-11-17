from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database.session import get_db, SessionLocal
from backend.app.services.weather_service import WeatherService
from backend.app.services.analytics_service import AnalyticsService
from backend.app.schemas.schemas import WeatherImpactResponse, WeatherResponse, WeatherHistoryResponse

router = APIRouter(tags=["Weather"])

@router.get("/weather", response_model=WeatherResponse, summary="Get latest meteorological conditions and forecast for a city")
def get_weather(
    city: Optional[str] = Query(None, description="Metropolitan city name (e.g. Delhi, Mumbai, Bengaluru)"),
    location_id: Optional[str] = Query(None, description="Optional corridor location code"),
    date: Optional[str] = Query(None, description="Optional historical date query (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Retrieves meteorological conditions.
    When live external provider is available and enabled, returns live conditions and next-day forecast.
    If external provider is offline or unavailable, gracefully falls back to verified historical records with clear source labeling.
    """
    if isinstance(city, Session):
        db = city
        city = None
    elif not isinstance(db, Session):
        db = SessionLocal()

    city_str = city if isinstance(city, str) else None
    loc_id = location_id if isinstance(location_id, str) else None
    date_str = date if isinstance(date, str) else None

    service = WeatherService(db)
    return service.get_current_and_forecast_weather(
        db=db,
        city_name=city_str,
        location_id=loc_id,
        date_str=date_str
    )

@router.get("/weather/history", response_model=WeatherHistoryResponse, summary="Query historical weather observations from database")
def get_weather_history(
    city: Optional[str] = Query(None, description="Metropolitan city filter"),
    location_id: Optional[str] = Query(None, description="Corridor location filter"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    date: Optional[str] = Query(None, description="Exact date filter (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=500, description="Pagination limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """
    Retrieves verified historical weather observations stored in the database.
    Supports city, location, and date range filtering.
    """
    if not isinstance(db, Session):
        db = SessionLocal()

    if hasattr(limit, "default"):
        limit = limit.default
    if hasattr(offset, "default"):
        offset = offset.default

    city_str = city if isinstance(city, str) else None
    loc_id = location_id if isinstance(location_id, str) else None
    s_date = start_date if isinstance(start_date, str) else None
    e_date = end_date if isinstance(end_date, str) else None
    d_exact = date if isinstance(date, str) else None

    service = WeatherService(db)
    return service.get_weather_history(
        db=db,
        city=city_str,
        location_id=loc_id,
        start_date=s_date,
        end_date=e_date,
        date=d_exact,
        limit=int(limit),
        offset=int(offset)
    )

@router.get("/weather/impact", response_model=WeatherImpactResponse, summary="Get precipitation and meteorological impact on congestion")
def get_weather_impact(
    city: Optional[str] = Query(None, description="Optional city filter"),
    location_id: Optional[str] = Query(None, description="Optional corridor location filter"),
    start_date: Optional[str] = Query(None, description="Optional start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Optional end date filter (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Computes empirical rainfall intensity bands, temperature bins, and Pearson correlation coefficients
    from joined ground-truth traffic and meteorological observations.
    """
    if isinstance(city, Session):
        db = city
        city = None
    elif not isinstance(db, Session):
        db = SessionLocal()

    city_name = city if isinstance(city, str) else None
    loc_id = location_id if isinstance(location_id, str) else None
    s_date = start_date if isinstance(start_date, str) else None
    e_date = end_date if isinstance(end_date, str) else None

    service = AnalyticsService(db)
    return service.get_weather_impact(
        city_name=city_name,
        location_id=loc_id,
        start_date=s_date,
        end_date=e_date
    )
