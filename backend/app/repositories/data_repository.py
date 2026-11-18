import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from backend.app.models.entities import (
    City, Location, TrafficRecord, WeatherRecord,
    Event, Prediction, ModelMetadata, DataSource
)

class DataRepository:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------------------
    # Cities & Locations Queries
    # -------------------------------------------------------------------------
    def get_all_cities(self) -> List[City]:
        return self.db.query(City).order_by(City.id).all()

    def get_city_by_name(self, city_name: str) -> Optional[City]:
        if not city_name:
            return None
        return self.db.query(City).filter(func.lower(City.city_name) == city_name.strip().lower()).first()

    def get_city_by_code(self, city_code: str) -> Optional[City]:
        if not city_code:
            return None
        return self.db.query(City).filter(func.upper(City.city_code) == city_code.strip().upper()).first()

    def get_locations_by_city_id(self, city_id: int) -> List[Location]:
        return self.db.query(Location).filter(Location.city_id == city_id).order_by(Location.id).all()

    def get_location_by_code_or_id(self, loc_identifier: str) -> Optional[Location]:
        if not loc_identifier:
            return None
        loc_str = str(loc_identifier).strip()
        if loc_str.isdigit():
            loc = self.db.query(Location).filter(Location.id == int(loc_str)).first()
            if loc:
                return loc
        return self.db.query(Location).filter(
            func.lower(Location.location_code) == loc_str.lower()
        ).first()

    def get_location_by_code(self, loc_code: str) -> Optional[Location]:
        return self.get_location_by_code_or_id(loc_code)

    def get_location_by_id(self, location_id: int) -> Optional[Location]:
        return self.db.query(Location).filter(Location.id == location_id).first()

    def get_corridor_stats(self, location_id: int) -> Dict[str, Any]:
        """Calculates actual database aggregate metrics for a single road corridor."""
        stats = self.db.query(
            func.avg(TrafficRecord.congestion_percentage).label("avg_congestion"),
            func.avg(TrafficRecord.observed_speed_kmh).label("avg_speed"),
            func.count(TrafficRecord.id).label("total_records"),
            func.max(TrafficRecord.congestion_percentage).label("max_congestion")
        ).filter(TrafficRecord.location_id == location_id).first()

        avg_c = round(float(stats.avg_congestion), 1) if stats and stats.avg_congestion is not None else None
        avg_s = round(float(stats.avg_speed), 1) if stats and stats.avg_speed is not None else None
        total = int(stats.total_records) if stats and stats.total_records else 0

        return {
            "avg_congestion_pct": avg_c,
            "observed_speed_kmh": avg_s,
            "total_records": total,
            "max_congestion_pct": round(float(stats.max_congestion), 1) if stats and stats.max_congestion is not None else None
        }

    def get_city_corridors_with_stats(self, city_id: int) -> List[Dict[str, Any]]:
        """Retrieves all corridors for a city with genuine DB aggregated speed & congestion."""
        locations = self.get_locations_by_city_id(city_id)
        results = []
        for loc in locations:
            c_stats = self.get_corridor_stats(loc.id)
            c_val = c_stats["avg_congestion_pct"]
            s_val = c_stats["observed_speed_kmh"]
            results.append({
                "id": loc.id,
                "location_code": loc.location_code,
                "location_name": loc.location_name,
                "corridor_name": loc.corridor_name,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "road_type": loc.road_type,
                "road_lanes": loc.road_lanes,
                "speed_limit_kmh": loc.speed_limit_kmh,
                "free_flow_speed_kmh": loc.free_flow_speed_kmh,
                "observed_speed_kmh": s_val,
                "accident_risk_score": loc.accident_risk_score,
                "avg_congestion_pct": c_val,
            })
        return results

    def search_locations(self, q: str = "", city_filter: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        """Searches locations with genuine DB aggregate stats."""
        query = self.db.query(Location).join(City)
        if city_filter:
            query = query.filter(func.lower(City.city_name) == city_filter.strip().lower())
        if q:
            term = f"%{q.strip().lower()}%"
            query = query.filter(
                (func.lower(Location.location_name).like(term)) |
                (func.lower(Location.corridor_name).like(term)) |
                (func.lower(Location.location_code).like(term))
            )

        locs = query.limit(limit).all()
        results = []
        for loc in locs:
            stats = self.get_corridor_stats(loc.id)
            c_val = stats["avg_congestion_pct"]
            s_val = stats["observed_speed_kmh"]
            results.append({
                "id": loc.id,
                "location_code": loc.location_code,
                "location_name": loc.location_name,
                "corridor_name": loc.corridor_name,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "road_type": loc.road_type,
                "road_lanes": loc.road_lanes,
                "speed_limit_kmh": loc.speed_limit_kmh,
                "free_flow_speed_kmh": loc.free_flow_speed_kmh,
                "observed_speed_kmh": s_val,
                "accident_risk_score": loc.accident_risk_score,
                "avg_congestion_pct": c_val,
            })
        return results

    # -------------------------------------------------------------------------
    # Traffic Trends & Time-Series Aggregations
    # -------------------------------------------------------------------------
    def get_hourly_trend_data(self, city_id: Optional[int] = None, location_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Computes 24-hour diurnal profile directly from TrafficRecord table.
        Hours with real records return genuine averages; unobserved hours return None to distinguish missing data from zero congestion.
        """
        query = self.db.query(
            TrafficRecord.hour,
            func.avg(TrafficRecord.congestion_percentage).label("avg_congestion"),
            func.count(TrafficRecord.id).label("record_count")
        )
        if location_id is not None:
            query = query.filter(TrafficRecord.location_id == location_id)
        elif city_id is not None:
            query = query.join(Location).filter(Location.city_id == city_id)

        rows = query.group_by(TrafficRecord.hour).all()
        data_by_hour = {r[0]: round(float(r[1]), 1) for r in rows if r[1] is not None}

        # Format 0-23 hours
        hourly_trend = []
        for h in range(24):
            is_peak = (8 <= h <= 11) or (17 <= h <= 21)
            hourly_trend.append({
                "hour": h,
                "avg_congestion": data_by_hour.get(h, None),
                "is_peak": is_peak,
            })
        return hourly_trend

    def get_weekly_trend_data(self, city_id: Optional[int] = None, location_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Computes Monday-Sunday day of week averages from stored records."""
        days_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        query = self.db.query(
            TrafficRecord.day_of_week,
            func.avg(TrafficRecord.congestion_percentage).label("avg_congestion")
        )
        if location_id is not None:
            query = query.filter(TrafficRecord.location_id == location_id)
        elif city_id is not None:
            query = query.join(Location).filter(Location.city_id == city_id)

        rows = query.group_by(TrafficRecord.day_of_week).all()
        data_by_day = {r[0]: round(float(r[1]), 1) for r in rows if r[1] is not None}

        weekly_trend = []
        for dow_idx, day_name in enumerate(days_map):
            weekly_trend.append({
                "day": day_name,
                "avg_congestion": data_by_day.get(dow_idx, None)
            })
        return weekly_trend

    def get_monthly_trend_data(self, city_id: Optional[int] = None, location_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Computes monthly congestion averages from stored records."""
        month_abbr = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
        query = self.db.query(
            TrafficRecord.month,
            func.avg(TrafficRecord.congestion_percentage).label("avg_congestion")
        )
        if location_id is not None:
            query = query.filter(TrafficRecord.location_id == location_id)
        elif city_id is not None:
            query = query.join(Location).filter(Location.city_id == city_id)

        rows = query.group_by(TrafficRecord.month).order_by(TrafficRecord.month).all()
        return [
            {
                "month": month_abbr.get(r[0], str(r[0])),
                "avg_congestion": round(float(r[1]), 1)
            }
            for r in rows if r[1] is not None
        ]

    def get_hourly_weekday_weekend_distribution(self, city_id: Optional[int] = None, location_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Computes 24h diurnal curve comparing actual weekday vs weekend records."""
        query = self.db.query(
            TrafficRecord.hour,
            TrafficRecord.is_weekend,
            func.avg(TrafficRecord.congestion_percentage).label("avg_congestion")
        )
        if location_id is not None:
            query = query.filter(TrafficRecord.location_id == location_id)
        elif city_id is not None:
            query = query.join(Location).filter(Location.city_id == city_id)

        rows = query.group_by(TrafficRecord.hour, TrafficRecord.is_weekend).all()
        
        wd_map = {}
        we_map = {}
        for h, is_we, avg_c in rows:
            if avg_c is not None:
                if is_we:
                    we_map[h] = round(float(avg_c), 1)
                else:
                    wd_map[h] = round(float(avg_c), 1)

        result = []
        for h in range(24):
            result.append({
                "hour": h,
                "weekday_congestion": wd_map.get(h, None),
                "weekend_congestion": we_map.get(h, None)
            })
        return result

    def get_location_history_records(
        self,
        location_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Returns genuine time-series history records for a corridor."""
        loc = self.db.query(Location).filter(Location.id == location_id).first()
        if not loc:
            raise ValueError(f"Corridor ID {location_id} not found.")

        query = self.db.query(TrafficRecord).filter(TrafficRecord.location_id == location_id)
        if start_date:
            try:
                s_dt = datetime.datetime.fromisoformat(start_date)
                query = query.filter(TrafficRecord.timestamp >= s_dt)
            except Exception:
                pass
        if end_date:
            try:
                e_dt = datetime.datetime.fromisoformat(end_date)
                query = query.filter(TrafficRecord.timestamp < e_dt + datetime.timedelta(days=1))
            except Exception:
                pass

        total_available = query.count()
        records = query.order_by(desc(TrafficRecord.timestamp)).limit(limit).all()

        formatted_records = [
            {
                "timestamp": r.timestamp.isoformat(),
                "observed_speed_kmh": r.observed_speed_kmh,
                "free_flow_speed_kmh": r.free_flow_speed_kmh,
                "congestion_percentage": r.congestion_percentage,
                "congestion_category": r.congestion_category,
                "is_peak": r.is_peak_hour,
            }
            for r in records
        ]

        min_ts = self.db.query(func.min(TrafficRecord.timestamp)).filter(TrafficRecord.location_id == location_id).scalar()
        max_ts = self.db.query(func.max(TrafficRecord.timestamp)).filter(TrafficRecord.location_id == location_id).scalar()
        period_str = f"{min_ts.strftime('%B %d, %Y')} – {max_ts.strftime('%B %d, %Y')}" if min_ts and max_ts else "No historical records"

        return {
            "location_code": loc.location_code,
            "location_name": loc.location_name,
            "corridor_name": loc.corridor_name,
            "historical_period": period_str,
            "total_records_available": total_available,
            "sample_records": formatted_records
        }

    # -------------------------------------------------------------------------
    # Weather & Meteorological Correlation
    # -------------------------------------------------------------------------
    def get_latest_weather_for_city(self, city_id: Optional[int] = None) -> Optional[WeatherRecord]:
        query = self.db.query(WeatherRecord)
        if city_id is not None:
            query = query.filter(WeatherRecord.city_id == city_id)
        return query.order_by(desc(WeatherRecord.timestamp)).first()

    def get_weather_impact_data(self, city_id=None, location_id=None, start_date=None, end_date=None):
        import pandas as pd
        query=self.db.query(TrafficRecord.congestion_percentage,TrafficRecord.observed_speed_kmh,
            WeatherRecord.precipitation_mm,WeatherRecord.temperature_c,WeatherRecord.humidity_pct,
            WeatherRecord.wind_speed_kmh,TrafficRecord.hour,City.city_name).join(Location,Location.id==TrafficRecord.location_id).join(City,City.id==Location.city_id).join(WeatherRecord,and_(WeatherRecord.city_id==Location.city_id,WeatherRecord.timestamp==TrafficRecord.timestamp))
        if location_id is not None:query=query.filter(TrafficRecord.location_id==location_id)
        elif city_id is not None:query=query.filter(Location.city_id==city_id)
        if start_date:query=query.filter(func.date(TrafficRecord.timestamp)>=start_date)
        if end_date:query=query.filter(func.date(TrafficRecord.timestamp)<=end_date)
        frame=pd.DataFrame(query.all(),columns=['congestion','speed','rain','temperature','humidity','wind','hour','city'])
        def corr(column):
            if len(frame)<3 or frame[column].nunique()<2 or frame.congestion.nunique()<2:return None
            return round(float(frame[column].corr(frame.congestion)),4)
        def summary(column):
            return {'mean':round(float(frame[column].mean()),2),'min':float(frame[column].min()),'max':float(frame[column].max()),'correlation':corr(column)} if len(frame) else None
        bands=[]
        for name,lower,upper in [('Dry (<0.5mm)',0,.5),('Light Rain (0.5-5mm)',.5,5),('Moderate (5-15mm)',5,15),('Heavy Monsoon (>15mm)',15,float('inf'))]:
            rows=frame[(frame.rain>=lower)&(frame.rain<upper)]
            bands.append({'band':name,'intensity':name,'sample_count':len(rows),'avg_congestion':round(float(rows.congestion.mean()),2) if len(rows) else None,'avg_speed_kmh':round(float(rows.speed.mean()),2) if len(rows) else None})
        temps=[]
        for name,lower,upper in [('Below 19 C',-float('inf'),19),('19 - 27 C',19,27),('27 - 36 C',27,36),('36 C and above',36,float('inf'))]:
            rows=frame[(frame.temperature>=lower)&(frame.temperature<upper)]
            temps.append({'temp_range':name,'sample_count':len(rows),'avg_congestion':round(float(rows.congestion.mean()),2) if len(rows) else None})
        dry,heavy=bands[0]['avg_congestion'],bands[-1]['avg_congestion']
        return {'heavy_rain_surge':round(heavy-dry,2) if dry is not None and heavy is not None else None,
            'rain_correlation':corr('rain'),'temp_correlation':corr('temperature'),'rain_bands':bands,'temp_bands':temps,
            'humidity_summary':summary('humidity'),'wind_summary':summary('wind'),'sample_count':len(frame),
            'status':'available' if len(frame) else 'unavailable','reason':None if len(frame) else 'Insufficient weather observations matched to traffic timestamps.',
            'city_comparison':[{'city':city,'mean_congestion':round(float(rows.congestion.mean()),2),'mean_rainfall_mm':round(float(rows.rain.mean()),2),'sample_count':len(rows)} for city,rows in frame.groupby('city')],
            'hourly':[{'hour':int(hour),'mean_congestion':round(float(rows.congestion.mean()),2),'rainfall_mm':round(float(rows.rain.mean()),2),'sample_count':len(rows)} for hour,rows in frame.groupby('hour')],
            'source':'Timestamp/city-joined database observations; historical source provenance unverified. Associations are not causal effects.'}

    # -------------------------------------------------------------------------
    # Events & Public Holidays
    # -------------------------------------------------------------------------
    def get_filtered_events(
        self,
        city_name: Optional[str] = None,
        city_id: Optional[int] = None,
        location_id: Optional[int] = None,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        event_type: Optional[str] = None,
        is_future: Optional[bool] = None
    ) -> List[Event]:
        query = self.db.query(Event).join(City)
        if location_id is not None:
            loc = self.get_location_by_id(location_id)
            if loc and loc.city_id:
                query = query.filter(Event.city_id == loc.city_id)
        elif city_id is not None:
            query = query.filter(Event.city_id == city_id)
        elif city_name:
            query = query.filter(func.lower(City.city_name) == city_name.strip().lower())

        if date:
            query = query.filter(Event.event_date == date.strip())
        else:
            if start_date:
                query = query.filter(Event.event_date >= start_date.strip())
            if end_date:
                query = query.filter(Event.event_date <= end_date.strip())

        if event_type:
            query = query.filter(func.lower(Event.event_type) == event_type.strip().lower())

        if is_future is not None:
            query = query.filter(Event.is_2026_future == is_future)

        return query.order_by(Event.event_date.asc()).all()

    def get_events_by_city_name(self, city_name: str = "") -> List[Event]:
        return self.get_filtered_events(city_name=city_name if city_name else None)

    def calculate_event_impact_delta(self, event, location_id=None):
        if event.is_2026_future:return None
        date=str(event.event_date)
        query=self.db.query(TrafficRecord.congestion_percentage).join(Location).filter(Location.city_id==event.city_id)
        if location_id is not None:query=query.filter(TrafficRecord.location_id==location_id)
        event_values=[r[0] for r in query.filter(func.date(TrafficRecord.timestamp)==date).all()]
        event_dates=[str(e[0]) for e in self.db.query(Event.event_date).filter(Event.city_id==event.city_id,Event.is_2026_future==False).all()]
        baseline=[r[0] for r in query.filter(TrafficRecord.day_of_week==event.event_date.weekday(),~func.date(TrafficRecord.timestamp).in_(event_dates)).all()]
        if not event_values or not baseline:return None
        return round(sum(event_values)/len(event_values)-sum(baseline)/len(baseline),2)

    def get_event_impact_metrics(self, city_id=None, location_id=None, start_date=None, end_date=None):
        # Existing records provide city/date, not venue radius or start/end times.
        # Compare against non-event dates with the same weekday in the same city/hour.
        event_q=self.db.query(Event).filter(Event.is_2026_future==False)
        if city_id is not None:event_q=event_q.filter(Event.city_id==city_id)
        events=event_q.all()
        keys={};all_dates=set()
        for event in events:
            key=(event.city_id,str(event.event_date));keys.setdefault(key,set()).add(event.event_type);all_dates.add(key)
        q=self.db.query(Location.city_id,func.date(TrafficRecord.timestamp),TrafficRecord.hour,TrafficRecord.day_of_week,TrafficRecord.congestion_percentage).join(Location,Location.id==TrafficRecord.location_id)
        if location_id is not None:q=q.filter(TrafficRecord.location_id==location_id)
        elif city_id is not None:q=q.filter(Location.city_id==city_id)
        if start_date:q=q.filter(func.date(TrafficRecord.timestamp)>=start_date)
        if end_date:q=q.filter(func.date(TrafficRecord.timestamp)<=end_date)
        rows=q.all();baselines={}
        for cid,date,hour,dow,value in rows:
            if (cid,date) not in all_dates:baselines.setdefault((cid,hour,dow),[]).append(float(value))
        normal={h:[] for h in range(24)};active={h:[] for h in range(24)};deltas={'Festival':[],'Public Holiday':[]}
        for cid,date,hour,dow,value in rows:
            comparison=baselines.get((cid,hour,dow),[])
            if (cid,date) in all_dates and comparison:
                baseline=sum(comparison)/len(comparison);active[hour].append(float(value));normal[hour].append(baseline)
                for category in keys[(cid,date)]:
                    if category in deltas:deltas[category].append(float(value)-baseline)
        mean=lambda xs:round(sum(xs)/len(xs),2) if xs else None
        return {'festival_delta':mean(deltas['Festival']),'holiday_delta':mean(deltas['Public Holiday']),
            'hourly_comparison':[{'hour':h,'normal_congestion':mean(normal[h]),'event_congestion':mean(active[h]),'has_event_data':bool(active[h]),'sample_count':len(active[h])} for h in range(24)],
            'data_backed':bool(any(active.values())),
            'source':'City-day annotations compared with same-city/hour/weekday non-event records. Event venue, duration, attendance and independent provenance unavailable; no causal effect claimed.'}

    # -------------------------------------------------------------------------
    # Governance, Quality & Coverage
    # -------------------------------------------------------------------------
    def get_all_model_metadata(self) -> List[ModelMetadata]:
        return self.db.query(ModelMetadata).order_by(ModelMetadata.id).all()

    def get_all_data_sources(self) -> List[DataSource]:
        return self.db.query(DataSource).order_by(DataSource.id).all()

    def get_data_quality_stats(self) -> Dict[str, Any]:
        total_traffic = self.db.query(func.count(TrafficRecord.id)).scalar() or 0
        complete_rows = self.db.query(func.count(TrafficRecord.id)).filter(
            TrafficRecord.observed_speed_kmh.isnot(None),
            TrafficRecord.congestion_percentage.isnot(None)
        ).scalar() or 0

        rate = round((complete_rows / total_traffic) * 100.0, 1) if total_traffic > 0 else 0.0
        duplicates = self.db.query(TrafficRecord.location_id, TrafficRecord.timestamp, func.count(TrafficRecord.id).label("n")).group_by(TrafficRecord.location_id, TrafficRecord.timestamp).having(func.count(TrafficRecord.id) > 1).all()
        return {
            "total_gold_records": total_traffic,
            "completeness_rate": rate,
            "duplicate_count": sum(row.n - 1 for row in duplicates),
            "target_definition": "Congestion Percentage: CP = ((v_free - v_obs) / v_free) * 100%",
            "validation_status": "Database structure checked; generated demonstration traffic, no verified GPS telemetry"
        }

    def get_data_coverage_stats(self) -> Dict[str, Any]:
        cities = self.db.query(City.city_name).all()
        city_names = [c[0] for c in cities]
        min_ts = self.db.query(func.min(TrafficRecord.timestamp)).scalar()
        max_ts = self.db.query(func.max(TrafficRecord.timestamp)).scalar()
        total_locs = self.db.query(func.count(Location.id)).scalar() or 0

        return {
            "cities_covered": city_names,
            "start_date": min_ts.strftime("%Y-%m-%d") if min_ts else "",
            "end_date": max_ts.strftime("%Y-%m-%d") if max_ts else "",
            "corridors_total": total_locs
        }

    # -------------------------------------------------------------------------
    # Predictions
    # -------------------------------------------------------------------------
    def save_prediction(self, pred_data: Dict[str, Any]) -> Prediction:
        prediction = Prediction(
            location_id=pred_data["location_id"],
            prediction_date=pred_data["prediction_date"],
            prediction_hour=pred_data["prediction_hour"],
            model_type=pred_data["model_type"],
            temperature_c=pred_data.get("temperature_c"),
            precipitation_mm=pred_data.get("precipitation_mm"),
            event_present=pred_data.get("event_present", False),
            event_name=pred_data.get("event_name"),
            predicted_congestion_pct=pred_data["predicted_congestion_pct"],
            congestion_category=pred_data["congestion_category"],
            baseline_congestion_pct=pred_data.get("baseline_congestion_pct"),
            shap_attribution_json=pred_data.get("shap_attribution_json"),
        )
        self.db.add(prediction)
        self.db.commit()
        self.db.refresh(prediction)
        return prediction

    def get_paginated_traffic_records(
        self,
        city: Optional[str] = None,
        location_code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
        sort: str = "timestamp_desc"
    ) -> Dict[str, Any]:
        """Returns paginated database traffic records with optional city, corridor and date filtering."""
        query = self.db.query(TrafficRecord).join(Location, Location.id == TrafficRecord.location_id).join(City, City.id == Location.city_id)
        if city and city.strip() and city.lower() != "all":
            query = query.filter(func.lower(City.city_name) == city.strip().lower())
        if location_code and location_code.strip() and location_code.lower() != "all":
            query = query.filter(
                (Location.location_code == location_code.strip()) |
                (func.lower(Location.location_name).ilike(f"%{location_code.strip().lower()}%"))
            )
        if start_date:
            try:
                s_dt = datetime.datetime.fromisoformat(start_date)
                query = query.filter(TrafficRecord.timestamp >= s_dt)
            except Exception:
                pass
        if end_date:
            try:
                e_dt = datetime.datetime.fromisoformat(end_date)
                query = query.filter(TrafficRecord.timestamp < e_dt + datetime.timedelta(days=1))
            except Exception:
                pass

        total = query.count()
        offset = max(0, (page - 1) * page_size)
        order={"timestamp_desc":TrafficRecord.timestamp.desc(),"timestamp_asc":TrafficRecord.timestamp.asc(),"congestion_desc":TrafficRecord.congestion_percentage.desc(),"congestion_asc":TrafficRecord.congestion_percentage.asc()}[sort]
        rows = query.order_by(order,TrafficRecord.id).offset(offset).limit(page_size).all()

        records = [
            {
                "id": r.id,
                "city": r.location.city.city_name if r.location and r.location.city else "",
                "location_code": r.location.location_code if r.location else "",
                "location_name": r.location.location_name if r.location else "",
                "corridor_name": r.location.corridor_name if r.location else "",
                "road_type": r.location.road_type if r.location else "",
                "timestamp": r.timestamp.isoformat(),
                "hour": r.hour,
                "day_of_week": r.day_of_week,
                "observed_speed_kmh": round(float(r.observed_speed_kmh), 1),
                "free_flow_speed_kmh": round(float(r.free_flow_speed_kmh), 1),
                "congestion_percentage": round(float(r.congestion_percentage), 1),
                "congestion_category": r.congestion_category,
                "is_peak": r.is_peak_hour,
            }
            for r in rows
        ]
        total_pages = max(1, (total + page_size - 1) // page_size)
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "records": records
        }
