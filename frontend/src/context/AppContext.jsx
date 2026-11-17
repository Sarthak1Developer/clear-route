import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

const AppContext = createContext();

export const CITIES = [
  { code: 'DEL', name: 'Delhi', state: 'Delhi NCT', lat: 28.6139, lng: 77.2090, zoom: 12 },
  { code: 'BOM', name: 'Mumbai', state: 'Maharashtra', lat: 19.0760, lng: 72.8777, zoom: 12 },
  { code: 'BLR', name: 'Bengaluru', state: 'Karnataka', lat: 12.9716, lng: 77.5946, zoom: 12 },
  { code: 'HYD', name: 'Hyderabad', state: 'Telangana', lat: 17.3850, lng: 78.4867, zoom: 12 },
  { code: 'CCU', name: 'Kolkata', state: 'West Bengal', lat: 22.5726, lng: 88.3639, zoom: 12 },
];

const DEFAULT_SETTINGS = {
  defaultCityCode: 'DEL',
  defaultModel: 'xgboost',
  temperatureUnit: 'C',
  refreshInterval: 30,
  toastEnabled: true,
  mapZoom: 12,
};

export const AppProvider = ({ children }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [cities, setCities] = useState(CITIES);
  const [selectedCity, setSelectedCity] = useState(CITIES[0]);
  const [healthStatus, setHealthStatus] = useState({ online: false, checking: true, details: null });
  const [toast, setToast] = useState(null);

  // Persistent settings state
  const [settings, setSettings] = useState(() => {
    try {
      const stored = localStorage.getItem('clearroute_settings');
      return stored ? { ...DEFAULT_SETTINGS, ...JSON.parse(stored) } : DEFAULT_SETTINGS;
    } catch {
      return DEFAULT_SETTINGS;
    }
  });

  const updateSettings = (newSettings) => {
    setSettings((prev) => {
      const updated = { ...prev, ...newSettings };
      try {
        localStorage.setItem('clearroute_settings', JSON.stringify(updated));
      } catch (e) {
        console.error('Failed to save settings:', e);
      }
      return updated;
    });
  };

  const resetSettings = () => {
    setSettings(DEFAULT_SETTINGS);
    try {
      localStorage.removeItem('clearroute_settings');
    } catch (e) {
      console.error('Failed to reset settings:', e);
    }
  };

  const showToast = (message, type = 'info') => {
    if (!settings.toastEnabled && type !== 'error') return;
    setToast({ message, type, id: Date.now() });
    setTimeout(() => setToast(null), 4000);
  };

  const checkHealth = async () => {
    try {
      const data = await api.getHealth();
      setHealthStatus({ online: true, checking: false, details: data });
    } catch (err) {
      setHealthStatus({ online: false, checking: false, details: null, error: err.message });
    }
  };

  // Load real cities from backend
  useEffect(() => {
    let isMounted = true;
    async function fetchCities() {
      try {
        const fetched = await api.getCities();
        if (isMounted && Array.isArray(fetched) && fetched.length > 0) {
          setCities(fetched);
          // If default city setting is configured, select it
          const preferred = fetched.find((c) => c.code === settings.defaultCityCode);
          if (preferred) {
            setSelectedCity(preferred);
          } else {
            setSelectedCity(fetched[0]);
          }
        }
      } catch {
        // Keep initial CITIES
      }
    }
    fetchCities();
    return () => { isMounted = false; };
  }, [settings.defaultCityCode]);

  useEffect(() => {
    checkHealth();
    const intervalSec = Number(settings.refreshInterval) || 30;
    if (intervalSec <= 0) return;
    const interval = setInterval(checkHealth, intervalSec * 1000);
    return () => clearInterval(interval);
  }, [settings.refreshInterval]);

  return (
    <AppContext.Provider
      value={{
        activeTab,
        setActiveTab,
        selectedCity,
        setSelectedCity,
        cities,
        healthStatus,
        checkHealth,
        toast,
        showToast,
        settings,
        updateSettings,
        resetSettings,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};


export const useApp = () => useContext(AppContext);
