#!/usr/bin/env python3
"""
Test script to verify virtual trading API endpoints
"""

import os
import sys
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')
django.setup()

from django.contrib.auth.models import User
from trading_app.models import VirtualWallet, VirtualTrade, VirtualPosition

def test_virtual_trading_api():
    """Test the virtual trading API endpoints"""
    
    base_url = "http://localhost:8000/api"
    
    print("🧪 Testing Virtual Trading API...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/alerts/", timeout=5)
        print(f"✅ Server is running (Status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start Django server first.")
        return
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return
    
    # Test 2: Check virtual wallet
    try:
        response = requests.get(f"{base_url}/virtual-wallets/")
        print(f"✅ Virtual wallets endpoint: {response.status_code}")
        if response.status_code == 200:
            wallets = response.json()
            print(f"   Found {len(wallets)} wallets")
    except Exception as e:
        print(f"❌ Error testing virtual wallets: {e}")
    
    # Test 3: Check virtual trades
    try:
        response = requests.get(f"{base_url}/virtual-trades/")
        print(f"✅ Virtual trades endpoint: {response.status_code}")
        if response.status_code == 200:
            trades = response.json()
            print(f"   Found {len(trades)} trades")
    except Exception as e:
        print(f"❌ Error testing virtual trades: {e}")
    
    # Test 4: Check virtual positions
    try:
        response = requests.get(f"{base_url}/virtual-positions/")
        print(f"✅ Virtual positions endpoint: {response.status_code}")
        if response.status_code == 200:
            positions = response.json()
            print(f"   Found {len(positions)} positions")
    except Exception as e:
        print(f"❌ Error testing virtual positions: {e}")
    
    # Test 5: Check dashboard
    try:
        response = requests.get(f"{base_url}/virtual-trading-dashboard/")
        print(f"✅ Virtual trading dashboard: {response.status_code}")
        if response.status_code == 200:
            dashboard = response.json()
            print(f"   Wallet balance: ₹{dashboard.get('wallet', {}).get('balance', 0):,.2f}")
            print(f"   Open positions: {len(dashboard.get('open_positions', []))}")
            print(f"   Recent trades: {len(dashboard.get('recent_trades', []))}")
        elif response.status_code == 404:
            print("   No virtual wallet found (expected if not logged in)")
    except Exception as e:
        print(f"❌ Error testing dashboard: {e}")
    
    print("\n📊 Database Status:")
    
    # Check database directly
    users = User.objects.all()
    print(f"   Users: {users.count()}")
    
    wallets = VirtualWallet.objects.all()
    print(f"   Virtual Wallets: {wallets.count()}")
    
    trades = VirtualTrade.objects.all()
    print(f"   Virtual Trades: {trades.count()}")
    
    positions = VirtualPosition.objects.all()
    print(f"   Virtual Positions: {positions.count()}")
    
    if wallets.exists():
        wallet = wallets.first()
        print(f"\n💰 Wallet Details:")
        print(f"   Balance: ₹{wallet.balance:,.2f}")
        print(f"   Available: ₹{wallet.available_balance:,.2f}")
        print(f"   Total P&L: ₹{wallet.total_pnl:,.2f}")
        print(f"   Win Rate: {wallet.win_rate:.1f}%")
        print(f"   Total Trades: {wallet.total_trades}")

if __name__ == "__main__":
    test_virtual_trading_api() 