import datetime
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.repositories.data_repository import DataRepository
from backend.app.services.inference_service import (
    inference_service,
    ModelNotAvailableError,
    PreprocessingArtifactMissingError,
    PredictionOutputValidationError
)
from backend.app.schemas.schemas import PredictionRequest, PredictionResponse, PredictionExplanationResponse
from backend.app.models.entities import Prediction, Location

logger = logging.getLogger("clearroute.routes.predictions")

router = APIRouter(tags=["Predictions"])

def resolve_temporal(req):
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
    try:
        date = datetime.date.fromisoformat(req.prediction_date) if req.prediction_date else now.date()
        clock = datetime.datetime.strptime(req.prediction_time, "%H:%M").time() if req.prediction_time else None
        if clock and req.hour is not None and req.hour != clock.hour:
            raise ValueError("hour conflicts with prediction_time")
        if req.prediction_date and req.day_of_week is not None and req.day_of_week != date.weekday():
            raise ValueError("day_of_week conflicts with prediction_date")
        if req.prediction_date and req.month is not None and req.month != date.month:
            raise ValueError("month conflicts with prediction_date")
        hour = clock.hour if clock else (req.hour if req.hour is not None else 12)
        dow = req.day_of_week if req.day_of_week is not None else date.weekday()
        month = req.month if req.month is not None else date.month
        return datetime.datetime.combine(date, datetime.time(hour)), date.isoformat(), (clock.strftime("%H:%M") if clock else f"{hour:02d}:00"), hour, dow, month
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid temporal input: {exc}")

@router.post("/predict", response_model=PredictionResponse, summary="Execute forward-looking congestion inference using serialized ML models")
def predict_congestion(req: PredictionRequest, db: Session = Depends(get_db)):
    """
    Executes actual forward inference using serialized ML models from ml/artifacts/.
    Validates input parameters and returns verified prediction outputs and SHAP attributions.
    """
    repo = DataRepository(db)
    loc = repo.get_location_by_code_or_id(req.location_id)
    if not loc:
        raise HTTPException(status_code=404, detail=f"Location corridor '{req.location_id}' not found.")

    if loc.city.city_name != req.city:
        raise HTTPException(status_code=400, detail="Selected corridor does not belong to the requested city.")
    dt, prediction_date, prediction_time, hour, day_of_week, month = resolve_temporal(req)

    # Validate model selection
    valid_models = ["historical_mean", "linear_regression", "random_forest", "xgboost"]
    model_type = req.model_type or "xgboost"
    if model_type not in valid_models:
        raise HTTPException(status_code=400, detail=f"Invalid model_type '{model_type}'. Choose from {valid_models}")

    # Resolve features with priority to explicit aliases
    temp_c = req.temperature_2m_c if req.temperature_2m_c is not None else (req.temperature_c if req.temperature_c is not None else 28.0)
    precip_mm = req.precipitation_mm if req.precipitation_mm is not None else 0.0
    humid_pct = req.relative_humidity_2m_pct if req.relative_humidity_2m_pct is not None else (req.humidity_pct if req.humidity_pct is not None else 65.0)
    wind_kmh = req.wind_speed_10m_kmh if req.wind_speed_10m_kmh is not None else (req.wind_speed_kmh if req.wind_speed_kmh is not None else 12.0)
    ev_present = bool(req.event_present)
    lanes = req.road_lanes if req.road_lanes is not None else getattr(loc, "road_lanes", 4)
    rtype = req.road_type if req.road_type is not None else getattr(loc, "road_type", "primary")
    ff_speed = req.free_flow_speed_kmh if req.free_flow_speed_kmh is not None else getattr(loc, "free_flow_speed_kmh", 60.0)
    length = req.length_m if req.length_m is not None else getattr(loc, "length_m", 3000.0)
    risk_score = req.accident_risk_score if req.accident_risk_score is not None else getattr(loc, "accident_risk_score", 0.5)

    # Run dedicated ML inference service
    try:
        pred_result = inference_service.predict(
            city=req.city,
            location_code=loc.location_code,
            hour=hour,
            day_of_week=day_of_week,
            month=month,
            model_type=model_type,
            temperature_c=temp_c,
            precipitation_mm=precip_mm,
            humidity_pct=humid_pct,
            wind_speed_kmh=wind_kmh,
            event_present=ev_present,
            event_name=req.event_name or "",
            event_type=req.event_type,
            event_intensity=req.event_intensity,
            road_lanes=lanes,
            road_type=rtype,
            free_flow_speed=ff_speed,
            accident_risk_score=risk_score,
            length_m=length,
            lag_speed_1h=req.lag_speed_1h,
            rolling_speed_3h=req.rolling_speed_3h,
            location_name=loc.location_name,
            corridor_name=loc.corridor_name,
            prediction_date=prediction_date,
            prediction_time=prediction_time,
        )
    except ModelNotAvailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except PreprocessingArtifactMissingError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except PredictionOutputValidationError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Inference execution failed. See server logs.")

    # Persist prediction record in database
    try:
        saved = repo.save_prediction({
            "location_id": loc.id,
            "prediction_date": dt.date() if hasattr(dt, "date") else datetime.date.today(),
            "prediction_hour": hour,
            "model_type": model_type,
            "temperature_c": temp_c,
            "precipitation_mm": precip_mm,
            "event_present": ev_present,
            "event_name": req.event_name,
            "predicted_congestion_pct": pred_result["predicted_congestion_pct"],
            "congestion_category": pred_result["congestion_category"],
            "baseline_congestion_pct": pred_result["historical_baseline_pct"],
            "shap_attribution_json": json.dumps({"model_id": model_type, "model_name": pred_result["model_name"], "model_version": pred_result["model_version"], "predicted_congestion": pred_result["predicted_congestion_pct"], "congestion_category": pred_result["congestion_category"], "base_value": pred_result["base_value"], "additive_check": pred_result["additive_check"], "category_impacts": pred_result["category_impacts"] or {}, "feature_contributions": pred_result["feature_contributions"] or [], "feature_values": pred_result["input_features"], "explanation_summary": pred_result["explanation_summary"], "limitations_and_caveats": pred_result["limitations_and_caveats"] or []}),
        })
    except Exception as e:
        db.rollback()
        logger.warning("Could not persist prediction record", exc_info=True)
        raise HTTPException(status_code=503, detail="Prediction could not be saved. Retry later.")

    pred_result["prediction_id"] = str(saved.id) if "saved" in locals() else pred_result["prediction_id"]
    return pred_result


@router.post("/predict/compare", summary="Run all available congestion models against the same scenario")
def compare_congestion_models(req: PredictionRequest, db: Session = Depends(get_db)):
    """
    Runs each available estimator against the exact same validated scenario.
    Individual model failures are reported explicitly; no substitute prediction is generated.
    """
    model_keys = ["xgboost", "random_forest", "linear_regression", "historical_mean"]
    results = []
    for model_key in model_keys:
        if not inference_service.is_model_available(model_key):
            results.append({
                "model": model_key,
                "status": "unavailable",
                "error": f"Model '{model_key}' or its required preprocessing artifact is not loaded."
            })
            continue
        try:
            model_request = req.model_copy(update={"model_type": model_key})
            result = predict_congestion(model_request, db)
            results.append({"model": model_key, "status": "success", "result": result})
        except HTTPException as exc:
            results.append({
                "model": model_key,
                "status": "error",
                "error": str(exc.detail),
                "http_status": exc.status_code
            })

    successful = [item for item in results if item["status"] == "success"]
    if not successful:
        raise HTTPException(status_code=503, detail={
            "message": "No model could produce a valid prediction.",
            "results": results
        })

    return {
        "status": "partial_success" if len(successful) != len(model_keys) else "success",
        "models_requested": len(model_keys),
        "models_succeeded": len(successful),
        "best_model_by_held_out_metrics": inference_service.get_best_model_key(),
        "results": results
    }

@router.post("/predict/explain", response_model=PredictionExplanationResponse, summary="Generate detailed individual SHAP attribution breakdown conforming to contract")
@router.post("/predictions/explain", response_model=PredictionExplanationResponse, include_in_schema=False)
def explain_congestion_prediction(req: PredictionRequest, db: Session = Depends(get_db)):
    """
    Executes actual forward inference and generates a standardized additive SHAP TreeExplainer explanation payload.
    Conforms strictly to Section 9.B of docs/ML_INTEGRATION_CONTRACT.md.
    """
    repo = DataRepository(db)
    loc = repo.get_location_by_code_or_id(req.location_id)
    if not loc:
        raise HTTPException(status_code=404, detail=f"Location corridor '{req.location_id}' not found.")

    if loc.city.city_name != req.city:
        raise HTTPException(status_code=400, detail="Selected corridor does not belong to the requested city.")
    dt, prediction_date, prediction_time, hour, day_of_week, month = resolve_temporal(req)

    valid_models = ["historical_mean", "linear_regression", "random_forest", "xgboost"]
    model_type = req.model_type or "xgboost"
    if model_type not in valid_models:
        raise HTTPException(status_code=400, detail=f"Invalid model_type '{model_type}'. Choose from {valid_models}")

    temp_c = req.temperature_2m_c if req.temperature_2m_c is not None else (req.temperature_c if req.temperature_c is not None else 28.0)
    precip_mm = req.precipitation_mm if req.precipitation_mm is not None else 0.0
    humid_pct = req.relative_humidity_2m_pct if req.relative_humidity_2m_pct is not None else (req.humidity_pct if req.humidity_pct is not None else 65.0)
    wind_kmh = req.wind_speed_10m_kmh if req.wind_speed_10m_kmh is not None else (req.wind_speed_kmh if req.wind_speed_kmh is not None else 12.0)
    ev_present = bool(req.event_present)
    lanes = req.road_lanes if req.road_lanes is not None else getattr(loc, "road_lanes", 4)
    rtype = req.road_type if req.road_type is not None else getattr(loc, "road_type", "primary")
    ff_speed = req.free_flow_speed_kmh if req.free_flow_speed_kmh is not None else getattr(loc, "free_flow_speed_kmh", 60.0)
    length = req.length_m if req.length_m is not None else getattr(loc, "length_m", 3000.0)
    risk_score = req.accident_risk_score if req.accident_risk_score is not None else getattr(loc, "accident_risk_score", 0.5)

    is_peak = (8 <= hour <= 11) or (17 <= hour <= 21)
    is_weekend = (day_of_week >= 5)
    is_raining = (precip_mm > 0.5)
    resolved_event_type = req.event_type if req.event_type else ("Festival" if ev_present else "None")
    resolved_event_intensity = float(req.event_intensity) if req.event_intensity is not None else (0.5 if ev_present else 0.0)

    features = {
        "city": req.city,
        "location_id": str(loc.location_code).strip(),
        "hour": int(hour),
        "day_of_week": int(day_of_week),
        "month": int(month),
        "temperature_2m_c": float(temp_c),
        "precipitation_mm": float(precip_mm),
        "relative_humidity_2m_pct": float(humid_pct),
        "wind_speed_10m_kmh": float(wind_kmh),
        "road_lanes": int(lanes),
        "length_m": float(length),
        "accident_risk_score": float(risk_score),
        "free_flow_speed_kmh": float(ff_speed),
        "road_type": str(rtype).lower(),
        "event_type": resolved_event_type,
        "event_intensity": resolved_event_intensity,
        "is_weekend": int(is_weekend),
        "is_peak_hour": int(is_peak),
        "is_holiday": 0,
        "event_present": 1 if ev_present else 0,
        "is_raining": 1 if is_raining else 0,
    }
    if req.lag_speed_1h is not None:
        features["lag_speed_1h"] = float(req.lag_speed_1h)
    if req.rolling_speed_3h is not None:
        features["rolling_speed_3h"] = float(req.rolling_speed_3h)

    try:
        explanation = inference_service.explain_prediction(features, model_key=model_type)
        return explanation
    except ModelNotAvailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except PreprocessingArtifactMissingError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Explanation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Explanation unavailable. See server logs.")

@router.get("/predictions/{prediction_id}/explain", response_model=PredictionExplanationResponse, summary="Retrieve individual SHAP explanation for a persisted prediction")
def get_prediction_explanation_by_id(prediction_id: str, db: Session = Depends(get_db)):
    """Retrieves full additive SHAP TreeExplainer explanation for a persisted prediction record."""
    pred = db.query(Prediction).filter(Prediction.id == int(prediction_id) if prediction_id.isdigit() else False).first()
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction not found")

    stored = json.loads(pred.shap_attribution_json or "null")
    if isinstance(stored, dict) and "feature_values" in stored:
        return {**stored, "prediction_id": str(pred.id)}
    raise HTTPException(status_code=409, detail="Exact explanation inputs were not retained for this legacy record; submit the original scenario to /api/predict/explain.")

@router.get("/predictions/{prediction_id}", summary="Retrieve stored prediction record by ID")
def get_prediction_by_id(prediction_id: str, db: Session = Depends(get_db)):
    """Retrieves a previously computed and persisted prediction by its record ID."""
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

@router.get("/models", summary="List available machine learning model architectures")
def get_available_models():
    """Lists the 4 available model approaches and algorithm families supported by the platform."""
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
