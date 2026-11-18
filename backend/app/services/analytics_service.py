import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy import func, desc
from backend.app.repositories.data_repository import DataRepository
from backend.app.models.entities import City, Location, TrafficRecord, WeatherRecord, Event

class AnalyticsService:
    def __init__(self, db: Session):
        self.repo = DataRepository(db)
        self.db = db

    def get_overview(self, city_name=None):
        from backend.app.services.profile_service import profile
        data=profile(self.db,city=city_name)
        cities=self.repo.get_all_cities()
        city=self.repo.get_city_by_name(city_name) if city_name else None
        city_comparison=[]
        for c in cities:
            row=self.db.query(func.avg(TrafficRecord.congestion_percentage),func.count(func.distinct(TrafficRecord.location_id))).join(Location).filter(Location.city_id==c.id).first()
            city_comparison.append({"city":c.city_name,"avg_congestion_pct":round(float(row[0]),2) if row[0] is not None else None,"corridor_count":row[1]})
        observed=[r for r in city_comparison if r["avg_congestion_pct"] is not None]
        days=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        dates=[r['key'] for r in data['daily']]
        network_mean=self.db.query(func.avg(TrafficRecord.congestion_percentage)).scalar()
        return {"network_avg_congestion_pct":round(float(network_mean),2) if network_mean is not None else None,"scope_city":city_name,"total_cities":len(cities),"total_locations":len(data['corridors']),"avg_congestion_pct":data['mean'],
                "most_congested_city":max(observed,key=lambda r:r['avg_congestion_pct'])['city'] if observed else 'Unavailable',
                "total_records_processed":data['sample_count'],"historical_coverage":f"{dates[0]} to {dates[-1]}" if dates else 'No historical records',
                "city_comparison":city_comparison,"hourly_trend":[{"hour":h,"avg_congestion":next((r['avg_congestion'] for r in data['hourly'] if int(r['key'])==h),None),"is_peak":8<=h<=11 or 17<=h<=21} for h in range(24)],
                "weekly_trend":[{"day":days[d],"avg_congestion":next((r['avg_congestion'] for r in data['weekly'] if int(r['key'])==d),None)} for d in range(7)],
                "monthly_trend":[{"month":months[int(r['key'])-1],"avg_congestion":r['avg_congestion']} for r in data['monthly']],
                "weather_correlation":self.repo.get_weather_impact_data(city_id=city.id if city else None)['rain_bands']}

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
        avg_congestion = round(float(avg_c_val), 2) if avg_c_val is not None else None

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
            peak_hours_str = f"{peak_h:02d}:00 – {(peak_h + 1) % 24:02d}:00 IST"
        else:
            peak_hours_str = "Unavailable"
            peak_c = avg_congestion

        # Rain impact in this city
        city_weather = self.repo.get_weather_impact_data(city_id=city.id)
        rain_delta = city_weather.get("heavy_rain_surge", 0.0)

        # 24-hr Weekday vs Weekend distribution
        hourly_dist = self.repo.get_hourly_weekday_weekend_distribution(city_id=city.id)

        # Top congested corridors ranked by actual database average
        corridors = self.repo.get_city_corridors_with_stats(city.id)
        corridors.sort(key=lambda x: x["avg_congestion_pct"] if x["avg_congestion_pct"] is not None else -1, reverse=True)

        # Category
        if avg_congestion is None:
            category = "Unavailable"
        elif avg_congestion <= 25.0:
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
        rain_stats = self.repo.get_weather_impact_data(location_id=loc.id)
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
            if not loc:
                raise HTTPException(status_code=404, detail="Unknown corridor")
            if city_name and loc.city.city_name.lower()!=city_name.lower():
                raise HTTPException(status_code=400, detail="Corridor does not belong to city")
            if loc:
                loc_id = loc.id
                city_id = loc.city_id
        elif city_name:
            c = self.repo.get_city_by_name(city_name)
            if not c:
                raise HTTPException(status_code=404, detail="Unknown city")
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
            if not loc:
                raise HTTPException(status_code=404, detail="Unknown corridor")
            if city_name and loc.city.city_name.lower()!=city_name.lower():
                raise HTTPException(status_code=400, detail="Corridor does not belong to city")
            if loc:
                loc_id = loc.id
                city_id = loc.city_id
        elif city_name:
            c = self.repo.get_city_by_name(city_name)
            if not c:
                raise HTTPException(status_code=404, detail="Unknown city")
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
