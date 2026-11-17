"""
ClearRoute Machine Learning Model Training & Comprehensive Validation Pipeline

Implements and benchmarks the 4 finalized models:
1. Historical Mean Baseline (Spatio-Temporal Segment Lookup)
2. Linear Regression (Ridge Regularized with Validation Tuning)
3. Random Forest Regressor (Multi-Tree Bagging Ensemble)
4. XGBoost Regressor (Gradient Boosted Decision Trees)

Features:
- Strict chronological 70% train, 15% validation, 15% test partitioning (zero leakage)
- Hyperparameter tuning using validation partition only
- Full held-out test evaluation: MAE, RMSE, R2
- Comprehensive residual diagnostics & skewness analysis
- Subgroup performance slices (by city and traffic condition)
- Matplotlib visual diagnostics (actual vs predicted, residuals, city breakdowns)
- SHAP TreeExplainer attributions
- Serialization of reproducible artifacts, metrics, and environment configurations
"""

import os
import sys
import json
import logging
import platform
import datetime
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt

# Ensure root directory in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from ml.preprocessing.preprocessor import TrafficDataPreprocessor
from ml.models.historical_mean import HistoricalMeanBaseline
from ml.models.linear_regression import LinearRegressionModel
from ml.models.random_forest import RandomForestModel
from ml.models.xgboost_model import XGBoostModel
from ml.evaluation.evaluator import ModelEvaluator
from ml.explainability.shap_explainer import TrafficShapExplainer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger("clearroute.ml.train")

RANDOM_SEED = 42

def record_environment_metadata(artifacts_dir: str, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame):
    """Records package versions, system specs, dataset version, and split bounds."""
    import sklearn
    import xgboost
    import shap

    config = {
        "training_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "random_seed": RANDOM_SEED,
        "environment": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "numpy_version": np.__version__,
            "pandas_version": pd.__version__,
            "scikit_learn_version": sklearn.__version__,
            "xgboost_version": xgboost.__version__,
            "shap_version": shap.__version__,
            "joblib_version": joblib.__version__,
            "matplotlib_version": matplotlib.__version__,
        },
        "dataset_split_chronology": {
            "train_samples": len(train_df),
            "train_period": f"{train_df['timestamp'].min()} to {train_df['timestamp'].max()}",
            "val_samples": len(val_df),
            "val_period": f"{val_df['timestamp'].min()} to {val_df['timestamp'].max()}",
            "test_samples": len(test_df),
            "test_period": f"{test_df['timestamp'].min()} to {test_df['timestamp'].max()}",
            "total_samples": len(train_df) + len(val_df) + len(test_df),
        },
        "target_variable": "congestion_percentage",
        "evaluation_partition": "Strictly Held-Out 15% Chronological Test Set",
    }

    config_path = os.path.join(artifacts_dir, "training_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    logger.info(f"Training configuration and environment metadata saved to {config_path}")
    return config

def plot_actual_vs_predicted(predictions_dict: dict, y_test: np.ndarray, plots_dir: str):
    """Generates a 2x2 multi-panel diagnostic plot of Actual vs Predicted congestion."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12), facecolor="#0A0F1D")
    palette = {"historical_mean": "#F59E0B", "linear_regression": "#3B82F6", "random_forest": "#10B981", "xgboost": "#06B6D4"}

    # Subsample 1,000 test points for clean visual rendering
    rng = np.random.default_rng(RANDOM_SEED)
    plot_idx = rng.choice(len(y_test), size=min(1200, len(y_test)), replace=False)
    y_sub = y_test[plot_idx]

    model_keys = ["historical_mean", "linear_regression", "random_forest", "xgboost"]
    for idx, (m_key, ax) in enumerate(zip(model_keys, axes.flatten())):
        y_p = predictions_dict[m_key][plot_idx]
        color = palette.get(m_key, "#06B6D4")

        ax.set_facecolor("#111827")
        ax.scatter(y_sub, y_p, alpha=0.35, color=color, s=18, edgecolors="none", label="Predictions")
        
        # 45-degree reference line
        min_v = 0.0
        max_v = max(float(y_sub.max()), float(y_p.max())) + 5.0
        ax.plot([min_v, max_v], [min_v, max_v], color="#EF4444", linestyle="--", linewidth=1.5, label="Ideal 1:1 Identity")

        ax.set_title(m_key.replace("_", " ").title(), color="#F9FAFB", fontsize=13, fontweight="bold", pad=10)
        ax.set_xlabel("Actual Congestion (%)", color="#9CA3AF", fontsize=10)
        ax.set_ylabel("Predicted Congestion (%)", color="#9CA3AF", fontsize=10)
        ax.tick_params(colors="#9CA3AF")
        ax.grid(True, color="#1F2937", linestyle=":", alpha=0.6)
        ax.legend(facecolor="#111827", edgecolor="#374151", labelcolor="#F9FAFB", fontsize=9)

    plt.suptitle("ClearRoute Held-Out Test Set: Actual vs. Predicted Congestion (%)", color="#F9FAFB", fontsize=16, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    out_path = os.path.join(plots_dir, "actual_vs_predicted.png")
    plt.savefig(out_path, dpi=200, facecolor=fig.get_facecolor())
    plt.close()
    logger.info(f"Diagnostic plot saved: {out_path}")

def plot_residual_distributions(predictions_dict: dict, y_test: np.ndarray, plots_dir: str):
    """Generates a 2x2 residual histogram with zero-error reference line."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), facecolor="#0A0F1D")
    palette = {"historical_mean": "#F59E0B", "linear_regression": "#3B82F6", "random_forest": "#10B981", "xgboost": "#06B6D4"}

    model_keys = ["historical_mean", "linear_regression", "random_forest", "xgboost"]
    for m_key, ax in zip(model_keys, axes.flatten()):
        residuals = y_test - predictions_dict[m_key]
        color = palette.get(m_key, "#06B6D4")

        ax.set_facecolor("#111827")
        ax.hist(residuals, bins=50, color=color, alpha=0.75, edgecolor="#1F2937", density=True)
        ax.axvline(0, color="#EF4444", linestyle="--", linewidth=1.5, label="Zero Bias (Residual = 0)")

        ax.set_title(f"{m_key.replace('_', ' ').title()} Residuals (y - ŷ)", color="#F9FAFB", fontsize=12, fontweight="bold")
        ax.set_xlabel("Residual Error (% Congestion)", color="#9CA3AF", fontsize=10)
        ax.set_ylabel("Probability Density", color="#9CA3AF", fontsize=10)
        ax.tick_params(colors="#9CA3AF")
        ax.grid(True, color="#1F2937", linestyle=":", alpha=0.6)
        ax.legend(facecolor="#111827", edgecolor="#374151", labelcolor="#F9FAFB", fontsize=9)

    plt.suptitle("ClearRoute Test Set Residual Error Distributions", color="#F9FAFB", fontsize=15, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    out_path = os.path.join(plots_dir, "residual_distributions.png")
    plt.savefig(out_path, dpi=200, facecolor=fig.get_facecolor())
    plt.close()
    logger.info(f"Residual plot saved: {out_path}")

def plot_subgroup_metrics(city_evals: dict, condition_evals: dict, plots_dir: str):
    """Generates comparative charts across cities and conditions."""
    # Plot 1: City Breakdown
    fig, ax = plt.subplots(figsize=(10, 6), facecolor="#0A0F1D")
    ax.set_facecolor("#111827")
    
    cities = sorted(list(city_evals["xgboost"].keys()))
    x = np.arange(len(cities))
    width = 0.2

    palette = [("#F59E0B", "Historical Mean"), ("#3B82F6", "Linear Regression"), ("#10B981", "Random Forest"), ("#06B6D4", "XGBoost")]
    model_keys = ["historical_mean", "linear_regression", "random_forest", "xgboost"]

    for i, (m_key, (col, lbl)) in enumerate(zip(model_keys, palette)):
        maes = [city_evals[m_key][c]["mae"] for c in cities]
        ax.bar(x + (i - 1.5) * width, maes, width, label=lbl, color=col, alpha=0.9, edgecolor="#1F2937")

    ax.set_ylabel("Mean Absolute Error (% Congestion)", color="#F9FAFB", fontsize=11)
    ax.set_title("Test MAE Performance by Metropolitan City", color="#F9FAFB", fontsize=14, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(cities, color="#F9FAFB", fontsize=11)
    ax.tick_params(colors="#9CA3AF")
    ax.grid(True, color="#1F2937", linestyle=":", alpha=0.6)
    ax.legend(facecolor="#111827", edgecolor="#374151", labelcolor="#F9FAFB")

    plt.tight_layout()
    city_out = os.path.join(plots_dir, "performance_by_city.png")
    plt.savefig(city_out, dpi=200, facecolor=fig.get_facecolor())
    plt.close()

    # Plot 2: Traffic Condition Breakdown
    fig, ax = plt.subplots(figsize=(12, 7), facecolor="#0A0F1D")
    ax.set_facecolor("#111827")

    conds = list(condition_evals["xgboost"].keys())
    x = np.arange(len(conds))
    width = 0.2

    for i, (m_key, (col, lbl)) in enumerate(zip(model_keys, palette)):
        maes = [condition_evals[m_key][c]["mae"] for c in conds]
        ax.barh(x + (i - 1.5) * width, maes, width, label=lbl, color=col, alpha=0.9, edgecolor="#1F2937")

    ax.set_xlabel("Mean Absolute Error (% Congestion)", color="#F9FAFB", fontsize=11)
    ax.set_title("Model MAE Across Traffic, Weather & Congestion Slices", color="#F9FAFB", fontsize=14, fontweight="bold", pad=12)
    ax.set_yticks(x)
    ax.set_yticklabels(conds, color="#F9FAFB", fontsize=10)
    ax.tick_params(colors="#9CA3AF")
    ax.grid(True, color="#1F2937", linestyle=":", alpha=0.6)
    ax.legend(facecolor="#111827", edgecolor="#374151", labelcolor="#F9FAFB")

    plt.tight_layout()
    cond_out = os.path.join(plots_dir, "performance_by_traffic_condition.png")
    plt.savefig(cond_out, dpi=200, facecolor=fig.get_facecolor())
    plt.close()
    logger.info(f"Subgroup comparative plots saved: {city_out}, {cond_out}")

def train_and_validate_all_models(
    gold_parquet_path: str = "data/gold/master_congestion/gold_master_congestion.parquet",
    artifacts_dir: str = "ml/artifacts"
) -> dict:
    """Executes the complete machine learning training and evaluation pipeline."""
    os.makedirs(artifacts_dir, exist_ok=True)
    plots_dir = os.path.join(artifacts_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    logger.info("================================================================")
    logger.info("STARTING FOUR-MODEL TRAINING PIPELINE (CHRONOLOGICAL SPLIT 70/15/15)")
    logger.info("================================================================")

    # 1. Load Gold Dataset
    if not os.path.exists(gold_parquet_path):
        raise FileNotFoundError(f"Gold dataset missing at {gold_parquet_path}. Run pipeline first.")
    df = pd.read_parquet(gold_parquet_path)
    logger.info(f"Loaded Gold analytical dataset: {len(df):,} rows x {len(df.columns)} columns.")

    # 2. Chronological Splitting (70% Train, 15% Val, 15% Test)
    preprocessor = TrafficDataPreprocessor()
    train_df, val_df, test_df = preprocessor.chronological_split(df, train_ratio=0.70, val_ratio=0.15)
    logger.info(f"Chronological Splits:")
    logger.info(f"  - Train Split (70%): {len(train_df):,} samples ({train_df['timestamp'].min()} to {train_df['timestamp'].max()})")
    logger.info(f"  - Val Split   (15%): {len(val_df):,} samples ({val_df['timestamp'].min()} to {val_df['timestamp'].max()})")
    logger.info(f"  - Test Split  (15%): {len(test_df):,} samples ({test_df['timestamp'].min()} to {test_df['timestamp'].max()})")

    # Record training environment metadata
    record_environment_metadata(artifacts_dir, train_df, val_df, test_df)

    # 3. Fit Preprocessing Strictly on Training Data
    X_train, y_train = preprocessor.fit_transform(train_df)
    X_val, y_val = preprocessor.transform(val_df)
    X_test, y_test = preprocessor.transform(test_df)
    preprocessor.save(os.path.join(artifacts_dir, "preprocessor.joblib"))
    logger.info(f"Fitted preprocessing pipeline serialized ({len(preprocessor.feature_names)} features).")

    # Storage for predictions & evaluations
    predictions = {}
    eval_summaries = {}
    city_evals = {}
    condition_evals = {}
    residuals_diagnostics = {}

    # =========================================================================
    # Model 1: Historical Mean Baseline
    # =========================================================================
    logger.info(">>> Training Model 1: Historical Mean Baseline (Lookup Engine)...")
    m1 = HistoricalMeanBaseline()
    m1.fit(train_df)
    m1_pred = m1.predict(test_df)
    m1_eval = ModelEvaluator.evaluate(y_test, m1_pred)
    m1.save(os.path.join(artifacts_dir, "model_historical_mean.joblib"))

    predictions["historical_mean"] = m1_pred
    eval_summaries["historical_mean"] = {
        "name": "Historical Mean Baseline",
        "family": "Spatio-Temporal Segment Lookup",
        "role": "Statistical Baseline",
        "mae": m1_eval["mae"],
        "rmse": m1_eval["rmse"],
        "r2": m1_eval["r2"],
        "is_primary": False,
    }
    residuals_diagnostics["historical_mean"] = m1_eval["residuals"]
    city_evals["historical_mean"] = ModelEvaluator.evaluate_by_city(test_df, y_test, m1_pred)
    condition_evals["historical_mean"] = ModelEvaluator.evaluate_by_condition(test_df, y_test, m1_pred)
    logger.info(f"Model 1 Test Results: MAE={m1_eval['mae']}%, RMSE={m1_eval['rmse']}, R2={m1_eval['r2']}")

    # =========================================================================
    # Model 2: Linear Regression (Ridge)
    # =========================================================================
    logger.info(">>> Training Model 2: Linear Regression (Ridge Regularized with Val Tuning)...")
    m2 = LinearRegressionModel()
    m2.tune_and_fit(X_train, y_train, X_val, y_val)
    m2_pred = m2.predict(X_test)
    m2_eval = ModelEvaluator.evaluate(y_test, m2_pred)
    m2.save(os.path.join(artifacts_dir, "model_linear_regression.joblib"))

    predictions["linear_regression"] = m2_pred
    eval_summaries["linear_regression"] = {
        "name": "Linear Regression (Ridge)",
        "family": "Regularized Parametric Estimator",
        "role": "Interpretable Baseline",
        "mae": m2_eval["mae"],
        "rmse": m2_eval["rmse"],
        "r2": m2_eval["r2"],
        "tuned_alpha": m2.alpha,
        "is_primary": False,
    }
    residuals_diagnostics["linear_regression"] = m2_eval["residuals"]
    city_evals["linear_regression"] = ModelEvaluator.evaluate_by_city(test_df, y_test, m2_pred)
    condition_evals["linear_regression"] = ModelEvaluator.evaluate_by_condition(test_df, y_test, m2_pred)
    logger.info(f"Model 2 Test Results: MAE={m2_eval['mae']}%, RMSE={m2_eval['rmse']}, R2={m2_eval['r2']} (alpha={m2.alpha})")

    # =========================================================================
    # Model 3: Random Forest Regressor
    # =========================================================================
    logger.info(">>> Training Model 3: Random Forest Regressor (Bagging Trees, Low-RAM Subsampling)...")
    # Subsample 35,000 training points for rapid fitting and lightweight serialization
    rng = np.random.default_rng(RANDOM_SEED)
    rf_sub_idx = rng.choice(len(X_train), size=min(35000, len(X_train)), replace=False)
    m3 = RandomForestModel(n_estimators=50, max_depth=10, random_state=RANDOM_SEED)
    m3.fit(X_train[rf_sub_idx], y_train[rf_sub_idx])
    m3_pred = m3.predict(X_test)
    m3_eval = ModelEvaluator.evaluate(y_test, m3_pred)
    m3.save(os.path.join(artifacts_dir, "model_random_forest.joblib"))

    predictions["random_forest"] = m3_pred
    eval_summaries["random_forest"] = {
        "name": "Random Forest Regressor",
        "family": "Multi-Tree Bagging Ensemble",
        "role": "Non-linear Ensemble",
        "mae": m3_eval["mae"],
        "rmse": m3_eval["rmse"],
        "r2": m3_eval["r2"],
        "is_primary": False,
    }
    residuals_diagnostics["random_forest"] = m3_eval["residuals"]
    city_evals["random_forest"] = ModelEvaluator.evaluate_by_city(test_df, y_test, m3_pred)
    condition_evals["random_forest"] = ModelEvaluator.evaluate_by_condition(test_df, y_test, m3_pred)
    logger.info(f"Model 3 Test Results: MAE={m3_eval['mae']}%, RMSE={m3_eval['rmse']}, R2={m3_eval['r2']}")

    # =========================================================================
    # Model 4: XGBoost Regressor
    # =========================================================================
    logger.info(">>> Training Model 4: XGBoost Regressor (Gradient Boosted Trees with Early Stopping)...")
    m4 = XGBoostModel(n_estimators=120, learning_rate=0.06, max_depth=6, random_state=RANDOM_SEED)
    m4.fit(X_train, y_train, eval_set=[(X_val, y_val)])
    m4_pred = m4.predict(X_test)
    m4_eval = ModelEvaluator.evaluate(y_test, m4_pred)
    m4.save(os.path.join(artifacts_dir, "model_xgboost.joblib"))

    predictions["xgboost"] = m4_pred
    eval_summaries["xgboost"] = {
        "name": "XGBoost Regressor",
        "family": "Gradient Boosted Trees",
        "role": "Primary Forecasting Model",
        "mae": m4_eval["mae"],
        "rmse": m4_eval["rmse"],
        "r2": m4_eval["r2"],
        "is_primary": False,
    }
    residuals_diagnostics["xgboost"] = m4_eval["residuals"]
    city_evals["xgboost"] = ModelEvaluator.evaluate_by_city(test_df, y_test, m4_pred)
    condition_evals["xgboost"] = ModelEvaluator.evaluate_by_condition(test_df, y_test, m4_pred)
    logger.info(f"Model 4 Test Results: MAE={m4_eval['mae']}%, RMSE={m4_eval['rmse']}, R2={m4_eval['r2']}")

    # =========================================================================
    # Genuine Model Selection (Highest R2 and lowest MAE on unobserved test split)
    # =========================================================================
    validation_predictions = {
        "historical_mean": m1.predict(val_df),
        "linear_regression": m2.predict(X_val),
        "random_forest": m3.predict(X_val),
        "xgboost": m4.predict(X_val),
    }
    validation_scores = {key: ModelEvaluator.evaluate(y_val, pred)
                         for key, pred in validation_predictions.items()}
    ranked_models = sorted(validation_scores,
        key=lambda key: (validation_scores[key]["r2"], -validation_scores[key]["mae"]), reverse=True)
    best_model_key = ranked_models[0]
    eval_summaries[best_model_key]["is_primary"] = True
    logger.info(f"CHAMPION MODEL SELECTED: {eval_summaries[best_model_key]['name']} (R2={eval_summaries[best_model_key]['r2']}, MAE={eval_summaries[best_model_key]['mae']}%)")

    # =========================================================================
    # Save Residual & Subgroup Performance Artifacts
    # =========================================================================
    res_path = os.path.join(artifacts_dir, "residual_analysis.json")
    with open(res_path, "w") as f:
        json.dump(residuals_diagnostics, f, indent=2)

    sub_path = os.path.join(artifacts_dir, "subgroup_performance.json")
    with open(sub_path, "w") as f:
        json.dump({"by_city": city_evals, "by_traffic_condition": condition_evals}, f, indent=2)

    # =========================================================================
    # SHAP Explainability on Best / Primary Model
    # =========================================================================
    logger.info(">>> Computing SHAP TreeExplainer Attributions on Held-Out Test Set...")
    try:
        chosen_tree_model = m4.model if hasattr(m4, "model") else m3.model
        explainer = TrafficShapExplainer(chosen_tree_model, preprocessor.feature_names)
        shap_sample = X_test[:250]
        global_importance = explainer.compute_global_importance(shap_sample)
        with open(os.path.join(artifacts_dir, "shap_summary.json"), "w") as f:
            json.dump({"global_importance": global_importance, "base_value": explainer.base_value}, f, indent=2)
        logger.info(f"SHAP summary computed ({len(global_importance)} features).")
    except Exception as e:
        logger.warning(f"Could not compute SHAP values directly: {e}")

    # =========================================================================
    # Feature Importance Artifact (Tabular Feature Rankings)
    # =========================================================================
    feature_imp_path = os.path.join(artifacts_dir, "feature_importance.json")
    feature_importance_dict = {
        "feature_names": preprocessor.feature_names,
        "ridge_coefficients": m2.get_coefficients(preprocessor.feature_names),
        "random_forest_importances": dict(zip(preprocessor.feature_names, [round(float(v), 5) for v in m3.get_feature_importances()])),
        "xgboost_importances": dict(zip(preprocessor.feature_names, [round(float(v), 5) for v in m4.get_feature_importances()])),
    }
    with open(feature_imp_path, "w") as f:
        json.dump(feature_importance_dict, f, indent=2)

    # =========================================================================
    # Save Metrics JSON
    # =========================================================================
    metrics_path = os.path.join(artifacts_dir, "metrics.json")
    output_meta = {
        "evaluation_partition": "Held-Out Chronological Test Set (15%)",
        "total_test_samples": len(test_df),
        "best_model": best_model_key,
        "selection_partition": "Chronological validation set; test used only for final metrics",
        "models": eval_summaries
    }
    with open(metrics_path, "w") as f:
        json.dump(output_meta, f, indent=2)
    logger.info(f"Reconciled genuine metrics saved to {metrics_path}")

    # =========================================================================
    # Visual Plots Generation
    # =========================================================================
    logger.info(">>> Generating Visual Diagnostic Plots...")
    plot_actual_vs_predicted(predictions, y_test, plots_dir)
    plot_residual_distributions(predictions, y_test, plots_dir)
    plot_subgroup_metrics(city_evals, condition_evals, plots_dir)

    logger.info("================================================================")
    logger.info("MODEL BENCHMARK SUMMARY (HELD-OUT 15% TEST SPLIT):")
    for k, v in eval_summaries.items():
        logger.info(f"[{k.upper():<18}] MAE: {v['mae']:>5}% | RMSE: {v['rmse']:>5} | R2: {v['r2']:>6} | Primary: {v['is_primary']}")
    logger.info("================================================================")

    return output_meta

if __name__ == "__main__":
    train_and_validate_all_models()
