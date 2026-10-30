from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.services.analytics_service import AnalyticsService
from backend.app.schemas.schemas import OverviewResponse

router = APIRouter(tags=["Overview"])

@router.get("/overview", response_model=OverviewResponse)
def get_overview(db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    return service.get_overview()
