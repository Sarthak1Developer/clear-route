from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database.session import get_db
from backend.app.repositories.data_repository import DataRepository
from backend.app.services.analytics_service import AnalyticsService
from backend.app.models.entities import TrafficRecord, Location
from backend.app.schemas.schemas import CityItem, CitySummaryResponse, CityLocationsResponse

router = APIRouter(tags=["Cities"])

@router.get("/cities", response_model=List[CityItem], summary="Get all monitored metropolitan cities with real aggregate metrics")
def get_all_cities(db: Session = Depends(get_db)):
    """Retrieves all monitored metropolitan cities with actual database-calculated congestion averages."""
    repo = DataRepository(db)
    cities = repo.get_all_cities()
    
    result = []
    for c in cities:
        locs = repo.get_locations_by_city_id(c.id)
        # Compute actual average congestion for this city from traffic records
        avg_c = db.query(func.avg(TrafficRecord.congestion_percentage))\
            .join(Location, Location.id == TrafficRecord.location_id)\
            .filter(Location.city_id == c.id)\
            .scalar()
        
        result.append({
            "code": c.city_code,
            "name": c.city_name,
            "state": c.state,
            "lat": c.latitude,
            "lng": c.longitude,
            "zoom": c.zoom_level,
            "corridor_count": len(locs),
            "avg_congestion_pct": round(float(avg_c), 1) if avg_c is not None else 0.0,
        })
    return result

@router.get("/cities/{city}/summary", response_model=CitySummaryResponse, summary="Get comprehensive analytics for a metropolitan city")
def get_city_summary(city: str, db: Session = Depends(get_db)):
    """Retrieves city analytical summary including peak hours, rain impact delta, and top congested corridors."""
    service = AnalyticsService(db)
    try:
        return service.get_city_summary(city)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/cities/{city}/locations", response_model=CityLocationsResponse, summary="Get road corridors and traffic sensors for a city")
def get_city_locations(city: str, db: Session = Depends(get_db)):
    """Retrieves monitored road corridors and arterial segments for a city with genuine observed speeds."""
    repo = DataRepository(db)
    c = repo.get_city_by_name(city)
    if not c:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found.")

    corridors = repo.get_city_corridors_with_stats(c.id)
    return {"city": c.city_name, "locations": corridors}
