#!/usr/bin/env python3
"""
Simulate virtual trades for testing the dashboard
"""

import os
import sys
import django
import random
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')
django.setup()

from django.contrib.auth.models import User
from trading_app.models import VirtualWallet, VirtualTrade, VirtualPosition, Instrument, RadarAlert
from django.utils import timezone

def simulate_trades():
    """Simulate some virtual trades for testing"""
    
    # Get the first user and their wallet
    user = User.objects.first()
    if not user:
        print("❌ No users found!")
        return
    
    wallet = VirtualWallet.objects.get(user=user)
    print(f"💰 Simulating trades for {user.username} (Balance: ₹{wallet.balance:,.2f})")
    
    # Get some instruments
    instruments = list(Instrument.objects.all()[:20])  # Get more instruments to avoid duplicates
    
    # Clear existing trades and positions for clean simulation
    VirtualTrade.objects.filter(wallet=wallet).delete()
    VirtualPosition.objects.filter(wallet=wallet).delete()
    
    # Reset wallet
    wallet.balance = Decimal('200000.00')
    wallet.total_invested = Decimal('0.00')
    wallet.total_pnl = Decimal('0.00')
    wallet.total_trades = 0
    wallet.winning_trades = 0
    wallet.losing_trades = 0
    wallet.save()
    
    print("🔄 Starting trade simulation...")
    
    # Simulate 5 trades with unique instruments
    used_instruments = set()
    
    for i in range(5):
        # Get a unique instrument
        available_instruments = [inst for inst in instruments if inst.instrument_key not in used_instruments]
        if not available_instruments:
            print("⚠️  No more unique instruments available")
            break
            
        instrument = random.choice(available_instruments)
        used_instruments.add(instrument.instrument_key)
        
        # Create a test alert
        alert = RadarAlert.objects.create(
            instrument_key=instrument.instrument_key,
            source_strategy='RealTime_ORB',
            alert_details={'score': 85 + i},
            indicators={'Close': 500 + (i * 50)},
            status='ACTIVE',
            priority='HIGH',
            alert_type='ENTRY'
        )
        
        # Simulate trade
        entry_price = Decimal(str(500 + (i * 50)))
        quantity = random.randint(10, 50)
        trade_type = 'BUY'
        
        # Calculate target and stop loss
        target_price = entry_price * Decimal('1.06')  # 6% profit
        stop_loss = entry_price * Decimal('0.98')     # 2% loss
        
        # Create trade
        trade = VirtualTrade.objects.create(
            wallet=wallet,
            alert=alert,
            instrument_key=instrument.instrument_key,
            tradingsymbol=instrument.tradingsymbol,
            trade_type=trade_type,
            quantity=quantity,
            entry_price=entry_price,
            target_price=target_price,
            stop_loss=stop_loss,
            status='EXECUTED',
            risk_amount=entry_price * quantity * Decimal('0.02'),
            risk_percentage=Decimal('2.00')
        )
        
        # Update wallet
        trade_value = entry_price * quantity
        wallet.total_invested += trade_value
        wallet.total_trades += 1
        wallet.save()
        
        # Create position
        position = VirtualPosition.objects.create(
            wallet=wallet,
            instrument_key=instrument.instrument_key,
            tradingsymbol=instrument.tradingsymbol,
            quantity=quantity,
            avg_entry_price=entry_price,
            current_price=entry_price
        )
        
        print(f"✅ Created trade {i+1}: {instrument.tradingsymbol} {trade_type} {quantity} shares @ ₹{entry_price:,.2f}")
    
    # Simulate some closed trades with P&L
    closed_trades = list(VirtualTrade.objects.filter(wallet=wallet))[:3]
    
    for i, trade in enumerate(closed_trades):
        # Simulate exit price (random profit/loss)
        if random.choice([True, False]):  # 50% chance of profit
            exit_price = trade.entry_price * Decimal('1.05')  # 5% profit
        else:
            exit_price = trade.entry_price * Decimal('0.97')  # 3% loss
        
        # Calculate P&L
        pnl = (exit_price - trade.entry_price) * trade.quantity
        
        # Update trade
        trade.exit_price = exit_price
        trade.pnl = pnl
        trade.status = 'CLOSED'
        trade.exit_time = timezone.now()
        trade.notes = f"Simulated close: {'PROFIT' if pnl > 0 else 'LOSS'}"
        if trade.entry_price > 0:
            trade.pnl_percentage = (pnl / (trade.entry_price * trade.quantity)) * 100
        trade.save()
        
        # Update wallet
        trade_value = trade.entry_price * trade.quantity
        wallet.total_invested -= trade_value
        wallet.total_pnl += pnl
        wallet.balance += pnl
        
        if pnl > 0:
            wallet.winning_trades += 1
        else:
            wallet.losing_trades += 1
        
        wallet.save()
        
        # Delete position
        VirtualPosition.objects.filter(
            wallet=wallet,
            instrument_key=trade.instrument_key
        ).delete()
        
        print(f"🔒 Closed trade {i+1}: {trade.tradingsymbol} P&L ₹{pnl:,.2f} ({trade.pnl_percentage:.2f}%)")
    
    # Update remaining positions with current prices
    positions = VirtualPosition.objects.filter(wallet=wallet)
    for position in positions:
        # Simulate current price movement
        price_change = random.uniform(-0.03, 0.05)  # -3% to +5%
        current_price = position.avg_entry_price * Decimal(str(1 + price_change))
        position.update_current_price(current_price)
        
        print(f"📊 Updated position: {position.tradingsymbol} @ ₹{current_price:,.2f} (P&L: ₹{position.unrealized_pnl:,.2f})")
    
    print(f"\n🎯 Simulation Complete!")
    print(f"💰 Final Balance: ₹{wallet.balance:,.2f}")
    print(f"📈 Total P&L: ₹{wallet.total_pnl:,.2f}")
    print(f"🎯 Win Rate: {wallet.win_rate:.1f}%")
    print(f"📋 Total Trades: {wallet.total_trades}")
    print(f"📊 Open Positions: {positions.count()}")

if __name__ == "__main__":
    simulate_trades() 