"""Source status attached to the active database, not inferred from a catalog label."""
import json
from sqlalchemy import inspect,text

def weather_source(db):
    if inspect(db.get_bind()).has_table('analytics_manifest'):
        row=db.execute(text('SELECT payload FROM analytics_manifest WHERE id=1')).scalar()
        if row:
            source=json.loads(row).get('weather_source',{})
            if source.get('provenance_type')=='genuine_external_api':
                return {'label':'Open-Meteo Historical Weather API / ERA5 (retrieval and checksum recorded)','verified':True,'kind':'reanalysis','retrieved_utc':source.get('retrieved_utc')}
    return {'label':'Gold weather annotations (external provenance unverified)','verified':False,'kind':'benchmark_context'}
