# trading_app/consumers.py

import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from decimal import Decimal
from .models import VirtualTrade, VirtualWallet, UserProfile
from django.contrib.auth.models import User
import logging
import re

logger = logging.getLogger(__name__)

class TradingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time trading updates"""
    
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        # Sanitize for Channels group name
        safe_user_id = re.sub(r'[^a-zA-Z0-9._-]', '_', self.user_id)
        self.room_group_name = f'trading_{safe_user_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial data
        await self.send_initial_data()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'get_wallet_data':
                await self.send_wallet_data()
            elif message_type == 'get_open_trades':
                await self.send_open_trades()
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def send_initial_data(self):
        """Send initial wallet and trade data"""
        await self.send_wallet_data()
        await self.send_open_trades()
    
    async def send_wallet_data(self):
        """Send wallet data to client"""
        wallet_data = await self.get_wallet_data()
        await self.send(text_data=json.dumps({
            'type': 'wallet_data',
            'data': wallet_data
        }))
    
    async def send_open_trades(self):
        """Send open trades data to client"""
        trades_data = await self.get_open_trades()
        await self.send(text_data=json.dumps({
            'type': 'open_trades',
            'data': trades_data
        }))
    
    async def trade_update(self, event):
        """Handle trade updates from price monitor"""
        await self.send(text_data=json.dumps({
            'type': 'trade_update',
            'data': event['data']
        }))
    
    async def price_update(self, event):
        """Handle price updates"""
        print(f"PriceConsumer: Sending price update to frontend: {event['data']}")  # DEBUG
        await self.send(text_data=json.dumps({
            'type': 'price_update',
            'data': event['data']
        }))
        print(f"PriceConsumer: Price update sent successfully")  # DEBUG
    
    @database_sync_to_async
    def get_wallet_data(self):
        """Get wallet data from database"""
        try:
            # Try to find user by email first, then by username
            try:
                # Use filter().first() to handle multiple users with same email
                user = User.objects.filter(email=self.user_id).first()
                if not user:
                    user = User.objects.get(username=self.user_id)
            except User.DoesNotExist:
                logger.error(f"User not found: {self.user_id}")
                return {'error': 'User not found'}
            
            try:
                wallet = VirtualWallet.objects.get(user=user)
            except VirtualWallet.DoesNotExist:
                logger.error(f"No VirtualWallet for user: {user}")
                return {'error': 'No VirtualWallet for user'}
            
            return {
                'balance': float(wallet.balance),
                'total_pnl': float(wallet.total_pnl),
                'total_trades': wallet.total_trades,
                'win_rate': float(wallet.win_rate),
                'total_value': float(wallet.total_value),
            }
        except Exception as e:
            logger.exception(f"Error in get_wallet_data: {e}")
            return {'error': str(e)}
    
    @database_sync_to_async
    def get_open_trades(self):
        """Get open trades from database"""
        try:
            # Try to find user by email first, then by username
            try:
                # Use filter().first() to handle multiple users with same email
                user = User.objects.filter(email=self.user_id).first()
                if not user:
                    user = User.objects.get(username=self.user_id)
            except User.DoesNotExist:
                logger.error(f"User not found: {self.user_id}")
                return []
            
            try:
                wallet = VirtualWallet.objects.get(user=user)
            except VirtualWallet.DoesNotExist:
                logger.error(f"No VirtualWallet for user: {user}")
                return []
            
            open_trades = VirtualTrade.objects.filter(
                wallet=wallet, 
                status='EXECUTED'
            )
            
            trades_data = []
            for trade in open_trades:
                trades_data.append({
                    'id': trade.id,
                    'instrument_key': trade.instrument_key,
                    'tradingsymbol': trade.tradingsymbol,
                    'trade_type': trade.trade_type,
                    'quantity': trade.quantity,
                    'entry_price': float(trade.entry_price),
                    'target_price': float(trade.target_price) if trade.target_price else None,
                    'stop_loss': float(trade.stop_loss) if trade.stop_loss else None,
                    'entry_time': trade.entry_time.isoformat(),
                })
            
            return trades_data
        except Exception as e:
            logger.exception(f"Error in get_open_trades: {e}")
            return []


class PriceConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time price updates"""
    
    async def connect(self):
        print("[PriceConsumer] connect() called")
        # Join the prices group to receive broadcast messages
        await self.channel_layer.group_add(
            "prices",
            self.channel_name
        )
        print(f"[PriceConsumer] Joined group 'prices' with channel {self.channel_name}")
        await self.accept()
        print("[PriceConsumer] WebSocket accepted")
    
    async def disconnect(self, close_code):
        print(f"[PriceConsumer] disconnect() called, code {close_code}")
        # Leave the prices group
        await self.channel_layer.group_discard(
            "prices",
            self.channel_name
        )
        print(f"[PriceConsumer] Left group 'prices' with channel {self.channel_name}")
    
    async def receive(self, text_data):
        """Handle incoming messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def price_update(self, event):
        print(f"[PriceConsumer] price_update() called with event: {event}")
        """Handle price updates from Upstox WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'price_update',
            'data': event['data']
        }))
        print(f"[PriceConsumer] Sent price update to frontend: {event['data']}")
    
    async def trade_executed(self, event):
        """Handle trade execution notifications"""
        await self.send(text_data=json.dumps({
            'type': 'trade_executed',
            'data': event['data']
        })) 