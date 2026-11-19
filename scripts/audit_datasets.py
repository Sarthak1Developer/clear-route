"""Inspect dataset files without modifying them; write machine-readable evidence."""
import argparse,gc,hashlib,json,sqlite3
from pathlib import Path
import pandas as pd

def inspect_file(path,root):
    item={'file':str(path.relative_to(root)).replace('\\','/'),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_status':'NOT VERIFIED: source attribution does not establish observational truth'}
    if path.suffix=='.db':
        with sqlite3.connect(f'file:{path.resolve().as_posix()}?mode=ro',uri=True) as db:
            item['integrity']=db.execute('pragma integrity_check').fetchall();item['foreign_key_violations']=db.execute('pragma foreign_key_check').fetchall()
            item['tables']={t:db.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0] for (t,) in db.execute("select name from sqlite_master where type='table'")}
        return item
    frame=pd.read_parquet(path) if path.suffix=='.parquet' else pd.read_csv(path,low_memory=False)
    item.update(records=len(frame),columns=len(frame.columns),schema={c:str(t) for c,t in frame.dtypes.items()},missing_values={c:int(n) for c,n in frame.isna().sum().items() if n},duplicate_rows=int(frame.duplicated().sum()))
    for col in ['city','location_id','location_code','latitude','longitude']:
        if col in frame:item[col+'_coverage']=sorted(map(str,frame[col].dropna().unique().tolist()))
    for col in ['timestamp','date','event_date']:
        if col in frame:
            dates=pd.to_datetime(frame[col],errors='coerce');item[col+'_range']=[str(dates.min()),str(dates.max())];item[col+'_invalid']=int(dates.isna().sum())
    keys=[c for c in ['location_id','timestamp'] if c in frame]
    if len(keys)==2:item['duplicate_corridor_timestamps']=int(frame.duplicated(keys).sum())
    item['units']={c:('percent' if 'pct' in c or 'percentage' in c else 'km/h' if 'kmh' in c or 'speed' in c else 'mm/hour' if 'precip' in c else 'C' if 'temperature' in c else 'metres' if 'length_m' in c else 'identifier/time/category or documented in dictionary') for c in frame}
    del frame;gc.collect();return item

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',default='.');parser.add_argument('--output',required=True);args=parser.parse_args();root=Path(args.root).resolve()
    files=sorted({p for folder in ['data','powerbi/exports'] for p in (root/folder).rglob('*') if p.suffix in {'.csv','.parquet','.db'} and p.is_file()})
    rows=[]
    for path in files:
        try:rows.append(inspect_file(path,root))
        except Exception as e:rows.append({'file':str(path.relative_to(root)),'status':'FAILED','error':type(e).__name__+': '+str(e)})
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(rows,indent=2),encoding='utf-8');print(f'Inspected {len(rows)} datasets; {sum("error" in r for r in rows)} unreadable')
