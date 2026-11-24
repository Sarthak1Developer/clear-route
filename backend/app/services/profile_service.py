"""Filtered historical statistics. All values originate in the selected database."""
import statistics
from sqlalchemy import func
from backend.app.models.entities import TrafficRecord, Location, City
from backend.app.repositories.data_repository import DataRepository
from fastapi import HTTPException

def profile(db, city=None, location=None, start_date=None, end_date=None, day_of_week=None, month=None):
    repo=DataRepository(db)
    city_obj=repo.get_city_by_name(city) if city else None
    loc=repo.get_location_by_code(location) if location else None
    if city and not city_obj:raise HTTPException(404,'Unknown city')
    if location and not loc:raise HTTPException(404,'Unknown corridor')
    if loc and city_obj and loc.city_id != city_obj.id:raise HTTPException(400,'Corridor does not belong to city')
    q=db.query(TrafficRecord).join(Location,Location.id==TrafficRecord.location_id)
    if city_obj:q=q.filter(Location.city_id==city_obj.id)
    if loc:q=q.filter(TrafficRecord.location_id==loc.id)
    if start_date:q=q.filter(func.date(TrafficRecord.timestamp)>=start_date)
    if end_date:q=q.filter(func.date(TrafficRecord.timestamp)<=end_date)
    if day_of_week is not None:q=q.filter(TrafficRecord.day_of_week==day_of_week)
    if month is not None:q=q.filter(TrafficRecord.month==month)
    count=q.count()
    values=[r[0] for r in q.with_entities(TrafficRecord.congestion_percentage).all()]
    avg=lambda xs: round(sum(xs)/len(xs),2) if xs else None
    def grouped(key):
        return [{'key':str(k),'avg_congestion':round(float(mean),2),'sample_count':n}
                for k,mean,n in q.with_entities(key,func.avg(TrafficRecord.congestion_percentage),func.count()).group_by(key).order_by(key).all()]
    hourly=grouped(TrafficRecord.hour)
    weekly=grouped(TrafficRecord.day_of_week)
    day=[r for r in weekly if int(r['key'])<5];weekend=[r for r in weekly if int(r['key'])>=5]
    weighted=lambda rows:round(sum(r['avg_congestion']*r['sample_count'] for r in rows)/sum(r['sample_count'] for r in rows),2) if rows else None
    return {'city':city_obj.city_name if city_obj else None,'location':loc.location_code if loc else None,
            'start_date':start_date,'end_date':end_date,'sample_count':count,'status':'available' if count else 'unavailable',
            'mean':avg(values),'median':round(statistics.median(values),2) if values else None,
            'minimum':min(values) if values else None,'maximum':max(values) if values else None,
            'weekday_mean':weighted(day),'weekend_mean':weighted(weekend),
            'peak_hour':max(hourly,key=lambda row:row['avg_congestion'])['key'] if hourly else None,
            'hourly':hourly,'weekly':weekly,'monthly':grouped(TrafficRecord.month),
            'daily':grouped(func.date(TrafficRecord.timestamp)),
            'corridors':[{'location_id':code,'mean':round(float(m),2),'sample_count':n} for code,m,n in q.with_entities(Location.location_code,func.avg(TrafficRecord.congestion_percentage),func.count()).group_by(Location.location_code).all()],
            'provenance':'Existing analytical dataset; real-world source truth is not independently verified'}
