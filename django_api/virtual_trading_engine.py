#!/usr/bin/env python3
"""
Virtual Trading Engine
Automatically takes trades based on alerts and manages virtual portfolio
"""

import os
import sys
import django
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import time
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')
django.setup()

from django.contrib.auth.models import User
from trading_app.models import (
    VirtualWallet, VirtualTrade, VirtualPosition, 
    RadarAlert, Instrument
)
from django.utils import timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def notify_virtual_trade_update(user, trade, wallet=None):
    """Send WebSocket events for trade update, wallet, and open trades."""
    channel_layer = get_channel_layer()
    group_name = f"trading_{user.username}"
    from trading_app.serializers import VirtualTradeSerializer
    trade_data = VirtualTradeSerializer(trade).data
    # Send trade update
    async_to_sync(channel_layer.group_send)(
        group_name,
        {"type": "trade_update", "data": trade_data}
    )
    # Optionally send wallet data
    if wallet:
        wallet_data = {
            'balance': float(wallet.balance),
            'total_pnl': float(wallet.total_pnl),
            'total_trades': wallet.total_trades,
            'win_rate': float(wallet.win_rate),
            'total_value': float(wallet.total_value),
        }
        async_to_sync(channel_layer.group_send)(
            group_name,
            {"type": "wallet_data", "data": wallet_data}
        )
    # Send open trades
    open_trades = VirtualTrade.objects.filter(wallet=wallet, status='EXECUTED')
    from trading_app.serializers import VirtualTradeSerializer
    open_trades_data = [VirtualTradeSerializer(t).data for t in open_trades]
    async_to_sync(channel_layer.group_send)(
        group_name,
        {"type": "open_trades", "data": open_trades_data}
    )

class VirtualTradingEngine:
    """
    Virtual trading engine that automatically executes trades based on alerts
    """
    
    def __init__(self, user=None):
        self.user = user or User.objects.first()
        self.wallet = VirtualWallet.objects.get(user=self.user)
        self.max_position_size = Decimal('0.10')  # 10% of wallet per trade
        self.risk_per_trade = Decimal('0.02')     # 2% risk per trade
        self.max_open_positions = 5               # Maximum 5 open positions
        
    def get_current_price(self, instrument_key):
        """
        Get current price for an instrument (simulated for now)
        In real implementation, this would fetch from Upstox API
        """
        try:
            # For now, use the last close price from indicators
            alert = RadarAlert.objects.filter(
                instrument_key=instrument_key,
                status='ACTIVE'
            ).first()
            
            if alert and alert.indicators:
                return Decimal(str(alert.indicators.get('Close', 0)))
            
            # Fallback: get from instrument data
            instrument = Instrument.objects.filter(instrument_key=instrument_key).first()
            if instrument:
                # Simulate a price around 100-1000 range
                import random
                return Decimal(str(random.randint(100, 1000)))
                
        except Exception as e:
            logger.error(f"Error getting current price for {instrument_key}: {e}")
        
        return Decimal('0')
    
    def calculate_position_size(self, entry_price, stop_loss=None):
        """
        Calculate position size based on risk management rules
        """
        if not entry_price or entry_price <= 0:
            return 0
            
        # Calculate risk amount (2% of wallet)
        risk_amount = self.wallet.balance * self.risk_per_trade
        
        # Calculate position size based on risk
        if stop_loss and stop_loss > 0:
            risk_per_share = abs(entry_price - stop_loss)
            if risk_per_share > 0:
                position_size = int(risk_amount / risk_per_share)
            else:
                position_size = 0
        else:
            # If no stop loss, use 2% of wallet
            position_size = int((self.wallet.balance * self.max_position_size) / entry_price)
        
        # Ensure minimum position size
        if position_size < 1:
            position_size = 1
            
        # Ensure we don't exceed available balance
        max_shares = int(self.wallet.available_balance / entry_price)
        position_size = min(position_size, max_shares)
        
        return position_size
    
    def should_take_trade(self, alert):
        """
        Determine if we should take a trade based on the alert
        """
        # Don't trade if we have too many open positions
        open_positions = VirtualPosition.objects.filter(wallet=self.wallet).count()
        if open_positions >= self.max_open_positions:
            logger.info(f"Max open positions reached ({open_positions}). Skipping trade.")
            return False
        
        # Don't trade if we don't have enough balance
        if self.wallet.available_balance < 10000:  # Minimum 10k balance
            logger.info(f"Insufficient balance (₹{self.wallet.available_balance:,.2f}). Skipping trade.")
            return False
        
        # Only trade on high-priority alerts
        if alert.priority not in ['HIGH', 'CRITICAL']:
            logger.info(f"Alert priority too low ({alert.priority}). Skipping trade.")
            return False
        
        # Don't trade if we already have a position in this stock
        existing_position = VirtualPosition.objects.filter(
            wallet=self.wallet,
            instrument_key=alert.instrument_key
        ).first()
        
        if existing_position:
            logger.info(f"Already have position in {alert.instrument_key}. Skipping trade.")
            return False
        
        return True
    
    def execute_trade(self, alert):
        """
        Execute a virtual trade based on the alert
        """
        try:
            if not self.should_take_trade(alert):
                return None
            
            # Get current price
            current_price = self.get_current_price(alert.instrument_key)
            if current_price <= 0:
                logger.warning(f"Invalid price for {alert.instrument_key}: {current_price}")
                return None
            
            # Get instrument details
            instrument = Instrument.objects.filter(instrument_key=alert.instrument_key).first()
            if not instrument:
                logger.warning(f"Instrument not found: {alert.instrument_key}")
                return None
            
            # Calculate entry price (current market price)
            entry_price = current_price
            
            # Calculate stop loss (2% below entry for buy, 2% above for sell)
            if alert.source_strategy in ['RealTime_ORB', 'Bullish_Scan']:
                trade_type = 'BUY'
                stop_loss = entry_price * Decimal('0.98')  # 2% below
                target_price = entry_price * Decimal('1.06')  # 6% above
            else:
                trade_type = 'SELL'
                stop_loss = entry_price * Decimal('1.02')  # 2% above
                target_price = entry_price * Decimal('0.94')  # 6% below
            
            # Calculate position size
            quantity = self.calculate_position_size(entry_price, stop_loss)
            if quantity <= 0:
                logger.warning(f"Invalid position size: {quantity}")
                return None
            
            # Calculate trade value
            trade_value = entry_price * quantity
            
            # Check if we have enough balance
            if trade_value > self.wallet.available_balance:
                logger.warning(f"Insufficient balance for trade: ₹{trade_value:,.2f} > ₹{self.wallet.available_balance:,.2f}")
                return None
            
            # Create the virtual trade
            virtual_trade = VirtualTrade.objects.create(
                wallet=self.wallet,
                alert=alert,
                instrument_key=alert.instrument_key,
                tradingsymbol=instrument.tradingsymbol,
                trade_type=trade_type,
                quantity=quantity,
                entry_price=entry_price,
                target_price=target_price,
                stop_loss=stop_loss,
                status='EXECUTED',
                risk_amount=trade_value * self.risk_per_trade,
                risk_percentage=self.risk_per_trade * 100
            )
            
            # Update wallet
            self.wallet.total_invested += trade_value
            self.wallet.total_trades += 1
            self.wallet.save()
            
            # Create or update position
            position, created = VirtualPosition.objects.get_or_create(
                wallet=self.wallet,
                instrument_key=alert.instrument_key,
                defaults={
                    'tradingsymbol': instrument.tradingsymbol,
                    'quantity': quantity,
                    'avg_entry_price': entry_price,
                    'current_price': entry_price
                }
            )
            
            if not created:
                # Update existing position
                total_quantity = position.quantity + quantity
                total_value = (position.avg_entry_price * position.quantity) + (entry_price * quantity)
                position.avg_entry_price = total_value / total_quantity
                position.quantity = total_quantity
                position.current_price = entry_price
                position.save()
            
            logger.info(f"✅ Executed {trade_type} trade: {instrument.tradingsymbol}")
            logger.info(f"   Quantity: {quantity} shares @ ₹{entry_price:,.2f}")
            logger.info(f"   Target: ₹{target_price:,.2f} | Stop Loss: ₹{stop_loss:,.2f}")
            logger.info(f"   Trade Value: ₹{trade_value:,.2f}")
            
            # --- WebSocket notification ---
            notify_virtual_trade_update(self.user, virtual_trade, self.wallet)
            
            return virtual_trade
            
        except Exception as e:
            logger.error(f"Error executing trade for {alert.instrument_key}: {e}")
            return None
    
    def update_positions(self):
        """
        Update current prices and P&L for all open positions
        """
        positions = VirtualPosition.objects.filter(wallet=self.wallet)
        
        for position in positions:
            try:
                current_price = self.get_current_price(position.instrument_key)
                if current_price > 0:
                    position.update_current_price(current_price)
                    
                    # Check for exit conditions
                    self.check_exit_conditions(position)
                    
            except Exception as e:
                logger.error(f"Error updating position {position.instrument_key}: {e}")
    
    def check_exit_conditions(self, position):
        """
        Check if position should be closed based on target/stop loss
        """
        try:
            # Get the most recent trade for this position
            trade = VirtualTrade.objects.filter(
                wallet=self.wallet,
                instrument_key=position.instrument_key,
                status='EXECUTED'
            ).order_by('-entry_time').first()
            
            if not trade:
                return
            
            current_price = position.current_price
            
            # Check target hit
            if trade.trade_type == 'BUY' and current_price >= trade.target_price:
                self.close_position(position, trade, current_price, 'TARGET_HIT')
            elif trade.trade_type == 'SELL' and current_price <= trade.target_price:
                self.close_position(position, trade, current_price, 'TARGET_HIT')
            
            # Check stop loss hit
            elif trade.trade_type == 'BUY' and current_price <= trade.stop_loss:
                self.close_position(position, trade, current_price, 'STOP_LOSS')
            elif trade.trade_type == 'SELL' and current_price >= trade.stop_loss:
                self.close_position(position, trade, current_price, 'STOP_LOSS')
                
        except Exception as e:
            logger.error(f"Error checking exit conditions for {position.instrument_key}: {e}")
    
    def close_position(self, position, trade, exit_price, reason):
        """
        Close a position and update wallet
        """
        try:
            # Calculate P&L
            if trade.trade_type == 'BUY':
                pnl = (exit_price - trade.entry_price) * trade.quantity
            else:
                pnl = (trade.entry_price - exit_price) * trade.quantity
            
            # Update trade
            trade.exit_price = exit_price
            trade.pnl = pnl
            trade.status = 'CLOSED'
            trade.exit_time = timezone.now()
            trade.notes = f"Closed: {reason}"
            if trade.entry_price > 0:
                trade.pnl_percentage = (pnl / (trade.entry_price * trade.quantity)) * 100
            trade.save()
            
            # Update wallet
            trade_value = trade.entry_price * trade.quantity
            self.wallet.total_invested -= trade_value
            self.wallet.total_pnl += pnl
            self.wallet.balance += pnl
            
            if pnl > 0:
                self.wallet.winning_trades += 1
            else:
                self.wallet.losing_trades += 1
            
            self.wallet.save()
            
            # Delete position
            position.delete()
            
            logger.info(f"🔒 Closed position: {position.tradingsymbol}")
            logger.info(f"   P&L: ₹{pnl:,.2f} ({trade.pnl_percentage:.2f}%)")
            logger.info(f"   Reason: {reason}")
            
            # --- WebSocket notification ---
            notify_virtual_trade_update(self.user, trade, self.wallet)
            
        except Exception as e:
            logger.error(f"Error closing position {position.instrument_key}: {e}")
    
    def process_alerts(self):
        """
        Process active alerts and take trades
        """
        active_alerts = RadarAlert.objects.filter(
            status='ACTIVE',
            priority__in=['HIGH', 'CRITICAL'],
            alert_type='ENTRY'  # Only trade on entry alerts
        ).order_by('-timestamp')
        
        logger.info(f"Processing {active_alerts.count()} active alerts...")
        
        for alert in active_alerts:
            # Check if we already have a trade for this alert
            existing_trade = VirtualTrade.objects.filter(alert=alert).first()
            if existing_trade:
                continue
            
            # Execute trade
            trade = self.execute_trade(alert)
            if trade:
                time.sleep(1)  # Small delay between trades
    
    def run(self):
        """
        Main run loop for the virtual trading engine
        """
        logger.info("🚀 Starting Virtual Trading Engine...")
        logger.info(f"💰 Wallet Balance: ₹{self.wallet.balance:,.2f}")
        logger.info(f"📊 Available Balance: ₹{self.wallet.available_balance:,.2f}")
        
        while True:
            try:
                # Process new alerts
                self.process_alerts()
                
                # Update existing positions
                self.update_positions()
                
                # Log wallet status
                logger.info(f"📈 Wallet Status: ₹{self.wallet.balance:,.2f} | P&L: ₹{self.wallet.total_pnl:,.2f} | Win Rate: {self.wallet.win_rate:.1f}%")
                
                # Wait before next iteration
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                logger.info("🛑 Virtual Trading Engine stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in trading engine: {e}")
                time.sleep(60)  # Wait longer on error

if __name__ == "__main__":
    engine = VirtualTradingEngine()
    engine.run() 