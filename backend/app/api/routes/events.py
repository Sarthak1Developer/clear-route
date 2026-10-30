from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.repositories.data_repository import DataRepository
from backend.app.services.analytics_service import AnalyticsService
from backend.app.schemas.schemas import EventItem, EventImpactResponse

router = APIRouter(tags=["Events"])

@router.get("/events")
def get_all_events(city: Optional[str] = None, db: Session = Depends(get_db)) -> Dict[str, Any]:
    repo = DataRepository(db)
    events = repo.get_events_by_city_name(city or "")
    
    items = []
    for ev in events:
        impact = 28.0 if ev.event_type == "Festival" else -18.0 if ev.event_type == "Public Holiday" else 19.5
        items.append({
            "id": ev.id,
            "city_name": ev.city.city_name if ev.city else "Metropolitan",
            "event_name": ev.event_name,
            "event_type": ev.event_type,
            "event_date": str(ev.event_date),
            "venue": ev.venue,
            "is_2026_future": ev.is_2026_future,
            "impact_delta": impact,
        })
    return {"city": city or "All Metros", "events": items}

@router.get("/events/{city}")
def get_events_by_city(city: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    repo = DataRepository(db)
    events = repo.get_events_by_city_name(city)
    
    items = []
    for ev in events:
        impact = 28.0 if ev.event_type == "Festival" else -18.0 if ev.event_type == "Public Holiday" else 19.5
        items.append({
            "id": ev.id,
            "city_name": ev.city.city_name if ev.city else city,
            "event_name": ev.event_name,
            "event_type": ev.event_type,
            "event_date": str(ev.event_date),
            "venue": ev.venue,
            "is_2026_future": ev.is_2026_future,
            "impact_delta": impact,
        })
    return {"city": city, "events": items}

@router.get("/events/impact", response_model=EventImpactResponse)
def get_event_impact(db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    return service.get_event_impact()
