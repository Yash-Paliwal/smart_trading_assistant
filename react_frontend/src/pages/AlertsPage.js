// src/pages/AlertsPage.js

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { getAlerts, getTradeLogs, createTradeLog, getScreenerStatus } from '../api/apiService';
import AlertCard from '../components/AlertCard';
import TradePlanModal from '../components/TradePlanModal';
import websocketService from '../services/websocketService';
import { useToast } from '../components/ToastProvider';

const AlertsPage = ({ setCurrentPage }) => {
  const [alerts, setAlerts] = useState([]);
  const [plannedStockKeys, setPlannedStockKeys] = useState(new Set());
  const [marketTrend, setMarketTrend] = useState('NEUTRAL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedStock, setSelectedStock] = useState(null);
  
  // **NEW: Alert category management**
  const [alertCategory, setAlertCategory] = useState('ENTRY'); // ENTRY, SCREENING
  const [lastUpdate, setLastUpdate] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds
  const [isRefreshing, setIsRefreshing] = useState(false); // **NEW: Refresh state**

  // **NEW: Market status check**
  const [marketStatus, setMarketStatus] = useState({ isOpen: false });

  // **NEW: Scan results state**
  const [scanResults, setScanResults] = useState(null);
  const [isScanning, setIsScanning] = useState(false);

  const [livePrices, setLivePrices] = useState({});
  const [screenerStocks, setScreenerStocks] = useState([]); // For new screener API
  const [screenerFilter, setScreenerFilter] = useState('ALL'); // ALL, WAITING, TRIGGERED
  const entryAlertRefs = useRef({}); // For smooth scroll
  const [highlightedEntryId, setHighlightedEntryId] = useState(null); // For microinteraction
  const [showExpired, setShowExpired] = useState(false);

  const toast = useToast();

  useEffect(() => {
    const checkMarketStatus = () => {
      const now = new Date();
      const currentDay = now.getDay();
      
      if (currentDay === 0 || currentDay === 6) {
        setMarketStatus({ isOpen: false });
        return;
      }
      
      const marketOpen = new Date(now);
      marketOpen.setHours(9, 15, 0, 0);
      
      const marketClose = new Date(now);
      marketClose.setHours(15, 30, 0, 0);
      
      const isOpen = now >= marketOpen && now <= marketClose;
      setMarketStatus({ isOpen });
    };
    
    checkMarketStatus();
    const interval = setInterval(checkMarketStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handlePriceUpdate = (data) => {
      console.log("Received price update:", data); // DEBUG LOG
      setLivePrices(prev => ({
        ...prev,
        [data.instrument_key]: data.current_price
      }));
    };
    
    // Connect to price WebSocket for live updates
    websocketService.connectPrices();
    
    websocketService.on('price_update', handlePriceUpdate);
    return () => {
      websocketService.off('price_update', handlePriceUpdate);
    };
  }, []);

  const fetchPageData = useCallback(async () => {
    try {
      let screeningData = [];
      let alertsData = [];
      let tradeLogsResponse = await getTradeLogs();
      const plannedKeys = new Set((tradeLogsResponse.data.results || []).map(log => log.instrument_key));
      setPlannedStockKeys(plannedKeys);

      if (alertCategory === 'SCREENING') {
        // Use new API for screening results
        const screenerResponse = await getScreenerStatus();
        screeningData = screenerResponse.data.results || [];
        setScreenerStocks(screeningData);
        setAlerts([]); // Not used for screening tab now
      } else {
        // Use old logic for ENTRY/ALL
        const alertsResponse = await getAlerts(`?category=${alertCategory}`);
        alertsData = alertsResponse.data.results || [];
        setAlerts(alertsData);
      }
      setLastUpdate(new Date());
      setError(null);
      setLoading(false);
      setIsRefreshing(false);
    } catch (err) {
      setError('Failed to fetch data. Make sure the Django API server is running.');
      setLoading(false);
      setIsRefreshing(false);
      console.error(err);
    }
  }, [alertCategory]);

  // **NEW: Trigger actual scanning function**
  const triggerScan = async () => {
    setIsScanning(true);
    setScanResults(null);
    
    try {
      // **NEW: Call the scanning endpoint**
      const response = await fetch('/api/trigger-scan/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          scan_type: 'comprehensive', // or 'screening', 'intraday'
          market_hours: marketStatus.isOpen
        })
      });
      
      if (!response.ok) {
        throw new Error(`Scan failed: ${response.statusText}`);
      }
      
      const scanData = await response.json();
      setScanResults(scanData);
      
      // **NEW: Show scan results notification**
      if (scanData.new_alerts > 0) {
        // You could add a toast notification here
        console.log(`Scan completed: ${scanData.new_alerts} new alerts found`);
        toast('Scan complete! New alerts found.', 'info');
      } else {
        console.log('Scan completed: No new alerts found');
      }
      
      // **NEW: Refresh the alerts data after scan**
      await fetchPageData();
      
    } catch (err) {
      console.error('Scan failed:', err);
      setError(`Scan failed: ${err.message}`);
      toast('Scan failed. Please try again.', 'error');
    } finally {
      setIsScanning(false);
    }
  };

  useEffect(() => {
    fetchPageData();
  }, [fetchPageData]);

  // **NEW: Auto-refresh functionality (only for entry alerts and when market is open)**
  useEffect(() => {
    if (!autoRefresh || alertCategory === 'SCREENING' || !marketStatus.isOpen) return;

    const interval = setInterval(() => {
      fetchPageData();
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchPageData, alertCategory, marketStatus.isOpen]);

  // **NEW: Clean up expired entry alerts from state**
  useEffect(() => {
    if (alertCategory === 'SCREENING') return;
    
    const interval = setInterval(() => {
      setAlerts(prevAlerts => 
        prevAlerts.filter(alert => {
          if (alert.is_time_sensitive && alert.remaining_minutes !== null && alert.remaining_minutes <= 0) {
            return false; // Remove expired entry alerts
          }
          return true;
        })
      );
    }, 60000); // Check every minute

    return () => clearInterval(interval);
  }, [alertCategory]);

  const handleOpenPlanModal = (stock) => {
    setSelectedStock(stock);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedStock(null);
  };

  const handleSavePlan = async (tradePlan) => {
    try {
      await createTradeLog(tradePlan);
      toast('Trade plan saved!', 'success');
      if (setCurrentPage) {
        setCurrentPage('plans');
      }
      handleCloseModal();
    } catch (err) {
      console.error("Failed to save trade plan:", err);
      toast('Failed to save trade plan. Please try again.', 'error');
    }
  };

  // **NEW: Enhanced manual refresh with actual scanning**
  const handleManualRefresh = async () => {
    if (isRefreshDisabled()) return;
    
    setIsRefreshing(true);
    setLoading(true);
    
    // **NEW: Trigger actual scan instead of just refreshing data**
    await triggerScan();
  };

  const handleCategoryChange = (category) => {
    setAlertCategory(category);
    setLoading(true);
  };

  // **NEW: Calculate statistics with better logic**
  const getStats = () => {
    const screeningAlerts = alerts.filter(alert => alert.category === 'SCREENING');
    const entryAlerts = alerts.filter(alert => alert.category === 'ENTRY');
    const highPriorityAlerts = alerts.filter(alert => alert.priority === 'HIGH');
    const expiringSoon = entryAlerts.filter(alert => 
      alert.remaining_minutes !== null && alert.remaining_minutes <= 15 && alert.remaining_minutes > 0
    );

    return {
      total: alerts.length,
      screening: screeningAlerts.length,
      entry: entryAlerts.length,
      highPriority: highPriorityAlerts.length,
      expiringSoon: expiringSoon.length
    };
  };

  const stats = getStats();

  // **NEW: Get refresh button text based on context**
  const getRefreshButtonText = () => {
    if (isScanning) return 'Scanning...';
    if (isRefreshing) return 'Refreshing...';
    if (!marketStatus.isOpen && alertCategory === 'ENTRY') return 'Market Closed';
    return 'Scan Now';
  };

  // **NEW: Check if refresh should be disabled**
  const isRefreshDisabled = () => {
    return isScanning || isRefreshing || (!marketStatus.isOpen && alertCategory === 'ENTRY');
  };

  // Stats for screening
  const getScreeningStats = () => {
    const total = screenerStocks.length;
    const triggered = screenerStocks.filter(s => s.entry_status === 'triggered').length;
    const waiting = total - triggered;
    return { total, triggered, waiting };
  };
  const screeningStats = getScreeningStats();

  // Filter for entry alerts (all non-SCREENING alert types)
  const entryAlerts = alerts.filter(alert => alert.alert_type !== 'SCREENING');
  // Filter for screening alerts (only SCREENING alert type)
  const screeningAlerts = alerts.filter(alert => alert.alert_type === 'SCREENING');

  // Filter out expired entry alerts for the ENTRY tab (strict: only show non-expired in main list)
  const filteredEntryAlerts = entryAlerts.filter(alert => {
    // Only show if NOT expired
    if (alert.status === 'EXPIRED') return false;
    if (typeof alert.remaining_minutes === 'number' && alert.remaining_minutes <= 0) return false;
    return true;
  });

  // Debug log for entry alerts being rendered
  if (typeof window !== 'undefined' && window.console) {
    console.log('Entry Alerts Rendered:', filteredEntryAlerts.map(a => [a.instrument_key, a.alert_type, a.id]));
  }

  // Collect expired entry alerts for collapsible section (strict: only expired)
  const expiredEntryAlerts = entryAlerts.filter(alert => {
    // Only show if expired
    if (alert.status === 'EXPIRED') return true;
    if (typeof alert.remaining_minutes === 'number' && alert.remaining_minutes <= 0) return true;
    return false;
  });

  // Filtered screening stocks for SCREENING tab
  const filteredScreenerStocks = screeningAlerts.filter(stock => {
    if (screenerFilter === 'ALL') return true;
    if (screenerFilter === 'WAITING') return stock.entry_status !== 'triggered';
    if (screenerFilter === 'TRIGGERED') return stock.entry_status === 'triggered';
    return true;
  });

  // Smooth scroll to entry alert
  const handleViewEntryAlert = (instrument_key) => {
    setCurrentPage && setCurrentPage('alerts');
    setTimeout(() => {
      if (entryAlertRefs.current[instrument_key]) {
        entryAlertRefs.current[instrument_key].scrollIntoView({ behavior: 'smooth', block: 'center' });
        setHighlightedEntryId(instrument_key);
        setTimeout(() => setHighlightedEntryId(null), 2000);
      }
    }, 100);
    setAlertCategory('ENTRY');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="container mx-auto p-4 md:p-8">
        {/* **NEW: Enhanced Header with Dashboard Stats */}
        <header className="text-center mb-12">
          <div className="mb-8">
            <h1 className="text-6xl font-extrabold mb-4 gradient-text">Radar Alerts</h1>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              High-confidence trade setups identified by our advanced AI engine with real-time market analysis
            </p>
          </div>
          
          {/* **NEW: Dashboard Statistics */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8 max-w-4xl mx-auto">
            <div className="glass p-4 rounded-xl border border-gray-600">
              <div className="text-2xl font-bold text-white">{stats.total}</div>
              <div className="text-sm text-gray-400">Total Alerts</div>
            </div>
            <div className="glass p-4 rounded-xl border border-gray-600">
              <div className="text-2xl font-bold text-green-400">{stats.screening}</div>
              <div className="text-sm text-gray-400">Screening</div>
            </div>
            <div className="glass p-4 rounded-xl border border-gray-600">
              <div className="text-2xl font-bold text-blue-400">{stats.entry}</div>
              <div className="text-sm text-gray-400">Entry Signals</div>
            </div>
            <div className="glass p-4 rounded-xl border border-gray-600">
              <div className="text-2xl font-bold text-red-400">{stats.highPriority}</div>
              <div className="text-sm text-gray-400">High Priority</div>
            </div>
            <div className="glass p-4 rounded-xl border border-gray-600">
              <div className="text-2xl font-bold text-orange-400">{stats.expiringSoon}</div>
              <div className="text-sm text-gray-400">Expiring Soon</div>
            </div>
          </div>
          
          {/* **NEW: Enhanced Alert category selector (ENTRY default, SCREENING secondary) */}
          <div className="mb-8">
            <div className="inline-flex bg-gray-800 rounded-xl p-1 shadow-lg border border-gray-700">
              <button
                onClick={() => setAlertCategory('ENTRY')}
                className={
                  alertCategory === 'ENTRY'
                    ? 'px-6 py-3 rounded-lg text-sm font-medium transition-all duration-200 bg-gradient-to-r from-red-600 to-pink-600 text-white shadow-lg'
                    : 'px-6 py-3 rounded-lg text-sm font-medium transition-all duration-200 text-gray-300 bg-transparent'
                }
              >
                <div className="flex items-center space-x-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span>Entry Alerts</span>
                </div>
              </button>
              <button
                onClick={() => setAlertCategory('SCREENING')}
                className={
                  alertCategory === 'SCREENING'
                    ? 'px-6 py-3 rounded-lg text-sm font-medium transition-all duration-200 bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-lg'
                    : 'px-6 py-3 rounded-lg text-sm font-medium transition-all duration-200 text-gray-300 bg-transparent'
                }
              >
                <div className="flex items-center space-x-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <span>Screened Picks</span>
                </div>
              </button>
            </div>
          </div>
          
          {/* **NEW: Enhanced Real-time status and controls (only for entry alerts) */}
          {alertCategory !== 'SCREENING' && (
            <div className="glass p-4 rounded-xl border border-gray-600 max-w-2xl mx-auto mb-8">
              <div className="flex flex-col md:flex-row items-center justify-center gap-4">
                {lastUpdate && (
                  <div className="flex items-center space-x-2">
                    <div className={`status-indicator ${marketStatus.isOpen ? 'status-active' : 'status-expired'}`}></div>
                    <span className="text-sm text-gray-300">
                      Last updated: {lastUpdate.toLocaleTimeString()}
                    </span>
                  </div>
                )}
                
                <div className="flex items-center gap-3">
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={autoRefresh && marketStatus.isOpen}
                      onChange={(e) => setAutoRefresh(e.target.checked)}
                      className="rounded bg-gray-700 border-gray-600 text-blue-500 focus:ring-blue-500"
                      disabled={!marketStatus.isOpen}
                    />
                    <span className="text-gray-300">Auto-refresh</span>
                  </label>
                  
                  <select
                    value={refreshInterval}
                    onChange={(e) => setRefreshInterval(Number(e.target.value))}
                    className="bg-gray-700 text-white px-3 py-1 rounded-lg text-sm border border-gray-600 focus:ring-blue-500 focus:border-blue-500"
                    disabled={!autoRefresh || !marketStatus.isOpen}
                  >
                    <option value={15}>15s</option>
                    <option value={30}>30s</option>
                    <option value={60}>1m</option>
                    <option value={120}>2m</option>
                  </select>
                  
                  <button
                    onClick={handleManualRefresh}
                    disabled={isRefreshDisabled()}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 shadow-md hover:shadow-lg ${
                      isRefreshDisabled()
                        ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                        : 'bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      {isScanning ? (
                        <div className="spinner w-4 h-4"></div>
                      ) : isRefreshing ? (
                        <div className="spinner w-4 h-4"></div>
                      ) : (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      )}
                      <span>{getRefreshButtonText()}</span>
                    </div>
                  </button>
                </div>
              </div>
              
              {/* **NEW: Market status message */}
              {!marketStatus.isOpen && alertCategory === 'ENTRY' && (
                <div className="mt-3 text-center">
                  <p className="text-sm text-gray-400">
                    Entry alerts are only available during market hours (9:15 AM - 3:30 PM IST)
                  </p>
                </div>
              )}
            </div>
          )}
          
          {/* **NEW: Scan Results Notification */}
          {scanResults && (
            <div className="mb-8">
              <div className={`glass p-4 rounded-xl border max-w-2xl mx-auto ${
                scanResults.new_alerts > 0 
                  ? 'border-green-500 bg-green-900/20' 
                  : 'border-blue-500 bg-blue-900/20'
              }`}>
                <div className="flex items-center justify-center space-x-3">
                  {scanResults.new_alerts > 0 ? (
                    <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  ) : (
                    <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  )}
                  <div className="text-center">
                    <p className={`font-semibold ${
                      scanResults.new_alerts > 0 ? 'text-green-400' : 'text-blue-400'
                    }`}>
                      Scan Completed
                    </p>
                    <p className="text-sm text-gray-400">
                      {scanResults.new_alerts > 0 
                        ? `${scanResults.new_alerts} new alerts found` 
                        : 'No new alerts found'
                      }
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Scanned {scanResults.stocks_scanned || 0} stocks in {scanResults.scan_duration || 0}s
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* **NEW: Enhanced Market trend indicator (only for screening alerts) */}
          {!loading && alertCategory !== 'ENTRY' && marketTrend !== 'NEUTRAL' && (
            <div className="mb-8">
              <div className={`inline-flex items-center space-x-3 px-6 py-3 rounded-full text-white font-semibold text-lg shadow-lg ${
                marketTrend === 'UP' 
                  ? 'bg-gradient-to-r from-green-500 to-emerald-500' 
                  : 'bg-gradient-to-r from-red-500 to-pink-500'
              }`}>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {marketTrend === 'UP' ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0v-8m0 8l-8-8-4 4-6-6" />
                  )}
                </svg>
                <span>Market Trend is {marketTrend} &mdash; Showing {marketTrend === 'UP' ? 'Bullish' : 'Bearish'} Setups</span>
              </div>
            </div>
          )}
        </header>

        {/* **NEW: Enhanced Main Content */}
        <main className="animate-fade-in">
          {loading && (
            <div className="flex justify-center items-center py-20">
              <div className="text-center">
                <div className="spinner mx-auto mb-4"></div>
                <p className="text-gray-400">Loading alerts...</p>
              </div>
            </div>
          )}
          
          {error && (
            <div className="text-center py-20">
              <div className="glass p-8 rounded-xl border border-red-500 max-w-md mx-auto">
                <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-red-400 font-semibold mb-2">Connection Error</p>
                <p className="text-gray-400 text-sm">{error}</p>
              </div>
            </div>
          )}
          
          {/* Keep the second, feature-rich block for ENTRY tab rendering */}
          {alertCategory === 'ENTRY' && !loading && !error && (
            <div>
              {filteredEntryAlerts.length > 0 ? (
                <div className="space-y-6">
                  {filteredEntryAlerts.map((alert, index) => {
                    const wasPremarketPick = screenerStocks.some(s => s.instrument_key === alert.instrument_key);
                    return (
                      <div key={alert.id} className="animate-slide-in" style={{ animationDelay: `${index * 0.1}s` }}>
                        <AlertCard 
                          alert={alert}
                          onPlan={handleOpenPlanModal}
                          hasPlan={plannedStockKeys.has(alert.instrument_key)}
                          livePrice={livePrices[alert.instrument_key]}
                        />
                        {wasPremarketPick && (
                          <span className="inline-block mt-2 px-3 py-1 rounded-full bg-gradient-to-r from-green-500 to-blue-500 text-white text-xs font-semibold shadow">Premarket Pick</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-20">
                  <div className="glass p-8 rounded-xl border border-gray-600 max-w-md mx-auto">
                    <svg className="w-16 h-16 text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <p className="text-gray-400 font-semibold mb-2">No active entry alerts</p>
                    <p className="text-gray-500 text-sm">Expired alerts are hidden automatically. Check back for new actionable signals.</p>
                  </div>
                </div>
              )}

              {/* Collapsible Expired Alerts Section */}
              {expiredEntryAlerts.length > 0 && (
                <div className="mt-10">
                  <button
                    className="w-full flex items-center justify-between px-6 py-3 rounded-lg bg-gradient-to-r from-gray-700 to-gray-800 text-white font-semibold shadow hover:from-gray-600 hover:to-gray-700 focus:outline-none"
                    onClick={() => setShowExpired(v => !v)}
                    aria-expanded={showExpired}
                  >
                    <span>Show Expired Alerts ({expiredEntryAlerts.length})</span>
                    <svg className={`w-5 h-5 transform transition-transform ${showExpired ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {showExpired && (
                    <div className="space-y-6 mt-4 animate-fade-in">
                      {expiredEntryAlerts.map((alert, index) => (
                        <div key={alert.id} className="opacity-60">
                          {/* Reuse the same card design, but faded */}
                          <div className="glass p-6 rounded-xl border border-gray-600 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                            <div>
                              <div className="flex items-center gap-3 mb-2">
                                <span className="text-2xl font-bold text-white">{alert.tradingsymbol}</span>
                                <span className="text-xs px-2 py-1 rounded bg-gray-700 text-gray-300 font-mono">{alert.instrument_key}</span>
                              </div>
                              <div className="text-sm text-gray-400 mb-1">Entry Alert <span className="font-semibold text-blue-400">(Expired)</span></div>
                              <div className="text-sm text-gray-400 mb-1">Entry: <span className="font-semibold text-green-400">₹{alert.indicators?.Entry_Price ?? '-'}</span> | Stop: <span className="font-semibold text-red-400">₹{alert.indicators?.Stop_Loss ?? '-'}</span> | Target: <span className="font-semibold text-yellow-400">₹{alert.indicators?.Target ?? '-'}</span></div>
                              <div className="text-sm text-gray-400 mb-1">Screened Reason:
                                <ul className="list-disc ml-6">
                                  {(alert.alert_details?.reasons || []).map((reason, i) => (
                                    <li key={i}>{reason}</li>
                                  ))}
                                </ul>
                              </div>
                            </div>
                            <div className="flex flex-col items-end gap-2">
                              <span className="px-4 py-2 rounded-full bg-gradient-to-r from-gray-500 to-gray-700 text-white font-semibold text-sm mb-1">Expired</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Screening Results Tab */}
          {alertCategory === 'SCREENING' && !loading && !error && (
            <div>
              {/* Stats and filter */}
              <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6 gap-4">
                <div className="flex gap-4 text-lg font-semibold text-white">
                  <span>Screened: <span className="text-blue-400">{screeningStats.total}</span></span>
                  <span>Entry Triggered: <span className="text-purple-400">{screeningStats.triggered}</span></span>
                  <span>Waiting: <span className="text-green-400">{screeningStats.waiting}</span></span>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => setScreenerFilter('ALL')} className={`px-3 py-1 rounded ${screenerFilter==='ALL' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300'}`}>All</button>
                  <button onClick={() => setScreenerFilter('WAITING')} className={`px-3 py-1 rounded ${screenerFilter==='WAITING' ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-300'}`}>Waiting</button>
                  <button onClick={() => setScreenerFilter('TRIGGERED')} className={`px-3 py-1 rounded ${screenerFilter==='TRIGGERED' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300'}`}>Triggered</button>
                </div>
              </div>
              {/* Render cards from screenerStocks, filtered by screenerFilter */}
              {screenerStocks.filter(stock => {
                if (screenerFilter === 'ALL') return true;
                if (screenerFilter === 'WAITING') return stock.entry_status !== 'triggered';
                if (screenerFilter === 'TRIGGERED') return stock.entry_status === 'triggered';
                return true;
              }).length > 0 ? (
                <div className="space-y-6">
                  {screenerStocks.filter(stock => {
                    if (screenerFilter === 'ALL') return true;
                    if (screenerFilter === 'WAITING') return stock.entry_status !== 'triggered';
                    if (screenerFilter === 'TRIGGERED') return stock.entry_status === 'triggered';
                    return true;
                  }).map((stock, index) => (
                    <div key={stock.id} className="animate-slide-in" style={{ animationDelay: `${index * 0.1}s` }}>
                      <div className="glass p-6 rounded-xl border border-gray-600 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                        <div>
                          <div className="flex items-center gap-3 mb-2">
                            <span className="text-2xl font-bold text-white">{stock.tradingsymbol}</span>
                            <span className="text-xs px-2 py-1 rounded bg-gray-700 text-gray-300 font-mono">{stock.instrument_key}</span>
                          </div>
                          <div className="text-sm text-gray-400 mb-1">Strategy: <span className="font-semibold text-green-400">{stock.source_strategy.replace('_', ' ')}</span></div>
                          <div className="text-sm text-gray-400 mb-1">Score: <span className="font-semibold text-blue-400">{stock.alert_details?.score ?? '-'}</span></div>
                          <div className="text-sm text-gray-400 mb-1">Reasons:
                            <ul className="list-disc ml-6">
                              {(stock.alert_details?.reasons || []).map((reason, i) => (
                                <li key={i}>{reason}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          {/* Status badge */}
                          {stock.entry_status === 'triggered' ? (
                            <span className="px-4 py-2 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold text-sm mb-1">Entry Triggered</span>
                          ) : (
                            <span className="px-4 py-2 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold text-sm mb-1">Waiting</span>
                          )}
                          {/* View Entry Alert button */}
                          {stock.entry_status === 'triggered' && stock.entry_alert && (
                            <button
                              onClick={() => handleViewEntryAlert(stock.instrument_key)}
                              className="px-3 py-1 rounded bg-blue-700 text-white text-xs font-semibold hover:bg-blue-800 transition"
                              title="View Entry Alert"
                            >
                              View Entry Alert
                            </button>
                          )}
                          {/* Plan button */}
                          <button
                            className="mt-2 px-4 py-2 rounded-lg bg-gradient-to-r from-yellow-500 to-orange-500 text-black font-semibold text-sm shadow hover:from-yellow-600 hover:to-orange-600"
                            onClick={() => handleOpenPlanModal(stock)}
                          >
                            Create Trade Plan
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-20">
                  <div className="glass p-8 rounded-xl border border-gray-600 max-w-md mx-auto">
                    <svg className="w-16 h-16 text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <p className="text-gray-400 font-semibold mb-2">No screening results found</p>
                    <p className="text-gray-500 text-sm">Screening results are generated at market open (9:00 AM IST).</p>
                  </div>
                </div>
              )}
            </div>
          )}
        </main>

        {isModalOpen && (
          <TradePlanModal 
            stock={selectedStock}
            onClose={handleCloseModal}
            onSubmit={handleSavePlan}
          />
        )}
      </div>
    </div>
  );
};

export default AlertsPage;
