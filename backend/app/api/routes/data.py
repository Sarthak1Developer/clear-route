from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database.session import get_db, SessionLocal
from backend.app.repositories.data_repository import DataRepository
from backend.app.schemas.schemas import DataSourceItem, DataQualityResponse, DataCoverageResponse

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
