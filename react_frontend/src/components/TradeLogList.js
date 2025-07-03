// src/components/TradeLogList.js

import React from 'react';

const TradeLogList = ({ tradeLogs, listType = 'plans', onActivate, onDelete, onCloseTrade }) => {
  // This component now receives an onCloseTrade handler function

  const getTitle = () => {
    if (listType === 'plans') return "My Trade Plans";
    if (listType === 'journal') return "My Trade Journal";
    return "Trade List";
  };

  const renderActions = (log) => {
    if (log.status === 'PLANNED' && onActivate && onDelete) {
      return (
        <>
          <button 
              onClick={() => onActivate(log)}
              className="text-green-400 hover:text-green-300 transition-colors text-sm font-semibold"
          >
              Activate
          </button>
          <button 
              onClick={() => onDelete(log.id)}
              className="text-red-500 hover:text-red-400 transition-colors text-sm font-semibold"
          >
              Delete
          </button>
        </>
      );
    }
    if (log.status === 'ACTIVE' && onCloseTrade) {
        return (
            <button 
                onClick={() => onCloseTrade(log)}
                className="text-yellow-400 hover:text-yellow-300 transition-colors text-sm font-semibold"
            >
                Close Trade
            </button>
        );
    }
    // No actions for CLOSED trades
    return null;
  };

  return (
    <div className="mb-12 p-6 bg-gray-800 border border-gray-700 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-white mb-4">{getTitle()}</h2>
      {tradeLogs.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-700">
            <thead className="bg-gray-700">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Stock</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Status</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Entry</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Stop-Loss</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Target</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">P&L</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-gray-800 divide-y divide-gray-700">
              {tradeLogs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{log.instrument_key.split('|')[1] || log.instrument_key}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        log.status === 'PLANNED' ? 'bg-blue-900 text-blue-300' : 
                        log.status === 'ACTIVE' ? 'bg-yellow-900 text-yellow-300' : 
                        'bg-green-900 text-green-300'
                    }`}>
                      {log.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{log.actual_entry_price || log.planned_entry_price}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-red-400">{log.stop_loss_price}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-green-400">{log.target_price}</td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-semibold ${log.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>{log.pnl.toFixed(2)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex items-center space-x-4">
                        {renderActions(log)}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-gray-500 italic">No trades found for this view.</p>
      )}
    </div>
  );
};

export default TradeLogList;
