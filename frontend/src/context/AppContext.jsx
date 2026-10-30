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

export const AppProvider = ({ children }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedCity, setSelectedCity] = useState(CITIES[0]);
  const [healthStatus, setHealthStatus] = useState({ online: false, checking: true, details: null });
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'info') => {
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

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <AppContext.Provider
      value={{
        activeTab,
        setActiveTab,
        selectedCity,
        setSelectedCity,
        cities: CITIES,
        healthStatus,
        checkHealth,
        toast,
        showToast,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);
