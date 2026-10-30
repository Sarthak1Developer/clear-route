import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

logger = logging.getLogger("clearroute.database")

Base = declarative_base()

def get_engine():
    db_url = settings.DATABASE_URL
    try:
        # Try connecting to configured database
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3} if "postgresql" in db_url else {}
        )
        # Test connection
        with engine.connect() as conn:
            logger.info("Successfully connected to PostgreSQL database.")
            return engine
    except Exception as e:
        if settings.DB_FALLBACK_SQLITE:
            logger.warning(
                f"PostgreSQL connection failed ({e}). Falling back to SQLite for local development: {settings.SQLITE_DB_PATH}"
            )
            os.makedirs(os.path.dirname(settings.SQLITE_DB_PATH), exist_ok=True)
            sqlite_url = f"sqlite:///{settings.SQLITE_DB_PATH}"
            return create_engine(sqlite_url, connect_args={"check_same_thread": False})
        raise e

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
