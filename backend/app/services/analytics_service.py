import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from backend.app.repositories.data_repository import DataRepository
from backend.app.models.entities import City, Location, TrafficRecord, WeatherRecord, Event

class AnalyticsService:
    def __init__(self, db: Session):
        self.repo = DataRepository(db)
        self.db = db

    def get_overview(self) -> Dict[str, Any]:
        """Calculates multi-city traffic analytical overview directly from database records."""
        cities = self.repo.get_all_cities()
        total_cities = len(cities)

        # City-wise comparison using actual traffic averages
        city_comparison = []
        city_stats = self.db.query(
            City.id,
            City.city_name,
            func.avg(TrafficRecord.congestion_percentage).label("avg_congestion"),
            func.count(func.distinct(TrafficRecord.location_id)).label("corridor_count")
        ).join(Location, Location.city_id == City.id)\
         .join(TrafficRecord, TrafficRecord.location_id == Location.id)\
         .group_by(City.id, City.city_name)\
         .all()

        stats_map = {row.id: (round(float(row.avg_congestion), 1), int(row.corridor_count)) for row in city_stats if row.avg_congestion is not None}

        total_corridors = 0
        sum_c = 0.0
        congested_city = "Bengaluru"
        max_c = -1.0

        for c in cities:
            if c.id in stats_map:
                avg_val, c_count = stats_map[c.id]
            else:
                locs = self.repo.get_locations_by_city_id(c.id)
                c_count = len(locs)
                avg_val = 0.0
            
            total_corridors += c_count
            sum_c += avg_val
            if avg_val > max_c:
                max_c = avg_val
                congested_city = c.city_name

            city_comparison.append({
                "city": c.city_name,
                "avg_congestion_pct": avg_val,
                "corridor_count": c_count,
            })

        # Overall network stats
        total_traffic = self.db.query(func.count(TrafficRecord.id)).scalar() or 0
        overall_avg = self.db.query(func.avg(TrafficRecord.congestion_percentage)).scalar()
        avg_congestion_pct = round(float(overall_avg), 1) if overall_avg is not None else 0.0

        min_ts = self.db.query(func.min(TrafficRecord.timestamp)).scalar()
        max_ts = self.db.query(func.max(TrafficRecord.timestamp)).scalar()
        if min_ts and max_ts:
            coverage_str = f"{min_ts.strftime('%B %d, %Y')} – {max_ts.strftime('%B %d, %Y')}"
        else:
            coverage_str = "April 1, 2019 – December 31, 2019"

        # Diurnal 24-hr distribution from database
        hourly_trend = self.repo.get_hourly_trend_data()

        # Day of week from database
        weekly_trend = self.repo.get_weekly_trend_data()

        # Monthly from database
        monthly_trend = self.repo.get_monthly_trend_data()

        # Weather correlation from database
        weather_metrics = self.repo.get_weather_impact_data()
        weather_correlation = [
            {
                "band": b["band"],
                "avg_congestion": b["avg_congestion"],
                "sample_count": b["sample_count"],
            }
            for b in weather_metrics["rain_bands"]
        ]

        return {
            "total_cities": total_cities,
            "total_locations": total_corridors,
            "avg_congestion_pct": avg_congestion_pct,
            "most_congested_city": congested_city,
            "total_records_processed": total_traffic,
            "historical_coverage": coverage_str,
            "city_comparison": city_comparison,
            "hourly_trend": hourly_trend,
            "weekly_trend": weekly_trend,
            "monthly_trend": monthly_trend,
            "weather_correlation": weather_correlation,
        }

    def get_city_summary(self, city_name: str) -> Dict[str, Any]:
        """Calculates genuine city profile and corridor rankings from database records."""
        city = self.repo.get_city_by_name(city_name)
        if not city:
            raise ValueError(f"City '{city_name}' is not in the supported metropolitan scope.")

        # City average congestion from real records
        avg_c_val = self.db.query(func.avg(TrafficRecord.congestion_percentage))\
            .join(Location, Location.id == TrafficRecord.location_id)\
            .filter(Location.city_id == city.id)\
            .scalar()
        avg_congestion = round(float(avg_c_val), 1) if avg_c_val is not None else 0.0

        # Peak hours analysis from actual hourly averages
        hourly_rows = self.db.query(
            TrafficRecord.hour,
            func.avg(TrafficRecord.congestion_percentage).label("avg_c")
        ).join(Location, Location.id == TrafficRecord.location_id)\
         .filter(Location.city_id == city.id)\
         .group_by(TrafficRecord.hour)\
         .order_by(desc("avg_c"))\
         .all()

        if hourly_rows:
            peak_row = hourly_rows[0]
            peak_h = peak_row[0]
            peak_c = round(float(peak_row[1]), 1)
            peak_hours_str = f"{peak_h:02d}:00 – {(peak_h + 2) % 24:02d}:00 IST"
        else:
            peak_hours_str = "18:00 – 20:00 IST"
            peak_c = avg_congestion

        # Rain impact in this city
        city_weather = self.repo.get_weather_impact_data(city_id=city.id)
        rain_delta = city_weather.get("heavy_rain_surge", 0.0)

        # 24-hr Weekday vs Weekend distribution
        hourly_dist = self.repo.get_hourly_weekday_weekend_distribution(city_id=city.id)

        # Top congested corridors ranked by actual database average
        corridors = self.repo.get_city_corridors_with_stats(city.id)
        corridors.sort(key=lambda x: x["avg_congestion_pct"], reverse=True)

        # Category
        if avg_congestion <= 25.0:
            category = "Low"
        elif avg_congestion <= 50.0:
            category = "Moderate"
        elif avg_congestion <= 75.0:
            category = "High"
        else:
            category = "Severe"

        return {
            "city": city.city_name,
            "state": city.state,
            "avg_congestion_pct": avg_congestion,
            "congestion_category": category,
            "peak_hours_str": peak_hours_str,
            "peak_hour_congestion_pct": peak_c,
            "rain_impact_delta": rain_delta,
            "hourly_distribution": hourly_dist,
            "top_congested_corridors": corridors,
        }

    def get_location_trends(self, loc_code: str) -> Dict[str, Any]:
        """Computes diurnal, weekly and monthly trends for a specific road corridor."""
        loc = self.repo.get_location_by_code_or_id(loc_code)
        if not loc:
            raise ValueError(f"Corridor '{loc_code}' not found.")

        stats = self.repo.get_corridor_stats(loc.id)
        corridor_avg = stats["avg_congestion_pct"]

        # Hourly trend for this corridor
        hourly_rows = self.db.query(
            TrafficRecord.hour,
            func.avg(TrafficRecord.congestion_percentage).label("avg_c"),
            func.avg(TrafficRecord.observed_speed_kmh).label("avg_s")
        ).filter(TrafficRecord.location_id == loc.id)\
         .group_by(TrafficRecord.hour)\
         .order_by(TrafficRecord.hour)\
         .all()

        h_c_map = {r[0]: round(float(r[1]), 1) for r in hourly_rows if r[1] is not None}
        h_s_map = {r[0]: round(float(r[2]), 1) for r in hourly_rows if r[2] is not None}

        hourly = []
        for h in range(24):
            c_val = h_c_map.get(h, None)
            s_val = h_s_map.get(h, None)
            hourly.append({
                "hour": h,
                "congestion_pct": c_val,
                "speed_kmh": s_val,
            })

        # Peak hour identification
        observed_hours = [r for r in hourly if r["congestion_pct"] is not None]
        if observed_hours:
            peak_item = max(observed_hours, key=lambda x: x["congestion_pct"])
            peak_hour = peak_item["hour"]
            peak_congestion = peak_item["congestion_pct"]
        else:
            peak_hour = None
            peak_congestion = None

        # Weekday vs weekend delta from DB
        wd_avg = self.db.query(func.avg(TrafficRecord.congestion_percentage)).filter(
            TrafficRecord.location_id == loc.id,
            TrafficRecord.is_weekend == False
        ).scalar()
        we_avg = self.db.query(func.avg(TrafficRecord.congestion_percentage)).filter(
            TrafficRecord.location_id == loc.id,
            TrafficRecord.is_weekend == True
        ).scalar()

        if wd_avg is not None and we_avg is not None:
            weekend_delta = round(float(we_avg) - float(wd_avg), 1)
        else:
            weekend_delta = None

        # Weekly trend (Mon-Sun)
        weekly = self.repo.get_weekly_trend_data(location_id=loc.id)

        # Monthly trend
        monthly = self.repo.get_monthly_trend_data(location_id=loc.id)

        # Rain delta
        rain_stats = self.repo.get_weather_impact_data(city_id=loc.city_id)
        rain_delta = rain_stats.get("heavy_rain_surge", 0.0)

        return {
            "location_code": loc.location_code,
            "location_name": loc.location_name,
            "corridor_name": loc.corridor_name,
            "avg_congestion": corridor_avg,
            "peak_hour": peak_hour,
            "peak_hour_congestion": peak_congestion,
            "weekend_delta": weekend_delta,
            "rain_delta": rain_delta,
            "hourly": hourly,
            "weekly": weekly,
            "monthly": monthly,
        }

    def get_event_impact(
        self,
        city_name: Optional[str] = None,
        location_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculates event impact and compares attendee surge vs normal commute days."""
        city_id = None
        loc_id = None
        if location_id:
            loc = self.repo.get_location_by_code(location_id)
            if loc:
                loc_id = loc.id
                city_id = loc.city_id
        elif city_name:
            c = self.repo.get_city_by_name(city_name)
            if c:
                city_id = c.id
        res = self.repo.get_event_impact_metrics(
            city_id=city_id,
            location_id=loc_id,
            start_date=start_date,
            end_date=end_date
        )
        res["city"] = city_name
        return res

    def get_weather_impact(
        self,
        city_name: Optional[str] = None,
        location_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculates actual meteorological correlation curves and precipitation bins from DB."""
        city_id = None
        loc_id = None
        if location_id:
            loc = self.repo.get_location_by_code(location_id)
            if loc:
                loc_id = loc.id
                city_id = loc.city_id
        elif city_name:
            c = self.repo.get_city_by_name(city_name)
            if c:
                city_id = c.id
        res = self.repo.get_weather_impact_data(
            city_id=city_id,
            location_id=loc_id,
            start_date=start_date,
            end_date=end_date
        )
        res["city"] = city_name
        res["location_id"] = location_id
        return res
