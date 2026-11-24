import React,{useEffect,useState} from 'react';
import {api} from '../../services/api';
export const HistoricalFilters=({city,value,onChange,hideCorridor=false})=>{
 const [locations,setLocations]=useState([]),[draft,setDraft]=useState(value),[error,setError]=useState('');
 useEffect(()=>{setDraft(value);setError('');},[value]);
 useEffect(()=>{let active=true;setLocations([]);api.getCityLocations(city).then(r=>active&&setLocations(r.locations)).catch(()=>{});return()=>{active=false;};},[city]);
 const field='bg-slate-900 border border-slate-700 rounded px-2 py-2 min-w-0 max-w-full';
 const apply=()=>{if(draft.start_date&&draft.end_date&&draft.start_date>draft.end_date){setError('From must be on or before To.');return;}setError('');onChange({...draft});};
 return <div className="space-y-2"><div className="flex flex-wrap gap-3 items-end text-xs">
  {!hideCorridor&&<label className="min-w-0">Corridor traffic <select aria-label="Historical corridor" className={field+' block w-full sm:max-w-xs'} value={draft.location_id||''} onChange={e=>setDraft({...draft,location_id:e.target.value})}><option value="">All city corridors</option>{locations.map(l=><option key={l.location_code} value={l.location_code}>{l.location_name}</option>)}</select></label>}
  <label>From <input aria-label="Historical start date" type="date" className={field+' block'} value={draft.start_date||''} onInput={e=>{const value=e.currentTarget.value;setDraft(previous=>({...previous,start_date:value}));}} onChange={e=>{const value=e.currentTarget.value;setDraft(previous=>({...previous,start_date:value}));}}/></label>
  <label>To <input aria-label="Historical end date" type="date" className={field+' block'} value={draft.end_date||''} onInput={e=>{const value=e.currentTarget.value;setDraft(previous=>({...previous,end_date:value}));}} onChange={e=>{const value=e.currentTarget.value;setDraft(previous=>({...previous,end_date:value}));}}/></label>
  <button type="button" className={field+' border-cyan-700 text-cyan-300'} onClick={apply}>Apply historical filters</button>
  <button type="button" className={field} onClick={()=>{setDraft({});setError('');onChange({});}}>Clear historical filters</button>
 </div><p className="text-xs text-slate-400">Historical traffic covers 1 Apr–31 Dec 2019. Edit the range, then select Apply. Dates outside coverage return no observations.</p>{error&&<p role="alert" className="text-xs text-rose-300">{error}</p>}</div>;
};
