import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request, HTTPException
import datetime
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.database.session import Base, engine
from backend.app.api.routes import (
    health, overview, cities, locations,
    predictions, events, weather, models,
    data, reports, analytics
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("clearroute.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist
    logger.info("Initializing ClearRoute database schema...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified.")
    except Exception as e:
        logger.error(f"Error initializing database tables: {e}")
    yield
    # Shutdown
    logger.info("Shutting down ClearRoute API...")

def validate_date_filters(request: Request):
    dates = {}
    for key in ("date", "start_date", "end_date"):
        value = request.query_params.get(key)
        if value:
            try:
                dates[key] = datetime.date.fromisoformat(value)
            except ValueError:
                raise HTTPException(status_code=422, detail=f"{key} must be a valid YYYY-MM-DD date")
    if dates.get("start_date") and dates.get("end_date") and dates["start_date"] > dates["end_date"]:
        raise HTTPException(status_code=422, detail="start_date must not exceed end_date")

app = FastAPI(
    dependencies=[Depends(validate_date_filters)],
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Smart Transportation & Predictive Traffic Analytics Platform for Indian Metropolitan Cities",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(overview.router, prefix=settings.API_V1_STR)
app.include_router(cities.router, prefix=settings.API_V1_STR)
app.include_router(locations.router, prefix=settings.API_V1_STR)
app.include_router(predictions.router, prefix=settings.API_V1_STR)
app.include_router(events.router, prefix=settings.API_V1_STR)
app.include_router(weather.router, prefix=settings.API_V1_STR)
app.include_router(models.router, prefix=settings.API_V1_STR)
app.include_router(data.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "ClearRoute Transportation Intelligence API is live.",
        "documentation": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
