"""Create a NEW application database reconciled to the checked-in Gold dataset.
Never mutates or replaces the source database. Weather/event source truth is unverified.
"""
import argparse
import hashlib
import json
import os
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def build_database(output, gold=ROOT/'data/gold/master_congestion/gold_master_congestion.parquet', metadata_db=ROOT/'data/clearroute_app.db'):
    output, gold, metadata_db = map(lambda p: Path(p).resolve(), (output, gold, metadata_db))
    if output.exists() or output.with_suffix(".manifest.json").exists() or output == metadata_db:
        raise FileExistsError('Refusing to overwrite an existing database; choose a new output path.')
    frame = pd.read_parquet(gold)
    required = ['location_id','city','timestamp','observed_speed_kmh','free_flow_speed_kmh','congestion_percentage']
    if frame[required].isna().any().any() or frame.duplicated(['location_id','timestamp']).any():
        raise ValueError('Gold has null keys/measurements or duplicate location timestamps.')
    expected = ((frame.free_flow_speed_kmh-frame.observed_speed_kmh)/frame.free_flow_speed_kmh).clip(0,1)*100
    if (frame.free_flow_speed_kmh <= 0).any() or not np.allclose(expected, frame.congestion_percentage, atol=.011):
        raise ValueError('Gold target is inconsistent with speed-derived congestion percentage.')
    frame['timestamp'] = pd.to_datetime(frame.timestamp)
    weather_cols = ['temperature_2m_c','precipitation_mm','relative_humidity_2m_pct','wind_speed_10m_kmh']
    if (frame.groupby(['city','timestamp'])[weather_cols].nunique(dropna=False)>1).any().any():
        raise ValueError('Conflicting city-hour weather across corridors; cannot deduplicate safely.')
    archive=ROOT/'data/external/era5_2019/weather.parquet'
    archive_manifest=json.loads(archive.with_name('manifest.json').read_text(encoding='utf-8'))
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=archive_manifest['parquet_sha256']:
        raise ValueError('Weather archive checksum mismatch; refusing to import unverified contents.')
    verified_weather=pd.read_parquet(archive)
    verified_weather['timestamp']=pd.to_datetime(verified_weather.timestamp)
    if verified_weather.duplicated(['city','timestamp']).any() or verified_weather.isna().any().any():
        raise ValueError('Weather archive has duplicate keys or missing observations.')
    keys=frame[['city','timestamp']].drop_duplicates()
    if len(keys.merge(verified_weather[['city','timestamp']],on=['city','timestamp'],validate='one_to_one'))!=len(keys):
        raise ValueError('Weather archive does not cover all Gold city-hour keys.')
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_name(output.stem+".building-"+uuid.uuid4().hex+".db")
    if temporary.exists():raise FileExistsError("An incomplete build already exists; choose a new output path and preserve that file.")
    source_hash = hashlib.sha256(metadata_db.read_bytes()).hexdigest()
    with closing(sqlite3.connect(f'file:{metadata_db.as_posix()}?mode=ro',uri=True)) as src, closing(sqlite3.connect(temporary)) as db:
        src.backup(db)
        db.execute('PRAGMA foreign_keys=ON')
        # These deletes affect only the newly-created copy, never metadata_db.
        for table in ['predictions','traffic_records','weather_records','events']:
            db.execute(f'DELETE FROM {table}')
        cities = dict(db.execute('SELECT city_name,id FROM cities'))
        locations = dict(db.execute('SELECT location_code,id FROM locations'))
        if set(frame.city)-set(cities) or set(frame.location_id)-set(locations):
            raise ValueError('Gold contains unknown city/corridor identifiers.')
        for code, group in frame.groupby('location_id'):
            row=group.iloc[0]
            db.execute('UPDATE locations SET location_name=?,latitude=?,longitude=?,road_type=?,road_lanes=?,free_flow_speed_kmh=?,accident_risk_score=? WHERE location_code=?',tuple(row[k].item() if hasattr(row[k],'item') else row[k] for k in ['location_name','latitude','longitude','road_type','road_lanes','free_flow_speed_kmh','accident_risk_score'])+(code,))
        traffic=pd.DataFrame({
            'location_id':frame.location_id.map(locations),'timestamp':frame.timestamp.dt.strftime('%Y-%m-%d %H:%M:%S.%f'),
            'hour':frame.timestamp.dt.hour,'day_of_week':frame.timestamp.dt.day_of_week,'month':frame.timestamp.dt.month,
            'is_weekend':(frame.timestamp.dt.day_of_week>=5).astype(int),'is_peak_hour':frame.is_peak_hour.astype(int),
            'observed_speed_kmh':frame.observed_speed_kmh,'free_flow_speed_kmh':frame.free_flow_speed_kmh,
            'congestion_percentage':frame.congestion_percentage,'congestion_category':frame.congestion_category})
        traffic.to_sql('traffic_records',db,if_exists='append',index=False,chunksize=2000)
        weather=verified_weather[['city','timestamp']+weather_cols].copy()
        weather['city_id']=weather.city.map(cities);weather['timestamp']=weather.timestamp.dt.strftime('%Y-%m-%d %H:%M:%S.%f')
        weather=weather.rename(columns=dict(zip(weather_cols,['temperature_c','precipitation_mm','humidity_pct','wind_speed_kmh'])))
        weather.drop(columns=['city']).to_sql('weather_records',db,if_exists='append',index=False,chunksize=2000)
        event_rows=frame[frame.event_present==1].assign(event_date=frame.timestamp.dt.strftime('%Y-%m-%d')).drop_duplicates(['city','event_date','event_name'])
        events=pd.DataFrame({'city_id':event_rows.city.map(cities),'event_name':event_rows.event_name,'event_type':event_rows.event_type,'event_date':event_rows.event_date,'is_2026_future':0,'source_attribution':'Gold dataset event annotation; provenance, venue and duration unverified'})
        events.to_sql('events',db,if_exists='append',index=False)
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS uq_traffic_location_timestamp ON traffic_records(location_id,timestamp)')
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS uq_weather_city_timestamp ON weather_records(city_id,timestamp)')
        db.execute('CREATE INDEX IF NOT EXISTS ix_events_city_date ON events(city_id,event_date)')
        metrics=json.loads((ROOT/'ml/artifacts/metrics.json').read_text())
        for key,m in metrics['models'].items():
            db.execute('UPDATE model_metadata SET mae=?,rmse=?,r2_score=?,is_primary=?,total_test_samples=? WHERE model_key=?',(m['mae'],m['rmse'],m['r2'],int(key==metrics['best_model']),metrics['total_test_samples'],key))
        manifest={'gold_sha256':hashlib.sha256(gold.read_bytes()).hexdigest(),'source_metadata_db_sha256':source_hash,'traffic_rows':len(traffic),'weather_source':archive_manifest,'weather_rows':len(weather),'event_rows':len(events),'target_formula':'clip((free_flow_speed_kmh-observed_speed_kmh)/free_flow_speed_kmh,0,1)*100','provenance':'Existing Gold benchmark; external sensor/weather/event provenance not independently verified','city_means':frame.groupby('city').congestion_percentage.mean().to_dict()}
        db.execute('CREATE TABLE IF NOT EXISTS analytics_manifest (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)')
        db.execute('INSERT INTO analytics_manifest VALUES (1,?)',(json.dumps(manifest),))
        if db.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Foreign key reconciliation failed')
        actual=db.execute('SELECT count(*),avg(congestion_percentage) FROM traffic_records').fetchone()
        assert actual[0]==len(frame) and abs(actual[1]-frame.congestion_percentage.mean())<1e-8
        db.commit()
    assert hashlib.sha256(metadata_db.read_bytes()).hexdigest()==source_hash,'Source database changed concurrently'
    if os.name=="nt":
        os.rename(temporary,output)  # Windows rename refuses existing destinations.
    else:
        os.link(temporary,output)  # POSIX link refuses existing destinations.
        temporary.unlink()
    output.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True);parser.add_argument('--gold',default=str(ROOT/'data/gold/master_congestion/gold_master_congestion.parquet'));parser.add_argument('--metadata-db',default=str(ROOT/'data/clearroute_app.db'))
    args=parser.parse_args();print(json.dumps(build_database(args.output,args.gold,args.metadata_db),indent=2))
