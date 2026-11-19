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

    def get_location_trends(self, loc_code, day_of_week=None, month=None, start_date=None, end_date=None):
        from backend.app.services.profile_service import profile
        loc=self.repo.get_location_by_code_or_id(loc_code)
        if not loc:raise ValueError(f"Corridor '{loc_code}' not found.")
        data=profile(self.db,location=loc.location_code,day_of_week=day_of_week,month=month,start_date=start_date,end_date=end_date)
        speed=self.db.query(TrafficRecord.hour,func.avg(TrafficRecord.observed_speed_kmh)).filter(TrafficRecord.location_id==loc.id)
        if day_of_week is not None:speed=speed.filter(TrafficRecord.day_of_week==day_of_week)
        if month is not None:speed=speed.filter(TrafficRecord.month==month)
        if start_date:speed=speed.filter(func.date(TrafficRecord.timestamp)>=start_date)
        if end_date:speed=speed.filter(func.date(TrafficRecord.timestamp)<=end_date)
        speeds=dict(speed.group_by(TrafficRecord.hour).all())
        by_hour={int(r['key']):r for r in data['hourly']}
        peak=int(data['peak_hour']) if data['peak_hour'] is not None else None
        return {'location_code':loc.location_code,'location_name':loc.location_name,'corridor_name':loc.corridor_name,
            'city':loc.city.city_name,'sample_count':data['sample_count'],'status':data['status'],
            'filters':{'day_of_week':day_of_week,'month':month,'start_date':start_date,'end_date':end_date},
            'avg_congestion':data['mean'],'peak_hour':peak,'peak_hour_congestion':by_hour[peak]['avg_congestion'] if peak is not None else None,
            'weekend_delta':round(data['weekend_mean']-data['weekday_mean'],2) if data['weekend_mean'] is not None and data['weekday_mean'] is not None else None,
            'rain_delta':self.repo.get_weather_impact_data(location_id=loc.id,start_date=start_date,end_date=end_date,day_of_week=day_of_week,month=month).get('heavy_rain_surge'),
            'hourly':[{'hour':h,'congestion_pct':by_hour.get(h,{}).get('avg_congestion'),'speed_kmh':round(speeds[h],2) if h in speeds else None,'sample_count':by_hour.get(h,{}).get('sample_count',0)} for h in range(24)],
            'weekly':[{'day':['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d],'avg_congestion':next((r['avg_congestion'] for r in data['weekly'] if int(r['key'])==d),None)} for d in range(7)],
            'monthly':[{'month':['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m-1],'avg_congestion':next((r['avg_congestion'] for r in data['monthly'] if int(r['key'])==m),None)} for m in range(4,13)]}

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
