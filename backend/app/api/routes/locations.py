from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database.session import get_db, SessionLocal
from backend.app.repositories.data_repository import DataRepository
from backend.app.services.analytics_service import AnalyticsService
from backend.app.schemas.schemas import LocationItem, LocationTrendsResponse

router = APIRouter(tags=["Locations"])

@router.get("/locations/search", response_model=List[LocationItem], summary="Search monitored road corridors across cities")
def search_locations(
    q: str = Query("", description="Search term for corridor, location name or code"),
    city: str = Query("", description="Optional metropolitan city filter"),
    limit: int = Query(20, description="Maximum number of corridor records to return"),
    db: Session = Depends(get_db),
):
    """Searches road corridors and intersections with actual average congestion and observed speeds."""
    if not isinstance(db, Session):
        db = SessionLocal()
    
    parsed_limit = 20
    if isinstance(limit, int):
        parsed_limit = limit
    elif hasattr(limit, "default") and isinstance(limit.default, int):
        parsed_limit = limit.default

    query_str = q if isinstance(q, str) else (q.default if hasattr(q, "default") else "")
    city_str = city if isinstance(city, str) else (city.default if hasattr(city, "default") else "")

    repo = DataRepository(db)
    return repo.search_locations(q=query_str, city_filter=city_str, limit=parsed_limit)

@router.get("/locations/{location_id}/trends", response_model=LocationTrendsResponse, summary="Get diurnal and weekly trends for a corridor")
def get_location_trends(location_id: str, db: Session = Depends(get_db)):
    """Retrieves 24-hour diurnal patterns, weekday vs weekend speed deltas, and monthly trends for a corridor."""
    if not isinstance(db, Session):
        db = SessionLocal()
    service = AnalyticsService(db)
    try:
        return service.get_location_trends(location_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/locations/{location_id}/history", summary="Get historical time-series speed and congestion observations")
def get_location_history(
    location_id: str,
    start_date: Optional[str] = Query(None, description="ISO format start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="ISO format end date YYYY-MM-DD"),
    limit: int = Query(50, description="Record pagination limit"),
    db: Session = Depends(get_db),
):
    """Retrieves genuine time-series observations from Uber Movement / traffic_records for a corridor."""
    if not isinstance(db, Session):
        db = SessionLocal()
    repo = DataRepository(db)
    loc = repo.get_location_by_code_or_id(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail=f"Location corridor '{location_id}' not found.")

    parsed_limit = 50
    if isinstance(limit, int):
        parsed_limit = limit
    elif hasattr(limit, "default") and isinstance(limit.default, int):
        parsed_limit = limit.default

    s_str = start_date if isinstance(start_date, str) else None
    e_str = end_date if isinstance(end_date, str) else None

    return repo.get_location_history_records(
        location_id=loc.id,
        start_date=s_str,
        end_date=e_str,
        limit=parsed_limit
    )
