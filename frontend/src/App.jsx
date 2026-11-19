import {DataReadiness} from './components/common/DataReadiness';
import React, { lazy, Suspense } from 'react';
import { useApp } from './context/AppContext';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';

const Overview = lazy(() => import('./pages/Overview').then(module => ({ default: module.Overview })));
const CityAnalytics = lazy(() => import('./pages/CityAnalytics').then(module => ({ default: module.CityAnalytics })));
const LocationAnalytics = lazy(() => import('./pages/LocationAnalytics').then(module => ({ default: module.LocationAnalytics })));
const CongestionPrediction = lazy(() => import('./pages/CongestionPrediction').then(module => ({ default: module.CongestionPrediction })));
const EventImpact = lazy(() => import('./pages/EventImpact').then(module => ({ default: module.EventImpact })));
const WeatherImpact = lazy(() => import('./pages/WeatherImpact').then(module => ({ default: module.WeatherImpact })));
const ModelPerformance = lazy(() => import('./pages/ModelPerformance').then(module => ({ default: module.ModelPerformance })));
const DataExplorer = lazy(() => import('./pages/DataExplorer').then(module => ({ default: module.DataExplorer })));
const Reports = lazy(() => import('./pages/Reports').then(module => ({ default: module.Reports })));
const Settings = lazy(() => import('./pages/Settings').then(module => ({ default: module.Settings })));

export const App = () => {
  const { activeTab } = useApp();

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'overview':
        return <Overview />;
      case 'city-analytics':
        return <CityAnalytics />;
      case 'location-analytics':
        return <LocationAnalytics />;
      case 'congestion-prediction':
        return <CongestionPrediction />;
      case 'event-impact':
        return <EventImpact />;
      case 'weather-impact':
        return <WeatherImpact />;
      case 'model-performance':
        return <ModelPerformance />;
      case 'data-explorer':
        return <DataExplorer />;
      case 'reports':
        return <Reports />;
      case 'settings':
        return <Settings />;
      default:
        return <Overview />;
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0F1D] text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-slate-950">
      {/* Fixed Left Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="md:pl-64 flex flex-col flex-1 min-w-0">
        <Header />
        <main className="flex-1 p-3 sm:p-6 max-w-7xl w-full mx-auto">
          <DataReadiness/>
          <Suspense fallback={<p role="status">Loading analytics page…</p>}>{renderActiveTab()}</Suspense>
        </main>
      </div>
    </div>
  );
};

export default App;
