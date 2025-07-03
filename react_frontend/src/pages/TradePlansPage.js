// src/pages/TradePlansPage.js

import React, { useState, useEffect, useCallback } from 'react';
import { getTradeLogs, updateTradeLog, deleteTradeLog } from '../api/apiService';
import Spinner from '../components/Spinner';
import TradeLogList from '../components/TradeLogList';
import ActivateTradeModal from '../components/ActivateTradeModal'; // Import the new modal

const TradePlansPage = () => {
  const [tradeLogs, setTradeLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // State to manage the activation modal
  const [isActivateModalOpen, setIsActivateModalOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);

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
      // After activating, remove the plan from this page's list
      setTradeLogs(prevLogs => prevLogs.filter(log => log.id !== tradeId));
      handleCloseActivateModal();
    } catch (err) {
      console.error("Failed to activate trade:", err);
      // Optionally show an error in the modal
    }
  };

  const handleDeletePlan = async (tradeId) => {
    // Ask for confirmation before deleting
    if (window.confirm('Are you sure you want to delete this trade plan?')) {
      try {
        await deleteTradeLog(tradeId);
        // After deleting, remove the plan from this page's list
        setTradeLogs(prevLogs => prevLogs.filter(log => log.id !== tradeId));
      } catch (err) {
        console.error("Failed to delete trade plan:", err);
      }
    }
  };

  return (
    <div className="container mx-auto p-4 md:p-8">
      <header className="text-center mb-10">
        <h1 className="text-5xl font-extrabold mb-2">My Trade Plans</h1>
        <p className="text-lg text-gray-400">Your active watchlist. Execute or manage your planned trades from here.</p>
      </header>
      <main>
        {loading && <Spinner />}
        {error && <p className="text-center text-red-500">{error}</p>}
        {!loading && !error && (
            <TradeLogList 
                tradeLogs={tradeLogs}
                listType="plans"
                onActivate={handleOpenActivateModal}
                onDelete={handleDeletePlan}
            />
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
