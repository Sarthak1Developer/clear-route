import React,{useEffect,useState} from 'react';
import {api} from '../../services/api';
import {HistoricalFilters} from './HistoricalFilters';
import {Card,MetricCard} from './Card';
import {ResponsiveContainer,LineChart,Line,XAxis,YAxis,Tooltip,CartesianGrid} from 'recharts';
export const HistoricalProfile=({city,location,showMonthly=false})=>{
 const [filters,setFilters]=useState({}),[data,setData]=useState(null),[error,setError]=useState(null),[loading,setLoading]=useState(false);
 useEffect(()=>{setFilters({});},[city]);
 useEffect(()=>{let active=true;setLoading(true);setError(null);api.getProfile({...filters,city,location:location||filters.location_id}).then(r=>active&&setData(r)).catch(e=>active&&setError(e.message)).finally(()=>active&&setLoading(false));return()=>{active=false;};},[city,location,filters]);
 const n=v=>Number.isFinite(v)?v.toFixed(2)+'%':'Unavailable';
 return <Card title="Filtered historical statistics" subtitle="Independent corridor/city statistics from the current analytical database; unverified real-world provenance.">
  <HistoricalFilters city={city} value={filters} onChange={setFilters} hideCorridor={!!location}/>
  {error?<p role="alert" className="text-rose-300 mt-3">{error}</p>:loading?<p role="status" className="mt-3">Loading filtered records…</p>:data&&<>
   <p className="text-xs text-slate-400 mt-3">{data.sample_count.toLocaleString()} observations{location?` for ${location}`:''}. {data.status==='unavailable'?'Insufficient observations for this filter.':''}</p>
   <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 mt-3">{[['Mean',data.mean],['Median',data.median],['Minimum',data.minimum],['Maximum',data.maximum],['Weekday mean',data.weekday_mean],['Weekend mean',data.weekend_mean]].map(([label,value])=><MetricCard key={label} title={label} value={n(value)}/>)}</div>
   {data.daily.length>0&&<div className="mt-5"><h4 className="text-sm mb-3">Daily mean congestion</h4><div className="h-56"><ResponsiveContainer width="100%" height="100%"><LineChart data={data.daily}><CartesianGrid stroke="#1f2937"/><XAxis dataKey="key" tick={{fontSize:9}} minTickGap={40}/><YAxis domain={[0,100]} unit="%"/><Tooltip/><Line dataKey="avg_congestion" stroke="#06b6d4" dot={false}/></LineChart></ResponsiveContainer></div></div>}
   {showMonthly&&data.monthly.length>0&&<div className="mt-5"><h4 className="text-sm mb-3">Monthly mean congestion</h4><div className="h-56"><ResponsiveContainer width="100%" height="100%"><LineChart data={data.monthly}><XAxis dataKey="key"/><YAxis domain={[0,100]} unit="%"/><Tooltip/><Line dataKey="avg_congestion" stroke="#a78bfa"/></LineChart></ResponsiveContainer></div></div>}
  </>}
 </Card>;
};
