import os
import sys
import json
import logging
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from ml.preprocessing.preprocessor import TrafficDataPreprocessor
from ml.models.historical_mean import HistoricalMeanBaseline
from ml.models.linear_regression import LinearRegressionModel
from ml.models.random_forest import RandomForestModel
from ml.models.xgboost_model import XGBoostModel
from ml.evaluation.evaluator import ModelEvaluator
from ml.explainability.shap_explainer import TrafficShapExplainer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger("train_all_models")

def train_and_evaluate(
    gold_parquet_path: str = "data/gold/master_congestion/gold_master_congestion.parquet",
    artifacts_dir: str = "ml/artifacts"
):
    os.makedirs(artifacts_dir, exist_ok=True)
    logger.info("================================================================")
    logger.info("STARTING FOUR-MODEL TRAINING PIPELINE (CHRONOLOGICAL SPLIT 70/15/15)")
    logger.info("================================================================")

    # 1. Load Gold Dataset
    df = pd.read_parquet(gold_parquet_path)
    logger.info(f"Loaded Gold analytical dataset ({len(df)} rows, {len(df.columns)} columns).")

    # 2. Chronological Train / Val / Test Split
    preprocessor = TrafficDataPreprocessor()
    train_df, val_df, test_df = preprocessor.chronological_split(df, train_ratio=0.70, val_ratio=0.15)
    logger.info(f"Split completed: Train={len(train_df)}, Validation={len(val_df)}, Test={len(test_df)}")

    # 3. Fit Preprocessing Transformers on Train Only
    X_train, y_train = preprocessor.fit_transform(train_df)
    X_val, y_val = preprocessor.transform(val_df)
    X_test, y_test = preprocessor.transform(test_df)
    preprocessor.save(os.path.join(artifacts_dir, "preprocessor.joblib"))
    logger.info("Preprocessing transformers serialized to ml/artifacts/preprocessor.joblib")

    results = {}

    # 4. Model 1: Historical Mean Baseline
    logger.info(">>> Training Model 1: Historical Mean Baseline...")
    m1 = HistoricalMeanBaseline()
    m1.fit(train_df)
    m1_test_preds = m1.predict(test_df)
    m1_eval = ModelEvaluator.evaluate(y_test, m1_test_preds)
    m1.save(os.path.join(artifacts_dir, "model_historical_mean.joblib"))
    results["historical_mean"] = {
        "name": "Historical Mean Baseline",
        "family": "Spatio-Temporal Segment Lookup",
        "role": "Statistical Baseline",
        **m1_eval,
        "is_primary": False
    }
    logger.info(f"Model 1 Test Results: MAE={m1_eval['mae']}%, RMSE={m1_eval['rmse']}, R2={m1_eval['r2']}")

    # 5. Model 2: Linear Regression (Ridge)
    logger.info(">>> Training Model 2: Linear Regression (Ridge Regularized)...")
    m2 = LinearRegressionModel(alpha=1.0)
    m2.fit(X_train, y_train)
    m2_test_preds = m2.predict(X_test)
    m2_eval = ModelEvaluator.evaluate(y_test, m2_test_preds)
    m2.save(os.path.join(artifacts_dir, "model_linear_regression.joblib"))
    results["linear_regression"] = {
        "name": "Linear Regression (Ridge)",
        "family": "Regularized Parametric Estimator",
        "role": "Interpretable Baseline",
        **m2_eval,
        "is_primary": False
    }
    logger.info(f"Model 2 Test Results: MAE={m2_eval['mae']}%, RMSE={m2_eval['rmse']}, R2={m2_eval['r2']}")

    # 6. Model 3: Random Forest Regressor
    logger.info(">>> Training Model 3: Random Forest Regressor...")
    m3 = RandomForestModel(n_estimators=100, max_depth=12, random_state=42)
    m3.fit(X_train, y_train)
    m3_test_preds = m3.predict(X_test)
    m3_eval = ModelEvaluator.evaluate(y_test, m3_test_preds)
    m3.save(os.path.join(artifacts_dir, "model_random_forest.joblib"))
    results["random_forest"] = {
        "name": "Random Forest Regressor",
        "family": "Multi-Tree Bagging Ensemble",
        "role": "Non-linear Ensemble",
        **m3_eval,
        "is_primary": False
    }
    logger.info(f"Model 3 Test Results: MAE={m3_eval['mae']}%, RMSE={m3_eval['rmse']}, R2={m3_eval['r2']}")

    # 7. Model 4: XGBoost Regressor (Primary Model)
    logger.info(">>> Training Model 4: XGBoost Regressor (Primary)...")
    m4 = XGBoostModel(n_estimators=150, learning_rate=0.05, max_depth=6, random_state=42)
    m4.fit(X_train, y_train, eval_set=[(X_val, y_val)])
    m4_test_preds = m4.predict(X_test)
    m4_eval = ModelEvaluator.evaluate(y_test, m4_test_preds)
    m4.save(os.path.join(artifacts_dir, "model_xgboost.joblib"))
    results["xgboost"] = {
        "name": "XGBoost Regressor",
        "family": "Gradient Boosted Trees",
        "role": "Primary Forecasting Model",
        **m4_eval,
        "is_primary": True
    }
    logger.info(f"Model 4 Test Results: MAE={m4_eval['mae']}%, RMSE={m4_eval['rmse']}, R2={m4_eval['r2']}")

    # 8. SHAP Explainability on Primary XGBoost Model
    logger.info(">>> Computing SHAP TreeExplainer Attributions on Held-Out Test Set...")
    try:
        explainer = TrafficShapExplainer(m4.model, preprocessor.feature_names)
        shap_sample = X_test[:100]
        global_importance = explainer.compute_global_importance(shap_sample)
        explainer.save_summary(global_importance, os.path.join(artifacts_dir, "shap_summary.json"))
    except Exception as e:
        logger.warning(f"Could not compute SHAP values directly: {e}")

    # 9. Save Evaluation Metrics JSON
    metrics_path = os.path.join(artifacts_dir, "metrics.json")
    best_key = max(results.keys(), key=lambda k: results[k]["r2"])
    output_meta = {
        "evaluation_partition": "Held-Out Chronological Test Set (15%)",
        "total_test_samples": len(test_df),
        "best_model": best_key,
        "models": results
    }
    with open(metrics_path, "w") as f:
        json.dump(output_meta, f, indent=2)
    logger.info(f"Model evaluation summary saved to {metrics_path}")

    logger.info("================================================================")
    logger.info("MODEL BENCHMARK SUMMARY (HELD-OUT 15% TEST SET):")
    for k, v in results.items():
        logger.info(f"[{k.upper():<18}] MAE: {v['mae']:>5}% | RMSE: {v['rmse']:>5} | R2: {v['r2']:>6}")
    logger.info(f"CHAMPION MODEL IDENTIFIED: {results[best_key]['name']} (R2={results[best_key]['r2']})")
    logger.info("================================================================")

if __name__ == "__main__":
    train_and_evaluate()
