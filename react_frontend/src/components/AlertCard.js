// src/components/AlertCard.js

import React from 'react';

const AlertCard = ({ alert, onPlan, hasPlan }) => {
  const alertDetails = typeof alert.alert_details === 'string' 
    ? JSON.parse(alert.alert_details) 
    : alert.alert_details || {};
  const indicators = typeof alert.indicators === 'string' 
    ? JSON.parse(alert.indicators) 
    : alert.indicators || {};
  
  const score = alertDetails.score || 0;
  const reasons = alertDetails.reasons || [];

  const handlePlanClick = () => {
    // --- DEBUGGING STEP ---
    // This will print a message to the browser console when the button is clicked.
    console.log("[DEBUG] 'Create Trade Plan' button clicked in AlertCard. Calling onPlan function...");
    // --- END DEBUGGING STEP ---
    onPlan(alert);
  };

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-lg p-6 mb-6">
      <div className="flex justify-between items-start mb-4 gap-4">
        <div>
          <h3 className="text-2xl font-bold text-white">{alert.tradingsymbol || alert.instrument_key}</h3>
          <p className="text-sm text-gray-400">{alert.instrument_key}</p>
        </div>
        <div className="text-right flex-shrink-0">
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${score >= 3 ? 'bg-green-500 text-white' : 'bg-yellow-500 text-black'}`}>
                Confidence: {score}
            </span>
            <p className="text-xs text-gray-500 mt-1">
                {new Date(alert.timestamp).toLocaleString()}
            </p>
        </div>
      </div>
      
      <div className="mb-4">
        <p className="text-lg font-semibold text-gray-300">Supporting Signals:</p>
        <ul className="list-disc list-inside mt-2 text-gray-400">
          {reasons.map((reason, index) => (
            <li key={index}>{reason}</li>
          ))}
        </ul>
      </div>

      <div className="border-t border-gray-700 pt-4 flex flex-col gap-4">
         <p className="text-md font-semibold text-gray-300 mb-2">Indicator Values:</p>
         <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="bg-gray-700 p-2 rounded-md"><p className="text-gray-400">Close Price</p><p className="text-white font-mono">{indicators.Close?.toFixed(2) || 'N/A'}</p></div>
            <div className="bg-gray-700 p-2 rounded-md"><p className="text-gray-400">RSI (14)</p><p className="text-white font-mono">{indicators.RSI?.toFixed(2) || 'N/A'}</p></div>
            <div className="bg-gray-700 p-2 rounded-md"><p className="text-gray-400">Volume</p><p className="text-white font-mono">{indicators.Volume?.toLocaleString() || 'N/A'}</p></div>
             <div className="bg-gray-700 p-2 rounded-md"><p className="text-gray-400">EMA (50)</p><p className="text-white font-mono">{indicators.EMA50?.toFixed(2) || 'N/A'}</p></div>
         </div>
         <div className="mt-4 flex justify-end">
            <button
                onClick={handlePlanClick}
                disabled={hasPlan}
                className={`px-6 py-2 rounded-md font-semibold text-white transition-colors ${
                    hasPlan 
                    ? 'bg-green-600 cursor-not-allowed' 
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
            >
                {hasPlan ? 'Plan Created' : 'Create Trade Plan'}
            </button>
         </div>
      </div>
    </div>
  );
};

export default AlertCard;
