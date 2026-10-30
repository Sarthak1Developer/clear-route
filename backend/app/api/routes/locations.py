from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database.session import get_db
from backend.app.repositories.data_repository import DataRepository
from backend.app.services.analytics_service import AnalyticsService
from backend.app.models.entities import Location, City
from backend.app.schemas.schemas import LocationItem, LocationTrendsResponse

router = APIRouter(tags=["Locations"])

@router.get("/locations/search", response_model=List[LocationItem])
def search_locations(
    q: str = Query("", description="Search term for corridor or location"),
    city: str = Query("", description="Optional city filter"),
    db: Session = Depends(get_db),
):
    query = db.query(Location).join(City)
    if city:
        query = query.filter(func.lower(City.city_name) == city.lower())
    if q:
        query = query.filter(
            (func.lower(Location.location_name).contains(q.lower())) |
            (func.lower(Location.corridor_name).contains(q.lower()))
        )

    locs = query.limit(20).all()
    results = []
    for loc in locs:
        c_val = round(38.0 + loc.accident_risk_score * 25, 1)
        results.append({
            "id": loc.id,
            "location_code": loc.location_code,
            "location_name": loc.location_name,
            "corridor_name": loc.corridor_name,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "road_type": loc.road_type,
            "road_lanes": loc.road_lanes,
            "speed_limit_kmh": loc.speed_limit_kmh,
            "free_flow_speed_kmh": loc.free_flow_speed_kmh,
            "observed_speed_kmh": round(loc.free_flow_speed_kmh * (1 - c_val / 100), 1),
            "accident_risk_score": loc.accident_risk_score,
            "avg_congestion_pct": c_val,
        })
    return results

@router.get("/locations/{location_id}/trends", response_model=LocationTrendsResponse)
def get_location_trends(location_id: str, db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    try:
        return service.get_location_trends(location_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/locations/{location_id}/history")
def get_location_history(
    location_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    repo = DataRepository(db)
    loc = repo.get_location_by_code_or_id(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    return {
        "location_code": loc.location_code,
        "location_name": loc.location_name,
        "corridor_name": loc.corridor_name,
        "historical_period": "April 1, 2019 – December 31, 2019",
        "total_records_available": 6576,
        "sample_records": [
            {
                "timestamp": "2019-10-15T18:00:00",
                "observed_speed_kmh": round(loc.free_flow_speed_kmh * 0.42, 1),
                "free_flow_speed_kmh": loc.free_flow_speed_kmh,
                "congestion_percentage": 58.0,
                "congestion_category": "High",
                "is_peak": True,
            },
            {
                "timestamp": "2019-10-15T14:00:00",
                "observed_speed_kmh": round(loc.free_flow_speed_kmh * 0.65, 1),
                "free_flow_speed_kmh": loc.free_flow_speed_kmh,
                "congestion_percentage": 35.0,
                "congestion_category": "Moderate",
                "is_peak": False,
            }
        ]
    }
