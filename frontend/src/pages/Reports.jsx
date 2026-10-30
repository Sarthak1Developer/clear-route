import React, { useState } from 'react';
import { api } from '../services/api';
import { Card, MetricCard } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { useApp } from '../context/AppContext';
import {
  FileBarChart, Download, Database, ExternalLink,
  Layers, CheckCircle2, FileSpreadsheet, BarChart2,
  Table, Sparkles
} from 'lucide-react';

export const Reports = () => {
  const { showToast } = useApp();
  const [downloading, setDownloading] = useState(null);

  const reportDatasets = [
    {
      id: 'city_summary',
      name: 'City-Wise Congestion Benchmarking',
      description: 'Aggregated congestion percentages, peak hour windows, and corridor counts across the 5 metropolitan cities.',
      format: 'CSV / Parquet',
      records: '5 Metro Profiles',
      layer: 'Gold Analytical',
    },
    {
      id: 'location_summary',
      name: 'Corridor & Location Congestion Index',
      description: 'Historical congestion, free-flow speeds, road types, and accident hazard scores for all 25+ monitored road corridors.',
      format: 'CSV / Parquet',
      records: '25+ Corridors',
      layer: 'Gold Analytical',
    },
    {
      id: 'hourly_patterns',
      name: 'Diurnal Hourly Traffic Distribution',
      description: 'Mean 24-hour congestion curve by hour of day (00:00 to 23:00 IST) comparing weekdays vs weekends.',
      format: 'CSV',
      records: '24 Hourly Intervals',
      layer: 'Gold Aggregation',
    },
    {
      id: 'weather_impact',
      name: 'Meteorological & Precipitation Impact Summary',
      description: 'Precipitation intensity classes, ambient temperature buckets, and observed congestion surges.',
      format: 'CSV',
      records: 'Atmospheric Bands',
      layer: 'Gold Analytical',
    },
    {
      id: 'model_evaluation',
      name: 'Model Benchmark & Evaluation Metrics',
      description: 'Held-out test set evaluation metrics (MAE, RMSE, R²) comparing all 4 modeling approaches with champion XGBoost weights.',
      format: 'JSON / CSV',
      records: '4 Model Architectures',
      layer: 'ML Evaluation Tier',
    },
    {
      id: 'gold_master_sample',
      name: 'Gold Master Analytical Dataset (Sample)',
      description: 'Harmonized tabular dataset containing traffic, weather, road geometry, and temporal features for BI consumption.',
      format: 'Parquet / CSV',
      records: 'Analytical Sample',
      layer: 'Gold Store',
    },
  ];

  const handleExport = async (datasetId) => {
    try {
      setDownloading(datasetId);
      // Trigger download from backend
      const link = document.createElement('a');
      link.href = `/api/reports/export/${datasetId}`;
      link.setAttribute('download', `clearroute_${datasetId}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      showToast(`Exported ${datasetId}.csv successfully`, 'success');
    } catch (err) {
      showToast(`Export failed: ${err.message}`, 'error');
    } finally {
      setTimeout(() => setDownloading(null), 1000);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono uppercase text-cyan-400 font-semibold tracking-wider">Business Intelligence</span>
            <span className="text-slate-600">•</span>
            <span className="text-xs text-slate-400">Microsoft Power BI & Tabular Data Exports</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <FileBarChart className="w-6 h-6 text-cyan-400" />
            <span>Analytical Reports & Power BI Datasets</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Export structured Gold-layer analytical tables formatted for Microsoft Power BI Desktop, academic evaluation summaries, and tabular data science exports.
          </p>
        </div>
      </div>

      {/* Power BI Architecture Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-blue-950/40 border border-slate-800 rounded-xl p-5 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <BarChart2 className="w-5 h-5 text-amber-400" />
            <h3 className="text-base font-bold text-white">Power BI 5-Section Dashboard Design</h3>
          </div>
          <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
            The project repository provides clean Gold-layer tabular files ready for consumption in Microsoft Power BI Desktop with 5 analytical report views:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 pt-2 text-[11px] text-slate-400">
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" /> 1. Executive Transportation Overview</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" /> 2. City-Wise Traffic Analytics</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" /> 3. Location-Wise Bottleneck Analysis</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" /> 4. Weather & Event Impact Dynamics</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" /> 5. Predictive ML Performance</span>
          </div>
        </div>

        <div className="flex-shrink-0 bg-slate-900/90 border border-slate-700/80 rounded-lg p-3 text-xs text-slate-300">
          <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Local Storage Path:</span>
          <code className="text-cyan-300 font-mono text-[11px] bg-slate-950 px-2 py-1 rounded block">
            powerbi/exports/
          </code>
        </div>
      </div>

      {/* Available Datasets Table */}
      <Card
        title="Ready-to-Export Gold Analytical Datasets"
        subtitle="Click 'Export CSV' to download clean dimension and fact tables for Power BI or external analytics"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {reportDatasets.map((ds) => (
            <div
              key={ds.id}
              className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition-all"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-cyan-950/60 text-cyan-300 border border-cyan-800/40">
                    {ds.layer}
                  </span>
                  <span className="text-[11px] text-slate-400 font-mono">{ds.records}</span>
                </div>
                <h4 className="text-sm font-semibold text-slate-100 mb-1">{ds.name}</h4>
                <p className="text-xs text-slate-400 mb-4 leading-relaxed">{ds.description}</p>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-slate-800/60">
                <span className="text-[10px] font-mono text-slate-500">Format: {ds.format}</span>
                <button
                  onClick={() => handleExport(ds.id)}
                  disabled={downloading === ds.id}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors border border-slate-700"
                >
                  <Download className="w-3.5 h-3.5 text-cyan-400" />
                  <span>{downloading === ds.id ? 'Exporting...' : 'Export CSV'}</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Power BI Desktop Instructions Card */}
      <Card title="How to Connect Microsoft Power BI Desktop">
        <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
          <div className="flex items-start gap-2">
            <div className="w-5 h-5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 flex items-center justify-center font-bold text-[10px] flex-shrink-0 mt-0.5">1</div>
            <div>
              <strong>Option A: Import Generated Gold CSV Files (Recommended for Offline Portability)</strong>
              <p className="text-slate-400 text-[11px] mt-0.5">
                Open Power BI Desktop $\rightarrow$ <em>Get Data</em> $\rightarrow$ <em>Text/CSV</em> $\rightarrow$ Select files from the <code>powerbi/exports/</code> directory. Relationships are automatically linked via <code>location_id</code> and <code>city_code</code>.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-2">
            <div className="w-5 h-5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 flex items-center justify-center font-bold text-[10px] flex-shrink-0 mt-0.5">2</div>
            <div>
              <strong>Option B: Live Database Connection (PostgreSQL)</strong>
              <p className="text-slate-400 text-[11px] mt-0.5">
                Open Power BI Desktop $\rightarrow$ <em>Get Data</em> $\rightarrow$ <em>PostgreSQL database</em> $\rightarrow$ Enter Server: <code>localhost:5432</code>, Database: <code>clearroute_db</code>, User: <code>clearroute_user</code>.
              </p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
