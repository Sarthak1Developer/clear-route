from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.session import get_db, SessionLocal
from backend.app.repositories.data_repository import DataRepository
from backend.app.services.analytics_service import AnalyticsService
from backend.app.schemas.schemas import EventItem, EventsListResponse, EventImpactResponse

router = APIRouter(tags=["Events"])

# NOTE: Specific route '/events/impact' MUST precede parameterized '/events/{city}'
@router.get("/events/impact", response_model=EventImpactResponse, summary="Get event and holiday traffic perturbation impact")
def get_event_impact(
    city: Optional[str] = Query(None, description="Metropolitan city name filter"),
    location_id: Optional[str] = Query(None, description="Optional corridor location filter"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Calculates empirical event impact comparing traffic during events vs normal commuting intervals.
    Never fabricates static percentages; accurately reports actual ground-truth delta or null when unobserved.
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
    return service.get_event_impact(
        city_name=city_name,
        location_id=loc_id,
        start_date=s_date,
        end_date=e_date
    )

@router.get("/events", response_model=EventsListResponse, summary="Get verified historical and forward-looking events with filtering")
def get_all_events(
    city: Optional[str] = Query(None, description="Metropolitan city filter"),
    location_id: Optional[str] = Query(None, description="Corridor location code"),
    date: Optional[str] = Query(None, description="Exact date filter (YYYY-MM-DD)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    event_type: Optional[str] = Query(None, description="Category filter (Festival, Public Holiday, Sports, Assembly, Concert)"),
    is_future: Optional[bool] = Query(None, description="Filter for 2026 future scenario events (True) or 2019 historical events (False)"),
    db: Session = Depends(get_db)
):
    """
    Retrieves events from the database with multi-dimensional filtering.
    Calculates actual historical traffic impact deltas against baseline without arbitrary hardcoded values.
    Returns source attribution and verification status.
    """
    if isinstance(city, Session):
        db = city
        city = None
    elif not isinstance(db, Session):
        db = SessionLocal()

    repo = DataRepository(db)
    city_str = city if isinstance(city, str) else None
    loc_id = location_id if isinstance(location_id, str) else None
    date_str = date if isinstance(date, str) else None
    s_date = start_date if isinstance(start_date, str) else None
    e_date = end_date if isinstance(end_date, str) else None
    ev_type = event_type if isinstance(event_type, str) else None
    future_flag = is_future if isinstance(is_future, bool) else None

    loc_obj = repo.get_location_by_code(loc_id) if loc_id else None
    if loc_id and not loc_obj:
        raise HTTPException(404,"Unknown corridor")
    if loc_obj and city_str and loc_obj.city.city_name.lower()!=city_str.lower():
        raise HTTPException(400,"Corridor does not belong to city")
    raw_loc_id = loc_obj.id if loc_obj else None

    events = repo.get_filtered_events(
        city_name=city_str,
        location_id=raw_loc_id,
        date=date_str,
        start_date=s_date,
        end_date=e_date,
        event_type=ev_type,
        is_future=future_flag
    )

    items = []
    for ev in events:
        impact = repo.calculate_event_impact_delta(ev, location_id=raw_loc_id)
        source_attr = ev.source_attribution
        is_verified = bool(source_attr and source_attr.strip().lower() not in ["", "unknown", "none", "unverified"])

        items.append({
            "id": ev.id,
            "city_name": ev.city.city_name if ev.city else "Metropolitan",
            "event_name": ev.event_name,
            "event_type": ev.event_type,
            "event_date": str(ev.event_date),
            "venue": ev.venue,
            "expected_attendance": ev.expected_attendance,
            "is_2026_future": ev.is_2026_future,
            "source": source_attr,
            "source_verified": False, # A nonempty attribution is not independent verification.
            "impact_delta": impact,
        })

    return {
        "city": city_str or "All Metros",
        "total_events": len(items),
        "events": items,
        "source_attribution": "Gazette of India, State Cultural Calendars & Police Traffic Advisories"
    }

@router.get("/events/{city}", response_model=EventsListResponse, summary="Get events filtered by metropolitan city")
def get_events_by_city(
    city: str,
    location_id: Optional[str] = Query(None, description="Optional corridor location filter"),
    date: Optional[str] = Query(None, description="Exact date filter (YYYY-MM-DD)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    event_type: Optional[str] = Query(None, description="Category filter"),
    is_future: Optional[bool] = Query(None, description="Filter future scenario events"),
    db: Session = Depends(get_db)
):
    """
    City-specific route for backwards compatibility with frontend API calls.
    """
    if not isinstance(db, Session):
        db = SessionLocal()

    return get_all_events(
        city=city,
        location_id=location_id,
        date=date,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        is_future=is_future,
        db=db
    )


@router.get("/events/{event_id}/observations", summary="City-day traffic around an annotated event date")
def event_observations(event_id: int, location_id: str | None = None, db: Session = Depends(get_db)):
    import datetime
    from sqlalchemy import func
    from backend.app.models.entities import Event,TrafficRecord,Location
    event=db.query(Event).filter(Event.id==event_id).first()
    if event is None:raise HTTPException(404,"Event not found")
    q=db.query(TrafficRecord).join(Location).filter(Location.city_id==event.city_id)
    if location_id:
        loc=DataRepository(db).get_location_by_code(location_id)
        if loc is None:raise HTTPException(404,"Corridor not found")
        if loc.city_id!=event.city_id:raise HTTPException(400,"Corridor does not belong to event city")
        q=q.filter(TrafficRecord.location_id==loc.id)
    windows=[]
    for offset,label in [(-1,"previous_day"),(0,"event_day"),(1,"following_day")]:
        date=event.event_date+datetime.timedelta(days=offset)
        average,count=q.with_entities(func.avg(TrafficRecord.congestion_percentage),func.count()).filter(func.date(TrafficRecord.timestamp)==str(date)).first()
        windows.append({"window":label,"date":str(date),"mean_congestion":round(float(average),2) if count else None,"sample_count":count})
    return {"event_id":event.id,"event_name":event.event_name,"city":event.city.city_name,"location_id":location_id,
        "status":"available" if any(r['sample_count'] for r in windows) else "unavailable",
        "resolution":"city-day annotation; exact venue radius and start/end times unavailable",
        "windows":windows,"matched_weekday_delta":DataRepository(db).calculate_event_impact_delta(event,loc.id if location_id else None),
        "source":event.source_attribution,"source_verified":False,"causal_effect_established":False}
