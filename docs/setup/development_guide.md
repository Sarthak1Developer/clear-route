# ClearRoute — Development, Setup & Operations Guide

## 1. Collaborative Hardware Workflow

To accommodate limited local hardware (RAM constraints on the primary development machine), the ClearRoute workflow is intentionally bifurcated:

```
[ Teammate Laptop: High Compute / RAM ]
   ├── Download raw Zenodo / OSM / Open-Meteo archives
   ├── Execute PySpark Big Data ETL (Bronze -> Silver -> Gold)
   ├── Train 4 ML Models (Baseline, Linear, RF, XGBoost)
   ├── Compute SHAP values & feature importance
   └── Push `data/gold/`, `ml/artifacts/`, and `powerbi/exports/` via Git LFS or shared drive
                 │
                 ▼
[ Primary Laptop: Antigravity Workspace ]
   ├── FastAPI Backend (reads SQLite/Postgres & loads model artifacts)
   ├── React 18 / Tailwind / Leaflet Frontend
   ├── Interactive visual prediction & analytics interface
   ├── Power BI Desktop report authoring
   └── System integration & end-to-end testing
```

---

## 2. Primary Laptop Setup (Frontend & Backend)

### Prerequisites:
- Python 3.11+
- Node.js 18+ and npm

### Step A: Backend Setup
```bash
# Navigate to project root
cd "d:\Sarthak Projects\Clear-Route"

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows

# Install backend dependencies
pip install -r backend/requirements.txt

# Verify database and seed sample/gold baseline data
python scripts/seed_database.py

# Start FastAPI Server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be live at: `http://127.0.0.1:8000/docs`

### Step B: Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
Frontend will be live at: `http://localhost:5173/`

---

## 3. Teammate Laptop Setup (Big Data & ML Pipeline)

### Prerequisites:
- Java 11 or 17 (Required for Apache Spark)
- Apache Spark 3.5+
- Python 3.10 or 3.11 with 16GB+ RAM recommended

### Step A: Install Dependencies
```bash
pip install -r bigdata/requirements-spark.txt
pip install -r backend/requirements.txt
```

### Step B: Execute PySpark Pipeline
```bash
# 1. Ingest Raw Datasets to Bronze
python bigdata/ingestion/run_ingestion.py

# 2. Run PySpark Cleaning & Standardization (Silver)
python bigdata/spark_jobs/silver_cleaning.py

# 3. Generate Unified Analytical Gold Dataset
python bigdata/spark_jobs/gold_feature_engineering.py
```

### Step C: Execute Model Training & SHAP Attribution
```bash
# Trains Baseline, Linear Regression, Random Forest, XGBoost
# Generates metrics.json, serialized .joblib artifacts, and SHAP explanations
python ml/training/train_all_models.py
```

### Step D: Export Analytical Tables for Power BI
```bash
python powerbi/exports/generate_bi_exports.py
```

---

## 4. Troubleshooting & Verification

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `psycopg2` fails on local machine | PostgreSQL server not installed or stopped | Set `DB_FALLBACK_SQLITE=True` in `.env` to automatically utilize SQLite for local development |
| Leaflet map tiles do not render | No internet connection or proxy restriction | OpenStreetMap tiles require web connectivity; check proxy/sandbox settings |
| PySpark `JAVA_HOME not set` | Missing Java Runtime | Install OpenJDK 17 and set `JAVA_HOME` in system environment variables |
