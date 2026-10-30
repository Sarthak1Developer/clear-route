import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import { Card, MetricCard } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { CongestionBadge } from '../components/common/Badge';
import { TrafficMap } from '../components/maps/TrafficMap';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
  Building2, MapPin, Gauge, Clock, CloudRain,
  Calendar, ArrowUpRight, Filter
} from 'lucide-react';

export const CityAnalytics = () => {
  const { cities, selectedCity, setSelectedCity, setActiveTab } = useApp();
  const [summary, setSummary] = useState(null);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function fetchCityData() {
      try {
        setLoading(true);
        const [sumRes, locsRes] = await Promise.all([
          api.getCitySummary(selectedCity.name),
          api.getCityLocations(selectedCity.name),
        ]);
        if (isMounted) {
          setSummary(sumRes);
          setLocations(locsRes.locations || []);
          setError(null);
        }
      } catch (err) {
        if (isMounted) setError(err.message);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    fetchCityData();
    return () => { isMounted = false; };
  }, [selectedCity]);

  const handleSelectMapLocation = (loc) => {
    // Navigate to location analytics with this location preselected
    sessionStorage.setItem('clearroute_selected_location', JSON.stringify(loc));
    setActiveTab('location-analytics');
  };

  return (
    <div className="space-y-6">
      {/* City Header & Controls */}
      <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono uppercase text-cyan-400 font-semibold tracking-wider">Metropolitan Profile</span>
            <span className="text-slate-600">•</span>
            <span className="text-xs text-slate-400">{selectedCity.state}</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
            <span>{selectedCity.name} Traffic Analytics</span>
            {summary && <CongestionBadge percentage={summary.avg_congestion_pct} />}
          </h1>
        </div>

        {/* City Pill Switcher */}
        <div className="flex flex-wrap items-center gap-1.5 bg-slate-900/80 p-1.5 rounded-lg border border-slate-800">
          {cities.map((city) => (
            <button
              key={city.code}
              onClick={() => setSelectedCity(city)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                selectedCity.code === city.code
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {city.name}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <LoadingSpinner label={`Aggregating spatio-temporal metrics for ${selectedCity.name}...`} />
      ) : error ? (
        <EmptyState title="City Analytics Error" message={error} reason={`No records found for ${selectedCity.name} in current database.`} />
      ) : summary ? (
        <>
          {/* City Key Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="City Mean Congestion"
              value={`${(summary.avg_congestion_pct || 45).toFixed(1)}%`}
              icon={Gauge}
              accentColor="cyan"
              description={`Category: ${summary.congestion_category || 'Moderate'}`}
            />
            <MetricCard
              title="Peak Congestion Window"
              value={summary.peak_hours_str || '18:00 - 20:00'}
              unit="IST"
              icon={Clock}
              accentColor="amber"
              description={`Peak Congestion: ${summary.peak_hour_congestion_pct || 68}%`}
            />
            <MetricCard
              title="Supported Corridors"
              value={locations.length}
              unit="Segments"
              icon={MapPin}
              accentColor="blue"
              description="OpenStreetMap + Zenodo Mapped"
            />
            <MetricCard
              title="Monsoon Rainfall Delta"
              value={`+${(summary.rain_impact_delta || 18.4).toFixed(1)}%`}
              icon={CloudRain}
              accentColor="rose"
              description="Congestion surge during heavy rain"
            />
          </div>

          {/* Interactive Geospatial Leaflet Map */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-cyan-400" />
                <span>Geographical Road Corridors & Density Zones</span>
              </h3>
              <span className="text-xs text-slate-400">Click marker to inspect corridor parameters</span>
            </div>
            <TrafficMap
              locations={locations}
              center={[selectedCity.lat, selectedCity.lng]}
              zoom={selectedCity.zoom || 12}
              onSelectLocation={handleSelectMapLocation}
              height="450px"
            />
          </div>

          {/* Hourly and Weekly Trends */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card
              title={`${selectedCity.name} Diurnal Hourly Curve`}
              subtitle="Hourly congestion profile comparing weekday commuters vs weekends"
            >
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={summary.hourly_distribution || []} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                    <XAxis dataKey="hour" stroke="#9CA3AF" tick={{ fontSize: 11 }} tickFormatter={(h) => `${h}:00`} />
                    <YAxis stroke="#9CA3AF" tick={{ fontSize: 11 }} domain={[0, 100]} unit="%" />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const d = payload[0].payload;
                          return (
                            <div className="bg-slate-900 border border-slate-700 p-2.5 rounded-lg text-xs shadow-xl">
                              <p className="font-bold text-slate-100">{d.hour}:00 IST</p>
                              <p className="text-cyan-400 font-mono">Weekday: {d.weekday_congestion}%</p>
                              <p className="text-blue-400 font-mono">Weekend: {d.weekend_congestion}%</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                    <Line type="monotone" name="Weekday (Mon-Fri)" dataKey="weekday_congestion" stroke="#06B6D4" strokeWidth={2.5} dot={false} />
                    <Line type="monotone" name="Weekend (Sat-Sun)" dataKey="weekend_congestion" stroke="#3B82F6" strokeWidth={2} strokeDasharray="4 4" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* Top Congested Corridors Table */}
            <Card
              title={`Most Congested Corridors in ${selectedCity.name}`}
              subtitle="Ranked by historical mean congestion index (2019 baseline)"
            >
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="text-[11px] uppercase bg-slate-900/80 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">Corridor</th>
                      <th className="py-2.5 px-2">Road Type</th>
                      <th className="py-2.5 px-2">Free Flow</th>
                      <th className="py-2.5 px-2">Avg Congestion</th>
                      <th className="py-2.5 px-2 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {locations.slice(0, 5).map((loc) => (
                      <tr key={loc.id || loc.location_code} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-3">
                          <div className="font-semibold text-slate-200">{loc.location_name}</div>
                          <div className="text-[10px] text-slate-400">{loc.corridor_name}</div>
                        </td>
                        <td className="py-2.5 px-2 font-mono uppercase text-slate-400">{loc.road_type}</td>
                        <td className="py-2.5 px-2 text-slate-300 font-mono">{loc.free_flow_speed_kmh} km/h</td>
                        <td className="py-2.5 px-2">
                          <CongestionBadge percentage={loc.avg_congestion_pct || loc.congestion_percentage} />
                        </td>
                        <td className="py-2.5 px-2 text-right">
                          <button
                            onClick={() => handleSelectMapLocation(loc)}
                            className="p-1 text-cyan-400 hover:text-cyan-300 hover:bg-cyan-950/40 rounded transition-colors"
                            title="Analyze Location"
                          >
                            <ArrowUpRight className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        </>
      ) : null}
    </div>
  );
};
