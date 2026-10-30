import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "ClearRoute - Smart Transportation & Predictive Traffic Analytics"

    # Server Configuration
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 5173
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    # Database
    DATABASE_URL: str = "postgresql://clearroute_user:clearroute_secure_password@localhost:5432/clearroute_db"
    DB_FALLBACK_SQLITE: bool = True
    SQLITE_DB_PATH: str = "data/clearroute_app.db"

    # Big Data & Storage Directories
    DATA_RAW_DIR: str = "data/raw"
    DATA_BRONZE_DIR: str = "data/bronze"
    DATA_SILVER_DIR: str = "data/silver"
    DATA_GOLD_DIR: str = "data/gold"
    DATA_SAMPLE_DIR: str = "data/sample"
    POWERBI_EXPORTS_DIR: str = "powerbi/exports"

    # Machine Learning Artifacts
    ML_ARTIFACTS_DIR: str = "ml/artifacts"
    DEFAULT_PREDICTION_MODEL: str = "xgboost"

    # External APIs
    OPEN_METEO_BASE_URL: str = "https://archive-api.open-meteo.com/v1/archive"
    OPEN_METEO_FORECAST_URL: str = "https://api.open-meteo.com/v1/forecast"
    TICKETMASTER_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
