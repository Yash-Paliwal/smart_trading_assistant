#!/usr/bin/env python3
"""
Test script for virtual trading engine
Creates test alerts and runs the trading engine
"""

import os
import sys
import django
import time
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')
django.setup()

from trading_app.models import RadarAlert, Instrument
from virtual_trading_engine import VirtualTradingEngine

def create_test_alerts():
    """Create some test high-priority entry alerts"""
    
    # Get some instruments
    instruments = Instrument.objects.all()[:5]
    
    for i, instrument in enumerate(instruments):
        # Create a high-priority entry alert
        alert = RadarAlert.objects.create(
            instrument_key=instrument.instrument_key,
            source_strategy='RealTime_ORB',
            alert_details={
                'score': 85 + i,
                'reasons': [
                    f'Strong breakout detected for {instrument.tradingsymbol}',
                    'Volume confirmation above average',
                    'Technical indicators aligned'
                ]
            },
            indicators={
                'Close': 500 + (i * 50),
                'RSI': 65 + i,
                'MACD': 2.5 + i,
                'Volume': 1000000 + (i * 100000),
                'EMA20': 490 + (i * 50),
                'EMA50': 480 + (i * 50),
                'EMA200': 450 + (i * 50)
            },
            status='ACTIVE',
            priority='HIGH',
            alert_type='ENTRY'
        )
        
        print(f"✅ Created test alert for {instrument.tradingsymbol}")

def test_virtual_trading():
    """Test the virtual trading engine"""
    
    print("🧪 Testing Virtual Trading Engine...")
    
    # Create test alerts
    create_test_alerts()
    
    # Initialize trading engine
    engine = VirtualTradingEngine()
    
    print(f"💰 Initial wallet balance: ₹{engine.wallet.balance:,.2f}")
    print(f"📊 Available balance: ₹{engine.wallet.available_balance:,.2f}")
    
    # Process alerts once
    print("\n📈 Processing alerts...")
    engine.process_alerts()
    
    # Check results
    print("\n📋 Results:")
    print(f"   Total trades: {engine.wallet.total_trades}")
    print(f"   Total invested: ₹{engine.wallet.total_invested:,.2f}")
    print(f"   Available balance: ₹{engine.wallet.available_balance:,.2f}")
    
    # Show open positions
    positions = engine.wallet.positions.all()
    if positions:
        print(f"\n📊 Open Positions ({positions.count()}):")
        for position in positions:
            print(f"   {position.tradingsymbol}: {position.quantity} shares @ ₹{position.avg_entry_price:,.2f}")
            if position.unrealized_pnl:
                print(f"     Unrealized P&L: ₹{position.unrealized_pnl:,.2f} ({position.unrealized_pnl_percentage:.2f}%)")
    else:
        print("\n📊 No open positions")
    
    # Show recent trades
    trades = engine.wallet.trades.all().order_by('-entry_time')[:5]
    if trades:
        print(f"\n📋 Recent Trades ({trades.count()}):")
        for trade in trades:
            status_emoji = "✅" if trade.status == 'EXECUTED' else "🔒"
            print(f"   {status_emoji} {trade.tradingsymbol} {trade.trade_type}: {trade.quantity} shares @ ₹{trade.entry_price:,.2f}")
            if trade.target_price:
                print(f"     Target: ₹{trade.target_price:,.2f} | Stop Loss: ₹{trade.stop_loss:,.2f}")

if __name__ == "__main__":
    test_virtual_trading() 