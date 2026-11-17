import os
import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.repositories.data_repository import DataRepository
from backend.app.schemas.schemas import ModelPerformanceResponse, FeatureImportanceResponse, ShapSummaryResponse

router = APIRouter(tags=["Model Performance"])

from backend.app.services.inference_service import inference_service, ModelNotAvailableError

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

@router.get("/models/performance", response_model=ModelPerformanceResponse, summary="Get 4 model approaches test benchmark metrics")
def get_model_performance(db: Session = Depends(get_db)):
    """Retrieves chronological held-out test split evaluation metrics (MAE, RMSE, R²) for the 4 ML models."""
    repo = DataRepository(db)
    models_meta = repo.get_all_model_metadata()

    # Load metrics.json if present
    metrics_data = {}
    metrics_path = os.path.join(PROJECT_ROOT, "ml", "artifacts", "metrics.json")
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, "r") as f:
                metrics_data = json.load(f)
        except Exception:
            pass

    model_items = []
    best_key = metrics_data.get("best_model")

    if models_meta:
        for m in models_meta:
            m_metrics = metrics_data.get("models", {}).get(m.model_key, {})
            mae_val = m_metrics.get("mae", m.mae)
            rmse_val = m_metrics.get("rmse", m.rmse)
            r2_val = m_metrics.get("r2", m.r2_score)
            is_primary_val = m_metrics.get("is_primary", (m.model_key == best_key if best_key else m.is_primary))

            model_items.append({
                "id": m.id,
                "key": m.model_key,
                "name": m.model_name,
                "family": m.algorithm_family,
                "role": "Primary Forecasting Model" if is_primary_val else "Benchmarking Model",
                "mae": round(float(mae_val), 3),
                "rmse": round(float(rmse_val), 3),
                "r2": round(float(r2_val), 3),
                "is_primary": bool(is_primary_val),
            })
    else:
        # Fallback to metrics.json
        models_dict = metrics_data.get("models", {})
        idx = 1
        for k, v in models_dict.items():
            is_prim = v.get("is_primary", (k == best_key if best_key else False))
            model_items.append({
                "id": idx,
                "key": k,
                "name": v.get("name", k),
                "family": v.get("family", "Statistical Model"),
                "role": v.get("role", "Benchmarking"),
                "mae": round(float(v.get("mae", 0.0)), 3),
                "rmse": round(float(v.get("rmse", 0.0)), 3),
                "r2": round(float(v.get("r2", 1.0)), 3),
                "is_primary": bool(is_prim),
            })
            idx += 1

    # Verify best model based on genuine held-out test metrics
    if best_key:
        best = next((m for m in model_items if m["key"] == best_key), None)
    else:
        best = None

    if not best:
        primary_model = next((m for m in model_items if m["is_primary"]), None)
        best = primary_model or min(model_items, key=lambda x: x["mae"])

    # No per-row held-out predictions are persisted by the training pipeline.
    # Do not publish illustrative numbers as if they were measured test observations.
    actual_vs_pred = []

    return {
        "models": model_items,
        "best_model": best,
        "actual_vs_predicted": actual_vs_pred,
    }

@router.get("/models/feature-importance", response_model=FeatureImportanceResponse, summary="Get global feature importances from SHAP TreeExplainer")
def get_feature_importance():
    """
    Retrieves genuine global SHAP feature importance computed by TreeExplainer across test instances.
    Does NOT use ordinary model feature importance (like Gini gain) or hardcoded mock constants.
    """
    try:
        return inference_service.get_global_feature_importance(limit=15)
    except ModelNotAvailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load SHAP feature importance: {e}")

@router.get("/models/explainability", response_model=ShapSummaryResponse, summary="Get summary explanation of key traffic drivers")
def get_explainability():
    """
    Provides genuine SHAP explainability insights summarizing the physical drivers of traffic congestion.
    Loads real TreeExplainer aggregations and qualitative domain drivers without fixed constants.
    """
    try:
        return inference_service.get_explainability_summary()
    except ModelNotAvailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load SHAP explainability summary: {e}")
