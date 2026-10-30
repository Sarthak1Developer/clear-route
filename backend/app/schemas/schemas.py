from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Health
class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    models_loaded: List[str]
    timestamp: str

# Overview
class CityComparisonItem(BaseModel):
    city: str
    avg_congestion_pct: float
    corridor_count: int

class HourlyTrendItem(BaseModel):
    hour: int
    avg_congestion: float
    is_peak: bool

class WeeklyTrendItem(BaseModel):
    day: str
    avg_congestion: float

class MonthlyTrendItem(BaseModel):
    month: str
    avg_congestion: float

class WeatherCorrelationItem(BaseModel):
    band: str
    avg_congestion: float
    sample_count: int

class OverviewResponse(BaseModel):
    total_cities: int
    total_locations: int
    avg_congestion_pct: float
    most_congested_city: str
    total_records_processed: int
    historical_coverage: str
    city_comparison: List[CityComparisonItem]
    hourly_trend: List[HourlyTrendItem]
    weekly_trend: List[WeeklyTrendItem]
    monthly_trend: List[MonthlyTrendItem]
    weather_correlation: List[WeatherCorrelationItem]

# Cities & Locations
class CityItem(BaseModel):
    code: str
    name: str
    state: str
    lat: float
    lng: float
    zoom: int
    corridor_count: int
    avg_congestion_pct: float

class LocationItem(BaseModel):
    id: int
    location_code: str
    location_name: str
    corridor_name: str
    latitude: float
    longitude: float
    road_type: str
    road_lanes: int
    speed_limit_kmh: float
    free_flow_speed_kmh: float
    observed_speed_kmh: Optional[float] = None
    accident_risk_score: float
    avg_congestion_pct: float

class CityLocationsResponse(BaseModel):
    city: str
    locations: List[LocationItem]

class CitySummaryResponse(BaseModel):
    city: str
    state: str
    avg_congestion_pct: float
    congestion_category: str
    peak_hours_str: str
    peak_hour_congestion_pct: float
    rain_impact_delta: float
    hourly_distribution: List[Dict[str, Any]]
    top_congested_corridors: List[LocationItem]

class LocationTrendsResponse(BaseModel):
    location_code: str
    location_name: str
    corridor_name: str
    avg_congestion: float
    peak_hour: int
    peak_hour_congestion: float
    weekend_delta: float
    rain_delta: float
    hourly: List[Dict[str, Any]]
    weekly: List[Dict[str, Any]]
    monthly: List[Dict[str, Any]]

# Prediction
class PredictionRequest(BaseModel):
    city: str
    location_id: str
    prediction_date: str = Field(..., description="Date string YYYY-MM-DD")
    prediction_time: str = Field(..., description="Time string HH:MM")
    model_type: str = Field("xgboost", description="historical_mean, linear_regression, random_forest, or xgboost")
    temperature_c: float = 28.0
    precipitation_mm: float = 0.0
    humidity_pct: float = 65.0
    wind_speed_kmh: float = 12.0
    event_present: bool = False
    event_name: Optional[str] = None

class ShapAttributionItem(BaseModel):
    feature: str
    value: Any
    impact_pct: float

class ConfidenceInterval(BaseModel):
    lower: float
    upper: float

class PredictionResponse(BaseModel):
    prediction_id: str
    city: str
    location_id: str
    prediction_date: str
    prediction_time: str
    predicted_congestion_pct: float
    congestion_category: str
    historical_baseline_pct: float
    difference_pct: float
    selected_model: str
    confidence_interval: Optional[ConfidenceInterval] = None
    shap_attributions: List[ShapAttributionItem]

# Events
class EventItem(BaseModel):
    id: int
    city_name: str
    event_name: str
    event_type: str
    event_date: str
    venue: Optional[str] = None
    is_2026_future: bool
    impact_delta: float

class EventImpactResponse(BaseModel):
    festival_delta: float
    holiday_delta: float
    hourly_comparison: List[Dict[str, Any]]

# Weather
class WeatherImpactResponse(BaseModel):
    heavy_rain_surge: float
    rain_correlation: float
    temp_correlation: float
    rain_bands: List[Dict[str, Any]]
    temp_bands: List[Dict[str, Any]]

# Models & Evaluation
class ModelItem(BaseModel):
    id: int
    key: str
    name: str
    family: str
    role: str
    mae: float
    rmse: float
    r2: float
    is_primary: bool

class ModelPerformanceResponse(BaseModel):
    models: List[ModelItem]
    best_model: ModelItem
    actual_vs_predicted: List[Dict[str, Any]]

class FeatureImportanceItem(BaseModel):
    name: str
    importance: float
    description: str

class FeatureImportanceResponse(BaseModel):
    model: str
    features: List[FeatureImportanceItem]

class ShapSummaryResponse(BaseModel):
    top_drivers: List[Dict[str, Any]]
    summary_text: str

# Data Quality & Sources
class DataSourceItem(BaseModel):
    id: int
    source_name: str
    category: str
    provenance_url: Optional[str] = None
    temporal_coverage: str
    spatial_coverage: str
    record_count: int
    license: str
    quality_status: str

class DataQualityResponse(BaseModel):
    total_gold_records: int
    completeness_rate: float
    duplicate_count: int
    target_definition: str
    validation_status: str

class DataCoverageResponse(BaseModel):
    cities_covered: List[str]
    start_date: str
    end_date: str
    corridors_total: int
