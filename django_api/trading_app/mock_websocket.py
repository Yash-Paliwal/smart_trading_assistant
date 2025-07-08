# trading_app/mock_websocket.py

import asyncio
import json
import logging
import random
from decimal import Decimal
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async
from .models import VirtualTrade, VirtualWallet, UserProfile
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class MockWebSocketClient:
    """Mock WebSocket client for testing with fake price data"""
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
        self.running = False
        self.price_interval = 5  # Update prices every 5 seconds
        
    @sync_to_async
    def get_instrument_keys_sync(self):
        """Get all instrument keys from open trades (sync version)"""
        try:
            open_trades = VirtualTrade.objects.filter(status='EXECUTED')
            instrument_keys = list(set(trade.instrument_key for trade in open_trades))
            
            # If no real trades, create some mock instruments for testing
            if not instrument_keys:
                instrument_keys = ['NSE_EQ|RELIANCE', 'NSE_EQ|TCS', 'NSE_EQ|INFY', 'NSE_EQ|HDFC']
            
            return instrument_keys
        except Exception as e:
            logger.error(f"Failed to get instrument keys: {e}")
            return ['NSE_EQ|RELIANCE', 'NSE_EQ|TCS', 'NSE_EQ|INFY']
    
    async def get_instrument_keys(self):
        """Get all instrument keys from open trades"""
        return await self.get_instrument_keys_sync()
    
    def generate_mock_price(self, base_price=1000):
        """Generate a realistic mock price"""
        # Add some random movement to the price
        change_percent = random.uniform(-2, 2)  # -2% to +2% change
        new_price = base_price * (1 + change_percent / 100)
        return round(new_price, 2)
    
    async def broadcast_mock_prices(self, instrument_keys):
        """Broadcast mock price updates"""
        try:
            for instrument_key in instrument_keys:
                # Generate a base price based on instrument
                if 'RELIANCE' in instrument_key:
                    base_price = 2500
                elif 'TCS' in instrument_key:
                    base_price = 3500
                elif 'INFY' in instrument_key:
                    base_price = 1500
                elif 'HDFC' in instrument_key:
                    base_price = 1800
                else:
                    base_price = 1000
                
                current_price = self.generate_mock_price(base_price)
                
                # Broadcast price update
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
                
                # Check trades for execution
                await self.check_trades_for_execution(instrument_key, current_price)
                
        except Exception as e:
            logger.error(f"Error broadcasting mock prices: {e}")
    
    @sync_to_async
    def get_open_trades_sync(self, instrument_key):
        """Get open trades for an instrument (sync version)"""
        try:
            return list(VirtualTrade.objects.filter(
                instrument_key=instrument_key,
                status='EXECUTED'
            ))
        except Exception as e:
            logger.error(f"Error getting open trades: {e}")
            return []
    
    async def check_trades_for_execution(self, instrument_key, current_price):
        """Check if any trades should be executed based on current price"""
        try:
            open_trades = await self.get_open_trades_sync(instrument_key)
            
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
    
    @sync_to_async
    def execute_trade_closure_sync(self, trade, exit_price, exit_reason):
        """Execute trade closure and update wallet (sync version)"""
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
            
            logger.info(f"Closed trade {trade.id} ({trade.tradingsymbol}) at {exit_price} - P&L: ₹{pnl:.2f}")
            
            return trade, pnl, exit_reason
            
        except Exception as e:
            logger.error(f"Error executing trade closure: {e}")
            return None, 0, exit_reason
    
    async def execute_trade_closure(self, trade, exit_price, exit_reason):
        """Execute trade closure and update wallet"""
        result = await self.execute_trade_closure_sync(trade, exit_price, exit_reason)
        if result[0]:  # If trade was successfully closed
            trade, pnl, exit_reason = result
            await self.broadcast_trade_update(trade, pnl, exit_reason)
    
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
    
    async def run(self):
        """Main run loop for mock price updates"""
        self.running = True
        logger.info("Starting Mock WebSocket Client")
        
        while self.running:
            try:
                # Get instrument keys
                instrument_keys = await self.get_instrument_keys()
                
                if instrument_keys:
                    # Broadcast mock prices
                    await self.broadcast_mock_prices(instrument_keys)
                    logger.info(f"Broadcasted mock prices for {len(instrument_keys)} instruments")
                
                # Wait before next update
                await asyncio.sleep(self.price_interval)
                
            except Exception as e:
                logger.error(f"Error in mock WebSocket loop: {e}")
                await asyncio.sleep(self.price_interval)
    
    def stop(self):
        """Stop the mock WebSocket client"""
        self.running = False
        logger.info("Mock WebSocket Client stopped")


# Global mock WebSocket client instance
mock_websocket_client = None

async def start_mock_websocket_client():
    """Start the mock WebSocket client"""
    global mock_websocket_client
    mock_websocket_client = MockWebSocketClient()
    await mock_websocket_client.run()

def stop_mock_websocket_client():
    """Stop the mock WebSocket client"""
    global mock_websocket_client
    if mock_websocket_client:
        mock_websocket_client.stop() 