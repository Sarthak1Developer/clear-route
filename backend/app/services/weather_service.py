import os
import json
import logging
import urllib.request
import urllib.error
import datetime
from fastapi import HTTPException
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.app.core.config import settings
from backend.app.models.entities import City, Location, WeatherRecord
from backend.app.repositories.data_repository import DataRepository

logger = logging.getLogger("weather_service")

# Approximate geographic centroid coordinates for Indian Metros
CITY_COORDINATES: Dict[str, Tuple[float, float]] = {
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946),
    "Hyderabad": (17.3850, 78.4867),
    "Kolkata": (22.5726, 88.3639),
}

WMO_WEATHER_CODES = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Monsoon Rain",
    71: "Slight Snow",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Slight Hail",
    99: "Thunderstorm with Heavy Hail"
}

class WeatherService:
    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def _fetch_external_live_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Attempts to retrieve live meteorological and forecast conditions from configured external provider.
        Returns None if provider is disabled, unconfigured, unreachable, or returns an error.
        Never generates fake live data.
        """
        if not settings.WEATHER_PROVIDER_ENABLED:
            logger.info("External weather provider is disabled via configuration.")
            return None

        forecast_base = settings.OPEN_METEO_FORECAST_URL or "https://api.open-meteo.com/v1/forecast"
        url = (
            f"{forecast_base}?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code"
            f"&hourly=precipitation,temperature_2m&forecast_days=1&timezone=Asia%2FKolkata"
        )

        if settings.WEATHER_API_KEY:
            url += f"&apikey={settings.WEATHER_API_KEY}"

        timeout = float(getattr(settings, "WEATHER_PROVIDER_TIMEOUT", 2.5))

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "ClearRoute-TrafficAnalytics/1.0",
                "Accept": "application/json"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    return data
                else:
                    logger.warning(f"External weather API returned non-200 status: {response.status}")
                    return None
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, Exception) as exc:
            logger.info(f"External weather provider unreachable ({exc}). Falling back to verified DB records.")
            return None

    def get_current_and_forecast_weather(
        self,
        db: Session,
        city_name: Optional[str] = None,
        location_id: Optional[str] = None,
        date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves weather records with provenance.
        If an external provider is available and no historical date is forced, returns live conditions.
        If provider is unreachable or historical date is requested, serves verified DB records.
        """
        repo = DataRepository(db)
        
        # 1. Resolve target City
        target_city = "Delhi"
        target_location = None

        if location_id:
            loc = repo.get_location_by_code(location_id)
            if not loc:
                raise HTTPException(status_code=404, detail="Unknown corridor")
            if loc:
                target_location = loc
                if loc.city:
                    target_city = loc.city.city_name
        elif city_name:
            city_obj = repo.get_city_by_name(city_name)
            if city_obj:
                target_city = city_obj.city_name
            else:
                target_city = city_name

        coords = CITY_COORDINATES.get(target_city)
        if coords is None:
            raise HTTPException(status_code=404, detail="No coordinates for requested city")
        city_obj = repo.get_city_by_name(target_city)
        if not city_obj:
            raise HTTPException(status_code=404, detail="Unknown city")
        city_id = city_obj.id

        # 2. If historical date is explicitly requested, query DB directly
        if date_str:
            matched_record = (
                db.query(WeatherRecord)
                .filter(WeatherRecord.city_id == city_id, func.date(WeatherRecord.timestamp) == date_str)
                .order_by(desc(WeatherRecord.timestamp))
                .first()
            )
            if matched_record:
                return {
                    "city": target_city,
                    "location_id": location_id,
                    "provenance": "Open-Meteo ERA5 Reanalysis (Database Archive)",
                    "provider_available": False,
                    "provider_status": f"Serving historical archive for {date_str}",
                    "timestamp": matched_record.timestamp.isoformat(),
                    "source": "Open-Meteo ERA5 Reanalysis (Database Archive)",
                    "current_context": {
                        "temperature_c": matched_record.temperature_c,
                        "precipitation_mm": matched_record.precipitation_mm,
                        "humidity_pct": matched_record.humidity_pct,
                        "wind_speed_kmh": matched_record.wind_speed_kmh,
                        "weather_condition": matched_record.weather_condition or ("Rain" if matched_record.precipitation_mm > 0.5 else "Clear / Overcast"),
                        "timestamp": matched_record.timestamp.isoformat(),
                        "is_live": False,
                        "source": "Open-Meteo ERA5 Reanalysis (Database Archive)"
                    },
                    "forecast_scenario": {
                        "available": False,
                        "precipitation_mm": 0.0,
                        "expected_surge_pct": None,
                        "summary": f"Historical record query for {date_str}; forecast not applicable"
                    }
                }

            raise HTTPException(status_code=404, detail="No weather observations for the requested date")

        # 3. Attempt external live weather fetch
        live_data = self._fetch_external_live_weather(coords[0], coords[1])
        if live_data and isinstance(live_data.get("current"), dict) and all(live_data["current"].get(key) is not None for key in ("temperature_2m", "precipitation", "relative_humidity_2m", "wind_speed_10m", "weather_code", "time")):
            current = live_data["current"]
            temp = float(current.get("temperature_2m", 28.0))
            precip = float(current.get("precipitation", 0.0))
            humidity = float(current.get("relative_humidity_2m", 60.0))
            wind = float(current.get("wind_speed_10m", 12.0))
            wcode = int(current.get("weather_code", 0))
            condition = WMO_WEATHER_CODES.get(wcode, "Clear / Overcast")
            time_str = current.get("time", datetime.datetime.utcnow().isoformat())

            # Evaluate next 24h precipitation from hourly array if available
            hourly = live_data.get("hourly", {})
            hourly_precip = hourly.get("precipitation", [])
            max_next_rain = max(hourly_precip[:24]) if hourly_precip else precip
            # A weather forecast alone cannot establish a congestion effect.
            expected_surge = None

            return {
                "city": target_city,
                "location_id": location_id,
                "provenance": "Open-Meteo Live Forecast API",
                "provider_available": True,
                "provider_status": "Active - Live meteorological telemetry stream",
                "timestamp": time_str,
                "source": "Open-Meteo Live Forecast API",
                "current_context": {
                    "temperature_c": temp,
                    "precipitation_mm": precip,
                    "humidity_pct": humidity,
                    "wind_speed_kmh": wind,
                    "weather_condition": condition,
                    "timestamp": time_str,
                    "is_live": True,
                    "source": "Open-Meteo Live Forecast API"
                },
                "forecast_scenario": {
                    "available": True,
                    "precipitation_mm": max_next_rain,
                    "expected_surge_pct": expected_surge,
                    "summary": f"Provider daily peak rainfall: {max_next_rain} mm. Congestion effect not evaluated."
                }
            }

        # 4. Graceful Fallback: Serve latest verified database record
        latest_record = (
            db.query(WeatherRecord)
            .filter(WeatherRecord.city_id == city_id)
            .order_by(desc(WeatherRecord.timestamp))
            .first()
        )

        if latest_record:
            return {
                "city": target_city,
                "location_id": location_id,
                "provenance": "Open-Meteo ERA5 Reanalysis (Database Archive)",
                "provider_available": False,
                "provider_status": "External provider unavailable or offline; serving latest verified historical archive",
                "timestamp": latest_record.timestamp.isoformat(),
                "source": "Open-Meteo ERA5 Reanalysis (Database Archive)",
                "current_context": {
                    "temperature_c": latest_record.temperature_c,
                    "precipitation_mm": latest_record.precipitation_mm,
                    "humidity_pct": latest_record.humidity_pct,
                    "wind_speed_kmh": latest_record.wind_speed_kmh,
                    "weather_condition": latest_record.weather_condition or ("Rain" if latest_record.precipitation_mm > 0.5 else "Clear / Overcast"),
                    "timestamp": latest_record.timestamp.isoformat(),
                    "is_live": False,
                    "source": "Open-Meteo ERA5 Reanalysis (Database Archive)"
                },
                "forecast_scenario": {
                    "available": False,
                    "precipitation_mm": 0.0,
                    "expected_surge_pct": None,
                    "summary": "External live forecast unavailable without active provider connection; relying on verified historical baseline"
                }
            }

        raise HTTPException(status_code=404, detail="No weather observations available; provider is unavailable")

    def get_weather_history(
        self,
        db: Session,
        city: Optional[str] = None,
        location_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Retrieves paginated historical weather observations from the database with filtering.
        """
        repo = DataRepository(db)
        query = db.query(WeatherRecord).join(City)

        city_resolved = city
        if location_id:
            loc = repo.get_location_by_code(location_id)
            if loc and loc.city:
                query = query.filter(City.id == loc.city_id)
                city_resolved = loc.city.city_name
        elif city:
            query = query.filter(func.lower(City.city_name) == city.strip().lower())

        if date:
            query = query.filter(func.date(WeatherRecord.timestamp) == date.strip())
        else:
            if start_date:
                query = query.filter(func.date(WeatherRecord.timestamp) >= start_date.strip())
            if end_date:
                query = query.filter(func.date(WeatherRecord.timestamp) <= end_date.strip())

        total = query.count()
        records = query.order_by(desc(WeatherRecord.timestamp)).offset(offset).limit(limit).all()

        items = []
        for r in records:
            items.append({
                "id": r.id,
                "city_name": r.city.city_name if r.city else "Unknown",
                "timestamp": r.timestamp.isoformat(),
                "temperature_c": r.temperature_c,
                "precipitation_mm": r.precipitation_mm,
                "humidity_pct": r.humidity_pct,
                "wind_speed_kmh": r.wind_speed_kmh,
                "weather_condition": r.weather_condition or ("Rain" if r.precipitation_mm > 0.5 else "Clear / Overcast"),
                "source": "Open-Meteo ERA5 Reanalysis"
            })

        return {
            "city": city_resolved,
            "location_id": location_id,
            "start_date": start_date or date,
            "end_date": end_date or date,
            "total_records": total,
            "limit": limit,
            "offset": offset,
            "source": "Open-Meteo ERA5 Reanalysis (Database Archive)",
            "records": items
        }
