// src/components/CloseTradeModal.js

import React, { useState } from 'react';

const CloseTradeModal = ({ tradeLog, onClose, onConfirm }) => {
  // State for the form fields
  const [exitPrice, setExitPrice] = useState('');
  const [notes, setNotes] = useState(tradeLog?.notes || ''); // Pre-fill with existing notes

  if (!tradeLog) {
    return null;
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Prepare the data to be sent to the API
    const closeData = {
      status: 'CLOSED',
      exit_price: parseFloat(exitPrice),
      notes: notes,
      // We can calculate the P&L on the frontend for immediate feedback,
      // but the backend should also calculate it for accuracy.
      pnl: parseFloat(exitPrice) - tradeLog.actual_entry_price,
    };
    
    // Call the onConfirm function passed from the parent page
    onConfirm(tradeLog.id, closeData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex justify-center items-center z-50">
      <div className="bg-gray-800 rounded-lg shadow-2xl p-8 w-full max-w-lg mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-white">Close Trade</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl">&times;</button>
        </div>
        
        <div className="mb-4">
            <p className="text-lg text-blue-400 font-semibold">{tradeLog.instrument_key.split('|')[1] || tradeLog.instrument_key}</p>
            <p className="text-sm text-gray-500">Entry Price: {tradeLog.actual_entry_price}</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="exitPrice" className="block text-sm font-medium text-gray-300">Exit Price</label>
              <input
                type="number"
                id="exitPrice"
                value={exitPrice}
                onChange={(e) => setExitPrice(e.target.value)}
                className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                required
                step="any"
              />
            </div>
            <div>
              <label htmlFor="notes" className="block text-sm font-medium text-gray-300">Final Notes</label>
              <textarea
                id="notes"
                rows="4"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., Exited due to target hit / stop-loss triggered."
              ></textarea>
            </div>
          </div>
          <div className="mt-8 flex justify-end space-x-4">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 rounded-md font-semibold text-gray-300 bg-gray-600 hover:bg-gray-500 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2 rounded-md font-semibold text-white bg-red-600 hover:bg-red-700 transition-colors"
            >
              Confirm & Close Trade
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CloseTradeModal;
