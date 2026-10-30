# ClearRoute: Smart Transportation & Predictive Traffic Analytics Platform

> **An Enterprise-Grade Big Data Analytics & Machine Learning Platform for Indian Metropolitan Cities**  
> *Developed for Academic & Production Transportation Intelligence*

---

## 📌 Executive Summary

**ClearRoute** is an intelligent traffic analytics and congestion prediction platform engineered specifically for Indian metropolitan cities: **Delhi, Mumbai, Bengaluru, Hyderabad, and Kolkata**.

The platform ingests, harmonizes, and analyzes historical urban traffic patterns along with meteorological conditions, public assemblies, festival calendars, and physical road infrastructure to answer complex urban planning questions:
- *What is the expected congestion index at Laxmi Nagar, Delhi tomorrow at 18:00 IST under monsoon rainfall?*
- *During which hours does Central Silk Board Junction in Bengaluru experience critical bottlenecking?*
- *How much does a 20mm/hr precipitation event amplify travel delay across Mumbai's Western Express Highway?*
- *What specific factors (weather, hour, road width, event) drive a model's prediction?*

### ⚠️ What ClearRoute Is NOT
ClearRoute is strictly an **analytical intelligence and predictive forecasting platform**. It is **NOT** a turn-by-turn GPS navigation system, shortest-path router, or live vehicle tracking dashboard.

---

## 🏛️ System Architecture

ClearRoute follows a layered **Medallion Data Architecture (Bronze → Silver → Gold)** powered by **Apache PySpark**, connected to a **FastAPI** high-throughput backend, a **React 18** modern dark analytics dashboard, and **Microsoft Power BI** analytical reports.

```
DATA SOURCES (Uber Movement 2019, OpenStreetMap, Open-Meteo ERA5, MoRTH India)
    │
    ▼
BRONZE LAYER (Raw, Immutable Extracts)
    │
    ▼
PYSPARK PROCESSING (Cleaning, Deduplication, Geo-validation, IST Time Alignment)
    │
    ▼
SILVER LAYER (Harmonized Geospatial & Traffic Tables)
    │
    ▼
FEATURE STORE (Temporal Lags, Weather Aggregations, Event Flags, Risk Scores)
    │
    ▼
GOLD ANALYTICAL DATASET (Parquet Partitions & PostgreSQL Analytical Tables)
    │
    ├───────────────────────────────────────────────┐
    ▼                                               ▼
ML MODEL PIPELINE                               FASTAPI REST SERVICE
├── Chronological Split (70/15/15)              ├── Connection Pool (PostgreSQL / SQLite)
├── 1. Historical Mean Baseline                 ├── Sub-20ms Serialized Inference
├── 2. Linear Regression (Ridge)                ├── Dynamic SHAP Explainability Engine
├── 3. Random Forest Regressor                  └── OpenAPI / Swagger Specifications
└── 4. XGBoost Regressor (Primary)                  │
    └── SHAP TreeExplainer Attributions             ▼
                                                REACT 18 ANALYTICS FRONTEND
                                                ├── Tailwind CSS Dark Theme
                                                ├── Interactive Leaflet OSM Maps
                                                ├── Recharts Temporal & Correlation Graphs
                                                └── Scenario-Based Prediction Interface
                                                    │
                                                    ▼
                                                MICROSOFT POWER BI REPORTING
                                                └── Gold-Layer Business Intelligence Models
```

---

## 🗺️ Geographical Scope & Supported Corridors

ClearRoute features real-world road segments and corridors across 5 major Indian metropolitan areas:

| Metropolitan City | Benchmark Locations Represented | Road Network Types |
| :--- | :--- | :--- |
| **Delhi** | Laxmi Nagar (Vikas Marg), Connaught Place, Karol Bagh, Hauz Khas, Nehru Place | Arterial, Radial Central Ring, Commercial Trunk |
| **Mumbai** | Andheri (SV Rd / WEH), Bandra Kurla Complex (BKC), Dadar TT Circle, Powai, Borivali | Expressways, High-Density Commercial, Suburban Arterials |
| **Bengaluru** | Whitefield, Koramangala, Indiranagar 100ft Rd, Electronic City, Central Silk Board | IT Corridors, Major Highway Junctions, Commercial Rings |
| **Hyderabad** | HITEC City, Gachibowli, Banjara Hills Road No. 1, Begumpet, Secunderabad | Cyberabad Expressways, Transit Hubs, Outer Corridors |
| **Kolkata** | Salt Lake Sector V, Park Street, Howrah Station Approach, New Town, Esplanade | Historic Transit Arterials, IT Hubs, Bridge Corridors |

---

## 🔬 Strict Data & Temporal Partitioning Strategy

- **Historical Training Pipeline (2019)**: April 1, 2019 – December 31, 2019. Derived from Uber Movement Zenodo archives, Open-Meteo ERA5 historical reanalysis, Geofabrik OSM road geometries, and 2019 Indian holiday records.
- **Contextual Future Pipeline (2026)**: Completely isolated from model training. Ingests 2026 event schedules, holiday gazettes, and weather forecast feeds for forward-looking prediction scenarios without causing data leakage.
- **Anti-Fabrication Guarantee**: No synthetic or random placeholder measurements are passed off as real data. If a specific hour or corridor lacks sensor coverage, the system clearly presents an empty state with data coverage boundaries.

---

## 🤖 Machine Learning Framework & Evaluation

Four distinct modeling paradigms are implemented:
1. **Model 1: Historical Mean Baseline** — Spatio-temporal segment-hour lookup benchmark.
2. **Model 2: Linear Regression** — Regularized parametric baseline delivering interpretable sensitivity coefficients.
3. **Model 3: Random Forest Regressor** — Multi-tree non-linear ensemble.
4. **Model 4: XGBoost Regressor** — Gradient boosted decision tree framework (Primary Model).

### Evaluation & Explainability
- **Split Strategy**: Strictly chronological (70% Train, 15% Validation, 15% Test) to eliminate temporal data leakage.
- **Metrics**: Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and $R^2$.
- **Explainability**: Integrated **SHAP TreeExplainer** providing global feature importance rankings and local per-prediction attribution waterfall charts.

---

## 💻 Tech Stack

- **Frontend**: React 18, Vite, Tailwind CSS, Lucide React, Recharts, Leaflet, React-Leaflet.
- **Backend API**: Python 3.11, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy.
- **Database & Storage**: PostgreSQL 15, SQLite (zero-config dev fallback), Apache Parquet.
- **Big Data Engine**: Apache Spark 3.5 / PySpark, PyArrow.
- **Machine Learning**: Scikit-learn, XGBoost, SHAP, NumPy, Pandas.
- **Business Intelligence**: Microsoft Power BI Desktop.

---

## 🚀 Quickstart Guide

### 1. Backend Setup
```bash
# Clone and enter directory
git clone https://github.com/your-org/clearroute.git
cd clearroute

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # On Windows

# Install requirements
pip install -r backend/requirements.txt

# Seed local database & compute baseline artifacts
python scripts/seed_database.py

# Start FastAPI server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 📊 Power BI Integration

The repository includes a dedicated `powerbi/` directory containing:
- Ready-to-import Gold-layer CSV/Parquet summaries.
- Data dictionary and star-schema relationships.
- Step-by-step setup documentation for Power BI Desktop.

---

## 📜 License & Academic Integrity

Developed for academic research and advanced transportation analytics. Raw data sources retain their respective licenses (Uber Movement Open Data, OpenStreetMap ODbL, Open-Meteo CC BY 4.0, MoRTH Open Government Data).
