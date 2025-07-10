// src/pages/TradeJournalPage.js

import React, { useState, useEffect, useCallback } from 'react';
import { getTradeLogs, updateTradeLog } from '../api/apiService';
import Spinner from '../components/Spinner';
import TradeLogList from '../components/TradeLogList';
import CloseTradeModal from '../components/CloseTradeModal'; // Import the new modal
import { useToast } from '../components/ToastProvider';

const TradeJournalPage = () => {
  const [tradeLogs, setTradeLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboard, setDashboard] = useState(null); // For analytics/insights
  const [filter, setFilter] = useState({ symbol: '', strategy: '', win: '', date: '' });
  const [sort, setSort] = useState('date_desc');
  const [editingNoteId, setEditingNoteId] = useState(null);
  const [noteValue, setNoteValue] = useState('');
  const toast = useToast();

  // State to manage the close trade modal
  const [isCloseModalOpen, setIsCloseModalOpen] = useState(false);
  const [selectedTrade, setSelectedTrade] = useState(null);

  // Fetch trade logs and dashboard analytics
  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [logsRes, dashRes] = await Promise.all([
        getTradeLogs(),
        fetch('http://localhost:8000/api/trade-journal-dashboard/').then(r => r.json())
      ]);
      const journalTrades = logsRes.data.results.filter(
        log => log.status === 'ACTIVE' || log.status === 'CLOSED'
      );
      setTradeLogs(journalTrades);
      setDashboard(dashRes);
      setError(null);
    } catch (err) {
      setError('Failed to fetch trade journal entries.');
      toast('Failed to fetch trade journal data.', 'error');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 30000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  // Filtering and sorting logic
  const filteredTrades = tradeLogs.filter(trade => {
    if (filter.symbol && trade.tradingsymbol !== filter.symbol) return false;
    if (filter.strategy && trade.strategy !== filter.strategy) return false;
    if (filter.win === 'win' && trade.pnl <= 0) return false;
    if (filter.win === 'loss' && trade.pnl >= 0) return false;
    // Add date filter if needed
    return true;
  }).sort((a, b) => {
    if (sort === 'date_desc') return new Date(b.trade_date) - new Date(a.trade_date);
    if (sort === 'date_asc') return new Date(a.trade_date) - new Date(b.trade_date);
    if (sort === 'pnl_desc') return (b.pnl || 0) - (a.pnl || 0);
    if (sort === 'pnl_asc') return (a.pnl || 0) - (b.pnl || 0);
    return 0;
  });

  // Note editing logic
  const handleEditNote = (trade) => {
    setEditingNoteId(trade.id);
    setNoteValue(trade.notes || '');
  };
  const handleSaveNote = async (tradeId) => {
    try {
      await updateTradeLog(tradeId, { notes: noteValue });
      setTradeLogs(prev => prev.map(t => t.id === tradeId ? { ...t, notes: noteValue } : t));
      setEditingNoteId(null);
      toast('Note updated!', 'success');
    } catch (err) {
      toast('Failed to update note.', 'error');
    }
  };

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
      setTradeLogs(prevLogs => prevLogs.map(log => (log.id === tradeId ? updatedLog : log)));
      handleCloseCloseModal();
      toast('Trade closed!', 'success');
    } catch (err) {
      toast('Failed to close trade.', 'error');
    }
  };


  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-4 md:p-8">
      <header className="text-center mb-10">
        <h1 className="text-5xl font-extrabold mb-2 gradient-text">My Trade Journal</h1>
        <p className="text-lg text-gray-400">Your permanent record of all executed trades.</p>
      </header>
      {/* Summary/Insights Section */}
      {dashboard && (
        <div className="mb-8 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          <div className="glass p-6 rounded-xl border border-blue-700 shadow-md animate-slide-in">
            <div className="text-sm text-gray-400 mb-1">Total Trades</div>
            <div className="text-2xl font-bold text-white">{dashboard.statistics.total_trades}</div>
          </div>
          <div className="glass p-6 rounded-xl border border-green-700 shadow-md animate-slide-in">
            <div className="text-sm text-gray-400 mb-1">Win Rate</div>
            <div className="text-2xl font-bold text-green-400">{dashboard.statistics.win_rate?.toFixed(1)}%</div>
          </div>
          <div className="glass p-6 rounded-xl border border-purple-700 shadow-md animate-slide-in">
            <div className="text-sm text-gray-400 mb-1">Avg P&L</div>
            <div className="text-2xl font-bold text-white">₹{((dashboard.statistics.avg_profit || 0) + (dashboard.statistics.avg_loss || 0)) / 2}</div>
          </div>
        </div>
      )}
      {/* Insights: best/worst, streaks, most traded, etc. */}
      {dashboard && (
        <div className="mb-8 max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass p-6 rounded-xl border border-yellow-700 animate-slide-in">
            <div className="text-sm text-gray-400 mb-1">Best Trade</div>
            {dashboard.insights.best_trade ? (
              <div className="text-lg text-green-400 font-bold">{dashboard.insights.best_trade.tradingsymbol} ₹{dashboard.insights.best_trade.pnl}</div>
            ) : <div className="text-gray-500">-</div>}
            <div className="text-sm text-gray-400 mt-2">Worst Trade</div>
            {dashboard.insights.worst_trade ? (
              <div className="text-lg text-red-400 font-bold">{dashboard.insights.worst_trade.tradingsymbol} ₹{dashboard.insights.worst_trade.pnl}</div>
            ) : <div className="text-gray-500">-</div>}
          </div>
          <div className="glass p-6 rounded-xl border border-pink-700 animate-slide-in">
            <div className="text-sm text-gray-400 mb-1">Streaks</div>
            <div className="text-white">Win: {dashboard.insights.streaks.longest_win} | Loss: {dashboard.insights.streaks.longest_loss}</div>
            <div className="text-gray-400 text-sm">Current Win: {dashboard.insights.streaks.current_win} | Current Loss: {dashboard.insights.streaks.current_loss}</div>
            <div className="text-sm text-gray-400 mt-2">Most Traded</div>
            <ul className="text-white text-lg font-semibold space-y-1">
              {dashboard.insights.most_traded.map((s, i) => (
                <li key={i}>{s.symbol} <span className="text-gray-400 text-sm">({s.count})</span></li>
              ))}
            </ul>
          </div>
        </div>
      )}
      {/* Filtering/Sorting Controls */}
      <div className="max-w-4xl mx-auto mb-6 flex flex-wrap gap-4 items-center">
        <input className="glass px-3 py-2 rounded border border-gray-600 text-white bg-transparent" placeholder="Symbol" value={filter.symbol} onChange={e => setFilter(f => ({ ...f, symbol: e.target.value }))} />
        <select className="glass px-3 py-2 rounded border border-gray-600 text-white bg-transparent" value={filter.win} onChange={e => setFilter(f => ({ ...f, win: e.target.value }))}>
          <option value="">All</option>
          <option value="win">Win</option>
          <option value="loss">Loss</option>
        </select>
        <select className="glass px-3 py-2 rounded border border-gray-600 text-white bg-transparent" value={sort} onChange={e => setSort(e.target.value)}>
          <option value="date_desc">Newest</option>
          <option value="date_asc">Oldest</option>
          <option value="pnl_desc">P&L High-Low</option>
          <option value="pnl_asc">P&L Low-High</option>
        </select>
      </div>
      <main>
        {loading && (
          <div className="flex justify-center items-center py-20">
            <div className="text-center">
              <div className="spinner mx-auto mb-4"></div>
              <p className="text-gray-400">Loading trade journal...</p>
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
            {filteredTrades.length === 0 ? (
              <div className="glass p-8 rounded-xl border border-gray-600 text-center">
                <svg className="w-16 h-16 text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p className="text-gray-400 font-semibold mb-2">No trades found</p>
                <p className="text-gray-500 text-sm">Your journal will appear here as you execute trades.</p>
              </div>
            ) : (
              filteredTrades.map((trade, idx) => (
                <div key={trade.id} className="glass p-6 rounded-xl border border-blue-600 shadow-md animate-slide-in flex flex-col md:flex-row md:items-center md:justify-between gap-6" style={{ animationDelay: `${idx * 0.05}s` }}>
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl font-bold text-white">{trade.tradingsymbol}</span>
                      <span className="text-xs px-2 py-1 rounded bg-gray-700 text-gray-300 font-mono">{trade.instrument_key}</span>
                      {trade.strategy && <span className="ml-2 px-2 py-1 rounded bg-purple-700 text-white text-xs font-mono">{trade.strategy}</span>}
                    </div>
                    <div className="text-sm text-gray-400 mb-1">Entry: <span className="font-semibold text-green-400">₹{trade.entry_price}</span> | Exit: <span className="font-semibold text-yellow-400">₹{trade.exit_price || '-'}</span> | Qty: <span className="font-semibold text-white">{trade.quantity}</span></div>
                    <div className="text-sm text-gray-400 mb-1">Type: <span className="font-semibold text-white">{trade.trade_type}</span> | Date: <span className="font-semibold text-white">{trade.trade_date}</span></div>
                    <div className="text-sm text-gray-400 mb-1">P&L: <span className={trade.pnl > 0 ? 'text-green-400 font-bold' : trade.pnl < 0 ? 'text-red-400 font-bold' : 'text-gray-300 font-bold'}>₹{trade.pnl}</span></div>
                    <div className="text-sm text-gray-400 mb-1">Notes: {editingNoteId === trade.id ? (
                      <span>
                        <input className="glass px-2 py-1 rounded border border-gray-600 text-white bg-transparent" value={noteValue} onChange={e => setNoteValue(e.target.value)} />
                        <button className="ml-2 px-3 py-1 rounded bg-green-600 text-white font-semibold text-xs" onClick={() => handleSaveNote(trade.id)}>Save</button>
                        <button className="ml-2 px-3 py-1 rounded bg-gray-600 text-white font-semibold text-xs" onClick={() => setEditingNoteId(null)}>Cancel</button>
                      </span>
                    ) : (
                      <span className="text-gray-300">{trade.notes || '-'} <button className="ml-2 px-2 py-1 rounded bg-blue-700 text-white text-xs" onClick={() => handleEditNote(trade)}>Edit</button></span>
                    )}</div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    {trade.status === 'ACTIVE' && (
                      <button
                        className="px-4 py-2 rounded-lg bg-gradient-to-r from-yellow-500 to-orange-500 text-white font-semibold text-sm shadow hover:from-yellow-600 hover:to-orange-600 transition"
                        onClick={() => handleOpenCloseModal(trade)}
                      >
                        Close Trade
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </main>
      {/* Render the close trade modal conditionally */}
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
