from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.repositories.data_repository import DataRepository
from backend.app.services.analytics_service import AnalyticsService
from backend.app.schemas.schemas import CityItem, CitySummaryResponse, CityLocationsResponse, LocationItem

router = APIRouter(tags=["Cities"])

@router.get("/cities", response_model=List[CityItem])
def get_all_cities(db: Session = Depends(get_db)):
    repo = DataRepository(db)
    cities = repo.get_all_cities()
    
    result = []
    for c in cities:
        locs = repo.get_locations_by_city_id(c.id)
        avg_c = 54.0 if c.city_code == "BLR" else 49.0 if c.city_code == "BOM" else 46.5 if c.city_code == "DEL" else 43.0 if c.city_code == "HYD" else 41.5
        result.append({
            "code": c.city_code,
            "name": c.city_name,
            "state": c.state,
            "lat": c.latitude,
            "lng": c.longitude,
            "zoom": c.zoom_level,
            "corridor_count": len(locs),
            "avg_congestion_pct": avg_c,
        })
    return result

@router.get("/cities/{city}/summary", response_model=CitySummaryResponse)
def get_city_summary(city: str, db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    try:
        return service.get_city_summary(city)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/cities/{city}/locations", response_model=CityLocationsResponse)
def get_city_locations(city: str, db: Session = Depends(get_db)):
    repo = DataRepository(db)
    c = repo.get_city_by_name(city)
    if not c:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found.")

    locations = repo.get_locations_by_city_id(c.id)
    items = []
    for loc in locations:
        c_val = round(min(88.0, 38.0 + loc.accident_risk_score * 30 + (8 if loc.road_type == "trunk" else 0)), 1)
        items.append({
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
    return {"city": c.city_name, "locations": items}
