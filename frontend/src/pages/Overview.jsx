import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import { Card, MetricCard } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { CongestionBadge } from '../components/common/Badge';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell
} from 'recharts';
import {
  Building2, MapPin, Gauge, AlertTriangle, Calendar,
  TrendingUp, CloudRain, ShieldCheck, ArrowRight
} from 'lucide-react';

export const Overview = () => {
  const { setActiveTab, setSelectedCity, cities } = useApp();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function fetchOverview() {
      try {
        setLoading(true);
        const res = await api.getOverview();
        if (isMounted) {
          setData(res);
          setError(null);
        }
      } catch (err) {
        if (isMounted) setError(err.message);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    fetchOverview();
    return () => { isMounted = false; };
  }, []);

  if (loading) return <LoadingSpinner label="Loading multi-city traffic analytical overview..." />;
  if (error) return <EmptyState title="Unable to Load Overview" message={error} reason="Verify backend server connection at http://127.0.0.1:8000." />;
  if (!data) return <EmptyState message="No analytical summary records retrieved from database." />;

  const getBarColor = (pct) => {
    if (pct > 75) return '#EF4444';
    if (pct > 50) return '#F97316';
    if (pct > 25) return '#F59E0B';
    return '#10B981';
  };

  return (
    <div className="space-y-6">
      {/* Platform Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 font-mono">Academic Big Data Project</span>
            <span className="text-xs text-slate-500">•</span>
            <span className="text-xs text-slate-400">Apache Spark · XGBoost · OpenStreetMap · ERA5</span>
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Indian Metropolitan Congestion Intelligence
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Multi-factor predictive analytics combining historical Uber Movement corridor speeds, Open-Meteo ERA5 weather reanalysis, official MoRTH accident contexts, and cultural event dynamics.
          </p>
        </div>
        <button
          onClick={() => setActiveTab('congestion-prediction')}
          className="flex-shrink-0 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-4 py-2.5 rounded-xl text-xs flex items-center gap-2 transition-all shadow-lg shadow-cyan-500/20"
        >
          <span>Run Predictive Inference</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Cities Monitored"
          value={data.total_cities || 5}
          unit="Metros"
          icon={Building2}
          accentColor="cyan"
          description="Delhi, Mumbai, BLR, HYD, Kolkata"
        />
        <MetricCard
          title="Monitored Road Corridors"
          value={data.total_locations || 25}
          unit="Corridors"
          icon={MapPin}
          accentColor="blue"
          description="Zenodo Uber Movement TAZ Segments"
        />
        <MetricCard
          title="Network Avg Congestion"
          value={`${(data.avg_congestion_pct || 46.2).toFixed(1)}%`}
          icon={Gauge}
          accentColor="amber"
          description={`Highest: ${data.most_congested_city || 'Bengaluru'}`}
        />
        <MetricCard
          title="Dataset Temporal Range"
          value="9 Months"
          unit="2019 Baseline"
          icon={Calendar}
          accentColor="emerald"
          description={`${data.total_records_processed?.toLocaleString() || '184,500'} hourly readings`}
        />
      </div>

      {/* Primary Analytics Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* City Comparison Bar Chart */}
        <Card
          title="Metropolitan Congestion Benchmarking"
          subtitle="Mean congestion index percentage across all monitored arterial corridors"
        >
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.city_comparison || []} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                <XAxis dataKey="city" stroke="#9CA3AF" tick={{ fontSize: 11 }} />
                <YAxis stroke="#9CA3AF" tick={{ fontSize: 11 }} domain={[0, 100]} unit="%" />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload;
                      return (
                        <div className="bg-slate-900 border border-slate-700 p-2.5 rounded-lg text-xs shadow-xl">
                          <p className="font-bold text-slate-100">{d.city}</p>
                          <p className="text-cyan-400 font-mono mt-1">Avg Congestion: {d.avg_congestion_pct}%</p>
                          <p className="text-slate-400 text-[11px]">Corridors Analyzed: {d.corridor_count}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="avg_congestion_pct" radius={[4, 4, 0, 0]}>
                  {(data.city_comparison || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getBarColor(entry.avg_congestion_pct)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Hourly Congestion Distribution */}
        <Card
          title="Diurnal Hourly Congestion Curve"
          subtitle="Mean network congestion profile by hour of day (00:00 - 23:00 IST)"
        >
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.hourly_trend || []} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <defs>
                  <linearGradient id="hourCongestion" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                <XAxis
                  dataKey="hour"
                  stroke="#9CA3AF"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(h) => `${h}:00`}
                />
                <YAxis stroke="#9CA3AF" tick={{ fontSize: 11 }} domain={[0, 100]} unit="%" />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload;
                      return (
                        <div className="bg-slate-900 border border-slate-700 p-2.5 rounded-lg text-xs shadow-xl">
                          <p className="font-bold text-slate-100">{d.hour}:00 IST</p>
                          <p className="text-cyan-400 font-mono mt-1">Mean Congestion: {d.avg_congestion}%</p>
                          <p className="text-slate-400 text-[11px]">{d.is_peak ? 'Commuter Peak Rush' : 'Off-Peak Interval'}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="avg_congestion"
                  stroke="#06B6D4"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#hourCongestion)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Secondary Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Weekly Day-of-Week Pattern */}
        <Card
          title="Day-of-Week Congestion Variation"
          subtitle="Weekday commuter volumes vs weekend leisure traffic"
        >
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.weekly_trend || []} margin={{ top: 10, right: 10, left: -25, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                <XAxis dataKey="day" stroke="#9CA3AF" tick={{ fontSize: 10 }} />
                <YAxis stroke="#9CA3AF" tick={{ fontSize: 10 }} domain={[0, 100]} unit="%" />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload;
                      return (
                        <div className="bg-slate-900 border border-slate-700 p-2 rounded text-xs">
                          <p className="font-bold text-slate-100">{d.day}</p>
                          <p className="text-cyan-400 font-mono">Congestion: {d.avg_congestion}%</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="avg_congestion" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Monthly Trend 2019 */}
        <Card
          title="2019 Monthly Progression"
          subtitle="April – December 2019 seasonal progression (Monsoon surge)"
        >
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.monthly_trend || []} margin={{ top: 10, right: 10, left: -25, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                <XAxis dataKey="month" stroke="#9CA3AF" tick={{ fontSize: 10 }} />
                <YAxis stroke="#9CA3AF" tick={{ fontSize: 10 }} domain={[0, 100]} unit="%" />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload;
                      return (
                        <div className="bg-slate-900 border border-slate-700 p-2 rounded text-xs">
                          <p className="font-bold text-slate-100">{d.month} 2019</p>
                          <p className="text-cyan-400 font-mono">Avg Congestion: {d.avg_congestion}%</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Line type="monotone" dataKey="avg_congestion" stroke="#10B981" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Rainfall vs Congestion Correlation */}
        <Card
          title="Precipitation Impact Banding"
          subtitle="Precipitation intensity classes (ERA5) vs mean congestion"
        >
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.weather_correlation || []} margin={{ top: 10, right: 10, left: -25, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                <XAxis dataKey="band" stroke="#9CA3AF" tick={{ fontSize: 9 }} />
                <YAxis stroke="#9CA3AF" tick={{ fontSize: 10 }} domain={[0, 100]} unit="%" />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload;
                      return (
                        <div className="bg-slate-900 border border-slate-700 p-2 rounded text-xs">
                          <p className="font-bold text-slate-100">{d.band}</p>
                          <p className="text-cyan-400 font-mono">Congestion: {d.avg_congestion}%</p>
                          <p className="text-slate-400 text-[10px]">Total Hours: {d.sample_count}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="avg_congestion" fill="#06B6D4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
};
