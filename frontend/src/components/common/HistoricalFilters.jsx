import React,{useEffect,useState} from 'react';
import {api} from '../../services/api';
export const HistoricalFilters=({city,value,onChange,hideCorridor=false})=>{
 const [locations,setLocations]=useState([]);
 useEffect(()=>{let active=true;setLocations([]);api.getCityLocations(city).then(r=>active&&setLocations(r.locations)).catch(()=>{});return()=>{active=false;};},[city]);
 const field='bg-slate-900 border border-slate-700 rounded px-2 py-2 min-w-0 max-w-full';
 return <div className="flex flex-wrap gap-3 items-end text-xs">
  {!hideCorridor&&<label className="min-w-0">Corridor traffic <select aria-label="Historical corridor" className={field+' block w-full sm:max-w-xs'} value={value.location_id||''} onChange={e=>onChange({...value,location_id:e.target.value})}><option value="">All city corridors</option>{locations.map(l=><option key={l.location_code} value={l.location_code}>{l.location_name}</option>)}</select></label>}
  <label>From <input aria-label="Historical start date" type="date" className={field+' block'} value={value.start_date||''} onChange={e=>onChange({...value,start_date:e.target.value})}/></label>
  <label>To <input aria-label="Historical end date" type="date" className={field+' block'} value={value.end_date||''} onChange={e=>onChange({...value,end_date:e.target.value})}/></label>
  <button className={field} onClick={()=>onChange({})}>Clear historical filters</button>
 </div>;
};
