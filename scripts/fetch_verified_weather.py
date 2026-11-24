"""Fetch a versioned ERA5 archive; refuses existing output and never simulates data.
The committed April–December 2019 snapshot includes the exact compressed API response.
"""
import argparse,datetime,gzip,hashlib,json,urllib.parse,urllib.request
from pathlib import Path
import pandas as pd
CITIES={'Delhi':(28.6139,77.2090),'Mumbai':(19.0760,72.8777),'Bengaluru':(12.9716,77.5946),'Hyderabad':(17.3850,78.4867),'Kolkata':(22.5726,88.3639)}

def fetch_archive(output,start='2019-04-01',end='2019-12-31'):
    output=Path(output)
    if output.exists():raise FileExistsError('Choose a new output directory; existing archive preserved.')
    params={'latitude':','.join(str(v[0]) for v in CITIES.values()),'longitude':','.join(str(v[1]) for v in CITIES.values()),'start_date':start,'end_date':end,'hourly':'temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m','timezone':'Asia/Kolkata','models':'era5'}
    url='https://archive-api.open-meteo.com/v1/archive?'+urllib.parse.urlencode(params)
    with urllib.request.urlopen(url,timeout=45) as response:raw=response.read()
    payload=json.loads(raw)
    if not isinstance(payload,list) or len(payload)!=len(CITIES):raise ValueError('Missing city responses')
    frames=[]
    expected=pd.date_range(start,pd.Timestamp(end)+pd.Timedelta(hours=23),freq='h')
    for city,record in zip(CITIES,payload):
        if record.get('timezone')!='Asia/Kolkata' or record.get('utc_offset_seconds')!=19800:raise ValueError('Unexpected timezone')
        hourly=record['hourly']
        frame=pd.DataFrame({'city':city,'timestamp':pd.to_datetime(hourly['time']),'temperature_2m_c':hourly['temperature_2m'],'precipitation_mm':hourly['precipitation'],'relative_humidity_2m_pct':hourly['relative_humidity_2m'],'wind_speed_10m_kmh':hourly['wind_speed_10m']})
        if not pd.DatetimeIndex(frame.timestamp).equals(expected) or frame.isna().any().any():raise ValueError('Incomplete hourly coverage')
        frames.append(frame)
    frame=pd.concat(frames,ignore_index=True)
    output.mkdir(parents=True,exist_ok=False)
    frame.to_parquet(output/'weather.parquet',index=False)
    (output/'response.json.gz').write_bytes(gzip.compress(raw,mtime=0))
    manifest={'url':url,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_name':'Open-Meteo Historical Weather API / ERA5','provenance_type':'genuine_external_api','models':'era5','timezone':'Asia/Kolkata','license':'CC BY 4.0','attribution_url':'https://open-meteo.com/en/docs/historical-weather-api','rows':len(frame),'cities':list(CITIES),'start_date':start,'end_date':end,'parquet_sha256':hashlib.sha256((output/'weather.parquet').read_bytes()).hexdigest(),'raw_response_sha256':hashlib.sha256(raw).hexdigest(),'returned_grid_coordinates':[{'city':city,'latitude':record['latitude'],'longitude':record['longitude']} for city,record in zip(CITIES,payload)]}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);args=parser.parse_args()
    print(json.dumps(fetch_archive(args.output),indent=2))
