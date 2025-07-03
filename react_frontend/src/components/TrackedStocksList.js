// src/components/TrackedStocksList.js

import React from 'react';

const TrackedStocksList = ({ trackedStocks }) => {
  // This component receives the list of tracked stock objects from the API

  return (
    <div className="mb-10 p-6 bg-gray-800 border border-gray-700 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-white mb-4">Today's Watchlist</h2>
      {trackedStocks.length > 0 ? (
        <div className="flex flex-wrap gap-3">
          {/* Loop through the tracked stocks and display each one as a badge */}
          {trackedStocks.map((stock) => (
            <div 
              key={stock.instrument_key}
              className="bg-gray-700 text-gray-200 px-4 py-2 rounded-full text-sm font-medium"
            >
              {/* We split the instrument key to show a cleaner trading symbol */}
              {stock.instrument_key.split('|')[1] || stock.instrument_key}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-gray-500 italic">You haven't tracked any stocks yet. Click "Track Stock" on an alert to add it to your watchlist.</p>
      )}
    </div>
  );
};

export default TrackedStocksList;
