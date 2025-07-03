// src/components/ActivateTradeModal.js

import React, { useState, useEffect } from 'react';

const ActivateTradeModal = ({ tradePlan, onClose, onActivate }) => {
  // Pre-fill the form with the data from the original plan
  const [actualEntry, setActualEntry] = useState('');

  useEffect(() => {
    if (tradePlan) {
      // Pre-fill the entry price from the plan, but allow the user to change it.
      setActualEntry(tradePlan.planned_entry_price || '');
    }
  }, [tradePlan]);

  if (!tradePlan) {
    return null;
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Prepare the data to be sent to the API
    const activationData = {
      status: 'ACTIVE',
      actual_entry_price: parseFloat(actualEntry),
    };
    
    // Call the onActivate function passed from the parent page
    onActivate(tradePlan.id, activationData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex justify-center items-center z-50">
      <div className="bg-gray-800 rounded-lg shadow-2xl p-8 w-full max-w-lg mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-white">Activate Trade</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl">&times;</button>
        </div>
        
        <div className="mb-4">
            <p className="text-lg text-blue-400 font-semibold">{tradePlan.instrument_key.split('|')[1] || tradePlan.instrument_key}</p>
            <p className="text-sm text-gray-500">Planned Entry: {tradePlan.planned_entry_price}</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="actualEntry" className="block text-sm font-medium text-gray-300">Actual Entry Price</label>
              <input
                type="number"
                id="actualEntry"
                value={actualEntry}
                onChange={(e) => setActualEntry(e.target.value)}
                className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                required
                step="any"
              />
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
              className="px-6 py-2 rounded-md font-semibold text-white bg-green-600 hover:bg-green-700 transition-colors"
            >
              Confirm & Activate
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ActivateTradeModal;
