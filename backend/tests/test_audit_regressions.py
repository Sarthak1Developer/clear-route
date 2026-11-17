import csv
import json
from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from backend.app.main import app
from backend.app.database.session import Base, get_db
from backend.app.services.inference_service import InferenceService, inference_service, ModelNotAvailableError
from ml.inference.predict import TrafficInferenceEngine
from ml.preprocessing.preprocessor import TrafficDataPreprocessor

client = TestClient(app)
BASE = {"city":"Delhi", "location_id":"DEL_001", "prediction_date":"2026-11-17", "prediction_time":"18:00"}

@pytest.mark.parametrize("change", [{"prediction_time":"24:00"},{"prediction_time":"18:90"},{"prediction_date":"bad","prediction_time":None},{"city":"Mumbai"},{"hour":4},{"day_of_week":0}])
def test_reject_inconsistent_scenario(change):
    assert client.post('/api/predict', json={**BASE, **change}).status_code == 400

@pytest.mark.parametrize("url", ['/api/data/records?start_date=bad','/api/locations/DEL_001/history?end_date=bad','/api/weather/history?start_date=2019-12-31&end_date=2019-01-01'])
def test_reject_bad_date_filters(url):
    assert client.get(url).status_code == 422

@pytest.mark.parametrize("key", ['historical_mean','linear_regression','random_forest','xgboost'])
def test_missing_artifacts_fail_closed(tmp_path, key):
    engine=TrafficInferenceEngine(tmp_path)
    with pytest.raises(ModelNotAvailableError):
        engine.predict(key, {"city":"Delhi","location_id":"DEL_001"})

@pytest.mark.parametrize("key", ['random_forest','xgboost'])
def test_missing_tree_explainer_never_substitutes_another_model(monkeypatch, key):
    monkeypatch.delitem(inference_service.shap_explainers,key)
    result=inference_service.explain_prediction({"city":"Delhi","location_id":"DEL_001","hour":18,"day_of_week":1},key)
    assert result['model_id']==key
    assert result['feature_contributions']==[]
    assert result['base_value'] is None

def test_historical_mean_does_not_invent_attributions():
    result=client.post('/api/predict',json={**BASE,'model_type':'historical_mean'}).json()
    assert result['shap_attributions']==[]
    assert result['confidence_interval'] is None

def test_stored_explanation_matches_original_scenario():
    result=client.post('/api/predict',json={**BASE,'humidity_pct':92,'road_lanes':8,'lag_speed_1h':11}).json()
    saved=client.get(f"/api/predictions/{result['prediction_id']}/explain").json()
    assert saved['feature_values']==result['input_features']
    assert saved['feature_contributions']==result['feature_contributions']
    assert saved['predicted_congestion']==result['predicted_congestion_pct']

def test_performance_chart_uses_exported_observations():
    result=client.get('/api/models/performance').json()
    with open('powerbi/exports/model_actual_vs_predicted.csv',newline='') as stream:
        row=next(csv.DictReader(stream))
    assert result['actual_vs_predicted'][0]['actual']==float(row['actual_congestion_pct'])
    assert result['actual_vs_predicted'][0]['predicted']==float(row['pred_xgboost'])

def test_end_date_includes_whole_day():
    result=client.get('/api/locations/DEL_001/history?start_date=2019-12-30&end_date=2019-12-30&limit=1000').json()
    assert result['total_records_available']>0
    assert any(row['timestamp'][11:13]!='00' for row in result['sample_records'])

def test_timestamp_groups_are_disjoint():
    frame=pd.DataFrame({'timestamp':pd.date_range('2019-01-01',periods=11,freq='h').repeat(7)})
    train,val,test=TrafficDataPreprocessor().chronological_split(frame)
    assert train.timestamp.max()<val.timestamp.min()<test.timestamp.min()
    assert val.timestamp.max()<test.timestamp.min()
    assert len(train)+len(val)+len(test)==len(frame)

def test_cors_rejects_unlisted_origin():
    result=client.options('/api/predict',headers={'Origin':'https://untrusted.example','Access-Control-Request-Method':'POST'})
    assert result.status_code==400
    assert 'access-control-allow-origin' not in result.headers

def test_unknown_export_is_404():
    assert client.get('/api/reports/export/unknown').status_code==404

def test_empty_database_health_and_analytics(tmp_path):
    engine=create_engine(f'sqlite:///{tmp_path / "empty.db"}',connect_args={'check_same_thread':False})
    Base.metadata.create_all(engine)
    def empty_db():
        with Session(engine) as session: yield session
    app.dependency_overrides[get_db]=empty_db
    try:
        assert client.get('/api/overview').json()['total_records_processed']==0
        assert client.get('/api/data/records').json()['records']==[]
        assert client.get('/api/data/coverage').json()['start_date']==''
        quality=client.get('/api/data/quality').json()
        assert quality['completeness_rate']==0
        assert 'GPS telemetry' in quality['validation_status']
    finally:
        app.dependency_overrides.clear()
        engine.dispose()

def test_production_pipeline_rejects_demonstration_before_writing():
    from bigdata.spark_jobs.run_pipeline import run_complete_pipeline
    with pytest.raises(RuntimeError,match='demonstration'):
        run_complete_pipeline()
