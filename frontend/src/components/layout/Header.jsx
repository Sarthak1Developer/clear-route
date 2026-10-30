import React from 'react';
import { useApp } from '../../context/AppContext';
import { Building2, ShieldCheck, Sparkles, AlertTriangle, CheckCircle, Info } from 'lucide-react';

export const Header = () => {
  const { cities, selectedCity, setSelectedCity, healthStatus, toast } = useApp();

  return (
    <header className="h-16 bg-[#0E1526]/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-20 px-6 flex items-center justify-between">
      {/* City Selector */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-700/80 rounded-lg px-3 py-1.5 shadow-inner">
          <Building2 className="w-4 h-4 text-cyan-400" />
          <span className="text-xs text-slate-400 font-medium">Metropolitan City:</span>
          <select
            value={selectedCity.code}
            onChange={(e) => {
              const city = cities.find((c) => c.code === e.target.value);
              if (city) setSelectedCity(city);
            }}
            className="bg-transparent text-xs font-semibold text-slate-100 focus:outline-none cursor-pointer pr-2"
          >
            {cities.map((city) => (
              <option key={city.code} value={city.code} className="bg-slate-900 text-slate-100">
                {city.name} ({city.state})
              </option>
            ))}
          </select>
        </div>

        <div className="hidden md:flex items-center gap-2 text-xs text-slate-400">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-slate-600"></span>
          <span>Lat: <strong className="text-slate-300 font-mono">{selectedCity.lat.toFixed(4)}°N</strong></span>
          <span>Lng: <strong className="text-slate-300 font-mono">{selectedCity.lng.toFixed(4)}°E</strong></span>
        </div>
      </div>

      {/* Right Badges & Indicators */}
      <div className="flex items-center gap-3">
        <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded bg-slate-800/40 border border-slate-700/50 text-[11px] text-slate-300">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Zenodo Uber Movement · OpenStreetMap · ERA5 Weather</span>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1 bg-cyan-950/40 border border-cyan-800/60 rounded-lg text-xs font-medium text-cyan-300">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-mono">Primary: XGBoost + SHAP</span>
        </div>
      </div>

      {/* Toast Notification Container */}
      {toast && (
        <div className="fixed top-20 right-6 z-50 animate-bounce duration-300">
          <div
            className={`flex items-center gap-2.5 px-4 py-2.5 rounded-lg border shadow-xl text-xs font-medium ${
              toast.type === 'error'
                ? 'bg-rose-950 border-rose-800 text-rose-200'
                : toast.type === 'success'
                ? 'bg-emerald-950 border-emerald-800 text-emerald-200'
                : 'bg-slate-900 border-slate-700 text-slate-200'
            }`}
          >
            {toast.type === 'error' && <AlertTriangle className="w-4 h-4 text-rose-400" />}
            {toast.type === 'success' && <CheckCircle className="w-4 h-4 text-emerald-400" />}
            {toast.type === 'info' && <Info className="w-4 h-4 text-cyan-400" />}
            <span>{toast.message}</span>
          </div>
        </div>
      )}
    </header>
  );
};
