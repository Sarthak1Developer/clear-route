import React from 'react';
import { useApp } from '../context/AppContext';
import { Card, MetricCard } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import {
  Settings as SettingsIcon, Server, Database,
  Cpu, CheckCircle2, AlertTriangle, RefreshCw,
  HardDrive, ShieldCheck, Laptop
} from 'lucide-react';

export const Settings = () => {
  const { healthStatus, checkHealth } = useApp();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono uppercase text-cyan-400 font-semibold tracking-wider">System Administration</span>
            <span className="text-slate-600">•</span>
            <span className="text-xs text-slate-400">Environment Diagnostics & Engine Connectivity</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <SettingsIcon className="w-6 h-6 text-cyan-400" />
            <span>Platform Settings & System Status</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Inspect live FastAPI backend health, PostgreSQL / SQLite storage engines, serialized model artifacts, and distributed compute configuration.
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
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Backend API */}
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">FastAPI REST Server</span>
            <div className={`w-2.5 h-2.5 rounded-full ${healthStatus.online ? 'bg-emerald-400 shadow-sm shadow-emerald-500/50' : 'bg-rose-400'}`} />
          </div>
          <div className="text-xl font-bold text-white font-mono mb-1">
            {healthStatus.online ? 'Online (200 OK)' : 'Offline / Standby'}
          </div>
          <p className="text-xs text-slate-400 font-mono">Host: 127.0.0.1:8000/api</p>
        </div>

        {/* Database */}
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Database Dialect</span>
            <Database className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-xl font-bold text-white font-mono mb-1">
            {healthStatus.details?.database || 'SQLite / PostgreSQL'}
          </div>
          <p className="text-xs text-slate-400 font-mono">Dialect: SQLAlchemy Engine</p>
        </div>

        {/* ML Inference */}
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">ML Artifacts</span>
            <Cpu className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-white font-mono mb-1">
            4 / 4 Loaded
          </div>
          <p className="text-xs text-slate-400 font-mono">Baseline, Ridge, RF, XGBoost</p>
        </div>
      </div>

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
