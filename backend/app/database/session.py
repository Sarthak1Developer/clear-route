import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

logger = logging.getLogger("clearroute.database")

Base = declarative_base()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

def resolve_sqlite_url(raw_url: str) -> str:
    if raw_url.startswith("sqlite:///"):
        path = raw_url[len("sqlite:///"):]
        if not os.path.isabs(path):
            abs_path = os.path.normpath(os.path.join(PROJECT_ROOT, path))
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            return f"sqlite:///{abs_path}"
    return raw_url

def get_engine():
    db_url = resolve_sqlite_url(settings.DATABASE_URL)
    canonical_path = os.path.normpath(os.path.join(PROJECT_ROOT,"data","clearroute_analytics.db"))
    if db_url.startswith("sqlite:///") and os.path.normcase(db_url[len("sqlite:///"):]) == os.path.normcase(canonical_path) and not os.path.exists(canonical_path):
        from scripts.build_analytics_database import build_database
        build_database(canonical_path)
    if db_url.startswith("sqlite:///") and os.path.normcase(db_url[len("sqlite:///"):]) == os.path.normcase(canonical_path) and not os.path.exists(os.path.splitext(canonical_path)[0]+".manifest.json"):
        raise RuntimeError("Analytical database has no build manifest; refusing an incomplete or unverified build.")
    is_sqlite = db_url.startswith("sqlite")
    connect_args = {"check_same_thread": False} if is_sqlite else {"connect_timeout": 3}
    
    try:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            connect_args=connect_args
        )
        with engine.connect() as conn:
            db_type = "SQLite" if is_sqlite else "PostgreSQL"
            logger.info(f"Successfully connected to {db_type} database.")
            return engine
    except Exception as e:
        if settings.DB_FALLBACK_SQLITE:
            sqlite_path = settings.SQLITE_DB_PATH
            if not os.path.isabs(sqlite_path):
                sqlite_path = os.path.normpath(os.path.join(PROJECT_ROOT, sqlite_path))
            logger.warning(
                f"Database connection failed ({e}). Falling back to SQLite for local development: {sqlite_path}"
            )
            os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
            if os.path.normcase(sqlite_path) == os.path.normcase(canonical_path) and not os.path.exists(sqlite_path):
                from scripts.build_analytics_database import build_database
                build_database(sqlite_path)
            sqlite_url = f"sqlite:///{sqlite_path}"
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
