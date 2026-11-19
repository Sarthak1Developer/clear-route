import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Card, MetricCard } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import {
  Settings as SettingsIcon, Server, Database,
  Cpu, CheckCircle2, AlertTriangle, RefreshCw,
  HardDrive, ShieldCheck, Laptop, Save, RotateCcw,
  Sliders, Bell, Map, Thermometer
} from 'lucide-react';

export const Settings = () => {
  const { healthStatus, checkHealth, settings, updateSettings, resetSettings, showToast, cities } = useApp();

  const [formState, setFormState] = useState({
    defaultCityCode: settings.defaultCityCode || 'DEL',
    defaultModel: settings.defaultModel || 'xgboost',
    temperatureUnit: settings.temperatureUnit || 'C',
    refreshInterval: settings.refreshInterval ?? 30,
    toastEnabled: settings.toastEnabled ?? true,
    mapZoom: settings.mapZoom || 12,
  });

  const handleSave = (e) => {
    e.preventDefault();
    updateSettings(formState);
    showToast('Application preferences saved successfully', 'success');
  };

  const handleReset = () => {
    resetSettings();
    setFormState({
      defaultCityCode: 'DEL',
      defaultModel: 'xgboost',
      temperatureUnit: 'C',
      refreshInterval: 30,
      toastEnabled: true,
      mapZoom: 12,
    });
    showToast('Preferences reset to default configuration', 'info');
  };

  const modelsLoadedList = healthStatus.details?.models_loaded || [];
  const modelsCount = healthStatus.details?.models_count ?? modelsLoadedList.length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono uppercase text-cyan-400 font-semibold tracking-wider">System Administration</span>
            <span className="text-slate-600">•</span>
            <span className="text-xs text-slate-400">Environment Diagnostics & Application Preferences</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <SettingsIcon className="w-6 h-6 text-cyan-400" />
            <span>Platform Settings & System Status</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Inspect live FastAPI backend health, database connection state, serialized ML model artifacts, and customize local operational preferences.
          </p>
        </div>

        <button
          onClick={checkHealth}
          className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-3.5 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 border border-slate-700 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
          <span>Ping Services</span>
        </button>
      </div>

      {/* Connectivity Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Backend API */}
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">FastAPI REST Server</span>
            <div className={`w-2.5 h-2.5 rounded-full ${healthStatus.online ? 'bg-emerald-400 shadow-sm shadow-emerald-500/50' : 'bg-rose-400'}`} />
          </div>
          <div className="text-xl font-bold text-white font-mono mb-1">
            {healthStatus.online ? 'Online (200 OK)' : 'Offline / Standby'}
          </div>
          <p className="text-xs text-slate-400 font-mono">v{healthStatus.details?.version || '1.0.0'} · Configured API endpoint</p>
        </div>

        {/* Database */}
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Database Engine</span>
            <Database className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-xl font-bold text-white font-mono mb-1">
            {healthStatus.details?.database || 'PostgreSQL / SQLite'}
          </div>
          <p className="text-xs text-slate-400 font-mono">
            {healthStatus.details?.records_count?.toLocaleString() ?? 'Unavailable'} traffic records
          </p>
        </div>

        {/* ML Inference */}
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">ML Artifacts</span>
            <Cpu className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-white font-mono mb-1">
            {modelsCount} / 4 Loaded
          </div>
          <p className="text-xs text-slate-400 font-mono truncate" title={modelsLoadedList.join(', ')}>
            {modelsLoadedList.length > 0 ? modelsLoadedList.join(', ') : 'No loaded models reported'}
          </p>
        </div>

        {/* System Environment */}
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Operational Target</span>
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-xl font-bold text-white font-mono mb-1">
            {healthStatus.details?.environment || 'Unavailable'}
          </div>
          <p className="text-xs text-slate-400 font-mono">2026 Context Isolation</p>
        </div>
      </div>

      {/* User Application Preferences Card */}
      <Card
        title="Application Preferences & Local Configuration"
        subtitle="Saved to browser local storage and applied across the entire ClearRoute dashboard session"
      >
        <form onSubmit={handleSave} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 text-xs">
            {/* Default Metro City */}
            <div className="space-y-2">
              <label className="block text-slate-300 font-semibold flex items-center gap-1.5">
                <Map className="w-4 h-4 text-cyan-400" />
                <span>Default Metropolitan City</span>
              </label>
              <select
                value={formState.defaultCityCode}
                onChange={(e) => setFormState({ ...formState, defaultCityCode: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 font-medium"
              >
                {cities.map((c) => (
                  <option key={c.code} value={c.code}>{c.name} ({c.state})</option>
                ))}
              </select>
              <p className="text-[11px] text-slate-500">Initial city focused when launching analytics.</p>
            </div>

            {/* Temperature Units */}
            <div className="space-y-2">
              <label className="block text-slate-300 font-semibold flex items-center gap-1.5">
                <Thermometer className="w-4 h-4 text-amber-400" />
                <span>Temperature Metric Unit</span>
              </label>
              <select
                value={formState.temperatureUnit}
                onChange={(e) => setFormState({ ...formState, temperatureUnit: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 font-medium"
              >
                <option value="C">Celsius (°C)</option>
                <option value="F">Fahrenheit (°F)</option>
              </select>
              <p className="text-[11px] text-slate-500">Display unit for ambient meteorological data.</p>
            </div>

            {/* Diagnostics Auto-Refresh Interval */}
            <div className="space-y-2">
              <label className="block text-slate-300 font-semibold flex items-center gap-1.5">
                <RefreshCw className="w-4 h-4 text-cyan-400" />
                <span>Health Polling Interval</span>
              </label>
              <select
                value={formState.refreshInterval}
                onChange={(e) => setFormState({ ...formState, refreshInterval: Number(e.target.value) })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 font-medium"
              >
                <option value={15}>Every 15 Seconds</option>
                <option value={30}>Every 30 Seconds (Default)</option>
                <option value={60}>Every 60 Seconds</option>
                <option value={0}>Disabled (Manual Ping Only)</option>
              </select>
              <p className="text-[11px] text-slate-500">Frequency of background backend connectivity checks.</p>
            </div>

            {/* Map Default Zoom Level */}
            <div className="space-y-2">
              <label className="block text-slate-300 font-semibold flex items-center gap-1.5">
                <Map className="w-4 h-4 text-blue-400" />
                <span>Map Default Zoom Level</span>
              </label>
              <select
                value={formState.mapZoom}
                onChange={(e) => setFormState({ ...formState, mapZoom: Number(e.target.value) })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500 font-medium font-mono"
              >
                <option value={11}>11 - Wide Regional Scope</option>
                <option value={12}>12 - Standard Metropolitan (Default)</option>
                <option value={13}>13 - Corridor Level Zoom</option>
                <option value={14}>14 - High Detail Street Level</option>
              </select>
              <p className="text-[11px] text-slate-500">Initial zoom scale for Leaflet geospatial maps.</p>
            </div>

            {/* Notification Toasts Toggle */}
            <div className="space-y-2">
              <label className="block text-slate-300 font-semibold flex items-center gap-1.5">
                <Bell className="w-4 h-4 text-purple-400" />
                <span>Toast Notifications</span>
              </label>
              <div className="pt-1">
                <label className="inline-flex items-center cursor-pointer gap-2">
                  <input
                    type="checkbox"
                    checked={formState.toastEnabled}
                    onChange={(e) => setFormState({ ...formState, toastEnabled: e.target.checked })}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-500"></div>
                  <span className="text-slate-300 text-xs">
                    {formState.toastEnabled ? 'Enabled' : 'Disabled'}
                  </span>
                </label>
              </div>
              <p className="text-[11px] text-slate-500">Show transient alert banners on prediction or export.</p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={handleReset}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-700/80 flex items-center gap-1.5 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset to Defaults</span>
            </button>
            <button
              type="submit"
              className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-5 py-2 rounded-xl text-xs flex items-center gap-2 transition-all shadow-lg shadow-cyan-500/20"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Save Application Preferences</span>
            </button>
          </div>
        </form>
      </Card>

      {/* Hardware Architecture Split Banner */}
      <Card title="Hardware Responsibility Partitioning">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-slate-300">
          <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 font-bold text-cyan-400 text-sm">
              <Laptop className="w-4 h-4" />
              <span>Primary Development Laptop (Local Workspace)</span>
            </div>
            <ul className="space-y-1 text-slate-400 text-[11px] list-disc list-inside">
              <li>React 18 + Vite Frontend Dashboard</li>
              <li>FastAPI REST API Service & Connection Pool</li>
              <li>SQLite / PostgreSQL local application store</li>
              <li>Serialized ML Model Inference & SHAP Local Attributions</li>
              <li>Power BI Desktop Report authoring & integration</li>
            </ul>
          </div>

          <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 font-bold text-blue-400 text-sm">
              <HardDrive className="w-4 h-4" />
              <span>Teammate Laptop (High Compute & RAM)</span>
            </div>
            <ul className="space-y-1 text-slate-400 text-[11px] list-disc list-inside">
              <li>Raw Zenodo Uber Movement CSV/JSON archive ingest</li>
              <li>Apache PySpark Medallion ETL (Bronze → Silver → Gold)</li>
              <li>Large-scale feature engineering & Parquet partitioning</li>
              <li>Batch training of XGBoost & Random Forest models</li>
              <li>SHAP TreeExplainer global attributions batch generation</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
};

