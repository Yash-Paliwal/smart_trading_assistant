// src/components/LiveTradingDashboard.js

import React, { useState, useEffect } from 'react';
import websocketService from '../services/websocketService';
import './LiveTradingDashboard.css';

const LiveTradingDashboard = ({ userId }) => {
    const [walletData, setWalletData] = useState(null);
    const [openTrades, setOpenTrades] = useState([]);
    const [priceUpdates, setPriceUpdates] = useState({});
    const [connectionStatus, setConnectionStatus] = useState('disconnected');
    const [lastUpdate, setLastUpdate] = useState(null);

    useEffect(() => {
        if (!userId) return;

        // Connect to WebSockets
        websocketService.connectTrading(userId);
        websocketService.connectPrices();
        websocketService.startPing();

        // Set up event listeners
        const handleWalletData = (data) => {
            setWalletData(data);
            setLastUpdate(new Date());
        };

        const handleOpenTrades = (data) => {
            setOpenTrades(data);
            setLastUpdate(new Date());
        };

        const handleTradeUpdate = (data) => {
            // Update open trades when a trade is closed
            websocketService.sendTradingMessage({ type: 'get_open_trades' });
            websocketService.sendTradingMessage({ type: 'get_wallet_data' });
            
            // Show notification
            showNotification(`Trade ${data.tradingsymbol} closed: ₹${data.pnl.toFixed(2)} (${data.exit_reason})`);
        };

        const handlePriceUpdate = (data) => {
            setPriceUpdates(prev => ({
                ...prev,
                [data.instrument_key]: {
                    price: data.current_price,
                    timestamp: data.timestamp
                }
            }));
        };

        const handleError = (error) => {
            console.error('WebSocket error:', error);
            showNotification(`Error: ${error.message}`, 'error');
        };

        // Add event listeners
        websocketService.on('wallet_data', handleWalletData);
        websocketService.on('open_trades', handleOpenTrades);
        websocketService.on('trade_update', handleTradeUpdate);
        websocketService.on('price_update', handlePriceUpdate);
        websocketService.on('error', handleError);

        // Update connection status
        const updateConnectionStatus = () => {
            const status = websocketService.getConnectionStatus();
            if (status.trading === WebSocket.OPEN && status.price === WebSocket.OPEN) {
                setConnectionStatus('connected');
            } else if (status.trading === WebSocket.CONNECTING || status.price === WebSocket.CONNECTING) {
                setConnectionStatus('connecting');
            } else {
                setConnectionStatus('disconnected');
            }
        };

        const statusInterval = setInterval(updateConnectionStatus, 1000);

        // Cleanup
        return () => {
            websocketService.off('wallet_data', handleWalletData);
            websocketService.off('open_trades', handleOpenTrades);
            websocketService.off('trade_update', handleTradeUpdate);
            websocketService.off('price_update', handlePriceUpdate);
            websocketService.off('error', handleError);
            clearInterval(statusInterval);
            websocketService.disconnect();
        };
    }, [userId]);

    const showNotification = (message, type = 'info') => {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    };

    const getCurrentPrice = (instrumentKey) => {
        const update = priceUpdates[instrumentKey];
        return update ? update.price : null;
    };

    const calculateUnrealizedPnL = (trade) => {
        const currentPrice = getCurrentPrice(trade.instrument_key);
        if (!currentPrice) return null;

        if (trade.trade_type === 'BUY') {
            return (currentPrice - trade.entry_price) * trade.quantity;
        } else {
            return (trade.entry_price - currentPrice) * trade.quantity;
        }
    };

    const getConnectionStatusColor = () => {
        switch (connectionStatus) {
            case 'connected': return '#4CAF50';
            case 'connecting': return '#FF9800';
            case 'disconnected': return '#F44336';
            default: return '#9E9E9E';
        }
    };

    if (!userId) {
        return <div className="dashboard-error">User ID required</div>;
    }

    return (
        <div className="live-trading-dashboard">
            {/* Header */}
            <div className="dashboard-header">
                <h2>Live Trading Dashboard</h2>
                <div className="connection-status">
                    <span 
                        className="status-indicator" 
                        style={{ backgroundColor: getConnectionStatusColor() }}
                    ></span>
                    <span className="status-text">
                        {connectionStatus.charAt(0).toUpperCase() + connectionStatus.slice(1)}
                    </span>
                    {lastUpdate && (
                        <span className="last-update">
                            Last update: {lastUpdate.toLocaleTimeString()}
                        </span>
                    )}
                </div>
            </div>

            {/* Wallet Summary */}
            {walletData && (
                <div className="wallet-summary">
                    <h3>Virtual Wallet</h3>
                    <div className="wallet-grid">
                        <div className="wallet-card">
                            <div className="card-label">Balance</div>
                            <div className="card-value">₹{walletData.balance?.toFixed(2) || '0.00'}</div>
                        </div>
                        <div className="wallet-card">
                            <div className="card-label">Total P&L</div>
                            <div className={`card-value ${walletData.total_pnl >= 0 ? 'positive' : 'negative'}`}>
                                ₹{walletData.total_pnl?.toFixed(2) || '0.00'}
                            </div>
                        </div>
                        <div className="wallet-card">
                            <div className="card-label">Total Value</div>
                            <div className="card-value">₹{walletData.total_value?.toFixed(2) || '0.00'}</div>
                        </div>
                        <div className="wallet-card">
                            <div className="card-label">Win Rate</div>
                            <div className="card-value">{(walletData.win_rate * 100)?.toFixed(1) || '0.0'}%</div>
                        </div>
                    </div>
                </div>
            )}

            {/* Open Trades */}
            <div className="open-trades-section">
                <h3>Open Trades ({openTrades.length})</h3>
                {openTrades.length === 0 ? (
                    <div className="no-trades">No open trades</div>
                ) : (
                    <div className="trades-grid">
                        {openTrades.map(trade => {
                            const unrealizedPnL = calculateUnrealizedPnL(trade);
                            const currentPrice = getCurrentPrice(trade.instrument_key);
                            
                            return (
                                <div key={trade.id} className="trade-card">
                                    <div className="trade-header">
                                        <span className="trade-symbol">{trade.tradingsymbol}</span>
                                        <span className={`trade-type ${trade.trade_type.toLowerCase()}`}>
                                            {trade.trade_type}
                                        </span>
                                    </div>
                                    
                                    <div className="trade-details">
                                        <div className="detail-row">
                                            <span>Quantity:</span>
                                            <span>{trade.quantity}</span>
                                        </div>
                                        <div className="detail-row">
                                            <span>Entry Price:</span>
                                            <span>₹{trade.entry_price}</span>
                                        </div>
                                        {currentPrice && (
                                            <div className="detail-row">
                                                <span>Current Price:</span>
                                                <span className={currentPrice >= trade.entry_price ? 'positive' : 'negative'}>
                                                    ₹{currentPrice}
                                                </span>
                                            </div>
                                        )}
                                        {unrealizedPnL !== null && (
                                            <div className="detail-row">
                                                <span>Unrealized P&L:</span>
                                                <span className={unrealizedPnL >= 0 ? 'positive' : 'negative'}>
                                                    ₹{unrealizedPnL.toFixed(2)}
                                                </span>
                                            </div>
                                        )}
                                        {trade.target_price && (
                                            <div className="detail-row">
                                                <span>Target:</span>
                                                <span>₹{trade.target_price}</span>
                                            </div>
                                        )}
                                        {trade.stop_loss && (
                                            <div className="detail-row">
                                                <span>Stop Loss:</span>
                                                <span>₹{trade.stop_loss}</span>
                                            </div>
                                        )}
                                    </div>
                                    
                                    <div className="trade-time">
                                        Entry: {new Date(trade.entry_time).toLocaleString()}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Price Updates */}
            {Object.keys(priceUpdates).length > 0 && (
                <div className="price-updates-section">
                    <h3>Live Prices</h3>
                    <div className="price-grid">
                        {Object.entries(priceUpdates).map(([instrumentKey, update]) => (
                            <div key={instrumentKey} className="price-card">
                                <div className="price-symbol">{instrumentKey}</div>
                                <div className="price-value">₹{update.price}</div>
                                <div className="price-time">
                                    {new Date(update.timestamp).toLocaleTimeString()}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default LiveTradingDashboard; 