// src/services/websocketService.js

class WebSocketService {
    constructor() {
        this.tradingSocket = null;
        this.priceSocket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.listeners = {
            wallet_data: [],
            open_trades: [],
            trade_update: [],
            price_update: [],
            trade_executed: [],
            error: []
        };
    }

    // Connect to trading WebSocket
    connectTrading(userId) {
        if (this.tradingSocket && this.tradingSocket.readyState === WebSocket.OPEN) {
            console.log('Trading WebSocket already connected');
            return;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Use Django server port for WebSocket connections and encode user ID
        const encodedUserId = encodeURIComponent(userId);
        const wsUrl = `${protocol}//localhost:8000/ws/trading/${encodedUserId}/`;
        
        console.log('Connecting to trading WebSocket:', wsUrl);
        
        this.tradingSocket = new WebSocket(wsUrl);
        
        this.tradingSocket.onopen = () => {
            console.log('Trading WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            
            // Send initial data request
            this.sendTradingMessage({
                type: 'get_wallet_data'
            });
            
            this.sendTradingMessage({
                type: 'get_open_trades'
            });
        };
        
        this.tradingSocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleTradingMessage(data);
            } catch (error) {
                console.error('Error parsing trading WebSocket message:', error);
                this.emit('error', { message: 'Invalid message format' });
            }
        };
        
        this.tradingSocket.onclose = (event) => {
            console.log('Trading WebSocket disconnected:', event.code, event.reason);
            this.isConnected = false;
            this.handleReconnect('trading', userId);
        };
        
        this.tradingSocket.onerror = (error) => {
            console.error('Trading WebSocket error:', error);
            this.emit('error', { message: 'WebSocket connection error' });
        };
    }

    // Connect to price WebSocket
    connectPrices() {
        if (this.priceSocket && this.priceSocket.readyState === WebSocket.OPEN) {
            console.log('Price WebSocket already connected');
            return;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Use Django server port for WebSocket connections
        const wsUrl = `${protocol}//localhost:8000/ws/prices/`;
        
        console.log('Connecting to price WebSocket:', wsUrl);
        
        this.priceSocket = new WebSocket(wsUrl);
        
        this.priceSocket.onopen = () => {
            console.log('Price WebSocket connected');
        };
        
        this.priceSocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handlePriceMessage(data);
            } catch (error) {
                console.error('Error parsing price WebSocket message:', error);
                this.emit('error', { message: 'Invalid message format' });
            }
        };
        
        this.priceSocket.onclose = (event) => {
            console.log('Price WebSocket disconnected:', event.code, event.reason);
            this.handleReconnect('price');
        };
        
        this.priceSocket.onerror = (error) => {
            console.error('Price WebSocket error:', error);
            this.emit('error', { message: 'WebSocket connection error' });
        };
    }

    // Handle reconnection
    handleReconnect(type, userId = null) {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error(`Max reconnection attempts reached for ${type} WebSocket`);
            this.emit('error', { message: 'Connection lost. Please refresh the page.' });
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`Reconnecting ${type} WebSocket in ${delay}ms (attempt ${this.reconnectAttempts})`);
        
        setTimeout(() => {
            if (type === 'trading' && userId) {
                this.connectTrading(userId);
            } else if (type === 'price') {
                this.connectPrices();
            }
        }, delay);
    }

    // Send message to trading WebSocket
    sendTradingMessage(message) {
        if (this.tradingSocket && this.tradingSocket.readyState === WebSocket.OPEN) {
            this.tradingSocket.send(JSON.stringify(message));
        } else {
            console.warn('Trading WebSocket not connected');
        }
    }

    // Send message to price WebSocket
    sendPriceMessage(message) {
        if (this.priceSocket && this.priceSocket.readyState === WebSocket.OPEN) {
            this.priceSocket.send(JSON.stringify(message));
        } else {
            console.warn('Price WebSocket not connected');
        }
    }

    // Handle trading WebSocket messages
    handleTradingMessage(data) {
        const { type, data: messageData } = data;
        
        switch (type) {
            case 'wallet_data':
                this.emit('wallet_data', messageData);
                break;
            case 'open_trades':
                this.emit('open_trades', messageData);
                break;
            case 'trade_update':
                this.emit('trade_update', messageData);
                break;
            case 'pong':
                // Handle ping-pong for connection health
                break;
            case 'error':
                this.emit('error', messageData);
                break;
            default:
                console.log('Unknown trading message type:', type);
        }
    }

    // Handle price WebSocket messages
    handlePriceMessage(data) {
        console.log('WebSocket received message:', data); // DEBUG
        const { type, data: messageData } = data;
        
        switch (type) {
            case 'price_update':
                console.log('Processing price_update:', messageData); // DEBUG
                this.emit('price_update', messageData);
                break;
            case 'trade_executed':
                this.emit('trade_executed', messageData);
                break;
            case 'pong':
                // Handle ping-pong for connection health
                break;
            case 'error':
                this.emit('error', messageData);
                break;
            default:
                console.log('Unknown price message type:', type);
        }
    }

    // Event listener management
    on(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event].push(callback);
        }
    }

    off(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }

    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${event} listener:`, error);
                }
            });
        }
    }

    // Ping to keep connection alive
    startPing() {
        this.pingInterval = setInterval(() => {
            if (this.tradingSocket && this.tradingSocket.readyState === WebSocket.OPEN) {
                this.sendTradingMessage({ type: 'ping' });
            }
            if (this.priceSocket && this.priceSocket.readyState === WebSocket.OPEN) {
                this.sendPriceMessage({ type: 'ping' });
            }
        }, 30000); // Ping every 30 seconds
    }

    stopPing() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    // Disconnect all WebSockets
    disconnect() {
        this.stopPing();
        
        if (this.tradingSocket) {
            this.tradingSocket.close();
            this.tradingSocket = null;
        }
        
        if (this.priceSocket) {
            this.priceSocket.close();
            this.priceSocket = null;
        }
        
        this.isConnected = false;
        this.reconnectAttempts = 0;
        
        console.log('All WebSocket connections closed');
    }

    // Get connection status
    getConnectionStatus() {
        return {
            trading: this.tradingSocket ? this.tradingSocket.readyState : WebSocket.CLOSED,
            price: this.priceSocket ? this.priceSocket.readyState : WebSocket.CLOSED,
            isConnected: this.isConnected
        };
    }
}

// Create singleton instance
const websocketService = new WebSocketService();

export default websocketService; 