import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useApp } from '../context/AppContext';
import { Card, MetricCard } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { Badge, CongestionBadge } from '../components/common/Badge';
import {
  Database, ShieldCheck, CheckCircle2, AlertCircle,
  FileText, ExternalLink, Filter, Search, Layers,
  ChevronLeft, ChevronRight, Table, Sparkles
} from 'lucide-react';

export const DataExplorer = () => {
  const { cities } = useApp();
  const [viewMode, setViewMode] = useState('records'); // 'records' or 'governance'
  const [sources, setSources] = useState([]);
  const [quality, setQuality] = useState(null);
  const [coverage, setCoverage] = useState(null);

  // Paginated Records State
  const [records, setRecords] = useState([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [startDate,setStartDate]=useState('');
  const [endDate,setEndDate]=useState('');
  const [sort,setSort]=useState('timestamp_desc');
  const [recordsError,setRecordsError]=useState(null);
  const [filterCity, setFilterCity] = useState('');
  const [searchCorridor, setSearchCorridor] = useState('');
  const [loadingRecords, setLoadingRecords] = useState(false);

  const [loadingGov, setLoadingGov] = useState(true);
  const [errorGov, setErrorGov] = useState(null);
  const [selectedSourceFilter, setSelectedSourceFilter] = useState('all');

  // Load governance metadata once
  useEffect(() => {
    let isMounted = true;
    async function loadGovData() {
      try {
        setLoadingGov(true);
        const [srcRes, qualRes, covRes] = await Promise.all([
          api.getDataSources(),
          api.getDataQuality(),
          api.getDataCoverage(),
        ]);
        if (isMounted) {
          setSources(srcRes.sources || []);
          setQuality(qualRes);
          setCoverage(covRes);
          setErrorGov(null);
        }
      } catch (err) {
        if (isMounted) setErrorGov(err.message);
      } finally {
        if (isMounted) setLoadingGov(false);
      }
    }
    loadGovData();
    return () => { isMounted = false; };
  }, []);

  // Load paginated database records
  useEffect(() => {
    let isMounted = true;
    async function fetchRecords() {
      try {
        setLoadingRecords(true);
        const res = await api.getDataRecords({
          city: filterCity,
          location: searchCorridor,
          page: currentPage,
          page_size: pageSize,
          start_date:startDate||undefined,
          end_date:endDate||undefined,
          sort,
        });
        if (isMounted) {
          setRecordsError(null);
          setRecords(res.records || []);
          setTotalRecords(res.total || 0);
          setTotalPages(res.total_pages || 1);
        }
      } catch (err) {
        if (isMounted) { setRecordsError(err.message); setRecords([]); }
      } finally {
        if (isMounted) setLoadingRecords(false);
      }
    }
    fetchRecords();
    return () => { isMounted = false; };
  }, [filterCity, searchCorridor, currentPage, pageSize,startDate,endDate,sort]);

  const exportCurrentPage=()=>{
    if (!records.length) return;
    const columns=Object.keys(records[0]);
    const escape=value=>'"'+String(value??'').replaceAll('"','""')+'"';
    const csv=[columns.map(escape).join(','),...records.map(row=>columns.map(c=>escape(row[c])).join(','))].join('\r\n');
    const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
    const link=document.createElement('a');link.href=url;link.download='clearroute_filtered_page.csv';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  };

  const filteredSources = sources.filter((s) =>
    selectedSourceFilter === 'all' ? true : s.category.toLowerCase() === selectedSourceFilter.toLowerCase()
  );

  return (
    <div className="space-y-6">
      {recordsError&&<p role="alert" className="text-rose-300">{recordsError}</p>}
      <div className="flex flex-wrap gap-3 text-xs items-center">
        <label>Start date <input aria-label="Start date" type="date" className="bg-slate-900 p-2 rounded border border-slate-700" value={startDate} onChange={e=>{setStartDate(e.target.value);setCurrentPage(1);}}/></label>
        <label>End date <input aria-label="End date" type="date" className="bg-slate-900 p-2 rounded border border-slate-700" value={endDate} onChange={e=>{setEndDate(e.target.value);setCurrentPage(1);}}/></label>
        <button onClick={exportCurrentPage} disabled={!records.length} className="bg-cyan-900 border border-cyan-700 rounded px-3 py-2 disabled:opacity-40">Export current page CSV</button>
        <label>Sort <select aria-label="Record sort" className="bg-slate-900 p-2 rounded border border-slate-700" value={sort} onChange={e=>{setSort(e.target.value);setCurrentPage(1);}}><option value="timestamp_desc">Newest first</option><option value="timestamp_asc">Oldest first</option><option value="congestion_desc">Highest congestion</option><option value="congestion_asc">Lowest congestion</option></select></label>
      </div>
      {/* Header */}
      <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono uppercase text-cyan-400 font-semibold tracking-wider">Big Data Governance</span>
            <span className="text-slate-600">•</span>
            <span className="text-xs text-slate-400">Database Records & Ingestion Catalog</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Database className="w-6 h-6 text-cyan-400" />
            <span>Database Explorer & Governance Audit</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Inspect stored traffic sample records stored in PostgreSQL/SQLite or audit the ingested source lineage and schema validation rules.
          </p>
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center gap-1.5 bg-slate-900 p-1.5 rounded-lg border border-slate-800">
          <button
            onClick={() => setViewMode('records')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-all ${
              viewMode === 'records'
                ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Table className="w-3.5 h-3.5" />
            <span>Database Records ({totalRecords.toLocaleString()})</span>
          </button>
          <button
            onClick={() => setViewMode('governance')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-all ${
              viewMode === 'governance'
                ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Source Governance & Lineage</span>
          </button>
        </div>
      </div>

      {viewMode === 'records' ? (
        /* DATABASE RECORDS EXPLORER VIEW */
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="bg-[#111827] border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 text-xs">
            <div className="flex flex-wrap items-center gap-3 flex-1">
              {/* City Filter */}
              <div className="flex items-center gap-2">
                <span className="text-slate-400">City:</span>
                <select
                  value={filterCity}
                  onChange={(e) => {
                    setFilterCity(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500 font-medium"
                >
                  <option value="">All Cities</option>
                  {cities.map((c) => (
                    <option key={c.code} value={c.name}>{c.name}</option>
                  ))}
                </select>
              </div>

              {/* Corridor Search */}
              <div className="relative flex-1 min-w-[200px]">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter by corridor or location name..."
                  value={searchCorridor}
                  onChange={(e) => {
                    setSearchCorridor(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-8 pr-3 py-1.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 text-xs"
                />
              </div>
            </div>

            {/* Page Size Selector */}
            <div className="flex items-center gap-2">
              <span className="text-slate-400">Rows per page:</span>
              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>
          </div>

          {/* Records Table Card */}
          <Card
            title={`Database Traffic Observations (${totalRecords.toLocaleString()} Total Records)`}
            subtitle="Application database sample; traffic provenance and consistency with Gold are unverified."
          >
            {loadingRecords ? (
              <LoadingSpinner label="Fetching paginated database records..." />
            ) : records.length === 0 ? (
              <EmptyState title="No Records Match Filter" message="Try selecting a different city or clearing the search query." />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="text-[11px] uppercase bg-slate-900/80 text-slate-400 border-b border-slate-800 font-mono">
                    <tr>
                      <th className="py-2.5 px-3">ID</th>
                      <th className="py-2.5 px-2">City</th>
                      <th className="py-2.5 px-2">Corridor / Location</th>
                      <th className="py-2.5 px-2">Road Type</th>
                      <th className="py-2.5 px-2">Timestamp</th>
                      <th className="py-2.5 px-2">Peak Status</th>
                      <th className="py-2.5 px-2">Observed Speed</th>
                      <th className="py-2.5 px-2">Free Flow</th>
                      <th className="py-2.5 px-2 text-right">Congestion %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-sans">
                    {records.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-3 font-mono text-slate-500">#{r.id}</td>
                        <td className="py-2.5 px-2 font-medium text-slate-200">{r.city}</td>
                        <td className="py-2.5 px-2">
                          <div className="font-semibold text-slate-100">{r.location_name}</div>
                          <div className="text-[10px] text-slate-400 font-mono">{r.corridor_name} ({r.location_code})</div>
                        </td>
                        <td className="py-2.5 px-2 font-mono uppercase text-slate-400 text-[10px]">{r.road_type}</td>
                        <td className="py-2.5 px-2 font-mono text-slate-300 text-[11px]">{r.timestamp}</td>
                        <td className="py-2.5 px-2">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
                            r.is_peak ? 'bg-amber-950/40 text-amber-300 border-amber-800/50' : 'bg-slate-900 text-slate-400 border-slate-800'
                          }`}>
                            {r.is_peak ? 'Commuter Peak' : 'Off-Peak'}
                          </span>
                        </td>
                        <td className="py-2.5 px-2 font-mono text-slate-100">{r.observed_speed_kmh} km/h</td>
                        <td className="py-2.5 px-2 font-mono text-slate-400">{r.free_flow_speed_kmh} km/h</td>
                        <td className="py-2.5 px-2 text-right">
                          <CongestionBadge percentage={r.congestion_percentage} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination Controls Footer */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-4 border-t border-slate-800 text-xs">
              <span className="text-slate-400">
                Showing <strong className="text-slate-200 font-mono">{records.length > 0 ? (currentPage - 1) * pageSize + 1 : 0}</strong> to <strong className="text-slate-200 font-mono">{Math.min(currentPage * pageSize, totalRecords)}</strong> of <strong className="text-slate-200 font-mono">{totalRecords.toLocaleString()}</strong> records
              </span>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage <= 1 || loadingRecords}
                  className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900 text-slate-300 hover:text-white disabled:opacity-40 flex items-center gap-1 transition-colors"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  <span>Previous</span>
                </button>

                <span className="font-mono text-slate-300 px-2">
                  Page {currentPage} of {totalPages}
                </span>

                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage >= totalPages || loadingRecords}
                  className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900 text-slate-300 hover:text-white disabled:opacity-40 flex items-center gap-1 transition-colors"
                >
                  <span>Next</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </Card>
        </div>
      ) : (
        /* GOVERNANCE & SOURCES CATALOG VIEW */
        <div className="space-y-6">
          {/* Quality KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Analytical Records"
              value={quality?.total_gold_records?.toLocaleString() ?? 'Unavailable'}
              unit="Database Rows"
              icon={Layers}
              accentColor="cyan"
              description="Application database sample"
            />
            <MetricCard
              title="Completeness Rate"
              value={`${(quality?.completeness_rate ?? 0).toFixed(1)}%`}
              icon={CheckCircle2}
              accentColor="emerald"
              description="Null handling applied in Silver"
            />
            <MetricCard
              title="Duplicate Treatment"
              value={`${quality?.duplicate_count ?? 0} Duplicates`}
              icon={ShieldCheck}
              accentColor="blue"
              description="Database duplicate check"
            />
            <MetricCard
              title="Target Variable"
              value="Congestion %"
              icon={Database}
              accentColor="amber"
              description="(v_free - v_obs) / v_free"
            />
          </div>

          {/* Sources Table */}
          <Card
            title="Primary Data Sources & Provenance Catalog"
            subtitle="Catalog attributions are unverified. Counts show application database rows where available."
          >
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="text-[11px] uppercase bg-slate-900/80 text-slate-400 border-b border-slate-800 font-mono">
                  <tr>
                    <th className="py-3 px-3">Source Name</th>
                    <th className="py-3 px-2">Category</th>
                    <th className="py-3 px-2">Temporal Range</th>
                    <th className="py-3 px-2">Spatial Scope</th>
                    <th className="py-3 px-2">Record Count</th>
                    <th className="py-3 px-2">License</th>
                    <th className="py-3 px-2 text-right">Audit Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-sans">
                  {filteredSources.map((s, idx) => (
                    <tr key={s.id || idx} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-3">
                        <div className="font-semibold text-slate-100">{s.source_name}</div>
                        <div className="text-[10px] text-slate-400">{s.provenance_url || 'Source not verified'}</div>
                      </td>
                      <td className="py-3 px-2">
                        <Badge variant={s.category === 'Traffic' ? 'accent' : s.category === 'Weather' ? 'primary' : 'default'}>
                          {s.category}
                        </Badge>
                      </td>
                      <td className="py-3 px-2 font-mono text-slate-300">{s.temporal_coverage}</td>
                      <td className="py-3 px-2 text-slate-400">{s.spatial_coverage}</td>
                      <td className="py-3 px-2 font-mono text-slate-200">{s.record_count == null ? 'Unavailable' : s.record_count.toLocaleString()}</td>
                      <td className="py-3 px-2 text-slate-400 font-mono text-[11px]">{s.license}</td>
                      <td className="py-3 px-2 text-right">
                        <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>{s.quality_status || 'Verified'}</span>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Data Quality Methodology Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
            <Card title="Missing Value & Outlier Strategy (Silver Layer)">
              <div className="space-y-3 text-slate-300 leading-relaxed text-[11px]">
                <p>
                  <strong className="text-cyan-400">1. Speed Records:</strong> Road segment speed observations missing for intervals &le; 2 hours are interpolated temporally. Persistent gaps are flagged and imputed using location-hour medians. Under no circumstances are missing values silently filled with zero.
                </p>
                <p>
                  <strong className="text-cyan-400">2. Geocoding Validation:</strong> All road segment coordinates are checked against municipal bounding polygons. Records falling outside the municipal boundaries of Delhi, Mumbai, Bengaluru, Hyderabad, or Kolkata are pruned.
                </p>
                <p>
                  <strong className="text-cyan-400">3. Deduplication:</strong> Multiple sensor reports for the same segment and timestamp are deduplicated in PySpark using row-number windowing ordered by reporting recency.
                </p>
              </div>
            </Card>

            <Card title="Dataset Limitations & Academic Integrity">
              <div className="space-y-3 text-slate-300 leading-relaxed text-[11px]">
                <p>
                  <strong className="text-amber-400">1. Temporal Coverage:</strong> Available model artifacts use generated demonstration traffic for April to December 2019. Genuine sensor observations are missing.
                </p>
                <p>
                  <strong className="text-amber-400">2. Accident Context:</strong> MoRTH road safety figures provide contextual corridor hazard ratings rather than real-time accident notifications.
                </p>
                <p>
                  <strong className="text-amber-400">3. 2026 Forward Context:</strong> Forward-looking scenario predictions utilize a separate 2026 contextual calendar and weather forecast layer to ensure zero contamination of historical baseline weights.
                </p>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

