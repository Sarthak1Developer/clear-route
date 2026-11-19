from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.models.entities import TrafficRecord, WeatherRecord, Location, Event
from backend.app.database.session import get_db, SessionLocal
from backend.app.repositories.data_repository import DataRepository
from backend.app.schemas.schemas import DataSourceItem, DataQualityResponse, DataCoverageResponse, PaginatedTrafficRecordsResponse


router = APIRouter(tags=["Data Governance"])

@router.get("/data/sources", summary="Get catalog of ingested Big Data sources")
def get_data_sources(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieves data governance catalog including license, spatial extent, and provenance URL."""
    if not isinstance(db, Session):
        db = SessionLocal()
    repo = DataRepository(db)
    sources = repo.get_all_data_sources()

    items = []
    for s in sources:
        items.append({
            "id": s.id,
            "source_name": "Generated traffic benchmark (legacy catalog claimed Uber Movement)" if s.category.lower() == "traffic" else s.source_name,
            "category": s.category,
            "provenance_url": None if s.category.lower() == "traffic" else s.provenance_url,
            "temporal_coverage": s.temporal_coverage,
            "spatial_coverage": s.spatial_coverage,
            "record_count": db.query({"Traffic": TrafficRecord, "Weather": WeatherRecord, "Infrastructure": Location}.get(s.category, Event)).count() if s.category in {"Traffic", "Weather", "Infrastructure"} or "holiday" in s.source_name.lower() else None,
            "license": "Demonstration dataset; external traffic license not verified" if s.category.lower() == "traffic" else s.license,
            "quality_status": "Generated demonstration data; not verified observations" if s.category.lower() == "traffic" else "Source attribution recorded; independent provenance not verified",
        })
    return {"sources": items}

@router.get("/data/quality", response_model=DataQualityResponse, summary="Get Big Data quality metrics and validation audit")
def get_data_quality(db: Session = Depends(get_db)):
    """Computes real-time data completeness, schema validation status, and row counts from stored records."""
    if not isinstance(db, Session):
        db = SessionLocal()
    repo = DataRepository(db)
    return repo.get_data_quality_stats()

@router.get("/data/coverage", response_model=DataCoverageResponse, summary="Get spatial and temporal coverage bounds")
def get_data_coverage(db: Session = Depends(get_db)):
    """Computes exact spatial cities covered, date boundaries, and corridor counts from stored records."""
    if not isinstance(db, Session):
        db = SessionLocal()
    repo = DataRepository(db)
    return repo.get_data_coverage_stats()

@router.get("/data/records", response_model=PaginatedTrafficRecordsResponse, summary="Query paginated database traffic records")
def get_data_records(
    city: Optional[str] = Query(None, description="City filter"),
    location: Optional[str] = Query(None, description="Location code or corridor filter"),
    start_date: Optional[str] = Query(None, description="Start date filter YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date filter YYYY-MM-DD"),
    sort: str = Query("timestamp_desc", pattern="^(timestamp_desc|timestamp_asc|congestion_desc|congestion_asc)$"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=5, le=200, description="Page size"),
    db: Session = Depends(get_db)
):
    """Retrieves paginated genuine traffic observations stored in the database."""
    if not isinstance(db, Session):
        db = SessionLocal()
    repo = DataRepository(db)
    return repo.get_paginated_traffic_records(
        city=city,
        location_code=location,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
        sort=sort
    )



@router.get('/data/readiness', summary='Active database, required artifacts and source limitations')
def data_readiness(db: Session = Depends(get_db)):
    from pathlib import Path
    from sqlalchemy import func,inspect,text
    import json
    from backend.app.services.inference_service import inference_service
    from backend.app.services.source_status import weather_source
    root=Path(__file__).resolve().parents[4]
    required=['data/gold/master_congestion/gold_master_congestion.parquet','data/external/era5_2019/weather.parquet','data/external/era5_2019/manifest.json','ml/artifacts/preprocessor.joblib','ml/artifacts/metrics.json']
    required += [f'ml/artifacts/model_{k}.joblib' for k in ['historical_mean','linear_regression','random_forest','xgboost']]
    files=[{'path':p,'available':(root/p).is_file()} for p in required]
    counts={'traffic':db.query(TrafficRecord).count(),'weather':db.query(WeatherRecord).count(),'corridors':db.query(Location).count(),'events':db.query(Event).count()}
    manifest={}
    if inspect(db.get_bind()).has_table('analytics_manifest'):
        row=db.execute(text('SELECT payload FROM analytics_manifest WHERE id=1')).scalar()
        if row:manifest=json.loads(row)
    loaded=inference_service.get_loaded_models()
    reconciled=bool(manifest) and counts['traffic']==manifest.get('traffic_rows')
    return {'status':'ready' if all(f['available'] for f in files) and reconciled and len(loaded)==4 else 'incomplete',
        'scope':'Academic benchmark application; not independently verified traffic observations',
        'counts':counts,'gold_reconciled':reconciled,'models_loaded':loaded,'required_files':files,
        'weather':weather_source(db),'traffic':{'kind':'generated_benchmark','observational_provenance_verified':False},
        'events':{'kind':'Gold city-day annotations','exact_duration_and_venue_available':False},
        'limitations':['Traffic is generated benchmark data. Real-world forecasting accuracy is not established.','Event annotations do not establish venue-level or causal effects.','Legacy raw-pipeline inputs lack risk scores, event intensity/confidence and weather provenance; application uses pinned Gold and the verified ERA5 archive.']}
