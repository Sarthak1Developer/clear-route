import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import { HourlyDetails } from '../components/common/HourlyDetails';
import { HistoricalProfile } from '../components/common/HistoricalProfile';
import { Card, MetricCard } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { CongestionBadge } from '../components/common/Badge';
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import {
  MapPin, Search, Calendar, Clock, CloudRain,
  ShieldAlert, Sparkles, Filter, ChevronDown, Compass
} from 'lucide-react';

export const LocationAnalytics = () => {
  const { selectedCity } = useApp();
  const [locations, setLocations] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingTrends, setLoadingTrends] = useState(false);
  const [error, setError] = useState(null);

  // Filters
  const [selectedDayFilter, setSelectedDayFilter] = useState('all');
  const [selectedMonthFilter, setSelectedMonthFilter] = useState('all');

  // Load locations for the active city
  useEffect(() => {
    let isMounted = true;
    async function loadCityLocations() {
      try {
        setLoading(true);
        setTrends(null);
        setSelectedLocation(null);
        setSelectedDayFilter('all');
        setSelectedMonthFilter('all');
        const res = await api.getCityLocations(selectedCity.name);
        const locs = res.locations || [];
        if (isMounted) {
          setLocations(locs);

          // Check if session storage pre-selected a location
          const saved = sessionStorage.getItem('clearroute_selected_location');
          if (saved) {
            try {
              const parsed = JSON.parse(saved);
              sessionStorage.removeItem('clearroute_selected_location');
              const found = locs.find(l => l.location_code === parsed.location_code || l.id === parsed.id);
              setSelectedLocation(found || locs[0] || null);
            } catch (e) {
              setSelectedLocation(locs[0] || null);
            }
          } else {
            setSelectedLocation(locs[0] || null);
          }
          setError(null);
        }
      } catch (err) {
        if (isMounted) setError(err.message);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadCityLocations();
    return () => { isMounted = false; };
  }, [selectedCity]);

  // Load trends when selectedLocation changes
  useEffect(() => {
    let isMounted = true;
    if (!selectedLocation) return;

    async function loadTrends() {
      try {
        setLoadingTrends(true);
        setTrends(null);
        setError(null);
        const res = await api.getLocationTrends(selectedLocation.location_code || selectedLocation.id,{...(selectedDayFilter!=='all'?{day_of_week:selectedDayFilter}:{}),...(selectedMonthFilter!=='all'?{month:selectedMonthFilter}:{})});
        if (isMounted) {
          setTrends(res);
        }
      } catch (err) {
        if(isMounted){setTrends(null);setError(err.message);}
      } finally {
        if (isMounted) setLoadingTrends(false);
      }
    }
    loadTrends();
    return () => { isMounted = false; };
  }, [selectedLocation,selectedDayFilter,selectedMonthFilter]);

  const weeklyChartData = (trends?.weekly || []).map((row) => ({ ...row, congestion_pct: row.congestion_pct ?? row.avg_congestion ?? null }));
  const monthlyChartData = (trends?.monthly || []).map((row) => ({ ...row, congestion_pct: row.congestion_pct ?? row.avg_congestion ?? null }));

  const filteredLocations = locations.filter((l) =>
    l.location_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    l.corridor_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) return <LoadingSpinner label={`Loading corridors for ${selectedCity.name}...`} />;
  if (error) return <EmptyState title="Location Analytics Unavailable" message={error} />;
  if (locations.length === 0) return <EmptyState title="No Corridors Mapped" message={`No OSM/Zenodo segments available yet for ${selectedCity.name}.`} />;

  return (
    <div className="space-y-6">
      {/* Search and Selector Bar */}
      <div className="bg-[#111827] border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder={`Search corridors in ${selectedCity.name} (e.g. Laxmi Nagar, Connaught Place)...`}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700/80 rounded-lg pl-10 pr-4 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        {/* Location Dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 whitespace-nowrap">Active Corridor:</span>
          <select
            value={selectedLocation ? (selectedLocation.location_code || selectedLocation.id) : ''}
            onChange={(e) => {
              const loc = locations.find((l) => (l.location_code || l.id) == e.target.value);
              if (loc) setSelectedLocation(loc);
            }}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs font-semibold text-slate-100 focus:outline-none focus:border-cyan-500 min-w-0 flex-1 w-full max-w-xs truncate"
          >
            {filteredLocations.map((loc) => (
              <option key={loc.id || loc.location_code} value={loc.location_code || loc.id}>
                {loc.location_name} — {loc.corridor_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {selectedLocation && (
        <>
          {/* Corridor Details Card */}
          <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-xs font-mono uppercase text-cyan-400 font-semibold">{selectedLocation.location_code}</span>
                <span className="text-slate-600">•</span>
                <span className="text-xs text-slate-400">{selectedCity.name}, {selectedCity.state}</span>
              </div>
              <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-3">
                <span>{selectedLocation.location_name}</span>
                <CongestionBadge percentage={selectedLocation.avg_congestion_pct ?? selectedLocation.congestion_percentage} />
              </h2>
              <p className="text-xs text-slate-400 mt-1 flex items-center gap-2 font-mono">
                <span>{selectedLocation.corridor_name}</span>
                <span>•</span>
                <span>Coordinates: [{selectedLocation.latitude.toFixed(4)}, {selectedLocation.longitude.toFixed(4)}]</span>
              </p>
            </div>

            {/* Infrastructure Specs */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-900/80 p-3 rounded-lg border border-slate-800/80 text-xs">
              <div>
                <span className="text-slate-500 text-[10px] uppercase font-bold">OSM Road Class</span>
                <p className="font-mono text-slate-200 uppercase font-semibold">{selectedLocation.road_type || 'Primary'}</p>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] uppercase font-bold">Lanes</span>
                <p className="font-mono text-slate-200 font-semibold">{selectedLocation.road_lanes ?? 'Unavailable'} Carriage Lanes</p>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] uppercase font-bold">Free Flow Speed</span>
                <p className="font-mono text-cyan-400 font-semibold">{selectedLocation.free_flow_speed_kmh ?? 'Unavailable'} km/h</p>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] uppercase font-bold">Accident Risk</span>
                <p className="font-mono text-amber-400 font-semibold">{selectedLocation.accident_risk_score ? `${(selectedLocation.accident_risk_score * 10).toFixed(1)} / 10` : 'Moderate'}</p>
              </div>
            </div>
          </div>

          {loadingTrends ? (
            <LoadingSpinner label={`Calculating diurnal and weekly congestion curves for ${selectedLocation.location_name}...`} />
          ) : trends && trends.avg_congestion != null ? (
            <>
              {/* Metric Cards Row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard
                  title="Historical Congestion"
                  value={Number.isFinite(trends.avg_congestion) ? `${trends.avg_congestion.toFixed(1)}%` : 'N/A'}
                  icon={Compass}
                  accentColor="cyan"
                  description={selectedMonthFilter==='all'?'Apr–Dec 2019 · selected weekdays':`Month ${selectedMonthFilter}, 2019 · selected weekdays`}
                />
                <MetricCard
                  title="Peak Bottleneck Hour"
                  value={trends.peak_hour !== undefined && trends.peak_hour !== null ? `${trends.peak_hour}:00` : 'N/A'}
                  unit="IST"
                  icon={Clock}
                  accentColor="rose"
                  description={trends.peak_hour_congestion !== undefined && trends.peak_hour_congestion !== null ? `Peak Severity: ${trends.peak_hour_congestion}%` : 'Off-Peak Normal'}
                />
                <MetricCard
                  title="Weekday vs Weekend Delta"
                  value={Number.isFinite(trends.weekend_delta) ? `${trends.weekend_delta > 0 ? '+' : ''}${trends.weekend_delta} pp` : 'N/A'}
                  icon={Calendar}
                  accentColor="blue"
                  description="Weekend minus weekday mean"
                />
                <MetricCard
                  title="Precipitation Sensitivity"
                  value={Number.isFinite(trends.rain_delta) ? `${trends.rain_delta>0?'+':''}${trends.rain_delta} pp` : 'N/A'}
                  icon={CloudRain}
                  accentColor="amber"
                  description="Precipitation ≥ 15 mm/hr difference"
                />
              </div>


              <div className="flex flex-wrap gap-3 text-xs"><label>Day <select aria-label="Corridor weekday" value={selectedDayFilter} onChange={e=>setSelectedDayFilter(e.target.value)} className="bg-slate-900 border border-slate-700 p-2 rounded"><option value="all">All days</option>{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map((d,i)=><option key={i} value={i}>{d}</option>)}</select></label><label>Month <select aria-label="Corridor month" value={selectedMonthFilter} onChange={e=>setSelectedMonthFilter(e.target.value)} className="bg-slate-900 border border-slate-700 p-2 rounded"><option value="all">All months</option>{['Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].map((m,i)=><option key={m} value={i+4}>{m}</option>)}</select></label></div>
              <HourlyDetails scope={`${selectedCity.name} / ${selectedLocation.location_name}`} rows={trends.hourly} valueKey="congestion_pct" count={trends.sample_count}/>
              {/* Hourly Trend Chart */}
              <Card
                title={`${selectedLocation.location_name} — 24-Hour Congestion Pattern`}
                subtitle="Diurnal congestion curve showing rush hour bottleneck peaks (08:00 - 11:00 and 17:00 - 21:00 IST)"
              >
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart key={`${selectedCity.code}-${selectedLocation.location_code}-${selectedDayFilter}-${selectedMonthFilter}`} data={(trends.hourly || []).map((row) => ({ ...row, congestion_pct: row.congestion_pct ?? null }))} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                      <defs>
                        <linearGradient id="locHourGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.5} />
                          <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                      <XAxis dataKey="hour" stroke="#9CA3AF" tick={{ fontSize: 11 }} tickFormatter={(h) => `${h}:00`} />
                      <YAxis stroke="#9CA3AF" tick={{ fontSize: 11 }} domain={[0, 100]} unit="%" />
                      <Tooltip
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const d = payload[0].payload;
                            return (
                              <div className="bg-slate-900 border border-slate-700 p-2.5 rounded text-xs shadow-xl">
                                <p className="font-bold text-slate-100">{d.hour}:00 IST</p>
                                <p className="text-cyan-400 font-mono mt-1">Mean Congestion: {d.congestion_pct}%</p>
                                <p className="text-slate-400 text-[10px]">Mean Observed Speed: {d.speed_kmh} km/h</p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="congestion_pct"
                        stroke="#06B6D4"
                        strokeWidth={2.5}
                        fill="url(#locHourGradient)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </Card>

              {/* Weekly and Monthly Trends Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Day of Week */}
                <Card
                  title="Day-of-Week Variation"
                  subtitle="Congestion index across Monday to Sunday"
                >
                  <div className="h-60 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={weeklyChartData} margin={{ top: 10, right: 10, left: -25, bottom: 20 }}>
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
                                  <p className="text-cyan-400 font-mono">Congestion: {d.congestion_pct}%</p>
                                </div>
                              );
                            }
                            return null;
                          }}
                        />
                        <Bar dataKey="congestion_pct" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Card>

                {/* Monthly Seasonal Progression */}
                <Card
                  title="Monthly Seasonal Trend (2019)"
                  subtitle="Monsoon progression (July - September) impact on corridor"
                >
                  <div className="h-60 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={monthlyChartData} margin={{ top: 10, right: 10, left: -25, bottom: 20 }}>
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
                                  <p className="text-cyan-400 font-mono">Congestion: {d.congestion_pct}%</p>
                                </div>
                              );
                            }
                            return null;
                          }}
                        />
                        <Line type="monotone" dataKey="congestion_pct" stroke="#F59E0B" strokeWidth={2} dot={{ r: 3 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </Card>
              </div>
            </>
          ) : null}
        </>
      )}
      <HistoricalProfile city={selectedCity.name} location={selectedLocation?.location_code}/>
    </div>
  );
};
