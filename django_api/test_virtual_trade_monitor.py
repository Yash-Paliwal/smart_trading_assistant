#!/usr/bin/env python3
"""
Test Virtual Trade Monitor - Demonstrates the automatic trade monitoring system
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')
django.setup()

from trading_app.models import VirtualTrade, VirtualWallet, User, Instrument, RadarAlert
from django.utils import timezone

def create_test_trades():
    """Create test virtual trades for demonstration"""
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
    )
    
    # Get or create virtual wallet
    wallet, created = VirtualWallet.objects.get_or_create(
        user=user,
        defaults={'balance': Decimal('200000.00')}
    )
    
    # Get some instruments for testing
    instruments = Instrument.objects.all()[:3]
    if not instruments.exists():
        print("No instruments found. Creating test instruments...")
        instruments = []
        for i in range(3):
            instrument = Instrument.objects.create(
                instrument_key=f'TEST_INSTRUMENT_{i}',
                tradingsymbol=f'TEST{i}',
                name=f'Test Instrument {i}',
                exchange='NSE'
            )
            instruments.append(instrument)
    
    # Create test alerts first
    test_alerts = []
    for i, instrument in enumerate(instruments):
        alert = RadarAlert.objects.create(
            instrument_key=instrument.instrument_key,
            source_strategy='Bullish_Scan',
            alert_details={'test': True},
            status='ACTIVE'
        )
        test_alerts.append(alert)
    
    # Create test trades with different scenarios
    test_trades = [
        {
            'instrument_key': instruments[0].instrument_key,
            'tradingsymbol': instruments[0].tradingsymbol,
            'alert': test_alerts[0],
            'trade_type': 'BUY',
            'quantity': 100,
            'entry_price': Decimal('150.00'),
            'target_price': Decimal('160.00'),  # 6.67% target
            'stop_loss': Decimal('140.00'),     # 6.67% stop loss
            'notes': 'Test BUY trade with target and stop loss'
        },
        {
            'instrument_key': instruments[1].instrument_key,
            'tradingsymbol': instruments[1].tradingsymbol,
            'alert': test_alerts[1],
            'trade_type': 'SELL',
            'quantity': 50,
            'entry_price': Decimal('200.00'),
            'target_price': Decimal('190.00'),  # 5% target
            'stop_loss': Decimal('210.00'),     # 5% stop loss
            'notes': 'Test SELL trade with target and stop loss'
        },
        {
            'instrument_key': instruments[2].instrument_key,
            'tradingsymbol': instruments[2].tradingsymbol,
            'alert': test_alerts[2],
            'trade_type': 'BUY',
            'quantity': 75,
            'entry_price': Decimal('100.00'),
            'target_price': None,  # No target - will close after 24 hours
            'stop_loss': Decimal('90.00'),      # 10% stop loss
            'notes': 'Test BUY trade with only stop loss'
        }
    ]
    
    created_trades = []
    for trade_data in test_trades:
        trade = VirtualTrade.objects.create(
            wallet=wallet,
            alert=trade_data['alert'],
            instrument_key=trade_data['instrument_key'],
            tradingsymbol=trade_data['tradingsymbol'],
            trade_type=trade_data['trade_type'],
            quantity=trade_data['quantity'],
            entry_price=trade_data['entry_price'],
            target_price=trade_data['target_price'],
            stop_loss=trade_data['stop_loss'],
            status='EXECUTED',
            entry_time=timezone.now(),
            notes=trade_data['notes']
        )
        created_trades.append(trade)
        print(f"Created test trade: {trade.tradingsymbol} {trade.trade_type} at {trade.entry_price}")
    
    return created_trades

def run_monitor_test():
    """Run the monitor command and show results"""
    
    print("\n" + "="*60)
    print("VIRTUAL TRADE MONITOR TEST")
    print("="*60)
    
    # Create test trades
    print("\n1. Creating test trades...")
    trades = create_test_trades()
    
    # Show initial state
    print(f"\n2. Initial state - {len(trades)} open trades:")
    for trade in trades:
        print(f"   {trade.tradingsymbol}: {trade.trade_type} {trade.quantity} @ {trade.entry_price}")
        if trade.target_price:
            print(f"     Target: {trade.target_price}, Stop Loss: {trade.stop_loss}")
    
    # Run monitor in dry-run mode first
    print("\n3. Running monitor in DRY-RUN mode...")
    os.system('python manage.py monitor_virtual_trades --dry-run')
    
    # Run monitor for real
    print("\n4. Running monitor for real...")
    os.system('python manage.py monitor_virtual_trades')
    
    # Show final state
    print("\n5. Final state:")
    for trade in VirtualTrade.objects.filter(wallet__user__username='test_user').order_by('-entry_time'):
        status_emoji = "✅" if trade.status == 'CLOSED' else "⏳"
        pnl_info = f"P&L: ₹{trade.pnl:.2f}" if trade.pnl is not None else ""
        print(f"   {status_emoji} {trade.tradingsymbol}: {trade.status} {pnl_info}")
    
    # Show wallet summary
    wallet = VirtualWallet.objects.get(user__username='test_user')
    print(f"\n6. Wallet Summary:")
    print(f"   Balance: ₹{wallet.balance:.2f}")
    print(f"   Total P&L: ₹{wallet.total_pnl:.2f}")
    print(f"   Total Trades: {wallet.total_trades}")
    print(f"   Win Rate: {wallet.win_rate:.1f}%")

def cleanup_test_data():
    """Clean up test data"""
    try:
        User.objects.filter(username='test_user').delete()
        print("\nTest data cleaned up.")
    except Exception as e:
        print(f"Error cleaning up: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--cleanup':
        cleanup_test_data()
    else:
        run_monitor_test() 