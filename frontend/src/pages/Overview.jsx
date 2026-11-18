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
  const { setActiveTab, setSelectedCity, selectedCity, cities } = useApp();
  const [data, setData] = useState(null);
  const [quality, setQuality] = useState(null);
  const [coverage, setCoverage] = useState(null);
  const [topLocations, setTopLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function fetchOverviewData() {
      try {
        setLoading(true);
        const [overviewRes, qualRes, covRes, locsRes] = await Promise.all([
          api.getOverview(selectedCity.name),
          api.getDataQuality().catch(() => null),
          api.getDataCoverage().catch(() => null),
          api.searchLocations('', selectedCity.name).catch(() => []),
        ]);
        if (isMounted) {
          setData(overviewRes);
          setQuality(qualRes);
          setCoverage(covRes);
          setTopLocations(Array.isArray(locsRes) ? locsRes : []);
          setError(null);
        }
      } catch (err) {
        if (isMounted) setError(err.message);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    fetchOverviewData();
    return () => { isMounted = false; };
  }, [selectedCity.name]);


  if (loading) return <LoadingSpinner label="Loading multi-city traffic analytical overview..." />;
  if (error) return <EmptyState title="Unable to Load Overview" message={error} reason="Verify backend server connection at http://127.0.0.1:8000." />;
  if (!data) return <EmptyState message="No analytical summary records retrieved from database." />;

  if (data.total_records_processed === 0) return <EmptyState title="Insufficient traffic observations" message="No records exist for the selected city." />;

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
            Explore generated traffic benchmarks alongside weather and event context. Observational validity and causal effects have not been established.
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
          value={Number.isFinite(data.total_cities) ? data.total_cities : 'N/A'}
          unit="Metros"
          icon={Building2}
          accentColor="cyan"
          description="Delhi, Mumbai, BLR, HYD, Kolkata"
        />
        <MetricCard
          title={`${selectedCity.name} Road Corridors`}
          value={Number.isFinite(data.total_locations) ? data.total_locations : 'N/A'}
          unit="Corridors"
          icon={MapPin}
          accentColor="blue"
          description="Configured demonstration corridors"
        />
        <MetricCard
          title="Network Avg Congestion"
          value={Number.isFinite(data.network_avg_congestion_pct) ? `${data.network_avg_congestion_pct.toFixed(1)}%` : 'N/A'}
          icon={Gauge}
          accentColor="amber"
          description={`${selectedCity.name} mean: ${Number.isFinite(data.avg_congestion_pct) ? data.avg_congestion_pct.toFixed(2) + '%' : 'Unavailable'}`}
        />
        <MetricCard
          title="Dataset Temporal Range"
          value={data.historical_coverage || 'N/A'}
          unit="2019 Baseline"
          icon={Calendar}
          accentColor="emerald"
          description={`${Number.isFinite(data.total_records_processed) ? data.total_records_processed.toLocaleString() : 'N/A'} traffic records`}
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
          title={`${selectedCity.name} Hourly Congestion Curve`}
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
          title={`${selectedCity.name} Day-of-Week Congestion`}
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
          title={`${selectedCity.name} Monthly Progression`}
          subtitle="Monthly averages from the application database"
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

      {/* Corridor Benchmarking & Data Quality Row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Location Benchmarking Table (7 cols) */}
        <div className="lg:col-span-7">
          <Card
            title="Arterial Road Corridor Comparisons"
            subtitle="Congestion index across monitored urban corridors and arterial segments"
          >
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="text-[11px] uppercase bg-slate-900/80 text-slate-400 border-b border-slate-800 font-mono">
                  <tr>
                    <th className="py-2.5 px-3">Corridor</th>
                    <th className="py-2.5 px-2">Road Type</th>
                    <th className="py-2.5 px-2">Lanes</th>
                    <th className="py-2.5 px-2">Free Flow</th>
                    <th className="py-2.5 px-2">Avg Congestion</th>
                    <th className="py-2.5 px-2 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-sans">
                  {topLocations.map((loc) => (
                    <tr key={loc.id || loc.location_code} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-2.5 px-3">
                        <div className="font-semibold text-slate-100">{loc.location_name}</div>
                        <div className="text-[10px] text-slate-400 font-mono">{loc.corridor_name}</div>
                      </td>
                      <td className="py-2.5 px-2 font-mono uppercase text-slate-400 text-[10px]">{loc.road_type}</td>
                      <td className="py-2.5 px-2 font-mono text-slate-300">{loc.road_lanes || 4}</td>
                      <td className="py-2.5 px-2 font-mono text-cyan-400">{loc.free_flow_speed_kmh} km/h</td>
                      <td className="py-2.5 px-2">
                        <CongestionBadge percentage={loc.avg_congestion_pct || loc.congestion_percentage} />
                      </td>
                      <td className="py-2.5 px-2 text-right">
                        <button
                          onClick={() => {
                            sessionStorage.setItem('clearroute_selected_location', JSON.stringify(loc));
                            const cityObj = cities.find(c => c.name.toLowerCase() === (loc.city || '').toLowerCase());
                            if (cityObj) setSelectedCity(cityObj);
                            setActiveTab('location-analytics');
                          }}
                          className="p-1 text-cyan-400 hover:text-cyan-300 hover:bg-cyan-950/40 rounded transition-colors"
                          title="Open in Location Analytics"
                        >
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        {/* Data Coverage & Quality Summary (5 cols) */}
        <div className="lg:col-span-5">
          <Card
            title="Big Data Governance & Quality Audit"
            subtitle="Coverage bounds, schema completeness, and window deduplication audit"
          >
            <div className="space-y-3 text-xs">
              <div className="p-3 bg-slate-900/70 rounded-lg border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-slate-400 text-[10px] uppercase font-bold block">Temporal Scope</span>
                  <p className="text-slate-100 font-mono font-semibold mt-0.5">
                    {coverage?.start_date || '2019-04-01'} to {coverage?.end_date || '2019-12-31'}
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-slate-400 text-[10px] uppercase font-bold block">Gold Records</span>
                  <p className="text-cyan-400 font-mono font-bold mt-0.5">
                    {quality?.total_gold_records?.toLocaleString() ?? 'Unavailable'}
                  </p>
                </div>
              </div>

              <div className="p-3 bg-slate-900/70 rounded-lg border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-slate-400 text-[10px] uppercase font-bold block">Completeness Rate</span>
                  <p className="text-emerald-400 font-mono font-bold mt-0.5">
                    {(quality?.completeness_rate ?? 0).toFixed(1)}% verified
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-slate-400 text-[10px] uppercase font-bold block">Duplicate Records</span>
                  <p className="text-emerald-400 font-mono font-bold mt-0.5">
                    {quality?.duplicate_count ?? 0} Duplicates (Deduplicated)
                  </p>
                </div>
              </div>

              <div className="p-3 bg-slate-900/70 rounded-lg border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-slate-400 text-[10px] uppercase font-bold block">Covered Metros</span>
                  <p className="text-slate-300 font-medium text-[11px] mt-0.5">
                    {(coverage?.cities_covered || ['Delhi', 'Mumbai', 'Bengaluru', 'Hyderabad', 'Kolkata']).join(', ')}
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-slate-400 text-[10px] uppercase font-bold block">Corridors</span>
                  <p className="text-blue-400 font-mono font-bold mt-0.5">
                    {coverage?.corridors_total ?? 0} segments
                  </p>
                </div>
              </div>

              <div className="px-3 py-2 bg-slate-950/60 rounded-lg border border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
                <span className="flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Validation Status:</span>
                </span>
                <span className="text-emerald-400 font-semibold uppercase text-[10px] font-mono">
                  {quality?.validation_status || 'Passed Quality Gate'}
                </span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

