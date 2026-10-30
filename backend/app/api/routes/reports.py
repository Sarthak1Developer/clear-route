import io
import csv
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

router = APIRouter(tags=["Reports & Exports"])

@router.get("/reports/export/{dataset_id}")
def export_dataset(dataset_id: str):
    output = io.StringIO()
    writer = csv.writer(output)

    if dataset_id == "city_summary":
        writer.writerow(["city_code", "city_name", "state", "latitude", "longitude", "avg_congestion_pct", "corridors_monitored"])
        writer.writerow(["DEL", "Delhi", "Delhi NCT", 28.6139, 77.2090, 46.5, 5])
        writer.writerow(["BOM", "Mumbai", "Maharashtra", 19.0760, 72.8777, 49.0, 5])
        writer.writerow(["BLR", "Bengaluru", "Karnataka", 12.9716, 77.5946, 54.0, 5])
        writer.writerow(["HYD", "Hyderabad", "Telangana", 17.3850, 78.4867, 43.0, 5])
        writer.writerow(["CCU", "Kolkata", "West Bengal", 22.5726, 88.3639, 41.5, 5])

    elif dataset_id == "location_summary":
        writer.writerow(["location_code", "city", "location_name", "corridor_name", "road_type", "lanes", "free_flow_speed", "observed_speed", "avg_congestion_pct"])
        writer.writerow(["DEL_001", "Delhi", "Laxmi Nagar", "Vikas Marg Arterial", "primary", 6, 55.0, 26.4, 52.0])
        writer.writerow(["DEL_002", "Delhi", "Connaught Place", "Radial Commercial Ring", "primary", 4, 45.0, 24.3, 46.0])
        writer.writerow(["BOM_001", "Mumbai", "Andheri West / East", "SV Road & Western Express", "trunk", 8, 65.0, 27.3, 58.0])
        writer.writerow(["BLR_001", "Bengaluru", "Whitefield", "ITPB Main Road", "primary", 4, 50.0, 21.5, 57.0])
        writer.writerow(["BLR_002", "Bengaluru", "Central Silk Board", "Hosur Outer Ring Junction", "trunk", 8, 60.0, 19.8, 67.0])
        writer.writerow(["HYD_001", "Hyderabad", "HITEC City", "Cyber Towers Arterial", "trunk", 6, 60.0, 31.8, 47.0])
        writer.writerow(["CCU_001", "Kolkata", "Salt Lake Sector V", "College More Major Arterial", "primary", 6, 50.0, 28.5, 43.0])

    elif dataset_id == "hourly_patterns":
        writer.writerow(["hour_of_day", "is_peak", "weekday_avg_congestion", "weekend_avg_congestion"])
        for h in range(24):
            is_peak = (8 <= h <= 11) or (17 <= h <= 21)
            wd = 74.0 if is_peak else 38.0 + (h % 3) * 3
            we = 45.0 if is_peak else 32.0 + (h % 2) * 2
            writer.writerow([h, int(is_peak), wd, we])

    elif dataset_id == "weather_impact":
        writer.writerow(["precipitation_band", "min_rain_mm", "max_rain_mm", "observed_congestion_pct", "speed_reduction_pct"])
        writer.writerow(["Dry", 0.0, 0.5, 38.2, 0.0])
        writer.writerow(["Light Rain", 0.5, 5.0, 48.7, 18.0])
        writer.writerow(["Moderate Rain", 5.0, 15.0, 63.4, 41.0])
        writer.writerow(["Heavy Monsoon", 15.0, 80.0, 79.1, 64.0])

    elif dataset_id == "model_evaluation":
        writer.writerow(["model_key", "model_name", "mae", "rmse", "r2_score", "is_champion"])
        writer.writerow(["historical_mean", "Historical Mean Baseline", 11.45, 14.82, 0.542, 0])
        writer.writerow(["linear_regression", "Linear Regression (Ridge)", 8.32, 10.95, 0.698, 0])
        writer.writerow(["random_forest", "Random Forest Regressor", 4.88, 6.54, 0.841, 0])
        writer.writerow(["xgboost", "XGBoost Regressor", 3.65, 4.92, 0.895, 1])

    else:
        # Generic sample
        writer.writerow(["city", "timestamp", "location", "temperature_c", "precipitation_mm", "congestion_pct"])
        writer.writerow(["Delhi", "2019-10-15 18:00", "Laxmi Nagar", 27.5, 0.0, 56.4])
        writer.writerow(["Mumbai", "2019-07-20 19:00", "Andheri", 29.0, 22.5, 82.1])
        writer.writerow(["Bengaluru", "2019-09-12 18:30", "Central Silk Board", 23.5, 8.0, 76.8])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=clearroute_{dataset_id}.csv"}
    )
