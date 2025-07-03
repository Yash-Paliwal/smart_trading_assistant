// src/pages/TradeJournalPage.js

import React, { useState, useEffect, useCallback } from 'react';
import { getTradeLogs, updateTradeLog } from '../api/apiService';
import Spinner from '../components/Spinner';
import TradeLogList from '../components/TradeLogList';
import CloseTradeModal from '../components/CloseTradeModal'; // Import the new modal

const TradeJournalPage = () => {
  const [tradeLogs, setTradeLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // State to manage the close trade modal
  const [isCloseModalOpen, setIsCloseModalOpen] = useState(false);
  const [selectedTrade, setSelectedTrade] = useState(null);

  const fetchTradeLogs = useCallback(async () => {
    try {
      const response = await getTradeLogs();
      // This page only shows trades that are ACTIVE or CLOSED.
      const journalTrades = response.data.results.filter(
        log => log.status === 'ACTIVE' || log.status === 'CLOSED'
      );
      setTradeLogs(journalTrades);
      setError(null);
    } catch (err) {
      setError('Failed to fetch trade journal entries.');
      console.error(err);
    } finally {
      if (loading) setLoading(false);
    }
  }, [loading]);

  useEffect(() => {
    fetchTradeLogs();
    // Set up a polling interval to refresh the data periodically
    const interval = setInterval(fetchTradeLogs, 30000);
    return () => clearInterval(interval); // Cleanup on unmount
  }, [fetchTradeLogs]);

  // --- Modal and Action Handlers ---

  const handleOpenCloseModal = (tradeLog) => {
    setSelectedTrade(tradeLog);
    setIsCloseModalOpen(true);
  };

  const handleCloseCloseModal = () => {
    setIsCloseModalOpen(false);
    setSelectedTrade(null);
  };

  const handleConfirmCloseTrade = async (tradeId, closeData) => {
    try {
      const response = await updateTradeLog(tradeId, closeData);
      const updatedLog = response.data;

      // Update the list to reflect the change in status and P&L
      setTradeLogs(prevLogs => 
        prevLogs.map(log => (log.id === tradeId ? updatedLog : log))
      );

      handleCloseCloseModal();
    } catch (err) {
      console.error("Failed to close trade:", err);
      // Optionally show an error in the modal
    }
  };


  return (
    <div className="container mx-auto p-4 md:p-8">
      <header className="text-center mb-10">
        <h1 className="text-5xl font-extrabold mb-2">My Trade Journal</h1>
        <p className="text-lg text-gray-400">Your permanent record of all executed trades.</p>
      </header>
      <main>
        {loading && <Spinner />}
        {error && <p className="text-center text-red-500">{error}</p>}
        {!loading && !error && (
            <TradeLogList 
                tradeLogs={tradeLogs} 
                listType="journal"
                onCloseTrade={handleOpenCloseModal}
            />
        )}
      </main>

      {/* Render the new close trade modal conditionally */}
      {isCloseModalOpen && (
          <CloseTradeModal 
            tradeLog={selectedTrade}
            onClose={handleCloseCloseModal}
            onConfirm={handleConfirmCloseTrade}
          />
      )}
    </div>
  );
};

export default TradeJournalPage;
