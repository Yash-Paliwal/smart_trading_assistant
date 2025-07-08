import React, { useState, useEffect } from 'react';
import { getVirtualTradingDashboard } from '../api/apiService';

const VirtualTradingPage = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

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
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Virtual Trading Dashboard</h1>
          <p className="text-gray-600">Track your virtual portfolio performance and trades</p>
        </div>

        {/* Portfolio Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Balance</p>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(wallet.balance)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total P&L</p>
                <p className={`text-2xl font-bold ${getPnlColor(wallet.total_pnl)}`}>
                  {formatCurrency(wallet.total_pnl)}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Win Rate</p>
                <p className="text-2xl font-bold text-gray-900">{Number(wallet.win_rate || 0).toFixed(1)}%</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-lg">
                <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Trades</p>
                <p className="text-2xl font-bold text-gray-900">{Number(wallet.total_trades || 0)}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Open Positions */}
          <div className="bg-white rounded-lg shadow-md">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Open Positions</h2>
              <p className="text-sm text-gray-600">{open_positions.length} active positions</p>
            </div>
            <div className="p-6">
              {open_positions.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 text-4xl mb-4">📊</div>
                  <p className="text-gray-600">No open positions</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {open_positions.map((position) => (
                    <div key={position.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-semibold text-gray-900">{position.tradingsymbol}</h3>
                          <p className="text-sm text-gray-600">
                            {Number(position.quantity || 0)} shares @ {formatCurrency(position.avg_entry_price)}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className={`font-semibold ${getPnlColor(position.unrealized_pnl)}`}>
                            {formatCurrency(position.unrealized_pnl)}
                          </p>
                          <p className={`text-sm ${getPnlColor(position.unrealized_pnl_percentage)}`}>
                            {formatPercentage(position.unrealized_pnl_percentage)}
                          </p>
                        </div>
                      </div>
                      <div className="flex justify-between text-sm text-gray-600">
                        <span>Current: {formatCurrency(position.current_price)}</span>
                        <span>Value: {formatCurrency(Number(position.current_price || 0) * Number(position.quantity || 0))}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Recent Trades */}
          <div className="bg-white rounded-lg shadow-md">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Recent Trades</h2>
              <p className="text-sm text-gray-600">Latest {recent_trades.length} trades</p>
            </div>
            <div className="p-6">
              {recent_trades.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 text-4xl mb-4">📈</div>
                  <p className="text-gray-600">No trades yet</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {recent_trades.map((trade) => (
                    <div key={trade.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-semibold text-gray-900">{trade.tradingsymbol}</h3>
                          <p className="text-sm text-gray-600">
                            {trade.trade_type} • {Number(trade.quantity || 0)} shares @ {formatCurrency(trade.entry_price)}
                          </p>
                        </div>
                        <div className="text-right">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            trade.status === 'EXECUTED' ? 'bg-green-100 text-green-800' :
                            trade.status === 'CLOSED' ? 'bg-gray-100 text-gray-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {trade.status}
                          </span>
                        </div>
                      </div>
                      {trade.pnl && (
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">P&L:</span>
                          <span className={`font-medium ${getPnlColor(trade.pnl)}`}>
                            {formatCurrency(trade.pnl)} ({formatPercentage(trade.pnl_percentage)})
                          </span>
                        </div>
                      )}
                      <div className="flex justify-between text-xs text-gray-500 mt-2">
                        <span>Entry: {new Date(trade.entry_time).toLocaleDateString()}</span>
                        {trade.exit_time && (
                          <span>Exit: {new Date(trade.exit_time).toLocaleDateString()}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Statistics */}
        {statistics && (
          <div className="mt-8 bg-white rounded-lg shadow-md">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Trading Statistics</h2>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <p className="text-sm text-gray-600">Profitable Trades</p>
                  <p className="text-2xl font-bold text-green-600">{Number(statistics.profitable_trades || 0)}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-600">Average Profit</p>
                  <p className="text-2xl font-bold text-green-600">{formatCurrency(statistics.avg_profit)}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-600">Average Loss</p>
                  <p className="text-2xl font-bold text-red-600">{formatCurrency(statistics.avg_loss)}</p>
                </div>
              </div>
            </div>
          </div>
        )}

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