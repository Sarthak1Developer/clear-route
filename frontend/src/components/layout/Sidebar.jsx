import React from 'react';
import { useApp } from '../../context/AppContext';
import {
  LayoutDashboard,
  Building2,
  MapPin,
  TrendingUp,
  Calendar,
  CloudRain,
  Cpu,
  Database,
  FileBarChart,
  Settings,
  Activity,
  Layers,
} from 'lucide-react';

export const Sidebar = () => {
  const { activeTab, setActiveTab, healthStatus } = useApp();

  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'city-analytics', label: 'City Analytics', icon: Building2 },
    { id: 'location-analytics', label: 'Location Analytics', icon: MapPin },
    { id: 'congestion-prediction', label: 'Congestion Prediction', icon: TrendingUp, highlight: true },
    { id: 'event-impact', label: 'Event Impact', icon: Calendar },
    { id: 'weather-impact', label: 'Weather Impact', icon: CloudRain },
    { id: 'model-performance', label: 'Model Performance', icon: Cpu },
    { id: 'data-explorer', label: 'Data Explorer', icon: Database },
    { id: 'reports', label: 'Reports & Power BI', icon: FileBarChart },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-[#0E1526] border-r border-slate-800 flex flex-col h-screen fixed left-0 top-0 z-30 select-none">
      {/* Brand Header */}
      <div className="h-16 px-5 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-950/50">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-base tracking-tight text-white font-mono">CLEAR<span className="text-cyan-400">ROUTE</span></span>
              <span className="text-[10px] px-1.5 py-0.2 bg-cyan-950 text-cyan-300 border border-cyan-800/60 rounded font-mono">v1.0</span>
            </div>
            <p className="text-[10px] text-slate-400 uppercase tracking-wider font-medium">Traffic Analytics & AI</p>
          </div>
        </div>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-800">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">
          Analytics Engine
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-150 group ${
                isActive
                  ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 shadow-sm shadow-cyan-950/40 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
              }`}
            >
              <Icon
                className={`w-4 h-4 transition-colors ${
                  isActive ? 'text-cyan-400' : 'text-slate-500 group-hover:text-slate-300'
                }`}
              />
              <span className="truncate">{item.label}</span>
              {item.highlight && (
                <span className="ml-auto flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* System Status Footer */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/40 text-xs">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[11px] text-slate-400 font-medium">Inference Engine</span>
          <div className="flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                healthStatus.online ? 'bg-emerald-400 shadow-sm shadow-emerald-500/50' : 'bg-amber-400'
              }`}
            />
            <span className="text-[11px] text-slate-300 font-mono">
              {healthStatus.online ? 'Online' : 'Standby'}
            </span>
          </div>
        </div>
        <div className="text-[10px] text-slate-500 font-mono truncate">
          Scope: 5 Metro Cities (2019/2026)
        </div>
      </div>
    </aside>
  );
};
