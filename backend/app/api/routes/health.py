import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.database.session import get_db
from backend.app.schemas.schemas import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy ({str(e)})"

    return {
        "status": "online",
        "version": "1.0.0",
        "database": db_status,
        "models_loaded": ["historical_mean", "linear_regression", "random_forest", "xgboost"],
        "timestamp": datetime.datetime.now().isoformat(),
    }
