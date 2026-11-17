from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
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
            "source_name": s.source_name,
            "category": s.category,
            "provenance_url": s.provenance_url,
            "temporal_coverage": s.temporal_coverage,
            "spatial_coverage": s.spatial_coverage,
            "record_count": s.record_count,
            "license": s.license,
            "quality_status": s.quality_status,
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
        page_size=page_size
    )

