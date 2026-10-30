import React from 'react';
import { useApp } from './context/AppContext';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';

import { Overview } from './pages/Overview';
import { CityAnalytics } from './pages/CityAnalytics';
import { LocationAnalytics } from './pages/LocationAnalytics';
import { CongestionPrediction } from './pages/CongestionPrediction';
import { EventImpact } from './pages/EventImpact';
import { WeatherImpact } from './pages/WeatherImpact';
import { ModelPerformance } from './pages/ModelPerformance';
import { DataExplorer } from './pages/DataExplorer';
import { Reports } from './pages/Reports';
import { Settings } from './pages/Settings';

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
      <div className="pl-64 flex flex-col flex-1 min-w-0">
        <Header />
        <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
          {renderActiveTab()}
        </main>
      </div>
    </div>
  );
};

export default App;
