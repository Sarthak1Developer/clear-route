"""
ClearRoute Big Data Pipeline - Bronze Layer
Ingestion: Open-Meteo Historical ERA5 Weather

Retrieves genuine historical hourly reanalysis weather data from the Open-Meteo
Historical Weather API (ECMWF ERA5) for the five supported metropolitan cities:
Delhi, Mumbai, Bengaluru, Hyderabad, and Kolkata for April 1 – December 31, 2019.

Provenance: Open-Meteo / ECMWF ERA5 Reanalysis (CC BY 4.0 License)
"""

import os
import sys
import json
import time
import logging
import datetime
import urllib.request
import urllib.error
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger("ingest_weather_openmeteo")

METRO_COORDINATES = {
    "Delhi": {"lat": 28.6139, "lon": 77.2090},
    "Mumbai": {"lat": 19.0760, "lon": 72.8777},
    "Bengaluru": {"lat": 12.9716, "lon": 77.5946},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867},
    "Kolkata": {"lat": 22.5726, "lon": 88.3639},
}

DEFAULT_START_DATE = "2019-04-01"
DEFAULT_END_DATE = "2019-12-31"

def fetch_city_weather(city: str, lat: float, lon: float, start_date: str, end_date: str, base_url: str) -> pd.DataFrame:
    """Fetches hourly historical ERA5 weather records from Open-Meteo API."""
    params = (
        f"latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}"
        f"&hourly=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code"
        f"&timezone=Asia%2FKolkata"
    )
    url = f"{base_url}?{params}"
    logger.info(f"Querying Open-Meteo ERA5 API for {city} ({lat}, {lon})...")
    
    req = urllib.request.Request(url, headers={"User-Agent": "ClearRoute-Traffic-ETL/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"Open-Meteo API returned HTTP status {response.status}")
        payload = json.loads(response.read().decode("utf-8"))
    
    hourly = payload.get("hourly", {})
    df_city = pd.DataFrame({
        "city": city,
        "latitude": lat,
        "longitude": lon,
        "timestamp": hourly["time"],
        "temperature_2m_c": hourly["temperature_2m"],
        "precipitation_mm": hourly["precipitation"],
        "relative_humidity_2m_pct": hourly["relative_humidity_2m"],
        "wind_speed_10m_kmh": hourly["wind_speed_10m"],
        "weather_code": hourly["weather_code"],
        "data_provenance": "Open-Meteo Historical Weather API (ECMWF ERA5 Reanalysis)",
        "provenance_type": "genuine_external_api",
        "ingestion_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })
    return df_city

def generate_fallback_weather(city: str, lat: float, lon: float, start_date_str: str, end_date_str: str) -> pd.DataFrame:
    """Deterministic offline fallback used ONLY if external API is completely unreachable."""
    logger.warning(f"Generating offline fallback weather for {city} (API unreachable).")
    start = datetime.datetime.fromisoformat(start_date_str)
    end = datetime.datetime.fromisoformat(end_date_str) + datetime.timedelta(days=1)
    
    records = []
    curr = start
    while curr < end:
        for h in range(24):
            dt = curr.replace(hour=h)
            month = dt.month
            is_monsoon = month in [6, 7, 8, 9]
            base_temp = 34.0 if month in [4, 5, 6] else 28.0 if is_monsoon else 21.0
            temp = base_temp + (2.5 if 12 <= h <= 15 else -3.0 if h <= 5 else 0.0)
            rain = 12.0 if (is_monsoon and h in [14, 18] and curr.day % 3 == 0) else 0.0
            records.append({
                "city": city,
                "latitude": lat,
                "longitude": lon,
                "timestamp": dt.strftime("%Y-%m-%dT%H:00"),
                "temperature_2m_c": round(temp, 1),
                "precipitation_mm": round(rain, 1),
                "relative_humidity_2m_pct": 80.0 if is_monsoon else 55.0,
                "wind_speed_10m_kmh": 16.0 if is_monsoon else 10.0,
                "weather_code": 63 if rain > 10 else 51 if rain > 0 else 0,
                "data_provenance": "Offline Climatic Simulation (Fallback)",
                "provenance_type": "simulated_fallback",
                "ingestion_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            })
        curr += datetime.timedelta(days=1)
    return pd.DataFrame(records)

def ingest_weather_era5(
    output_dir: str = "data/bronze/weather_era5",
    start_date: str = DEFAULT_START_DATE,
    end_date: str = DEFAULT_END_DATE,
    force_refresh: bool = False
) -> str:
    """Ingests hourly weather records into the Bronze layer."""
    os.makedirs(output_dir, exist_ok=True)
    bronze_csv = os.path.join(output_dir, "raw_weather_era5_hourly.csv")
    meta_json = os.path.join(output_dir, "provenance_metadata.json")

    # If cached file exists and not forced, verify and return
    if os.path.exists(bronze_csv) and not force_refresh:
        logger.info(f"Using existing cached Bronze weather records from {bronze_csv}")
        return bronze_csv

    base_url = os.environ.get("OPENMETEO_API_URL") or os.environ.get("WEATHER_API_URL") or "https://archive-api.open-meteo.com/v1/archive"
    
    city_frames = []
    is_genuine = True

    for city, coords in METRO_COORDINATES.items():
        try:
            df_c = fetch_city_weather(city, coords["lat"], coords["lon"], start_date, end_date, base_url)
            city_frames.append(df_c)
            time.sleep(0.5)  # Respect API rate limits
        except Exception as e:
            logger.warning(f"Failed to fetch live ERA5 weather for {city}: {e}. Activating fallback.")
            is_genuine = False
            df_fallback = generate_fallback_weather(city, coords["lat"], coords["lon"], start_date, end_date)
            city_frames.append(df_fallback)

    df_weather = pd.concat(city_frames, ignore_index=False).reset_index(drop=True)
    df_weather.to_csv(bronze_csv, index=False)

    provenance = {
        "dataset_name": "Hourly Meteorological Observations (ERA5)",
        "source_name": "Open-Meteo Historical Weather API (ECMWF ERA5 Reanalysis)" if is_genuine else "Offline Climatic Simulation Fallback",
        "provenance_type": "genuine_external_api" if is_genuine else "simulated_fallback",
        "api_endpoint": base_url,
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "temporal_coverage": f"{start_date} to {end_date}",
        "spatial_coverage": list(METRO_COORDINATES.keys()),
        "total_records": len(df_weather),
        "collection_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "attributes": ["temperature_2m_c", "precipitation_mm", "relative_humidity_2m_pct", "wind_speed_10m_kmh", "weather_code"]
    }

    with open(meta_json, "w") as f:
        json.dump(provenance, f, indent=2)

    logger.info(f"Bronze ERA5 weather saved to {bronze_csv} ({len(df_weather)} records, Genuine: {is_genuine}).")
    return bronze_csv

if __name__ == "__main__":
    ingest_weather_era5()
