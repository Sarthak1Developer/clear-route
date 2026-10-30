import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Boolean,
    DateTime, Date, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    city_code = Column(String(10), unique=True, nullable=False, index=True)
    city_name = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    zoom_level = Column(Integer, default=12)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    locations = relationship("Location", back_populates="city", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="city", cascade="all, delete-orphan")
    weather_records = relationship("WeatherRecord", back_populates="city", cascade="all, delete-orphan")

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True)
    location_code = Column(String(50), unique=True, nullable=False, index=True)
    location_name = Column(String(150), nullable=False)
    corridor_name = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    road_type = Column(String(50), nullable=False) # trunk, primary, secondary, tertiary
    road_lanes = Column(Integer, default=4, nullable=False)
    speed_limit_kmh = Column(Float, default=50.0, nullable=False)
    free_flow_speed_kmh = Column(Float, default=60.0, nullable=False)
    accident_risk_score = Column(Float, default=0.5, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    city = relationship("City", back_populates="locations")
    traffic_records = relationship("TrafficRecord", back_populates="location", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="location", cascade="all, delete-orphan")

class TrafficRecord(Base):
    __tablename__ = "traffic_records"

    id = Column(BigInteger, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    hour = Column(Integer, nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False)
    is_weekend = Column(Boolean, default=False, nullable=False)
    is_peak_hour = Column(Boolean, default=False, nullable=False)
    observed_speed_kmh = Column(Float, nullable=False)
    free_flow_speed_kmh = Column(Float, nullable=False)
    congestion_percentage = Column(Float, nullable=False)
    congestion_category = Column(String(20), nullable=False)

    location = relationship("Location", back_populates="traffic_records")

class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id = Column(BigInteger, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    temperature_c = Column(Float, nullable=False)
    precipitation_mm = Column(Float, nullable=False)
    humidity_pct = Column(Float, nullable=False)
    wind_speed_kmh = Column(Float, nullable=False)
    weather_condition = Column(String(100))

    city = relationship("City", back_populates="weather_records")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True)
    event_name = Column(String(200), nullable=False)
    event_type = Column(String(100), nullable=False) # Festival, Sports, Concert, Public Holiday, Assembly
    event_date = Column(Date, nullable=False, index=True)
    venue = Column(String(200))
    latitude = Column(Float)
    longitude = Column(Float)
    expected_attendance = Column(Integer, default=0)
    is_2026_future = Column(Boolean, default=False, nullable=False, index=True)
    source_attribution = Column(String(200))

    city = relationship("City", back_populates="events")

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    prediction_date = Column(Date, nullable=False, index=True)
    prediction_hour = Column(Integer, nullable=False)
    model_type = Column(String(50), nullable=False)
    temperature_c = Column(Float)
    precipitation_mm = Column(Float)
    event_present = Column(Boolean, default=False)
    event_name = Column(String(200))
    predicted_congestion_pct = Column(Float, nullable=False)
    congestion_category = Column(String(20), nullable=False)
    baseline_congestion_pct = Column(Float)
    shap_attribution_json = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    location = relationship("Location", back_populates="predictions")

class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id = Column(Integer, primary_key=True, index=True)
    model_key = Column(String(50), unique=True, nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    algorithm_family = Column(String(100), nullable=False)
    training_period = Column(String(100), nullable=False)
    total_training_samples = Column(Integer, nullable=False)
    total_test_samples = Column(Integer, nullable=False)
    mae = Column(Float, nullable=False)
    rmse = Column(Float, nullable=False)
    r2_score = Column(Float, nullable=False)
    hyperparameters_json = Column(Text)
    is_primary = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(100), unique=True, nullable=False)
    category = Column(String(100), nullable=False)
    provenance_url = Column(String(300))
    temporal_coverage = Column(String(100))
    spatial_coverage = Column(String(200))
    license = Column(String(100))
    record_count = Column(BigInteger, default=0)
    quality_status = Column(String(50), default="Verified")
    data_quality_notes = Column(Text)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
