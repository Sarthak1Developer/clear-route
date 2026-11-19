import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.database.session import get_db
from backend.app.schemas.schemas import HealthResponse
from backend.app.services.inference_service import inference_service

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse, summary="Check API server, database and ML engine health")
def health_check(db: Session = Depends(get_db)):
    """Verifies database connectivity and reports serialized machine learning models loaded into memory."""
    db_status = "connected"
    records_count = None
    try:
        records_count = db.execute(text("SELECT count(*) FROM traffic_records")).scalar_one()
    except Exception as e:
        db_status = "unhealthy"

    loaded = inference_service.get_loaded_models()

    return {
        "status": "online" if db_status == "connected" and len(loaded) == 4 else "degraded",
        "version": "1.0.0",
        "records_count": records_count,
        "environment": "Evaluation",
        "database": db_status,
        "models_loaded": loaded,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
