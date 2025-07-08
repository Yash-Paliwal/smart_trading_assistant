// src/api/apiService.js

import axios from 'axios';

// The proxy in setupProxy.js will forward these requests.
const API_BASE_URL = '/api';

// Function to get the CSRF token from cookies
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}


// --- Axios Instance Configuration ---
// Create a global axios instance with default settings.
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  // **THE FIX:** This tells axios to send cookies with every request.
  // This is necessary for Django's session authentication to work.
  withCredentials: true, 
});


// Attach CSRF token to each request
apiClient.interceptors.request.use(config => {
  const csrfToken = getCookie('csrftoken');
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken;
  }
  return config;
});

// --- Auth Functions ---

/**
 * Fetches the data for the currently logged-in user.
 */
export const getCurrentUser = () => {
  return apiClient.get(`/api/auth/user/`);
};

/**
 * Sends a request to the backend to log the user out.
 */
export const logout = () => {
  return apiClient.post(`/auth/logout/`);
};


// --- Data Functions ---

/**
 * Fetches the list of all radar alerts.
 */
export const getAlerts = () => {
  return apiClient.get(`/api/alerts/`);
};

/**
 * Fetches the list of all existing trade logs (trade plans).
 */
export const getTradeLogs = () => {
  return apiClient.get(`/api/tradelogs/`);
};

/**
 * Creates a new trade plan (TradeLog entry).
 * @param {object} tradePlan - The trade plan data.
 */
export const createTradeLog = (tradePlan) => {
  return apiClient.post(`/api/tradelogs/`, tradePlan);
};

/**
 * Updates an existing trade log (e.g., to activate it or close it).
 * @param {number} id - The ID of the trade log to update.
 * @param {object} updateData - The data to update.
 */
export const updateTradeLog = (id, updateData) => {
  return apiClient.patch(`/api/tradelogs/${id}/`, updateData);
};

/**
 * Deletes a trade log.
 * @param {number} id - The ID of the trade log to delete.
 */
export const deleteTradeLog = (id) => {
  return apiClient.delete(`/api/tradelogs/${id}/`);
};

export const getVirtualTradingDashboard = async () => {
  return await apiClient.get('/api/virtual-trading-dashboard/');
};

/**
 * Fetches the full premarket screener list for today, with entry alert status for each stock.
 */
export const getScreenerStatus = () => {
  return apiClient.get(`/screener-status/`);
};
