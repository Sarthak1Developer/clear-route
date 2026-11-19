"""Safe local launcher: build the separate Gold-reconciled store, then serve."""
import argparse,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8000);parser.add_argument('--host',default='127.0.0.1');args=parser.parse_args()
    from scripts.build_analytics_database import build_database
    database=ROOT/'data/clearroute_analytics_v2.db'
    if not database.exists():build_database(database)
    manifest=database.with_suffix('.manifest.json')
    if not manifest.exists():raise RuntimeError('Missing analytical manifest. Choose a new database output and rebuild safely.')
    import hashlib
    build=json.loads(manifest.read_text())
    expected=build['gold_sha256']
    weather=ROOT/'data/external/era5_2019/weather.parquet'
    if hashlib.sha256(weather.read_bytes()).hexdigest()!=build.get('weather_source',{}).get('parquet_sha256'):
        raise RuntimeError('Weather archive changed since database build. Create a new versioned store; existing data was preserved.')
    if hashlib.sha256((ROOT/'data/gold/master_congestion/gold_master_congestion.parquet').read_bytes()).hexdigest()!=expected:
        raise RuntimeError('Gold changed since database build. Create a new versioned analytical store; existing data was preserved.')
    os.environ['DATABASE_URL']='sqlite:///'+database.as_posix()
    import uvicorn
    uvicorn.run('backend.app.main:app',host=args.host,port=args.port)
