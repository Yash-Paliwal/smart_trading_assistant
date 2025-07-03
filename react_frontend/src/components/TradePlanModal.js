// src/components/TradePlanModal.js

import React, { useState, useEffect } from 'react';

const TradePlanModal = ({ stock, onClose, onSubmit }) => {
  // Use useEffect to set the initial state when the component receives the stock prop
  const [entryPrice, setEntryPrice] = useState('');
  const [stopLoss, setStopLoss] = useState('');
  const [target, setTarget] = useState('');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    if (stock && stock.indicators) {
      const close = stock.indicators.Close;
      // We need to make sure our indicator calculator provides the 'Low' price.
      // For now, let's assume it does for the logic.
      const low = stock.indicators.Low || (close * 0.98); // Fallback to 2% below close
      
      if (close && low) {
        const suggestedEntry = close.toFixed(2);
        const suggestedStopLoss = low.toFixed(2);
        
        // Calculate suggested target with a 1.5:1 risk/reward ratio
        const risk = suggestedEntry - suggestedStopLoss;
        if (risk > 0) {
            const suggestedTarget = (parseFloat(suggestedEntry) + (risk * 1.5)).toFixed(2);
            setTarget(suggestedTarget);
        }

        setEntryPrice(suggestedEntry);
        setStopLoss(suggestedStopLoss);
      }
      
      // Pre-fill notes with the reasons from the alert
      const reasons = stock.alert_details?.reasons || [];
      setNotes(reasons.join('\n'));
    }
  }, [stock]); // This effect runs whenever the 'stock' prop changes

  if (!stock) {
    return null;
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    const tradePlan = {
      instrument_key: stock.instrument_key,
      planned_entry_price: parseFloat(entryPrice),
      stop_loss_price: parseFloat(stopLoss),
      target_price: parseFloat(target),
      notes: notes,
    };
    onSubmit(tradePlan);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex justify-center items-center z-50">
      <div className="bg-gray-800 rounded-lg shadow-2xl p-8 w-full max-w-lg mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-white">Create Trade Plan</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl">&times;</button>
        </div>
        <div className="mb-4">
            <p className="text-lg text-blue-400 font-semibold">{stock.tradingsymbol || stock.instrument_key}</p>
            <p className="text-sm text-gray-500">Last Price: {stock.indicators?.Close?.toFixed(2) || 'N/A'}</p>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="entryPrice" className="block text-sm font-medium text-gray-300">Planned Entry Price</label>
              <input type="number" id="entryPrice" value={entryPrice} onChange={(e) => setEntryPrice(e.target.value)} className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 text-white" required step="any" />
            </div>
            <div>
              <label htmlFor="stopLoss" className="block text-sm font-medium text-gray-300">Stop-Loss Price</label>
              <input type="number" id="stopLoss" value={stopLoss} onChange={(e) => setStopLoss(e.target.value)} className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 text-white" required step="any" />
            </div>
            <div>
              <label htmlFor="target" className="block text-sm font-medium text-gray-300">Target Price</label>
              <input type="number" id="target" value={target} onChange={(e) => setTarget(e.target.value)} className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 text-white" step="any" />
            </div>
            <div>
              <label htmlFor="notes" className="block text-sm font-medium text-gray-300">Notes / Strategy</label>
              <textarea id="notes" rows="4" value={notes} onChange={(e) => setNotes(e.target.value)} className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 text-white"></textarea>
            </div>
          </div>
          <div className="mt-8 flex justify-end space-x-4">
            <button type="button" onClick={onClose} className="px-6 py-2 rounded-md font-semibold text-gray-300 bg-gray-600 hover:bg-gray-500">Cancel</button>
            <button type="submit" className="px-6 py-2 rounded-md font-semibold text-white bg-blue-600 hover:bg-blue-700">Save Plan</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TradePlanModal;
