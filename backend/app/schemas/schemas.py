from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator

# Health
class HealthResponse(BaseModel):
    records_count: Optional[int] = None
    environment: str = "Evaluation"
    status: str
    version: str
    database: str
    models_loaded: List[str]
    timestamp: str

# Overview
class CityComparisonItem(BaseModel):
    city: str
    avg_congestion_pct: Optional[float] = None
    corridor_count: int

class HourlyTrendItem(BaseModel):
    hour: int
    avg_congestion: Optional[float] = None
    is_peak: bool

class WeeklyTrendItem(BaseModel):
    day: str
    avg_congestion: Optional[float] = None

class MonthlyTrendItem(BaseModel):
    month: str
    avg_congestion: Optional[float] = None

class WeatherCorrelationItem(BaseModel):
    band: str
    avg_congestion: Optional[float] = None
    sample_count: int

class OverviewResponse(BaseModel):
    network_avg_congestion_pct: Optional[float] = None
    scope_city: Optional[str] = None
    total_cities: int
    total_locations: int
    avg_congestion_pct: Optional[float] = None
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
    avg_congestion_pct: Optional[float] = None

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
    avg_congestion_pct: Optional[float] = None

class CityLocationsResponse(BaseModel):
    city: str
    locations: List[LocationItem]

class CitySummaryResponse(BaseModel):
    city: str
    state: str
    avg_congestion_pct: Optional[float] = None
    congestion_category: str
    peak_hours_str: str
    peak_hour_congestion_pct: Optional[float] = None
    rain_impact_delta: Optional[float] = None
    hourly_distribution: List[Dict[str, Any]]
    top_congested_corridors: List[LocationItem]

class LocationTrendsResponse(BaseModel):
    city: str = ""
    sample_count: int = 0
    status: str = "available"
    filters: Dict[str, Any] = {}
    location_code: str
    location_name: str
    corridor_name: str
    avg_congestion: Optional[float] = None
    peak_hour: Optional[int] = None
    peak_hour_congestion: Optional[float] = None
    weekend_delta: Optional[float] = None
    rain_delta: Optional[float] = None
    hourly: List[Dict[str, Any]]
    weekly: List[Dict[str, Any]]
    monthly: List[Dict[str, Any]]

# Prediction
class PredictionRequest(BaseModel):
    city: str
    location_id: str
    prediction_date: Optional[str] = Field(None, description="Date string YYYY-MM-DD")
    prediction_time: Optional[str] = Field(None, description="Time string HH:MM")
    hour: Optional[int] = Field(None, ge=0, le=23, description="Hour of day (0-23)")
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    month: Optional[int] = Field(None, ge=1, le=12, description="Month of year (1-12)")
    model_type: Optional[str] = Field("xgboost", description="historical_mean, linear_regression, random_forest, or xgboost")
    temperature_c: Optional[float] = Field(28.0, description="Temperature in Celsius")
    temperature_2m_c: Optional[float] = Field(None, description="Temperature in Celsius (ML Contract alias)")
    precipitation_mm: Optional[float] = Field(0.0, ge=0.0, description="Precipitation in mm (>= 0.0)")
    humidity_pct: Optional[float] = Field(65.0, ge=0.0, le=100.0, description="Relative humidity %")
    relative_humidity_2m_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="Relative humidity % (ML Contract alias)")
    wind_speed_kmh: Optional[float] = Field(12.0, ge=0.0, description="Wind speed in km/h")
    wind_speed_10m_kmh: Optional[float] = Field(None, ge=0.0, description="Wind speed in km/h (ML Contract alias)")
    road_lanes: Optional[int] = Field(None, ge=1, description="Number of carriageway lanes (>= 1)")
    road_type: Optional[str] = Field(None, description="Road class: primary, secondary, trunk")
    length_m: Optional[float] = Field(None, ge=0.0, description="Corridor length in meters")
    free_flow_speed_kmh: Optional[float] = Field(None, ge=0.0, description="Free flow speed in km/h")
    accident_risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Accident hazard score [0, 1]")
    event_present: Optional[Union[bool, int]] = Field(False, description="Event present flag (bool or 0/1)")
    event_name: Optional[str] = None
    event_type: Optional[str] = Field(None, description="None, Festival, Public Holiday, Sports, Assembly")
    event_intensity: Optional[float] = Field(None, ge=0.0, le=1.0, description="Severity weight of event [0, 1]")
    lag_speed_1h: Optional[float] = Field(None, ge=0.0, description="Observed speed at t-1 in km/h")
    rolling_speed_3h: Optional[float] = Field(None, ge=0.0, description="Mean speed over prior 3 hours in km/h")

    @field_validator("city")
    @classmethod
    def validate_city(cls, v: str) -> str:
        valid_cities = {"Delhi", "Mumbai", "Bengaluru", "Hyderabad", "Kolkata"}
        if v not in valid_cities:
            raise ValueError(f"City '{v}' is invalid. Allowed metropolitan areas: {sorted(valid_cities)}")
        return v

    @field_validator("road_type")
    @classmethod
    def validate_road_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_types = {"primary", "secondary", "trunk"}
            if v.lower() not in valid_types:
                raise ValueError(f"Road type '{v}' is invalid. Allowed types: {sorted(valid_types)}")
            return v.lower()
        return v

class ShapAttributionItem(BaseModel):
    feature: str
    value: Any
    impact_pct: float

class ConfidenceInterval(BaseModel):
    lower: float
    upper: float

class LocationInfo(BaseModel):
    location_id: str
    city: str
    location_name: Optional[str] = None
    corridor_name: Optional[str] = None
    road_type: Optional[str] = None
    road_lanes: Optional[int] = None
    length_m: Optional[float] = None
    free_flow_speed_kmh: Optional[float] = None
    accident_risk_score: Optional[float] = None

class AdditiveCheck(BaseModel):
    base_value: float
    sum_attributions: float
    reconstructed_prediction: float
    is_consistent: bool

class FeatureContributionItem(BaseModel):
    feature: str
    display_name: str
    category: str
    feature_value: Any
    attribution_value: float
    direction: str
    percentage_contribution: float

class PredictionResponse(BaseModel):
    prediction_id: str
    status: str = "success"
    timestamp: str
    city: str
    location_id: str
    location_name: Optional[str] = None
    corridor_name: Optional[str] = None
    location_info: Optional[LocationInfo] = None
    prediction_date: str
    prediction_time: str
    predicted_congestion_pct: float
    congestion_category: str
    model_name: str
    model_version: str = "1.0.0"
    selected_model: str
    historical_baseline_pct: Optional[float] = None
    difference_pct: Optional[float] = None
    confidence_interval: Optional[ConfidenceInterval] = None
    input_features: Optional[Dict[str, Any]] = None
    base_value: Optional[float] = None
    additive_check: Optional[AdditiveCheck] = None
    category_impacts: Optional[Dict[str, float]] = None
    feature_contributions: Optional[List[FeatureContributionItem]] = None
    explanation_summary: Optional[str] = None
    limitations_and_caveats: Optional[List[str]] = None
    shap_attributions: List[ShapAttributionItem] = Field(default_factory=list)

class PredictionExplanationResponse(BaseModel):
    prediction_id: str
    model_id: str
    model_name: str
    model_version: str = "1.0.0"
    predicted_congestion: float
    congestion_category: Optional[str] = None
    base_value: Optional[float] = None
    additive_check: Optional[AdditiveCheck] = None
    category_impacts: Dict[str, float]
    feature_contributions: List[FeatureContributionItem]
    feature_values: Optional[Dict[str, Any]] = None
    explanation_summary: str
    limitations_and_caveats: List[str]

# Events
class EventItem(BaseModel):
    id: int
    city_name: str
    event_name: str
    event_type: str
    event_date: str
    venue: Optional[str] = None
    expected_attendance: Optional[int] = 0
    is_2026_future: bool
    source: Optional[str] = Field(None, description="Official publication, gazette, or municipal advisory source")
    source_verified: bool = Field(False, description="True only if source is confirmed and non-empty")
    impact_delta: Optional[float] = Field(None, description="Actual observed percentage point difference from baseline or null if unobserved/future")

class EventsListResponse(BaseModel):
    city: str
    total_events: int = 0
    events: List[EventItem]
    source_attribution: Optional[str] = "Official Gazettes, Municipal Advisories, and Event Organizers"

class EventImpactResponse(BaseModel):
    city: Optional[str] = None
    festival_delta: Optional[float] = Field(None, description="Average percentage point surge on observed festival dates vs baseline")
    holiday_delta: Optional[float] = Field(None, description="Average percentage point delta on observed public holiday dates vs baseline")
    hourly_comparison: List[Dict[str, Any]] = Field(default_factory=list, description="Hourly baseline vs event congestion profiles")
    data_backed: bool = Field(True, description="Indicates whether metrics are computed from ground-truth database records")
    source: Optional[str] = Field("State Gazettes & Historical Traffic Database", description="Source provenance")

# Weather
class WeatherRecordItem(BaseModel):
    id: int
    city_name: str
    timestamp: str
    temperature_c: float
    precipitation_mm: float
    humidity_pct: float
    wind_speed_kmh: float
    weather_condition: Optional[str] = None
    source: str = "Open-Meteo ERA5 Reanalysis"

class WeatherHistoryResponse(BaseModel):
    city: Optional[str] = None
    location_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_records: int
    limit: int
    offset: int
    source: str = "Open-Meteo ERA5 Reanalysis (Database Archive)"
    records: List[WeatherRecordItem]

class WeatherContext(BaseModel):
    temperature_c: float
    precipitation_mm: float
    humidity_pct: float
    wind_speed_kmh: float
    weather_condition: Optional[str] = None
    timestamp: Optional[str] = None
    is_live: bool = False
    source: Optional[str] = "Open-Meteo ERA5 Reanalysis (Database Archive)"

class WeatherResponse(BaseModel):
    city: str
    location_id: Optional[str] = None
    provenance: str
    provider_available: bool = False
    provider_status: str = "Historical Database Archive"
    timestamp: Optional[str] = None
    current_context: WeatherContext
    forecast_scenario: Optional[Dict[str, Any]] = None
    source: str = "Open-Meteo ERA5 Reanalysis (Database Archive)"

class WeatherImpactResponse(BaseModel):
    weather_provenance: Optional[Dict[str, Any]] = None
    rain_summary: Optional[Dict[str, Any]] = None
    heavy_rain_reason: Optional[str] = None
    status: str = "unavailable"
    reason: Optional[str] = None
    sample_count: int = 0
    humidity_summary: Optional[Dict[str, Any]] = None
    wind_summary: Optional[Dict[str, Any]] = None
    city_comparison: List[Dict[str, Any]] = Field(default_factory=list)
    hourly: List[Dict[str, Any]] = Field(default_factory=list)
    city: Optional[str] = None
    location_id: Optional[str] = None
    heavy_rain_surge: Optional[float] = None
    rain_correlation: Optional[float] = None
    temp_correlation: Optional[float] = None
    rain_bands: List[Dict[str, Any]]
    temp_bands: List[Dict[str, Any]]
    source: Optional[str] = "Joined Traffic & Open-Meteo ERA5 Observations"

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
    evaluation_sample_count: Optional[int] = None
    evaluation_period: Optional[str] = None
    evaluation_context: str = "Generated demonstration traffic; metrics are not validated real-world forecast accuracy."
    models: List[ModelItem]
    best_model: ModelItem
    actual_vs_predicted: List[Dict[str, Any]]

class FeatureImportanceItem(BaseModel):
    name: str
    feature: Optional[str] = None
    display_name: Optional[str] = None
    importance: float
    mean_abs_shap_pct: Optional[float] = None
    category: Optional[str] = None
    rank: Optional[int] = None
    description: str

class FeatureImportanceResponse(BaseModel):
    model: str
    model_version: str = "1.0.0"
    base_value: Optional[float] = None
    features: List[FeatureImportanceItem]
    total_features_evaluated: Optional[int] = None

class TopDriverItem(BaseModel):
    driver: str
    feature: Optional[str] = None
    mean_shap_pct: float
    direction: str
    category: Optional[str] = None
    rank: Optional[int] = None

class ShapSummaryResponse(BaseModel):
    model: str = "XGBoost Regressor (TreeExplainer)"
    model_version: str = "1.0.0"
    base_value: float = 24.05
    top_drivers: List[TopDriverItem]
    category_drivers: Optional[Dict[str, str]] = None
    summary_text: str
    limitations_and_caveats: Optional[List[str]] = None

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

class TrafficRecordExplorerItem(BaseModel):
    id: int
    city: str
    location_code: str
    location_name: str
    corridor_name: str
    road_type: str
    timestamp: str
    hour: int
    day_of_week: int
    observed_speed_kmh: float
    free_flow_speed_kmh: float
    congestion_percentage: float
    congestion_category: str
    is_peak: bool

class PaginatedTrafficRecordsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    records: List[TrafficRecordExplorerItem]

