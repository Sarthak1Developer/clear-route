import React, {useEffect, useState} from 'react';
import {useApp} from '../context/AppContext';
import {api} from '../services/api';
import {Card} from '../components/common/Card';
import {LoadingSpinner} from '../components/common/LoadingSpinner';
import {BarChart,Bar,ResponsiveContainer,XAxis,YAxis,Tooltip,CartesianGrid} from 'recharts';

const MODELS=[['xgboost','XGBoost'],['random_forest','Random Forest'],['linear_regression','Linear Regression'],['historical_mean','Historical Mean']];
const number=(value,digits=2)=>Number.isFinite(value)?value.toFixed(digits):'Unavailable';
const inputClass='w-full min-w-0 rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-slate-100';
export const CongestionPrediction=()=>{
  const {cities,selectedCity,setSelectedCity}=useApp();
  const [locations,setLocations]=useState([]);
  const [form,setForm]=useState({location_id:'',prediction_date:new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Kolkata',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date()),hour:18,temperature_c:28,precipitation_mm:0,humidity_pct:65,wind_speed_kmh:12,event_present:false,event_name:''});
  const [result,setResult]=useState(null),[error,setError]=useState(null),[loading,setLoading]=useState(false),[locationLoading,setLocationLoading]=useState(false);
  useEffect(()=>{
    let current=true;setResult(null);setError(null);setLocations([]);setLocationLoading(true);
    setForm(f=>({...f,location_id:''}));
    api.getCityLocations(selectedCity.name).then(data=>{if(current){setLocations(data.locations);setForm(f=>({...f,location_id:data.locations[0]?.location_code||''}));}}).catch(e=>current&&setError(e.message)).finally(()=>current&&setLocationLoading(false));
    return()=>{current=false;};
  },[selectedCity.name]);
  const change=(name,value)=>{setForm(f=>({...f,[name]:value}));setResult(null);};
  async function predict(event){
    event.preventDefault();setLoading(true);setError(null);setResult(null);
    const {hour,...fields}=form;
    try{setResult(await api.compareCongestionModels({...fields,city:selectedCity.name,prediction_time:`${String(hour).padStart(2,'0')}:00`,event_name:form.event_present?form.event_name:null}));}
    catch(e){setError(e.message);}finally{setLoading(false);}
  }
  const predictions=(result?.results||[]).filter(r=>r.status==='success').map(r=>({model:MODELS.find(m=>m[0]===r.model)?.[1]||r.model,value:r.result.predicted_congestion_pct}));
  const spread=predictions.length>1?Math.max(...predictions.map(r=>r.value))-Math.min(...predictions.map(r=>r.value)):null;
  return <div className="space-y-6">
    <header><h1 className="text-2xl font-bold">Congestion Prediction — Four-Model Comparison</h1><p className="text-sm text-slate-400 mt-2">One hypothetical scenario, four existing estimators. Benchmark accuracy does not establish real-world forecasting validity.</p></header>
    <Card title="Scenario parameters" subtitle="Time is IST. Weather and event values below are hypothetical inputs, not retrieved observations.">
      <form onSubmit={predict} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <label className="text-xs space-y-2"><span>City</span><select aria-label="Prediction city" className={inputClass} value={selectedCity.code} onChange={e=>setSelectedCity(cities.find(c=>c.code===e.target.value))}>{cities.map(c=><option key={c.code} value={c.code}>{c.name}</option>)}</select></label>
          <label className="text-xs space-y-2"><span>Road corridor</span><select aria-label="Road corridor" className={inputClass} required disabled={locationLoading} value={form.location_id} onChange={e=>change('location_id',e.target.value)}><option value="">{locationLoading?'Loading corridors…':'Select corridor'}</option>{locations.map(l=><option key={l.location_code} value={l.location_code}>{l.location_name} — {l.corridor_name}</option>)}</select></label>
          <label className="text-xs space-y-2"><span>Date</span><input aria-label="Prediction date" type="date" required className={inputClass} value={form.prediction_date} onChange={e=>change('prediction_date',e.target.value)}/></label>
          <label className="text-xs space-y-2"><span>Hour (IST)</span><select aria-label="Prediction hour" className={inputClass} value={form.hour} onChange={e=>change('hour',Number(e.target.value))}>{Array.from({length:24},(_,h)=><option key={h} value={h}>{String(h).padStart(2,'0')}:00</option>)}</select></label>
          {[['precipitation_mm','Rainfall (mm/hour)',0,150],['temperature_c','Temperature (C)',-20,60],['humidity_pct','Humidity (%)',0,100],['wind_speed_kmh','Wind speed (km/h)',0,150]].map(([name,label,min,max])=><label key={name} className="text-xs space-y-2"><span>{label}</span><input type="number" required step="0.1" min={min} max={max} className={inputClass} value={form[name]} onChange={e=>change(name,Number(e.target.value))}/></label>)}
        </div>
        <label className="flex gap-2 text-sm"><input type="checkbox" checked={form.event_present} onChange={e=>change('event_present',e.target.checked)}/>Hypothetical event or assembly</label>
        {form.event_present&&<label className="block text-xs">Event information (optional)<input className={inputClass} value={form.event_name} onChange={e=>change('event_name',e.target.value)} placeholder="Describe your hypothetical event"/></label>}
        <button disabled={loading||locationLoading||!form.location_id} className="rounded-lg px-5 py-3 bg-cyan-600 text-slate-950 font-semibold disabled:opacity-50">{loading?'Running all four models…':'Predict Congestion Using All 4 Models'}</button>
      </form>
    </Card>
    {error&&<div role="alert" className="p-4 rounded-lg border border-rose-800 bg-rose-950/30 text-rose-200">{error}</div>}
    {loading&&<LoadingSpinner label="Validating one scenario and running all four estimators…"/>}
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      {MODELS.map(([key,name])=>{const item=result?.results?.find(r=>r.model===key),data=item?.result,m=item?.metrics;return <Card key={key} title={name} subtitle={item?`Status: ${item.status}`:'Awaiting scenario'}>
        <p className="text-3xl font-mono text-cyan-300">{data?`${number(data.predicted_congestion_pct,1)}%`:'—'}</p>
        <p className="text-xs text-slate-400 mt-2">{item?`Model ${item.available?'loaded':'unavailable'}`:'Model availability checked on prediction'}</p>
        {item?.error&&<p role="alert" className="text-xs text-rose-300 mt-2">{item.error}</p>}
        {m&&<p className="text-xs text-slate-400 mt-3">Held-out MAE {number(m.mae)} · RMSE {number(m.rmse)} · R² {number(m.r2,4)}</p>}
        {data&&<><p className="text-xs text-slate-400 mt-2">{item.explanation_available?'Model-specific contributions available':'Explanation unavailable for this model.'}</p><details className="mt-3 text-xs"><summary className="cursor-pointer text-cyan-300">Advanced model diagnostics</summary><p className="mt-2">{data.explanation_summary}</p>{data.base_value!=null&&<p className="mt-2">Explanation baseline: {number(data.base_value)}%. Reconstruction check: {data.additive_check?.is_consistent?'passed':'unavailable'}.</p>}{data.feature_contributions?.length>0&&<ul className="mt-2 space-y-1">{data.feature_contributions.slice(0,8).map(c=><li key={c.feature}>{c.display_name}: {c.attribution_value>0?'+':''}{number(c.attribution_value)} percentage points</li>)}</ul>}<p className="mt-2">{key==='linear_regression'?'Exact coefficient decomposition, not tree SHAP.':key==='historical_mean'?'Historical mean does not model weather or event interventions.':'TreeExplainer for this estimator.'}</p><p className="mt-2">Prediction ID {data.prediction_id}; executed {data.timestamp}.</p></details></>}
      </Card>;})}
    </div>
    {result&&<Card title="Side-by-side comparison" subtitle={`${result.models_succeeded} of 4 models succeeded. Prediction spread: ${number(spread)} percentage points.`}>
      {predictions.length>0?<div className="h-72 min-w-0"><ResponsiveContainer width="100%" height="100%"><BarChart data={predictions} margin={{bottom:30,left:0,right:10}}><CartesianGrid stroke="#1F2937"/><XAxis dataKey="model" tick={{fontSize:10}} interval={0}/><YAxis domain={[0,100]} unit="%"/><Tooltip/><Bar dataKey="value" name="Predicted congestion (%)" fill="#06B6D4"/></BarChart></ResponsiveContainer></div>:<p>No valid model outputs.</p>}
      <p className="text-xs text-slate-400">Best stored benchmark: {result.best_model_by_held_out_metrics||'Unavailable'}. All metrics refer to the existing chronological benchmark, not verified sensor-data forecast accuracy. SHAP describes model associations, not causal effects.</p>
    </Card>}
  </div>;
};
