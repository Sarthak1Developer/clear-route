import datetime
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.repositories.data_repository import DataRepository
from backend.app.services.inference_service import inference_service
from backend.app.schemas.schemas import PredictionRequest, PredictionResponse
from backend.app.models.entities import Prediction

router = APIRouter(tags=["Predictions"])

@router.post("/predict", response_model=PredictionResponse)
def predict_congestion(req: PredictionRequest, db: Session = Depends(get_db)):
    repo = DataRepository(db)
    loc = repo.get_location_by_code_or_id(req.location_id)
    if not loc:
        raise HTTPException(status_code=404, detail=f"Location corridor '{req.location_id}' not found.")

    # Parse hour and day of week
    try:
        dt = datetime.datetime.strptime(req.prediction_date, "%Y-%m-%d")
        day_of_week = dt.weekday()
        hour = int(req.prediction_time.split(":")[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date or time format: {e}")

    # Validate model selection
    valid_models = ["historical_mean", "linear_regression", "random_forest", "xgboost"]
    if req.model_type not in valid_models:
        raise HTTPException(status_code=400, detail=f"Invalid model_type. Choose from {valid_models}")

    # Run inference service
    pred_result = inference_service.predict(
        city=req.city,
        location_code=loc.location_code,
        hour=hour,
        day_of_week=day_of_week,
        model_type=req.model_type,
        temperature_c=req.temperature_c,
        precipitation_mm=req.precipitation_mm,
        humidity_pct=req.humidity_pct,
        wind_speed_kmh=req.wind_speed_kmh,
        event_present=req.event_present,
        road_lanes=loc.road_lanes,
        road_type=loc.road_type,
        free_flow_speed=loc.free_flow_speed_kmh,
        accident_risk_score=loc.accident_risk_score,
    )

    # Persist prediction record in PostgreSQL / SQLite
    try:
        repo.save_prediction({
            "location_id": loc.id,
            "prediction_date": dt.date(),
            "prediction_hour": hour,
            "model_type": req.model_type,
            "temperature_c": req.temperature_c,
            "precipitation_mm": req.precipitation_mm,
            "event_present": req.event_present,
            "event_name": req.event_name,
            "predicted_congestion_pct": pred_result["predicted_congestion_pct"],
            "congestion_category": pred_result["congestion_category"],
            "baseline_congestion_pct": pred_result["historical_baseline_pct"],
            "shap_attribution_json": json.dumps(pred_result["shap_attributions"]),
        })
    except Exception as e:
        # Log error but don't fail user request
        print(f"Warning: could not persist prediction record: {e}")

    return {
        "prediction_id": pred_result["prediction_id"],
        "city": req.city,
        "location_id": loc.location_code,
        "prediction_date": req.prediction_date,
        "prediction_time": req.prediction_time,
        "predicted_congestion_pct": pred_result["predicted_congestion_pct"],
        "congestion_category": pred_result["congestion_category"],
        "historical_baseline_pct": pred_result["historical_baseline_pct"],
        "difference_pct": pred_result["difference_pct"],
        "selected_model": req.model_type,
        "confidence_interval": pred_result.get("confidence_interval"),
        "shap_attributions": pred_result["shap_attributions"],
    }

@router.get("/predictions/{prediction_id}")
def get_prediction_by_id(prediction_id: str, db: Session = Depends(get_db)):
    pred = db.query(Prediction).filter(Prediction.id == int(prediction_id) if prediction_id.isdigit() else False).first()
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    return {
        "id": pred.id,
        "date": str(pred.prediction_date),
        "hour": pred.prediction_hour,
        "model": pred.model_type,
        "predicted_pct": pred.predicted_congestion_pct,
        "category": pred.congestion_category,
    }

@router.get("/models")
def get_available_models():
    return {
        "models": [
            {
                "key": "historical_mean",
                "name": "Historical Mean Baseline",
                "family": "Statistical Segment-Hour Aggregation",
                "description": "Calculates historical average congestion for a road corridor and time slot as a benchmark.",
            },
            {
                "key": "linear_regression",
                "name": "Linear Regression (Ridge)",
                "family": "Regularized Parametric Estimator",
                "description": "Establishes a transparent linear relationship between weather, time, road capacity, and congestion.",
            },
            {
                "key": "random_forest",
                "name": "Random Forest Regressor",
                "family": "Multi-Tree Bagging Ensemble",
                "description": "Captures non-linear relationships and feature interactions without parametric assumptions.",
            },
            {
                "key": "xgboost",
                "name": "XGBoost Regressor (Primary)",
                "family": "Gradient Boosted Decision Trees",
                "description": "Optimized objective tree boosting capturing compound meteorological and spatio-temporal bottlenecks.",
            },
        ]
    }
