// src/pages/AlertsPage.js

import React, { useState, useEffect, useCallback } from 'react';
import { getAlerts, getTradeLogs, createTradeLog } from '../api/apiService';
import AlertCard from '../components/AlertCard';
import Spinner from '../components/Spinner';
import TradePlanModal from '../components/TradePlanModal';

const AlertsPage = ({ setCurrentPage }) => {
  const [alerts, setAlerts] = useState([]);
  const [plannedStockKeys, setPlannedStockKeys] = useState(new Set());
  const [marketTrend, setMarketTrend] = useState('NEUTRAL'); // State for the market trend hint
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedStock, setSelectedStock] = useState(null);

  const fetchPageData = useCallback(async () => {
    try {
      const [alertsResponse, tradeLogsResponse] = await Promise.all([
        getAlerts(),
        getTradeLogs()
      ]);
      
      const alertsData = alertsResponse.data.results || [];
      const sortedAlerts = alertsData.sort((a, b) => (b.alert_details?.score || 0) - (a.alert_details?.score || 0));
      setAlerts(sortedAlerts);
      
      // **RE-ADD MARKET TREND LOGIC**
      // Determine the market trend from the first alert's strategy name.
      if (sortedAlerts.length > 0) {
        const firstAlertStrategy = sortedAlerts[0].source_strategy;
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
    }
  }, [loading]);

  useEffect(() => {
    fetchPageData();
  }, [fetchPageData]);

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
      // After saving, switch to the 'plans' page to see the new plan
      if (setCurrentPage) {
        setCurrentPage('plans');
      }
      handleCloseModal();
    } catch (err) {
      console.error("Failed to save trade plan:", err);
    }
  };

  return (
    <div className="container mx-auto p-4 md:p-8">
      <header className="text-center mb-10">
        <h1 className="text-5xl font-extrabold mb-2">Radar Alerts</h1>
        <p className="text-lg text-gray-400">High-confidence trade setups identified by the engine.</p>
        
        {/* **RE-ADD MARKET TREND UI** */}
        {!loading && marketTrend !== 'NEUTRAL' && (
          <div className="mt-4 inline-block">
            <span className={`px-4 py-2 rounded-full text-white font-semibold text-sm ${
                marketTrend === 'UP' ? 'bg-green-600' : 'bg-red-600'
            }`}>
              Market Trend is {marketTrend} &mdash; Showing {marketTrend === 'UP' ? 'Bullish' : 'Bearish'} Setups
            </span>
          </div>
        )}
      </header>

      <main>
        {loading && <Spinner />}
        {error && <p className="text-center text-red-500">{error}</p>}
        
        {!loading && !error && (
          <div>
            {alerts.length > 0 ? (
              alerts.map(alert => (
                <AlertCard 
                  key={alert.id} 
                  alert={alert}
                  onPlan={handleOpenPlanModal}
                  hasPlan={plannedStockKeys.has(alert.instrument_key)}
                />
              ))
            ) : (
              <p className="text-center text-gray-500">No alerts found for today's market conditions.</p>
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
  );
};

export default AlertsPage;
