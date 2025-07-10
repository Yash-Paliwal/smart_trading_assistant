// src/pages/TradePlansPage.js

import React, { useState, useEffect, useCallback } from 'react';
import { getTradeLogs, updateTradeLog, deleteTradeLog } from '../api/apiService';
import Spinner from '../components/Spinner';
import TradeLogList from '../components/TradeLogList';
import ActivateTradeModal from '../components/ActivateTradeModal'; // Import the new modal
import { useToast } from '../components/ToastProvider';

const TradePlansPage = () => {
  const [tradeLogs, setTradeLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // State to manage the activation modal
  const [isActivateModalOpen, setIsActivateModalOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);

  const toast = useToast();

  const fetchTradeLogs = useCallback(async () => {
    try {
      const response = await getTradeLogs();
      // This page should only show PLANNED trades.
      const plannedTrades = response.data.results.filter(log => log.status === 'PLANNED');
      setTradeLogs(plannedTrades);
      setError(null);
    } catch (err) {
      setError('Failed to fetch trade plans.');
      console.error(err);
    } finally {
      if (loading) {
        setLoading(false);
      }
    }
  }, [loading]);

  useEffect(() => {
    fetchTradeLogs();
    // Set up a polling interval to refresh the data
    const interval = setInterval(fetchTradeLogs, 30000);
    return () => clearInterval(interval); // Cleanup on unmount
  }, [fetchTradeLogs]);

  // Compute summary stats
  const totalPlans = tradeLogs.length;
  const mostCommonStocks = (() => {
    const counts = {};
    tradeLogs.forEach(log => {
      counts[log.tradingsymbol] = (counts[log.tradingsymbol] || 0) + 1;
    });
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([symbol, count]) => ({ symbol, count }));
  })();

  // --- Modal and Action Handlers ---

  const handleOpenActivateModal = (tradePlan) => {
    setSelectedPlan(tradePlan);
    setIsActivateModalOpen(true);
  };

  const handleCloseActivateModal = () => {
    setIsActivateModalOpen(false);
    setSelectedPlan(null);
  };

  const handleActivateTrade = async (tradeId, activationData) => {
    try {
      await updateTradeLog(tradeId, activationData);
      setTradeLogs(prevLogs => prevLogs.filter(log => log.id !== tradeId));
      handleCloseActivateModal();
      toast('Trade activated!', 'success');
    } catch (err) {
      console.error("Failed to activate trade:", err);
      toast('Failed to activate trade. Please try again.', 'error');
    }
  };

  const handleDeletePlan = async (tradeId) => {
      try {
        await deleteTradeLog(tradeId);
        setTradeLogs(prevLogs => prevLogs.filter(log => log.id !== tradeId));
      toast('Trade plan deleted.', 'info');
      } catch (err) {
        console.error("Failed to delete trade plan:", err);
      toast('Failed to delete trade plan. Please try again.', 'error');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-4 md:p-8">
      <header className="text-center mb-10">
        <h1 className="text-5xl font-extrabold mb-2 gradient-text">My Trade Plans</h1>
        <p className="text-lg text-gray-400">Your active watchlist. Execute or manage your planned trades from here.</p>
      </header>
      {/* Summary Section */}
      <div className="mb-8 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
        <div className="glass p-6 rounded-xl border border-blue-700 shadow-md animate-slide-in">
          <div className="text-sm text-gray-400 mb-1">Total Plans</div>
          <div className="text-2xl font-bold text-white">{totalPlans}</div>
        </div>
        <div className="glass p-6 rounded-xl border border-purple-700 shadow-md animate-slide-in">
          <div className="text-sm text-gray-400 mb-1">Most Common Stocks</div>
          {mostCommonStocks.length > 0 ? (
            <ul className="text-white text-lg font-semibold space-y-1">
              {mostCommonStocks.map((s, i) => (
                <li key={i}>{s.symbol} <span className="text-gray-400 text-sm">({s.count})</span></li>
              ))}
            </ul>
          ) : <div className="text-gray-500">No plans yet</div>}
        </div>
        <div className="glass p-6 rounded-xl border border-green-700 shadow-md animate-slide-in">
          <div className="text-sm text-gray-400 mb-1">Last Updated</div>
          <div className="text-2xl font-bold text-white">{new Date().toLocaleTimeString()}</div>
        </div>
      </div>
      <main>
        {loading && (
          <div className="flex justify-center items-center py-20">
            <div className="text-center">
              <div className="spinner mx-auto mb-4"></div>
              <p className="text-gray-400">Loading trade plans...</p>
            </div>
          </div>
        )}
        {error && (
          <div className="text-center py-20">
            <div className="glass p-8 rounded-xl border border-red-500 max-w-md mx-auto">
              <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-red-400 font-semibold mb-2">Error</p>
              <p className="text-gray-400 text-sm">{error}</p>
            </div>
          </div>
        )}
        {!loading && !error && (
          <div className="space-y-6 max-w-3xl mx-auto">
            {tradeLogs.length === 0 ? (
              <div className="glass p-8 rounded-xl border border-gray-600 text-center">
                <svg className="w-16 h-16 text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p className="text-gray-400 font-semibold mb-2">No trade plans found</p>
                <p className="text-gray-500 text-sm">Create a trade plan from the Alerts page to get started.</p>
              </div>
            ) : (
              tradeLogs.map((plan, idx) => (
                <div key={plan.id} className="glass p-6 rounded-xl border border-blue-600 shadow-md animate-slide-in flex flex-col md:flex-row md:items-center md:justify-between gap-6" style={{ animationDelay: `${idx * 0.05}s` }}>
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl font-bold text-white">{plan.tradingsymbol}</span>
                      <span className="text-xs px-2 py-1 rounded bg-gray-700 text-gray-300 font-mono">{plan.instrument_key}</span>
                    </div>
                    <div className="text-sm text-gray-400 mb-1">Entry: <span className="font-semibold text-green-400">₹{plan.planned_entry_price}</span> | Stop: <span className="font-semibold text-red-400">₹{plan.stop_loss_price}</span> | Target: <span className="font-semibold text-yellow-400">₹{plan.target_price}</span></div>
                    <div className="text-sm text-gray-400 mb-1">Notes: <span className="text-gray-300">{plan.notes || '-'}</span></div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <button
                      className="px-4 py-2 rounded-lg bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold text-sm shadow hover:from-green-600 hover:to-emerald-600 transition"
                      onClick={() => handleOpenActivateModal(plan)}
                    >
                      Activate
                    </button>
                    <button
                      className="px-4 py-2 rounded-lg bg-gradient-to-r from-red-500 to-pink-500 text-white font-semibold text-sm shadow hover:from-red-600 hover:to-pink-600 transition"
                      onClick={() => handleDeletePlan(plan.id)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </main>
      {/* Render the new activation modal conditionally */}
      {isActivateModalOpen && (
        <ActivateTradeModal 
            tradePlan={selectedPlan}
            onClose={handleCloseActivateModal}
            onActivate={handleActivateTrade}
        />
      )}
    </div>
  );
};

export default TradePlansPage;
