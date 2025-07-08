// src/components/AlertCard.js

import React, { useState, useEffect } from 'react';

const AlertCard = ({ alert, onPlan, hasPlan, livePrice }) => {
  const [remainingTime, setRemainingTime] = useState(alert.remaining_minutes);
  
  const alertDetails = typeof alert.alert_details === 'string' 
    ? JSON.parse(alert.alert_details) 
    : alert.alert_details || {};
  const indicators = typeof alert.indicators === 'string' 
    ? JSON.parse(alert.indicators) 
    : alert.indicators || {};
  
  const score = alertDetails.score || 0;
  const reasons = alertDetails.reasons || [];

  // **NEW: Enhanced priority classification logic**
  const getPriorityLevel = () => {
    if (!alert.is_time_sensitive) return 'SCREENING';
    
    // **NEW: Enhanced priority logic for entry alerts**
    const volumeConfirmation = indicators.Volume_Confirmation || false;
    const riskReward = indicators.Risk_Reward || 0;
    const rsi = indicators.RSI || 50;
    const volume = indicators.Volume || 0;
    const avgVolume = indicators.Average_Volume || 0;
    
    let priorityScore = 0;
    
    // Volume confirmation adds significant weight
    if (volumeConfirmation) priorityScore += 3;
    
    // Risk/Reward ratio
    if (riskReward >= 2.0) priorityScore += 2;
    else if (riskReward >= 1.5) priorityScore += 1;
    
    // RSI conditions
    if (rsi >= 70 || rsi <= 30) priorityScore += 1; // Overbought/Oversold
    
    // Volume analysis
    if (volume > avgVolume * 1.5) priorityScore += 1; // High volume
    
    // Score from alert details
    priorityScore += score;
    
    // **NEW: Priority classification based on score**
    if (priorityScore >= 6) return 'HIGH';
    if (priorityScore >= 4) return 'MEDIUM';
    return 'LOW';
  };

  // **NEW: Enhanced expiry classification**
  const getExpiryStatus = () => {
    if (!alert.is_time_sensitive || remainingTime === null) return 'NONE';
    
    if (remainingTime <= 0) return 'EXPIRED';
    if (remainingTime <= 5) return 'CRITICAL';
    if (remainingTime <= 15) return 'URGENT';
    if (remainingTime <= 30) return 'WARNING';
    return 'SAFE';
  };

  const priorityLevel = getPriorityLevel();
  const expiryStatus = getExpiryStatus();

  // **NEW: Countdown timer for time-sensitive alerts only**
  useEffect(() => {
    if (!alert.is_time_sensitive || remainingTime === null || remainingTime <= 0) return;

    const interval = setInterval(() => {
      setRemainingTime(prev => {
        if (prev <= 1) {
          return 0;
        }
        return prev - 1;
      });
    }, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [remainingTime, alert.is_time_sensitive]);

  const handlePlanClick = () => {
    console.log("[DEBUG] 'Create Trade Plan' button clicked in AlertCard. Calling onPlan function...");
    onPlan(alert);
  };

  // **NEW: Enhanced priority color with better logic**
  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'HIGH': return 'bg-gradient-to-r from-red-500 to-pink-500 text-white';
      case 'MEDIUM': return 'bg-gradient-to-r from-yellow-500 to-orange-500 text-black';
      case 'LOW': return 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white';
      case 'SCREENING': return 'bg-gradient-to-r from-green-500 to-emerald-500 text-white';
      default: return 'bg-gradient-to-r from-gray-500 to-gray-600 text-white';
    }
  };

  // **NEW: Enhanced alert type color**
  const getAlertTypeColor = (alertType) => {
    switch (alertType) {
      case 'ORB': return 'bg-gradient-to-r from-purple-500 to-indigo-500 text-white';
      case 'BREAKOUT': return 'bg-gradient-to-r from-green-500 to-emerald-500 text-white';
      case 'REVERSAL': return 'bg-gradient-to-r from-orange-500 to-red-500 text-white';
      default: return 'bg-gradient-to-r from-gray-500 to-gray-600 text-white';
    }
  };

  // **NEW: Enhanced strategy color for screening alerts**
  const getStrategyColor = (strategy) => {
    switch (strategy) {
      case 'Bullish_Scan': return 'bg-gradient-to-r from-green-500 to-emerald-500 text-white';
      case 'Bearish_Scan': return 'bg-gradient-to-r from-red-500 to-pink-500 text-white';
      case 'Daily_Confluence_Scan': return 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white';
      case 'Full_Scan': return 'bg-gradient-to-r from-purple-500 to-indigo-500 text-white';
      default: return 'bg-gradient-to-r from-gray-500 to-gray-600 text-white';
    }
  };

  // **NEW: Enhanced confidence color**
  const getConfidenceColor = (score) => {
    if (score >= 4) return 'bg-gradient-to-r from-green-500 to-emerald-500 text-white';
    if (score >= 3) return 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white';
    if (score >= 2) return 'bg-gradient-to-r from-yellow-500 to-orange-500 text-black';
    return 'bg-gradient-to-r from-red-500 to-pink-500 text-white';
  };

  // **NEW: Enhanced expiry color based on status**
  const getExpiryColor = (status) => {
    switch (status) {
      case 'CRITICAL': return 'bg-gradient-to-r from-red-600 to-pink-600 text-white animate-pulse';
      case 'URGENT': return 'bg-gradient-to-r from-orange-500 to-red-500 text-white';
      case 'WARNING': return 'bg-gradient-to-r from-yellow-500 to-orange-500 text-black';
      case 'SAFE': return 'bg-gradient-to-r from-green-500 to-emerald-500 text-white';
      case 'EXPIRED': return 'bg-gradient-to-r from-gray-500 to-gray-600 text-white';
      default: return 'bg-gradient-to-r from-gray-500 to-gray-600 text-white';
    }
  };

  // **NEW: Get expiry status text**
  const getExpiryText = (status) => {
    switch (status) {
      case 'CRITICAL': return `${remainingTime}m left - CRITICAL!`;
      case 'URGENT': return `${remainingTime}m left - URGENT`;
      case 'WARNING': return `${remainingTime}m left - WARNING`;
      case 'SAFE': return `${remainingTime}m left`;
      case 'EXPIRED': return 'EXPIRED';
      default: return '';
    }
  };

  return (
    <div className={`glass card-hover rounded-xl shadow-lg p-6 mb-6 animate-fade-in ${
      expiryStatus === 'CRITICAL' ? 'border-2 border-red-500 animate-pulse' : 
      expiryStatus === 'URGENT' ? 'border-2 border-orange-500' :
      expiryStatus === 'WARNING' ? 'border-2 border-yellow-500' :
      'border border-gray-700'
    }`}>
      {/* Header Section */}
      <div className="flex justify-between items-start mb-6 gap-4">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <h3 className="text-2xl font-bold text-white">{alert.tradingsymbol || alert.instrument_key}</h3>
            {livePrice !== undefined && (
              <span className="ml-2 px-2 py-1 rounded bg-green-700 text-white text-sm font-mono">
                Live: ₹{livePrice.toFixed(2)}
              </span>
            )}
            {expiryStatus === 'CRITICAL' && (
              <div className="animate-countdown">
                <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                </svg>
              </div>
            )}
          </div>
          <p className="text-sm text-gray-400 font-mono">{alert.instrument_key}</p>
        </div>
        
        <div className="text-right flex-shrink-0">
          <div className="flex flex-col gap-3">
            {/* **NEW: Enhanced badges with better classification */}
            <div className="flex gap-2 justify-end">
              {alert.is_time_sensitive ? (
                // Entry alerts: Priority and Alert Type
                <>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold shadow-md ${getPriorityColor(priorityLevel)}`}>
                    {priorityLevel}
                  </span>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold shadow-md ${getAlertTypeColor(alert.alert_type)}`}>
                    {alert.alert_type}
                  </span>
                </>
              ) : (
                // Screening alerts: Strategy
                <span className={`px-3 py-1 rounded-full text-xs font-semibold shadow-md ${getStrategyColor(alert.source_strategy)}`}>
                  {alert.source_strategy.replace('_', ' ')}
                </span>
              )}
            </div>
            
            {/* **NEW: Enhanced remaining time indicator with better classification */}
            {alert.is_time_sensitive && remainingTime !== null && (
              <div className={`px-4 py-2 rounded-lg text-sm font-semibold shadow-md ${getExpiryColor(expiryStatus)}`}>
                <div className="flex items-center justify-center space-x-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{getExpiryText(expiryStatus)}</span>
                </div>
              </div>
            )}
            
            <span className={`px-4 py-2 rounded-lg text-sm font-semibold shadow-md ${getConfidenceColor(score)}`}>
              <div className="flex items-center justify-center space-x-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Confidence: {score}</span>
              </div>
            </span>
            
            <p className="text-xs text-gray-500 mt-1">
              {new Date(alert.timestamp).toLocaleString()}
            </p>
          </div>
        </div>
      </div>
      
      {/* Supporting Signals Section */}
      <div className="mb-6">
        <div className="flex items-center space-x-2 mb-3">
          <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <p className="text-lg font-semibold text-gray-300">Supporting Signals:</p>
        </div>
        <ul className="list-none space-y-2">
          {reasons.map((reason, index) => (
            <li key={index} className="flex items-start space-x-2 text-gray-400">
              <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
              <span>{reason}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Indicators Section */}
      <div className="border-t border-gray-700 pt-6">
        <div className="flex items-center space-x-2 mb-4">
          <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p className="text-lg font-semibold text-gray-300">Indicator Values:</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-6">
          <div className="glass p-3 rounded-lg border border-gray-600">
            <p className="text-gray-400 text-xs uppercase tracking-wide">Close Price</p>
            <p className="text-white font-mono text-lg font-semibold">₹{indicators.Close?.toFixed(2) || 'N/A'}</p>
          </div>
          <div className="glass p-3 rounded-lg border border-gray-600">
            <p className="text-gray-400 text-xs uppercase tracking-wide">RSI (14)</p>
            <p className="text-white font-mono text-lg font-semibold">{indicators.RSI?.toFixed(2) || 'N/A'}</p>
          </div>
          <div className="glass p-3 rounded-lg border border-gray-600">
            <p className="text-gray-400 text-xs uppercase tracking-wide">Volume</p>
            <p className="text-white font-mono text-lg font-semibold">{indicators.Volume?.toLocaleString() || 'N/A'}</p>
          </div>
          <div className="glass p-3 rounded-lg border border-gray-600">
            <p className="text-gray-400 text-xs uppercase tracking-wide">EMA (50)</p>
            <p className="text-white font-mono text-lg font-semibold">₹{indicators.EMA50?.toFixed(2) || 'N/A'}</p>
          </div>
        </div>
        
        {/* **NEW: ORB-specific indicators for entry alerts */}
        {alert.is_time_sensitive && alert.alert_type === 'ORB' && indicators.Entry_Price && (
          <div className="mb-6">
            <div className="flex items-center space-x-2 mb-4">
              <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              <p className="text-lg font-semibold text-gray-300">Trade Setup:</p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="bg-gradient-to-r from-blue-900 to-blue-800 p-3 rounded-lg border border-blue-700">
                <p className="text-blue-300 text-xs uppercase tracking-wide">Entry Price</p>
                <p className="text-white font-mono text-lg font-semibold">₹{indicators.Entry_Price?.toFixed(2)}</p>
              </div>
              <div className="bg-gradient-to-r from-red-900 to-red-800 p-3 rounded-lg border border-red-700">
                <p className="text-red-300 text-xs uppercase tracking-wide">Stop Loss</p>
                <p className="text-white font-mono text-lg font-semibold">₹{indicators.Stop_Loss?.toFixed(2)}</p>
              </div>
              <div className="bg-gradient-to-r from-green-900 to-green-800 p-3 rounded-lg border border-green-700">
                <p className="text-green-300 text-xs uppercase tracking-wide">Target</p>
                <p className="text-white font-mono text-lg font-semibold">₹{indicators.Target?.toFixed(2)}</p>
              </div>
              <div className="bg-gradient-to-r from-purple-900 to-purple-800 p-3 rounded-lg border border-purple-700">
                <p className="text-purple-300 text-xs uppercase tracking-wide">Risk/Reward</p>
                <p className="text-white font-mono text-lg font-semibold">1:{indicators.Risk_Reward?.toFixed(2)}</p>
              </div>
            </div>
          </div>
        )}
        
        {/* **NEW: Screening-specific indicators */}
        {!alert.is_time_sensitive && (
          <div className="mb-6">
            <div className="flex items-center space-x-2 mb-4">
              <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              <p className="text-lg font-semibold text-gray-300">Fundamental Data:</p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="bg-gradient-to-r from-green-900 to-green-800 p-3 rounded-lg border border-green-700">
                <p className="text-green-300 text-xs uppercase tracking-wide">Sector</p>
                <p className="text-white font-mono text-lg font-semibold">{indicators.Sector || 'N/A'}</p>
              </div>
              <div className="bg-gradient-to-r from-blue-900 to-blue-800 p-3 rounded-lg border border-blue-700">
                <p className="text-blue-300 text-xs uppercase tracking-wide">Market Cap</p>
                <p className="text-white font-mono text-lg font-semibold">{indicators.Market_Cap || 'N/A'}</p>
              </div>
              <div className="bg-gradient-to-r from-purple-900 to-purple-800 p-3 rounded-lg border border-purple-700">
                <p className="text-purple-300 text-xs uppercase tracking-wide">Volume Avg</p>
                <p className="text-white font-mono text-lg font-semibold">{indicators.Average_Volume?.toLocaleString() || 'N/A'}</p>
              </div>
              <div className="bg-gradient-to-r from-orange-900 to-orange-800 p-3 rounded-lg border border-orange-700">
                <p className="text-orange-300 text-xs uppercase tracking-wide">52W High</p>
                <p className="text-white font-mono text-lg font-semibold">₹{indicators.Year_High?.toFixed(2) || 'N/A'}</p>
              </div>
            </div>
          </div>
        )}
        
        {/* Action Button */}
        <div className="flex justify-end">
          <button
            onClick={handlePlanClick}
            disabled={hasPlan || (alert.is_time_sensitive && remainingTime === 0)}
            className={`px-6 py-3 rounded-lg font-semibold text-white transition-all duration-200 shadow-md hover:shadow-lg ${
              hasPlan 
                ? 'bg-gradient-to-r from-green-500 to-emerald-500 cursor-not-allowed' 
                : alert.is_time_sensitive && remainingTime === 0
                ? 'bg-gradient-to-r from-gray-500 to-gray-600 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 hover:transform hover:scale-105'
            }`}
          >
            <div className="flex items-center space-x-2">
              {hasPlan ? (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Plan Created</span>
                </>
              ) : alert.is_time_sensitive && remainingTime === 0 ? (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Alert Expired</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  <span>Create Trade Plan</span>
                </>
              )}
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default AlertCard;
