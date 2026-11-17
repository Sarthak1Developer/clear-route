"""Protect the developer database from API tests that persist predictions."""
import os
import sqlite3
import tempfile
from pathlib import Path

if not os.environ.get("DATABASE_URL"):
    source = Path(__file__).parent / "data" / "clearroute_app.db"
    target = Path(tempfile.mkdtemp(prefix="clearroute-tests-")) / "test.db"
    if source.exists():
        with sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True) as src, sqlite3.connect(target) as dst:
            src.backup(dst)
    os.environ["DATABASE_URL"] = f"sqlite:///{target.as_posix()}"
os.environ.setdefault("WEATHER_PROVIDER_ENABLED", "false")
