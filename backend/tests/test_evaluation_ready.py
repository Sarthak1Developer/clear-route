"""Regression checks against the real, checked-in Gold corpus and a new database."""
import hashlib
from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from backend.app.main import app
from backend.app.database.session import get_db
from scripts.build_analytics_database import build_database

@pytest.fixture(scope='module')
def canonical(tmp_path_factory):
    path=tmp_path_factory.mktemp('canonical')/'analytics.db'
    before=hashlib.sha256(Path('data/clearroute_app.db').read_bytes()).hexdigest()
    manifest=build_database(path)
    assert hashlib.sha256(Path('data/clearroute_app.db').read_bytes()).hexdigest()==before
    engine=create_engine(f'sqlite:///{path.as_posix()}',connect_args={'check_same_thread':False})
    def get_session():
        with Session(engine) as session:yield session
    app.dependency_overrides[get_db]=get_session
    with TestClient(app) as client:yield client,manifest
    app.dependency_overrides.clear();engine.dispose()

def test_independent_five_city_metrics_match_gold(canonical):
    client,manifest=canonical
    values=[]
    for city,expected in manifest['city_means'].items():
        actual=client.get('/api/overview',params={'city':city}).json()
        assert actual['total_records_processed']==33000
        assert abs(actual['avg_congestion_pct']-expected)<.0051
        values.append(actual['avg_congestion_pct'])
    assert len(set(values))==5

def test_all_corridors_and_date_filters_match_gold(canonical):
    client,_=canonical
    gold=pd.read_parquet('data/gold/master_congestion/gold_master_congestion.parquet')
    for code,rows in gold.groupby('location_id'):
        result=client.get('/api/analytics/profile',params={'location':code}).json()
        assert result['sample_count']==6600
        assert abs(result['mean']-rows.congestion_percentage.mean())<.0051
        assert result['minimum']==rows.congestion_percentage.min()
        assert result['maximum']==rows.congestion_percentage.max()
    result=client.get('/api/analytics/profile?city=Delhi&start_date=2019-04-01&end_date=2019-04-01').json()
    assert result['sample_count']==120
    assert len(result['daily'])==1
    missing=client.get('/api/analytics/profile?city=Delhi&start_date=2030-01-01').json()
    assert missing['mean'] is None and missing['status']=='unavailable'

def test_weather_empty_is_not_zero(canonical):
    client,_=canonical
    result=client.get('/api/weather/impact?city=Delhi&start_date=2030-01-01').json()
    assert result['sample_count']==0
    assert result['heavy_rain_surge'] is None
    assert result['rain_correlation'] is None
    assert all(b['avg_congestion'] is None for b in result['rain_bands'])

def test_four_models_identical_features_and_real_failure(canonical,monkeypatch):
    from backend.app.services.inference_service import inference_service
    client,_=canonical
    request={'city':'Delhi','location_id':'DEL_001','prediction_date':'2026-11-18','prediction_time':'18:00','precipitation_mm':10,'event_present':True}
    response=client.post('/api/predict/compare',json=request)
    assert response.status_code==200
    result=response.json();assert result['models_succeeded']==4
    features=[x['result']['input_features'] for x in result['results']]
    assert all(f==features[0] for f in features)
    assert features[0]['length_m']==2400
    monkeypatch.delitem(inference_service.models,'random_forest')
    partial=client.post('/api/predict/compare',json=request).json()
    assert partial['models_succeeded']==3
    assert next(x for x in partial['results'] if x['model']=='random_forest')['status']=='unavailable'
    assert client.post('/api/predict/compare',json={**request,'location_id':'INVALID'}).status_code==404

def test_sorted_paginated_records(canonical):
    client,_=canonical
    result=client.get('/api/data/records?city=Delhi&start_date=2019-04-01&end_date=2019-04-01&sort=congestion_desc&page_size=10').json()
    assert result['total']==120
    numbers=[r['congestion_percentage'] for r in result['records']]
    assert numbers==sorted(numbers,reverse=True)
    assert client.get('/api/data/records?sort=invalid').status_code==422

def test_database_builder_never_overwrites(canonical,tmp_path):
    target=tmp_path/'existing.db';target.write_bytes(b'preserve me')
    with pytest.raises(FileExistsError):build_database(target)
    assert target.read_bytes()==b'preserve me'

def test_event_window_observations_use_actual_days(canonical):
    client,_=canonical
    event=client.get('/api/events?city=Delhi').json()['events'][0]
    result=client.get(f"/api/events/{event['id']}/observations").json()
    assert result['status']=='available'
    assert len(result['windows'])==3
    assert all(row['sample_count']==120 for row in result['windows'])
    assert result['causal_effect_established'] is False
    assert 'start/end' in result['resolution']

def test_profile_rejects_mixed_city_corridor(canonical):
    client,_=canonical
    assert client.get('/api/analytics/profile?city=Mumbai&location=DEL_001').status_code==400
    assert client.get('/api/events?city=Mumbai&location_id=DEL_001').status_code==400
    assert client.get('/api/weather/impact?city=Mumbai&location_id=DEL_001').status_code==400


def test_health_counts_the_active_database(canonical):
    client,_=canonical
    result=client.get('/api/health').json()
    assert result['records_count']==165000
    assert len(result['models_loaded'])==4
