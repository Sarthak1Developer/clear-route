import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import { Card, MetricCard } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { CongestionBadge } from '../components/common/Badge';
import {
  BarChart, Bar, ResponsiveContainer, XAxis, YAxis,
  CartesianGrid, Tooltip, Cell, ReferenceLine
} from 'recharts';
import {
  Sparkles, Calendar, Clock, CloudRain, Wind,
  Thermometer, MapPin, Gauge, AlertTriangle, ArrowRight,
  TrendingUp, HelpCircle, Layers, CheckCircle2
} from 'lucide-react';

export const CongestionPrediction = () => {
  const { cities, selectedCity, setSelectedCity, showToast } = useApp();
  const [locations, setLocations] = useState([]);
  const [selectedLocationId, setSelectedLocationId] = useState('');
  const [loadingLocations, setLoadingLocations] = useState(false);

  // Form Inputs
  const [predictionDate, setPredictionDate] = useState('2026-11-05');
  const [predictionHour, setPredictionHour] = useState(18); // 18:00 IST
  const [modelType, setModelType] = useState('xgboost'); // historical_mean, linear_regression, random_forest, xgboost
  const [temperature, setTemperature] = useState(28.0);
  const [precipitation, setPrecipitation] = useState(12.5);
  const [humidity, setHumidity] = useState(75.0);
  const [windSpeed, setWindSpeed] = useState(14.0);
  const [eventPresent, setEventPresent] = useState(true);
  const [eventName, setEventName] = useState('Major Cultural & Commercial Assembly');

  // Prediction Output State
  const [predicting, setPredicting] = useState(false);
  const [predictionResult, setPredictionResult] = useState(null);
  const [predictionError, setPredictionError] = useState(null);

  // Fetch locations when city changes
  useEffect(() => {
    let isMounted = true;
    async function loadCityLocations() {
      try {
        setLoadingLocations(true);
        const res = await api.getCityLocations(selectedCity.name);
        const locs = res.locations || [];
        if (isMounted) {
          setLocations(locs);
          if (locs.length > 0) {
            setSelectedLocationId(locs[0].location_code || locs[0].id);
          }
        }
      } catch (err) {
        console.error('Error fetching city locations:', err);
      } finally {
        if (isMounted) setLoadingLocations(false);
      }
    }
    loadCityLocations();
    return () => { isMounted = false; };
  }, [selectedCity]);

  // Handle Predict Submission
  const handlePredict = async (e) => {
    e.preventDefault();
    if (!selectedLocationId) {
      showToast('Please select a corridor for prediction', 'error');
      return;
    }

    try {
      setPredicting(true);
      setPredictionError(null);

      const payload = {
        city: selectedCity.name,
        location_id: selectedLocationId,
        prediction_date: predictionDate,
        prediction_time: `${String(predictionHour).padStart(2, '0')}:00`,
        model_type: modelType,
        temperature_c: Number(temperature),
        precipitation_mm: Number(precipitation),
        humidity_pct: Number(humidity),
        wind_speed_kmh: Number(windSpeed),
        event_present: Boolean(eventPresent),
        event_name: eventPresent ? eventName : '',
      };

      const result = await api.predictCongestion(payload);
      setPredictionResult(result);
      showToast('Prediction inference completed successfully', 'success');
    } catch (err) {
      setPredictionError(err.message);
      showToast(err.message, 'error');
    } finally {
      setPredicting(false);
    }
  };

  const selectedLocObj = locations.find((l) => (l.location_code || l.id) == selectedLocationId);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono uppercase text-cyan-400 font-semibold tracking-wider">Multi-Factor Inference</span>
            <span className="text-slate-600">•</span>
            <span className="text-xs text-slate-400">Independent 2026 Context Pipeline</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-cyan-400" />
            <span>Congestion Prediction & SHAP Attribution</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Simulate forward-looking 2026 scenarios using serialized ML estimators without retraining. Model explains feature contributions with SHAP TreeExplainer.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Prediction Input Form (5 cols) */}
        <div className="lg:col-span-5 bg-[#111827] border border-slate-800 rounded-xl p-5 shadow-lg">
          <h3 className="text-sm font-semibold text-slate-100 uppercase tracking-wider mb-4 pb-2 border-b border-slate-800 flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Scenario Parameters</span>
          </h3>

          <form onSubmit={handlePredict} className="space-y-4 text-xs">
            {/* City Selector */}
            <div>
              <label className="block text-slate-400 font-medium mb-1">Target Metropolitan City</label>
              <select
                value={selectedCity.code}
                onChange={(e) => {
                  const c = cities.find((ci) => ci.code === e.target.value);
                  if (c) setSelectedCity(c);
                }}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 font-medium"
              >
                {cities.map((c) => (
                  <option key={c.code} value={c.code}>{c.name} ({c.state})</option>
                ))}
              </select>
            </div>

            {/* Location Selector */}
            <div>
              <label className="block text-slate-400 font-medium mb-1">Supported Road Corridor</label>
              <select
                value={selectedLocationId}
                onChange={(e) => setSelectedLocationId(e.target.value)}
                disabled={loadingLocations || locations.length === 0}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 font-medium truncate"
              >
                {locations.map((loc) => (
                  <option key={loc.id || loc.location_code} value={loc.location_code || loc.id}>
                    {loc.location_name} ({loc.corridor_name})
                  </option>
                ))}
              </select>
            </div>

            {/* Date & Hour Row */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 font-medium mb-1 flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Date (2026 Context)</span>
                </label>
                <input
                  type="date"
                  value={predictionDate}
                  onChange={(e) => setPredictionDate(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Hour of Day (IST)</span>
                </label>
                <select
                  value={predictionHour}
                  onChange={(e) => setPredictionHour(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
                >
                  {Array.from({ length: 24 }).map((_, h) => (
                    <option key={h} value={h}>{String(h).padStart(2, '0')}:00 {h >= 8 && h <= 11 ? '(AM Peak)' : h >= 17 && h <= 21 ? '(PM Peak)' : ''}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Model Architecture Selector */}
            <div>
              <label className="block text-slate-400 font-medium mb-1 flex items-center justify-between">
                <span>Model Architecture</span>
                <span className="text-[10px] text-cyan-400 font-mono">Exactly 4 Approaches</span>
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'xgboost', label: 'XGBoost (Primary)', desc: 'Gradient Boosted Trees' },
                  { id: 'random_forest', label: 'Random Forest', desc: 'Non-linear Ensemble' },
                  { id: 'linear_regression', label: 'Linear Regression', desc: 'Interpretable Baseline' },
                  { id: 'historical_mean', label: 'Historical Mean', desc: 'Naive Statistical Baseline' },
                ].map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => setModelType(m.id)}
                    className={`p-2 rounded-lg border text-left transition-all ${
                      modelType === m.id
                        ? 'bg-cyan-950/40 border-cyan-500 text-cyan-200'
                        : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="font-semibold text-[11px] truncate">{m.label}</div>
                    <div className="text-[9px] text-slate-500 truncate">{m.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Weather Scenario Sliders */}
            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800 space-y-3">
              <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider block">
                Meteorological Scenario (Open-Meteo Inputs)
              </span>

              {/* Rain Slider */}
              <div>
                <div className="flex justify-between text-slate-400 text-[11px] mb-1">
                  <span className="flex items-center gap-1">
                    <CloudRain className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Rainfall / Precipitation</span>
                  </span>
                  <span className="font-mono text-cyan-300 font-bold">{precipitation} mm/hr</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="60"
                  step="0.5"
                  value={precipitation}
                  onChange={(e) => setPrecipitation(parseFloat(e.target.value))}
                  className="w-full accent-cyan-500"
                />
              </div>

              {/* Temperature Slider */}
              <div>
                <div className="flex justify-between text-slate-400 text-[11px] mb-1">
                  <span className="flex items-center gap-1">
                    <Thermometer className="w-3.5 h-3.5 text-amber-400" />
                    <span>Temperature</span>
                  </span>
                  <span className="font-mono text-amber-300 font-bold">{temperature}°C</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="48"
                  step="0.5"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full accent-amber-500"
                />
              </div>

              {/* Wind & Humidity Grid */}
              <div className="grid grid-cols-2 gap-2 pt-1 text-[11px]">
                <div>
                  <span className="text-slate-400 block mb-1">Humidity (%)</span>
                  <input
                    type="number"
                    min="10"
                    max="100"
                    value={humidity}
                    onChange={(e) => setHumidity(parseFloat(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 font-mono"
                  />
                </div>
                <div>
                  <span className="text-slate-400 block mb-1">Wind (km/h)</span>
                  <input
                    type="number"
                    min="0"
                    max="80"
                    value={windSpeed}
                    onChange={(e) => setWindSpeed(parseFloat(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Event Scenario Toggle */}
            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">
                  Major Event / Assembly
                </span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={eventPresent}
                    onChange={(e) => setEventPresent(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-8 h-4 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-cyan-500"></div>
                </label>
              </div>

              {eventPresent && (
                <input
                  type="text"
                  placeholder="Event name (e.g. Cricket Match / Durga Puja)..."
                  value={eventName}
                  onChange={(e) => setEventName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-100 placeholder-slate-500 text-[11px]"
                />
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={predicting}
              className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold py-3 px-4 rounded-xl text-xs flex items-center justify-center gap-2 transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50"
            >
              {predicting ? (
                <>
                  <LoadingSpinner className="p-0 !text-slate-950" label="" />
                  <span>Evaluating Serialized Model...</span>
                </>
              ) : (
                <>
                  <span>Calculate Congestion & SHAP Breakdown</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Prediction Results & SHAP Explanations (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {predicting ? (
            <div className="h-full flex items-center justify-center bg-[#111827] border border-slate-800 rounded-xl p-12">
              <LoadingSpinner label="Running tree-based inference and computing SHAP TreeExplainer local values..." />
            </div>
          ) : predictionError ? (
            <EmptyState
              title="Inference Error"
              message={predictionError}
              reason="Ensure backend is running and model artifacts are generated in ml/artifacts/."
            />
          ) : predictionResult ? (
            <>
              {/* Prediction Summary Header */}
              <div className="bg-[#111827] border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
                  <div>
                    <span className="text-[11px] font-mono text-cyan-400 uppercase tracking-wider font-semibold">
                      Forecast Result · {predictionResult.selected_model.toUpperCase()}
                    </span>
                    <h3 className="text-xl font-bold text-white mt-1">
                      {selectedLocObj?.location_name || 'Selected Corridor'}
                    </h3>
                    <p className="text-xs text-slate-400">
                      {predictionResult.prediction_date} at {predictionResult.prediction_time} IST
                    </p>
                  </div>

                  <div className="text-right">
                    <span className="text-3xl font-extrabold font-mono text-slate-50">
                      {predictionResult.predicted_congestion_pct.toFixed(1)}%
                    </span>
                    <div className="mt-1">
                      <CongestionBadge percentage={predictionResult.predicted_congestion_pct} />
                    </div>
                  </div>
                </div>

                {/* Historical Delta Comparison */}
                <div className="grid grid-cols-3 gap-3 mt-4 text-xs">
                  <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-bold">Predicted Index</span>
                    <p className="text-base font-bold text-slate-100 font-mono mt-0.5">
                      {predictionResult.predicted_congestion_pct.toFixed(1)}%
                    </p>
                  </div>
                  <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-bold">Historical Baseline</span>
                    <p className="text-base font-bold text-slate-400 font-mono mt-0.5">
                      {(predictionResult.historical_baseline_pct || 48.0).toFixed(1)}%
                    </p>
                  </div>
                  <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-bold">Scenario Delta</span>
                    <p
                      className={`text-base font-bold font-mono mt-0.5 ${
                        predictionResult.difference_pct >= 0 ? 'text-rose-400' : 'text-emerald-400'
                      }`}
                    >
                      {predictionResult.difference_pct >= 0 ? `+${predictionResult.difference_pct.toFixed(1)}%` : `${predictionResult.difference_pct.toFixed(1)}%`}
                    </p>
                  </div>
                </div>

                {/* Confidence Interval (if supported) */}
                {predictionResult.confidence_interval && (
                  <div className="mt-4 px-3 py-2 bg-slate-900/50 rounded-lg border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Empirical 95% Confidence Interval:</span>
                    </span>
                    <span className="font-mono text-slate-200">
                      [{predictionResult.confidence_interval.lower.toFixed(1)}% — {predictionResult.confidence_interval.upper.toFixed(1)}%]
                    </span>
                  </div>
                )}
              </div>

              {/* SHAP Feature Attribution Chart */}
              <Card
                title="SHAP Feature Attributions (Local Explainability)"
                subtitle="Quantifies how each input feature shifts the predicted congestion above (+) or below (-) the baseline"
              >
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      layout="vertical"
                      data={predictionResult.shap_attributions || []}
                      margin={{ top: 10, right: 30, left: 110, bottom: 10 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" horizontal={false} />
                      <XAxis type="number" stroke="#9CA3AF" tick={{ fontSize: 10 }} unit="%" />
                      <YAxis
                        type="category"
                        dataKey="feature"
                        stroke="#9CA3AF"
                        tick={{ fontSize: 10 }}
                      />
                      <Tooltip
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const d = payload[0].payload;
                            return (
                              <div className="bg-slate-900 border border-slate-700 p-2.5 rounded text-xs shadow-xl">
                                <p className="font-bold text-slate-100">{d.feature}</p>
                                <p className="text-slate-400">Value: <span className="font-mono text-slate-200">{d.value}</span></p>
                                <p className={`font-mono mt-1 ${d.impact_pct >= 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                                  SHAP Impact: {d.impact_pct > 0 ? `+${d.impact_pct.toFixed(2)}%` : `${d.impact_pct.toFixed(2)}%`}
                                </p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <ReferenceLine x={0} stroke="#6B7280" />
                      <Bar dataKey="impact_pct" radius={[0, 4, 4, 0]}>
                        {(predictionResult.shap_attributions || []).map((entry, index) => (
                          <Cell
                            key={`shap-${index}`}
                            fill={entry.impact_pct >= 0 ? '#EF4444' : '#10B981'}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="mt-3 p-3 bg-slate-900/60 rounded-lg border border-slate-800 text-xs text-slate-400 leading-relaxed">
                  <strong className="text-slate-200">SHAP Interpretation:</strong> Red bars indicate variables that significantly increase congestion (e.g. evening commuter peak hour rush, heavy monsoon precipitation, or public events). Green bars indicate dampening factors (e.g. off-peak hours or high-capacity multi-lane highway classifications).
                </div>
              </Card>
            </>
          ) : (
            <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-[#111827] border border-slate-800 rounded-xl p-8 text-center">
              <div className="p-4 bg-slate-900 rounded-full border border-slate-800 text-cyan-400 mb-4">
                <Gauge className="w-10 h-10" />
              </div>
              <h3 className="text-base font-semibold text-slate-200 mb-2">Inference Engine Ready</h3>
              <p className="text-xs text-slate-400 max-w-md mb-6 leading-relaxed">
                Configure your meteorological, temporal, and spatial scenario on the left and click "Calculate Congestion" to generate multi-factor forecasts and tree SHAP attributions.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-2 text-[11px] text-slate-500 font-mono">
                <span className="px-2 py-1 bg-slate-900 rounded border border-slate-800">XGBoost 3.2</span>
                <span className="px-2 py-1 bg-slate-900 rounded border border-slate-800">SHAP TreeExplainer</span>
                <span className="px-2 py-1 bg-slate-900 rounded border border-slate-800">2026 Context Isolation</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
