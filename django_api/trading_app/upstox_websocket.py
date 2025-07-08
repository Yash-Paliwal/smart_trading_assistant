# trading_app/upstox_websocket.py

import asyncio
import json
import websockets
import logging
from decimal import Decimal
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import VirtualTrade, VirtualWallet, UserProfile
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class UpstoxWebSocketClient:
    """WebSocket client for Upstox real-time price feed"""
    
    def __init__(self):
        self.websocket = None
        self.channel_layer = get_channel_layer()
        self.running = False
        self.reconnect_delay = 5
        self.max_reconnect_delay = 300
        
    async def connect(self):
        """Connect to Upstox WebSocket"""
        try:
            # Get access token from user profile
            user_profile = await self.get_user_profile()
            if not user_profile:
                logger.error("No user profile with Upstox access token found")
                return False
            
            # Upstox WebSocket URL
            ws_url = "wss://ws-api.upstox.com/index/dash/stream"
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(
                ws_url,
                extra_headers={
                    'Authorization': f'Bearer {user_profile.upstox_access_token}',
                    'Accept': 'application/json'
                }
            )
            
            logger.info("Connected to Upstox WebSocket")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Upstox WebSocket: {e}")
            return False
    
    async def subscribe_to_instruments(self, instrument_keys):
        """Subscribe to instrument price updates"""
        if not self.websocket:
            return
        
        try:
            # Subscribe message format for Upstox
            subscribe_message = {
                "action": "subscribe",
                "symbols": instrument_keys
            }
            
            await self.websocket.send(json.dumps(subscribe_message))
            logger.info(f"Subscribed to {len(instrument_keys)} instruments")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to instruments: {e}")
    
    async def get_instrument_keys(self):
        """Get all instrument keys from open trades"""
        try:
            open_trades = VirtualTrade.objects.filter(status='EXECUTED')
            instrument_keys = list(set(trade.instrument_key for trade in open_trades))
            return instrument_keys
        except Exception as e:
            logger.error(f"Failed to get instrument keys: {e}")
            return []
    
    async def get_user_profile(self):
        """Get user profile with Upstox access token"""
        try:
            user_profile = UserProfile.objects.filter(
                upstox_access_token__isnull=False
            ).first()
            return user_profile
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return None
    
    async def process_price_update(self, data):
        """Process price update and check for trade execution"""
        try:
            # Extract price data from Upstox message
            if 'data' in data:
                for instrument_data in data['data']:
                    instrument_key = instrument_data.get('instrument_key')
                    current_price = Decimal(str(instrument_data.get('last_price', 0)))
                    
                    if instrument_key and current_price > 0:
                        # Check open trades for this instrument
                        await self.check_trades_for_execution(instrument_key, current_price)
                        
                        # Broadcast price update to frontend
                        await self.broadcast_price_update(instrument_key, current_price)
                        
        except Exception as e:
            logger.error(f"Error processing price update: {e}")
    
    async def check_trades_for_execution(self, instrument_key, current_price):
        """Check if any trades should be executed based on current price"""
        try:
            open_trades = VirtualTrade.objects.filter(
                instrument_key=instrument_key,
                status='EXECUTED'
            )
            
            for trade in open_trades:
                should_close, exit_price, exit_reason = self.should_close_trade(trade, current_price)
                
                if should_close:
                    await self.execute_trade_closure(trade, exit_price, exit_reason)
                    
        except Exception as e:
            logger.error(f"Error checking trades for execution: {e}")
    
    def should_close_trade(self, trade, current_price):
        """Determine if a trade should be closed"""
        # Check target price
        if trade.target_price and current_price >= trade.target_price:
            return True, trade.target_price, 'Target hit'
        
        # Check stop loss
        if trade.stop_loss and current_price <= trade.stop_loss:
            return True, trade.stop_loss, 'Stop loss hit'
        
        # Check time limit (24 hours)
        time_open = timezone.now() - trade.entry_time
        if time_open.total_seconds() > 24 * 60 * 60:  # 24 hours
            return True, current_price, 'Time limit exceeded'
        
        return False, None, None
    
    async def execute_trade_closure(self, trade, exit_price, exit_reason):
        """Execute trade closure and update wallet"""
        try:
            # Update trade
            trade.exit_price = exit_price
            trade.exit_time = timezone.now()
            trade.status = 'CLOSED'
            trade.notes = f'Automatically closed: {exit_reason}'
            
            # Calculate P&L
            if trade.trade_type == 'BUY':
                pnl = (exit_price - trade.entry_price) * trade.quantity
            else:  # SELL
                pnl = (trade.entry_price - exit_price) * trade.quantity
            
            trade.pnl = pnl
            trade.pnl_percentage = (pnl / (trade.entry_price * trade.quantity)) * 100
            trade.save()
            
            # Update wallet
            wallet = trade.wallet
            wallet.total_pnl += pnl
            wallet.total_trades += 1
            
            if pnl > 0:
                wallet.winning_trades += 1
            else:
                wallet.losing_trades += 1
            
            wallet.total_invested -= (trade.entry_price * trade.quantity)
            wallet.balance += pnl
            wallet.save()
            
            # Broadcast trade update
            await self.broadcast_trade_update(trade, pnl, exit_reason)
            
            logger.info(f"Closed trade {trade.id} ({trade.tradingsymbol}) at {exit_price} - P&L: ₹{pnl:.2f}")
            
        except Exception as e:
            logger.error(f"Error executing trade closure: {e}")
    
    async def broadcast_price_update(self, instrument_key, current_price):
        """Broadcast price update to all connected clients"""
        try:
            message = {
                'type': 'price_update',
                'data': {
                    'instrument_key': instrument_key,
                    'current_price': float(current_price),
                    'timestamp': timezone.now().isoformat()
                }
            }
            
            await self.channel_layer.group_send(
                'price_updates',
                message
            )
            
        except Exception as e:
            logger.error(f"Error broadcasting price update: {e}")
    
    async def broadcast_trade_update(self, trade, pnl, exit_reason):
        """Broadcast trade update to user's trading room"""
        try:
            message = {
                'type': 'trade_update',
                'data': {
                    'trade_id': trade.id,
                    'tradingsymbol': trade.tradingsymbol,
                    'status': 'CLOSED',
                    'exit_price': float(trade.exit_price),
                    'pnl': float(pnl),
                    'pnl_percentage': float(trade.pnl_percentage),
                    'exit_reason': exit_reason,
                    'timestamp': timezone.now().isoformat()
                }
            }
            
            # Send to user's trading room
            room_name = f'trading_{trade.wallet.user.username}'
            await self.channel_layer.group_send(
                room_name,
                message
            )
            
        except Exception as e:
            logger.error(f"Error broadcasting trade update: {e}")
    
    async def listen_for_messages(self):
        """Listen for messages from Upstox WebSocket"""
        try:
            while self.running and self.websocket:
                try:
                    message = await self.websocket.recv()
                    data = json.loads(message)
                    
                    # Process price updates
                    await self.process_price_update(data)
                    
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket connection closed")
                    break
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON message received")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except Exception as e:
            logger.error(f"Error in message listener: {e}")
    
    async def run(self):
        """Main run loop with reconnection logic"""
        self.running = True
        
        while self.running:
            try:
                # Connect to WebSocket
                if await self.connect():
                    # Get instrument keys to subscribe to
                    instrument_keys = await self.get_instrument_keys()
                    
                    if instrument_keys:
                        await self.subscribe_to_instruments(instrument_keys)
                    
                    # Listen for messages
                    await self.listen_for_messages()
                
                # Reconnection logic
                if self.running:
                    logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
                    await asyncio.sleep(self.reconnect_delay)
                    self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
                    
            except Exception as e:
                logger.error(f"Error in main run loop: {e}")
                await asyncio.sleep(self.reconnect_delay)
    
    def stop(self):
        """Stop the WebSocket client"""
        self.running = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())


# Global WebSocket client instance
websocket_client = None

async def start_websocket_client():
    """Start the WebSocket client"""
    global websocket_client
    websocket_client = UpstoxWebSocketClient()
    await websocket_client.run()

def stop_websocket_client():
    """Stop the WebSocket client"""
    global websocket_client
    if websocket_client:
        websocket_client.stop() 