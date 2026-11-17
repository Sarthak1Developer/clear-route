import io
import csv
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database.session import get_db, SessionLocal
from backend.app.repositories.data_repository import DataRepository
from backend.app.models.entities import City, Location, TrafficRecord, ModelMetadata

router = APIRouter(tags=["Reports & Exports"])

@router.get("/reports/export/{dataset_id}", summary="Export structured analytical datasets formatted for Power BI / CSV")
def export_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Exports actual database-driven tables as CSV attachments for tabular ingestion and Power BI reporting."""
    if not isinstance(db, Session):
        db = SessionLocal()
    repo = DataRepository(db)
    output = io.StringIO()
    writer = csv.writer(output)

    if dataset_id == "city_summary":
        writer.writerow(["city_code", "city_name", "state", "latitude", "longitude", "avg_congestion_pct", "corridors_monitored"])
        cities = repo.get_all_cities()
        for c in cities:
            avg_c = db.query(func.avg(TrafficRecord.congestion_percentage))\
                .join(Location, Location.id == TrafficRecord.location_id)\
                .filter(Location.city_id == c.id)\
                .scalar()
            loc_cnt = len(repo.get_locations_by_city_id(c.id))
            writer.writerow([
                c.city_code, c.city_name, c.state, c.latitude, c.longitude,
                round(float(avg_c), 1) if avg_c is not None else 0.0,
                loc_cnt
            ])

    elif dataset_id == "location_summary":
        writer.writerow(["location_code", "city", "location_name", "corridor_name", "road_type", "lanes", "free_flow_speed", "observed_speed", "avg_congestion_pct"])
        cities = repo.get_all_cities()
        for c in cities:
            corridors = repo.get_city_corridors_with_stats(c.id)
            for loc in corridors:
                writer.writerow([
                    loc["location_code"], c.city_name, loc["location_name"], loc["corridor_name"],
                    loc["road_type"], loc["road_lanes"], loc["speed_limit_kmh"],
                    loc["observed_speed_kmh"], loc["avg_congestion_pct"]
                ])

    elif dataset_id == "hourly_patterns":
        writer.writerow(["hour_of_day", "is_peak", "weekday_avg_congestion", "weekend_avg_congestion"])
        dist = repo.get_hourly_weekday_weekend_distribution()
        for item in dist:
            h = item["hour"]
            is_peak = int((8 <= h <= 11) or (17 <= h <= 21))
            writer.writerow([
                h, is_peak,
                item["weekday_congestion"] if item["weekday_congestion"] is not None else "",
                item["weekend_congestion"] if item["weekend_congestion"] is not None else ""
            ])

    elif dataset_id == "weather_impact":
        writer.writerow(["precipitation_band", "avg_congestion_pct", "avg_speed_kmh", "sample_count"])
        weather_stats = repo.get_weather_impact_data()
        for band in weather_stats["rain_bands"]:
            writer.writerow([
                band["band"], band["avg_congestion"], band["avg_speed_kmh"], band["sample_count"]
            ])

    elif dataset_id == "model_evaluation":
        writer.writerow(["model_key", "model_name", "algorithm_family", "mae", "rmse", "r2_score", "is_champion"])
        models = repo.get_all_model_metadata()
        for m in models:
            writer.writerow([
                m.model_key, m.model_name, m.algorithm_family, m.mae, m.rmse, m.r2_score, int(m.is_primary)
            ])

    else:
        # Default / gold_master_sample: real traffic records
        writer.writerow(["city", "location_code", "timestamp", "hour", "day_of_week", "observed_speed_kmh", "free_flow_speed_kmh", "congestion_pct", "category"])
        records = db.query(TrafficRecord).join(Location).join(City).limit(500).all()
        for r in records:
            writer.writerow([
                r.location.city.city_name if r.location and r.location.city else "Metropolitan",
                r.location.location_code if r.location else "",
                r.timestamp.isoformat(),
                r.hour,
                r.day_of_week,
                r.observed_speed_kmh,
                r.free_flow_speed_kmh,
                r.congestion_percentage,
                r.congestion_category
            ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=clearroute_{dataset_id}.csv"}
    )
