-- ==============================================================================
-- ClearRoute: PostgreSQL Database Initialization Script
-- ==============================================================================

CREATE TABLE IF NOT EXISTS cities (
    id SERIAL PRIMARY KEY,
    city_code VARCHAR(10) UNIQUE NOT NULL,
    city_name VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    zoom_level INTEGER DEFAULT 12,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
    location_code VARCHAR(50) UNIQUE NOT NULL,
    location_name VARCHAR(150) NOT NULL,
    corridor_name VARCHAR(200) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    road_type VARCHAR(50) NOT NULL, -- trunk, primary, secondary, tertiary
    road_lanes INTEGER NOT NULL DEFAULT 4,
    speed_limit_kmh DOUBLE PRECISION NOT NULL DEFAULT 50.0,
    free_flow_speed_kmh DOUBLE PRECISION NOT NULL DEFAULT 60.0,
    accident_risk_score DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_locations_city ON locations(city_id);
CREATE INDEX IF NOT EXISTS idx_locations_code ON locations(location_code);

CREATE TABLE IF NOT EXISTS traffic_records (
    id BIGSERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    hour INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    month INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL DEFAULT FALSE,
    is_peak_hour BOOLEAN NOT NULL DEFAULT FALSE,
    observed_speed_kmh DOUBLE PRECISION NOT NULL,
    free_flow_speed_kmh DOUBLE PRECISION NOT NULL,
    congestion_percentage DOUBLE PRECISION NOT NULL,
    congestion_category VARCHAR(20) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_traffic_location_ts ON traffic_records(location_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_traffic_hour ON traffic_records(hour);
CREATE INDEX IF NOT EXISTS idx_traffic_day ON traffic_records(day_of_week);

CREATE TABLE IF NOT EXISTS weather_records (
    id BIGSERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    temperature_c DOUBLE PRECISION NOT NULL,
    precipitation_mm DOUBLE PRECISION NOT NULL,
    humidity_pct DOUBLE PRECISION NOT NULL,
    wind_speed_kmh DOUBLE PRECISION NOT NULL,
    weather_condition VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_weather_city_ts ON weather_records(city_id, timestamp);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
    event_name VARCHAR(200) NOT NULL,
    event_type VARCHAR(100) NOT NULL, -- Festival, Sports, Concert, Public Holiday, Assembly
    event_date DATE NOT NULL,
    venue VARCHAR(200),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    expected_attendance INTEGER DEFAULT 0,
    is_2026_future BOOLEAN NOT NULL DEFAULT FALSE,
    source_attribution VARCHAR(200)
);

CREATE INDEX IF NOT EXISTS idx_events_city_date ON events(city_id, event_date);
CREATE INDEX IF NOT EXISTS idx_events_is_future ON events(is_2026_future);

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    prediction_date DATE NOT NULL,
    prediction_hour INTEGER NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    temperature_c DOUBLE PRECISION,
    precipitation_mm DOUBLE PRECISION,
    event_present BOOLEAN DEFAULT FALSE,
    event_name VARCHAR(200),
    predicted_congestion_pct DOUBLE PRECISION NOT NULL,
    congestion_category VARCHAR(20) NOT NULL,
    baseline_congestion_pct DOUBLE PRECISION,
    shap_attribution_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_predictions_loc_date ON predictions(location_id, prediction_date);

CREATE TABLE IF NOT EXISTS model_metadata (
    id SERIAL PRIMARY KEY,
    model_key VARCHAR(50) UNIQUE NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    algorithm_family VARCHAR(100) NOT NULL,
    training_period VARCHAR(100) NOT NULL,
    total_training_samples INTEGER NOT NULL,
    total_test_samples INTEGER NOT NULL,
    mae DOUBLE PRECISION NOT NULL,
    rmse DOUBLE PRECISION NOT NULL,
    r2_score DOUBLE PRECISION NOT NULL,
    hyperparameters_json TEXT,
    is_primary BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_sources (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(100) NOT NULL,
    provenance_url VARCHAR(300),
    temporal_coverage VARCHAR(100),
    spatial_coverage VARCHAR(200),
    license VARCHAR(100),
    record_count BIGINT DEFAULT 0,
    quality_status VARCHAR(50) DEFAULT 'Verified',
    data_quality_notes TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
