// src/pages/TradeLogPage.js

import React, { useState, useEffect, useCallback } from 'react';
import { getTradeLogs } from '../api/apiService';
import TradeLogList from '../components/TradeLogList';
import Spinner from '../components/Spinner';

const TradeLogPage = () => {
  const [tradeLogs, setTradeLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTradeLogs = useCallback(async () => {
    try {
      const response = await getTradeLogs();
      setTradeLogs(response.data.results);
      setError(null);
    } catch (err) {
      setError('Failed to fetch trade logs.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTradeLogs();
  }, [fetchTradeLogs]);

  return (
    <div className="container mx-auto p-4 md:p-8">
      <header className="text-center mb-10">
        <h1 className="text-5xl font-extrabold mb-2">Trade Journal</h1>
        <p className="text-lg text-gray-400">All your planned and executed trades.</p>
      </header>
      <main>
        {loading && <Spinner />}
        {error && <p className="text-center text-red-500">{error}</p>}
        {!loading && !error && <TradeLogList tradeLogs={tradeLogs} />}
      </main>
    </div>
  );
};

export default TradeLogPage;
