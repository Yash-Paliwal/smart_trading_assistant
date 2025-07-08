// src/pages/AlertsPage.js

import React, { useState, useEffect, useCallback } from 'react';
import { getAlerts, getTradeLogs, createTradeLog } from '../api/apiService';
import AlertCard from '../components/AlertCard';
import TradePlanModal from '../components/TradePlanModal';
import websocketService from '../services/websocketService';

const AlertsPage = ({ setCurrentPage }) => {
  const [alerts, setAlerts] = useState([]);
  const [plannedStockKeys, setPlannedStockKeys] = useState(new Set());
  const [marketTrend, setMarketTrend] = useState('NEUTRAL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedStock, setSelectedStock] = useState(null);
  
  // **NEW: Alert category management**
  const [alertCategory, setAlertCategory] = useState('ALL'); // ALL, SCREENING, ENTRY
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
      const [alertsResponse, tradeLogsResponse] = await Promise.all([
        getAlerts(`?category=${alertCategory}`),
        getTradeLogs()
      ]);
      
      const alertsData = alertsResponse.data.results || [];
      
      // **NEW: Separate handling for different alert types**
      const screeningAlerts = alertsData.filter(alert => alert.category === 'SCREENING');
      const entryAlerts = alertsData.filter(alert => alert.category === 'ENTRY');
      
      // Sort screening alerts by confidence score
      const sortedScreeningAlerts = screeningAlerts.sort((a, b) => 
        (b.alert_details?.score || 0) - (a.alert_details?.score || 0)
      );
      
      // Sort entry alerts by priority and remaining time
      const sortedEntryAlerts = entryAlerts.sort((a, b) => {
        // Sort by priority first (HIGH > MEDIUM > LOW)
        const priorityOrder = { 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1 };
        const aPriority = priorityOrder[a.priority] || 1;
        const bPriority = priorityOrder[b.priority] || 1;
        
        if (aPriority !== bPriority) {
          return bPriority - aPriority;
        }
        
        // Then by remaining time (shorter time first - more urgent)
        const aTime = a.remaining_minutes || 999;
        const bTime = b.remaining_minutes || 999;
        return aTime - bTime;
      });
      
      // Combine alerts based on category filter
      let finalAlerts = [];
      if (alertCategory === 'ALL') {
        finalAlerts = [...sortedEntryAlerts, ...sortedScreeningAlerts];
      } else if (alertCategory === 'ENTRY') {
        finalAlerts = sortedEntryAlerts;
      } else if (alertCategory === 'SCREENING') {
        finalAlerts = sortedScreeningAlerts;
      }
      
      setAlerts(finalAlerts);
      setLastUpdate(new Date());
      
      // Determine market trend from screening alerts
      if (screeningAlerts.length > 0) {
        const firstAlertStrategy = screeningAlerts[0].source_strategy;
        if (firstAlertStrategy === 'Bullish_Scan') {
          setMarketTrend('UP');
        } else if (firstAlertStrategy === 'Bearish_Scan') {
          setMarketTrend('DOWN');
        } else {
          setMarketTrend('NEUTRAL');
        }
      } else {
        setMarketTrend('NEUTRAL');
      }

      const plannedKeys = new Set((tradeLogsResponse.data.results || []).map(log => log.instrument_key));
      setPlannedStockKeys(plannedKeys);
      
      setError(null);
    } catch (err) {
      setError('Failed to fetch data. Make sure the Django API server is running.');
      console.error(err);
    } finally {
      if (loading) setLoading(false);
      setIsRefreshing(false); // **NEW: Reset refresh state**
    }
  }, [loading, alertCategory]);

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
      } else {
        console.log('Scan completed: No new alerts found');
      }
      
      // **NEW: Refresh the alerts data after scan**
      await fetchPageData();
      
    } catch (err) {
      console.error('Scan failed:', err);
      setError(`Scan failed: ${err.message}`);
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
      if (setCurrentPage) {
        setCurrentPage('plans');
      }
      handleCloseModal();
    } catch (err) {
      console.error("Failed to save trade plan:", err);
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
          
          {/* **NEW: Enhanced Alert category selector */}
          <div className="mb-8">
            <div className="inline-flex bg-gray-800 rounded-xl p-1 shadow-lg border border-gray-700">
              <button
                onClick={() => handleCategoryChange('ALL')}
                className={
                  alertCategory === 'ALL'
                    ? 'px-6 py-3 rounded-lg text-sm font-medium transition-all duration-200 bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                    : 'px-6 py-3 rounded-lg text-sm font-medium transition-all duration-200 text-gray-300 bg-transparent'
                }
              >
                <div className="flex items-center space-x-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                  </svg>
                  <span>All Alerts</span>
                </div>
              </button>
              <button
                onClick={() => handleCategoryChange('ENTRY')}
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
                onClick={() => handleCategoryChange('SCREENING')}
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
                  <span>Screening Results</span>
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
          
          {!loading && !error && (
            <div>
              {alerts.length > 0 ? (
                <div className="space-y-6">
                  {alerts.map((alert, index) => (
                    <div key={alert.id} className="animate-slide-in" style={{ animationDelay: `${index * 0.1}s` }}>
                      <AlertCard 
                        alert={alert}
                        onPlan={handleOpenPlanModal}
                        hasPlan={plannedStockKeys.has(alert.instrument_key)}
                        livePrice={livePrices[alert.instrument_key]}
                      />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-20">
                  <div className="glass p-8 rounded-xl border border-gray-600 max-w-md mx-auto">
                    <svg className="w-16 h-16 text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <p className="text-gray-400 font-semibold mb-2">No {alertCategory.toLowerCase()} alerts found</p>
                    {alertCategory === 'ENTRY' && (
                      <p className="text-gray-500 text-sm">
                        Check back during market hours (9:15 AM - 3:30 PM IST) for real-time ORB alerts.
                      </p>
                    )}
                    {alertCategory === 'SCREENING' && (
                      <p className="text-gray-500 text-sm">
                        Screening results are generated at market open (9:00 AM IST).
                      </p>
                    )}
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
