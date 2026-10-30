/**
 * ClearRoute - API Service Layer
 * Communicates with FastAPI backend with structured error handling
 */

const BASE_URL = import.meta.env.VITE_API_URL || '/api';

async function handleResponse(response) {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message = errorData.detail || errorData.message || `HTTP Error ${response.status}: ${response.statusText}`;
    throw new Error(message);
  }
  return response.json();
}

export const api = {
  // System Health & Overview
  async getHealth() {
    return fetch(`${BASE_URL}/health`).then(handleResponse);
  },

  async getOverview() {
    return fetch(`${BASE_URL}/overview`).then(handleResponse);
  },

  // Cities
  async getCities() {
    return fetch(`${BASE_URL}/cities`).then(handleResponse);
  },

  async getCitySummary(city) {
    return fetch(`${BASE_URL}/cities/${encodeURIComponent(city)}/summary`).then(handleResponse);
  },

  async getCityLocations(city) {
    return fetch(`${BASE_URL}/cities/${encodeURIComponent(city)}/locations`).then(handleResponse);
  },

  // Locations
  async searchLocations(query = '', city = '') {
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (city) params.append('city', city);
    return fetch(`${BASE_URL}/locations/search?${params.toString()}`).then(handleResponse);
  },

  async getLocationHistory(locationId, filters = {}) {
    const params = new URLSearchParams(filters);
    return fetch(`${BASE_URL}/locations/${encodeURIComponent(locationId)}/history?${params.toString()}`).then(handleResponse);
  },

  async getLocationTrends(locationId) {
    return fetch(`${BASE_URL}/locations/${encodeURIComponent(locationId)}/trends`).then(handleResponse);
  },

  // Predictions
  async getAvailableModels() {
    return fetch(`${BASE_URL}/models`).then(handleResponse);
  },

  async predictCongestion(payload) {
    return fetch(`${BASE_URL}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(handleResponse);
  },

  async getPredictionById(predictionId) {
    return fetch(`${BASE_URL}/predictions/${encodeURIComponent(predictionId)}`).then(handleResponse);
  },

  // Events
  async getEvents(city = '') {
    const url = city ? `${BASE_URL}/events/${encodeURIComponent(city)}` : `${BASE_URL}/events`;
    return fetch(url).then(handleResponse);
  },

  async getEventImpact() {
    return fetch(`${BASE_URL}/events/impact`).then(handleResponse);
  },

  // Weather
  async getWeather(city = '') {
    const params = city ? `?city=${encodeURIComponent(city)}` : '';
    return fetch(`${BASE_URL}/weather${params}`).then(handleResponse);
  },

  async getWeatherImpact() {
    return fetch(`${BASE_URL}/weather/impact`).then(handleResponse);
  },

  // Model Performance & Explainability
  async getModelPerformance() {
    return fetch(`${BASE_URL}/models/performance`).then(handleResponse);
  },

  async getFeatureImportance() {
    return fetch(`${BASE_URL}/models/feature-importance`).then(handleResponse);
  },

  async getExplainability() {
    return fetch(`${BASE_URL}/models/explainability`).then(handleResponse);
  },

  // Data Explorer
  async getDataSources() {
    return fetch(`${BASE_URL}/data/sources`).then(handleResponse);
  },

  async getDataQuality() {
    return fetch(`${BASE_URL}/data/quality`).then(handleResponse);
  },

  async getDataCoverage() {
    return fetch(`${BASE_URL}/data/coverage`).then(handleResponse);
  },

  // Reports
  async exportDataset(datasetKey) {
    window.open(`${BASE_URL}/reports/export/${encodeURIComponent(datasetKey)}`, '_blank');
  }
};
