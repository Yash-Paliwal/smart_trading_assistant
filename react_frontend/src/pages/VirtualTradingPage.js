import React, { useState, useEffect } from 'react';
import { getVirtualTradingDashboard } from '../api/apiService';
import websocketService from '../services/websocketService';
import { useToast } from '../components/ToastProvider';

const VirtualTradingPage = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const toast = useToast();

  useEffect(() => {
    fetchDashboardData();
    const user = JSON.parse(localStorage.getItem('user'));
    if (user && user.username) {
      websocketService.connectTrading(user.username);
      websocketService.on('wallet_data', handleWalletData);
      websocketService.on('open_trades', handleOpenTrades);
      websocketService.on('trade_update', handleTradeUpdate);
    }
    return () => {
      websocketService.off('wallet_data', handleWalletData);
      websocketService.off('open_trades', handleOpenTrades);
      websocketService.off('trade_update', handleTradeUpdate);
    };
  }, []);

  const handleWalletData = (wallet) => {
    setDashboardData(prev => prev ? { ...prev, wallet } : { wallet });
  };
  const handleOpenTrades = (openTrades) => {
    setDashboardData(prev => prev ? { ...prev, open_positions: openTrades } : { open_positions: openTrades });
  };
  const handleTradeUpdate = (trade) => {
    setDashboardData(prev => {
      if (!prev) return prev;
      let open_positions = prev.open_positions || [];
      let recent_trades = prev.recent_trades || [];
      if (trade.status === 'CLOSED') {
        recent_trades = [trade, ...recent_trades].slice(0, 10);
        open_positions = open_positions.filter(t => t.id !== trade.id);
        toast(`Trade closed: ${trade.tradingsymbol} (${trade.pnl > 0 ? 'Profit' : 'Loss'})`, trade.pnl > 0 ? 'success' : 'warning');
      } else {
        const exists = open_positions.find(t => t.id === trade.id);
        if (exists) {
          open_positions = open_positions.map(t => t.id === trade.id ? trade : t);
        } else {
          open_positions = [trade, ...open_positions];
          toast(`New trade: ${trade.tradingsymbol}`, 'info');
        }
      }
      return { ...prev, open_positions, recent_trades };
    });
  };

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await getVirtualTradingDashboard();
      setDashboardData(response.data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2
    }).format(Number(amount || 0));
  };

  const formatPercentage = (value) => {
    return `${Number(value || 0) > 0 ? '+' : ''}${Number(value || 0).toFixed(2)}%`;
  };

  const getPnlColor = (pnl) => {
    const val = Number(pnl || 0);
    if (!val) return 'text-gray-600';
    return val > 0 ? 'text-green-600' : 'text-red-600';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading virtual trading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Error Loading Dashboard</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchDashboardData}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-600 text-6xl mb-4">📊</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">No Dashboard Data</h2>
          <p className="text-gray-600">Unable to load virtual trading data.</p>
        </div>
      </div>
    );
  }

  const { wallet, open_positions, recent_trades, statistics } = dashboardData;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl md:text-5xl font-extrabold mb-2 gradient-text">Virtual Trading Dashboard</h1>
          <p className="text-lg text-gray-400">Track your virtual portfolio performance and trades</p>
        </div>

        {/* Portfolio Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="glass p-6 rounded-xl border border-green-600 shadow-md animate-slide-in">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Total Balance</p>
                <p className="text-2xl font-bold text-white">{formatCurrency(wallet.balance)}</p>
              </div>
            </div>
          </div>

          <div className="glass p-6 rounded-xl border border-blue-600 shadow-md animate-slide-in" style={{ animationDelay: '0.05s' }}>
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Total P&L</p>
                <p className={`text-2xl font-bold ${getPnlColor(wallet.total_pnl)}`}>{formatCurrency(wallet.total_pnl)}</p>
              </div>
            </div>
          </div>

          <div className="glass p-6 rounded-xl border border-purple-600 shadow-md animate-slide-in" style={{ animationDelay: '0.1s' }}>
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Win Rate</p>
                <p className="text-2xl font-bold text-white">{Number(wallet.win_rate || 0).toFixed(1)}%</p>
              </div>
            </div>
          </div>

          <div className="glass p-6 rounded-xl border border-orange-600 shadow-md animate-slide-in" style={{ animationDelay: '0.15s' }}>
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-lg">
                <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Total Trades</p>
                <p className="text-2xl font-bold text-white">{Number(wallet.total_trades || 0)}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Open Positions */}
          <div className="glass p-6 rounded-xl border border-blue-700 shadow-md animate-slide-in">
            <h2 className="text-2xl font-bold text-white mb-4">Open Positions</h2>
            {(!open_positions || open_positions.length === 0) ? (
              <div className="text-center py-12">
                <svg className="w-12 h-12 text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p className="text-gray-400 font-semibold mb-2">No open positions</p>
                <p className="text-gray-500 text-sm">Your open trades will appear here in real time.</p>
                </div>
              ) : (
              <div className="space-y-6">
                {open_positions.map((trade, idx) => (
                  <div key={trade.id} className="glass p-4 rounded-lg border border-blue-500 shadow animate-slide-in" style={{ animationDelay: `${idx * 0.05}s` }}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xl font-bold text-white">{trade.tradingsymbol}</span>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold shadow-md ${trade.pnl >= 0 ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white' : 'bg-gradient-to-r from-red-500 to-pink-500 text-white'}`}>{trade.pnl >= 0 ? 'Profit' : 'Loss'}</span>
                        </div>
                    <div className="flex flex-wrap gap-4 text-sm text-gray-300 mb-2">
                      <span>Entry: <span className="font-semibold text-green-400">₹{trade.entry_price}</span></span>
                      <span>Qty: <span className="font-semibold text-blue-400">{trade.quantity}</span></span>
                      <span>Type: <span className="font-semibold text-yellow-400">{trade.trade_type}</span></span>
                      <span>Current: <span className="font-semibold text-white">₹{trade.current_price}</span></span>
                      <span>P&L: <span className={trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}>₹{trade.pnl}</span></span>
                        </div>
                    <div className="text-xs text-gray-400">Opened at: {new Date(trade.trade_date).toLocaleString()}</div>
                    </div>
                  ))}
                </div>
              )}
          </div>

          {/* Recent Trades */}
          <div className="glass p-6 rounded-xl border border-gray-700 shadow-md animate-slide-in">
            <h2 className="text-2xl font-bold text-white mb-4">Recent Trades</h2>
            {(!recent_trades || recent_trades.length === 0) ? (
              <div className="text-center py-12">
                <svg className="w-12 h-12 text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p className="text-gray-400 font-semibold mb-2">No recent trades</p>
                <p className="text-gray-500 text-sm">Your closed trades will appear here.</p>
                </div>
              ) : (
              <div className="space-y-6">
                {recent_trades.map((trade, idx) => (
                  <div key={trade.id} className="glass p-4 rounded-lg border border-gray-500 shadow animate-slide-in opacity-80" style={{ animationDelay: `${idx * 0.05}s` }}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xl font-bold text-white">{trade.tradingsymbol}</span>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold shadow-md ${trade.pnl >= 0 ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white' : 'bg-gradient-to-r from-red-500 to-pink-500 text-white'}`}>{trade.pnl >= 0 ? 'Profit' : 'Loss'}</span>
                        </div>
                    <div className="flex flex-wrap gap-4 text-sm text-gray-300 mb-2">
                      <span>Entry: <span className="font-semibold text-green-400">₹{trade.entry_price}</span></span>
                      <span>Exit: <span className="font-semibold text-red-400">₹{trade.exit_price}</span></span>
                      <span>Qty: <span className="font-semibold text-blue-400">{trade.quantity}</span></span>
                      <span>Type: <span className="font-semibold text-yellow-400">{trade.trade_type}</span></span>
                      <span>P&L: <span className={trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}>₹{trade.pnl}</span></span>
                        </div>
                    <div className="text-xs text-gray-400">Closed at: {new Date(trade.exit_date).toLocaleString()}</div>
                    </div>
                  ))}
                </div>
              )}
          </div>
        </div>

        {/* Statistics */}
        {statistics && (
          <div className="mt-8 glass p-8 rounded-xl border border-gray-700 shadow-md animate-slide-in">
            <h2 className="text-2xl font-bold text-white mb-6">Trading Statistics</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div className="text-center">
                <p className="text-sm text-gray-400">Profitable Trades</p>
                <p className="text-2xl font-bold text-green-400">{Number(statistics.profitable_trades || 0)}</p>
                </div>
                <div className="text-center">
                <p className="text-sm text-gray-400">Average Profit</p>
                <p className="text-2xl font-bold text-green-400">{formatCurrency(statistics.avg_profit)}</p>
                </div>
                <div className="text-center">
                <p className="text-sm text-gray-400">Average Loss</p>
                <p className="text-2xl font-bold text-red-400">{formatCurrency(statistics.avg_loss)}</p>
              </div>
            </div>
          </div>
        )}

        {/* Insights Section */}
        <div className="mt-12">
          <h2 className="text-3xl font-bold text-white mb-6">Insights</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Best/Worst Trade */}
            <div className="glass p-6 rounded-xl border border-green-700 shadow-md animate-slide-in">
              <h3 className="text-xl font-semibold text-green-400 mb-2">Best Trade</h3>
              {dashboardData.insights && dashboardData.insights.best_trade ? (
                <div>
                  <div className="text-lg font-bold text-white">{dashboardData.insights.best_trade.tradingsymbol}</div>
                  <div className="text-sm text-gray-400 mb-1">P&L: <span className="text-green-400 font-semibold">₹{dashboardData.insights.best_trade.pnl}</span></div>
                  <div className="text-xs text-gray-400">Closed at: {new Date(dashboardData.insights.best_trade.exit_time).toLocaleString()}</div>
                </div>
              ) : <div className="text-gray-500">No data yet</div>}
            </div>
            <div className="glass p-6 rounded-xl border border-red-700 shadow-md animate-slide-in">
              <h3 className="text-xl font-semibold text-red-400 mb-2">Worst Trade</h3>
              {dashboardData.insights && dashboardData.insights.worst_trade ? (
                <div>
                  <div className="text-lg font-bold text-white">{dashboardData.insights.worst_trade.tradingsymbol}</div>
                  <div className="text-sm text-gray-400 mb-1">P&L: <span className="text-red-400 font-semibold">₹{dashboardData.insights.worst_trade.pnl}</span></div>
                  <div className="text-xs text-gray-400">Closed at: {new Date(dashboardData.insights.worst_trade.exit_time).toLocaleString()}</div>
                </div>
              ) : <div className="text-gray-500">No data yet</div>}
            </div>
          </div>
          {/* Per-Strategy Stats */}
          <div className="glass p-6 rounded-xl border border-blue-700 shadow-md animate-slide-in mt-8">
            <h3 className="text-xl font-semibold text-blue-400 mb-4">Strategy Performance</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm text-left">
                <thead>
                  <tr className="text-gray-300">
                    <th className="px-4 py-2">Strategy</th>
                    <th className="px-4 py-2">Trades</th>
                    <th className="px-4 py-2">Win Rate</th>
                    <th className="px-4 py-2">Avg P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboardData.insights && dashboardData.insights.strategy_stats && dashboardData.insights.strategy_stats.length > 0 ? (
                    dashboardData.insights.strategy_stats.map((s, i) => (
                      <tr key={i} className="border-t border-gray-700">
                        <td className="px-4 py-2 text-white font-semibold">{s.strategy}</td>
                        <td className="px-4 py-2">{s.count}</td>
                        <td className="px-4 py-2">{s.win_rate.toFixed(1)}%</td>
                        <td className="px-4 py-2">₹{Number(s.avg_pnl).toFixed(2)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan={4} className="text-center text-gray-500 py-4">No data yet</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
          {/* Equity Curve */}
          <div className="glass p-6 rounded-xl border border-purple-700 shadow-md animate-slide-in mt-8">
            <h3 className="text-xl font-semibold text-purple-400 mb-4">Equity Curve</h3>
            {dashboardData.insights && dashboardData.insights.equity_curve && dashboardData.insights.equity_curve.length > 1 ? (
              <svg width="100%" height="180" viewBox="0 0 400 180" className="w-full h-44">
                {(() => {
                  const data = dashboardData.insights.equity_curve;
                  const min = Math.min(...data.map(d => d.balance));
                  const max = Math.max(...data.map(d => d.balance));
                  const points = data.map((d, i) => {
                    const x = (i / (data.length - 1)) * 380 + 10;
                    const y = 170 - ((d.balance - min) / (max - min || 1)) * 160;
                    return `${x},${y}`;
                  }).join(' ');
                  return <polyline points={points} fill="none" stroke="#a78bfa" strokeWidth="3" />;
                })()}
              </svg>
            ) : <div className="text-gray-500">Not enough data for chart</div>}
          </div>
          {/* Streaks, Most Traded, Fastest/Slowest */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-8">
            <div className="glass p-6 rounded-xl border border-yellow-700 shadow-md animate-slide-in">
              <h3 className="text-lg font-semibold text-yellow-400 mb-2">Win/Loss Streaks</h3>
              {dashboardData.insights && dashboardData.insights.streaks ? (
                <>
                  <div className="text-sm text-gray-300">Current Win: <span className="text-green-400 font-bold">{dashboardData.insights.streaks.current_win}</span></div>
                  <div className="text-sm text-gray-300">Current Loss: <span className="text-red-400 font-bold">{dashboardData.insights.streaks.current_loss}</span></div>
                  <div className="text-sm text-gray-300">Longest Win: <span className="text-green-400 font-bold">{dashboardData.insights.streaks.longest_win}</span></div>
                  <div className="text-sm text-gray-300">Longest Loss: <span className="text-red-400 font-bold">{dashboardData.insights.streaks.longest_loss}</span></div>
                </>
              ) : <div className="text-gray-500">No data yet</div>}
            </div>
            <div className="glass p-6 rounded-xl border border-pink-700 shadow-md animate-slide-in">
              <h3 className="text-lg font-semibold text-pink-400 mb-2">Most Traded Stocks</h3>
              {dashboardData.insights && dashboardData.insights.most_traded && dashboardData.insights.most_traded.length > 0 ? (
                <ul className="text-sm text-white space-y-1">
                  {dashboardData.insights.most_traded.map((s, i) => (
                    <li key={i} className="flex justify-between"><span>{s.symbol}</span><span className="text-gray-400">{s.count} trades</span></li>
                  ))}
                </ul>
              ) : <div className="text-gray-500">No data yet</div>}
            </div>
            <div className="glass p-6 rounded-xl border border-cyan-700 shadow-md animate-slide-in">
              <h3 className="text-lg font-semibold text-cyan-400 mb-2">Fastest/Slowest Trade</h3>
              {dashboardData.insights && dashboardData.insights.fastest_trade ? (
                <div className="mb-2">
                  <div className="text-xs text-gray-400">Fastest</div>
                  <div className="text-white font-semibold">{dashboardData.insights.fastest_trade.tradingsymbol}</div>
                  <div className="text-gray-400 text-xs">{dashboardData.insights.fastest_trade.entry_time && dashboardData.insights.fastest_trade.exit_time ? `${((new Date(dashboardData.insights.fastest_trade.exit_time) - new Date(dashboardData.insights.fastest_trade.entry_time)) / 60 / 1000).toFixed(1)} min` : '-'}</div>
                </div>
              ) : <div className="text-gray-500">No data yet</div>}
              {dashboardData.insights && dashboardData.insights.slowest_trade ? (
                <div>
                  <div className="text-xs text-gray-400">Slowest</div>
                  <div className="text-white font-semibold">{dashboardData.insights.slowest_trade.tradingsymbol}</div>
                  <div className="text-gray-400 text-xs">{dashboardData.insights.slowest_trade.entry_time && dashboardData.insights.slowest_trade.exit_time ? `${((new Date(dashboardData.insights.slowest_trade.exit_time) - new Date(dashboardData.insights.slowest_trade.entry_time)) / 60 / 1000).toFixed(1)} min` : '-'}</div>
                </div>
              ) : <div className="text-gray-500">No data yet</div>}
            </div>
          </div>
        </div>

        {/* Refresh Button */}
        <div className="mt-8 text-center">
          <button
            onClick={fetchDashboardData}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Refresh Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

export default VirtualTradingPage; 