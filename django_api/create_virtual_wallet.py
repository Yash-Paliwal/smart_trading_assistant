#!/usr/bin/env python3
"""
Script to create a virtual wallet for the current user
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')
django.setup()

from django.contrib.auth.models import User
from trading_app.models import VirtualWallet
from decimal import Decimal

def create_virtual_wallet(username=None):
    """Create a virtual wallet for the specified user or the first user"""
    
    if username:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            print(f"❌ User '{username}' not found!")
            return False
    else:
        # Get the first user (for testing)
        users = User.objects.all()
        if not users.exists():
            print("❌ No users found in the database!")
            print("💡 Please create a user first or log in through the frontend.")
            return False
        user = users.first()
    
    # Check if wallet already exists
    wallet, created = VirtualWallet.objects.get_or_create(
        user=user,
        defaults={
            'balance': Decimal('200000.00'),  # 2 lakh rupees
            'total_invested': Decimal('0.00'),
            'total_pnl': Decimal('0.00'),
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0
        }
    )
    
    if created:
        print(f"✅ Created virtual wallet for {user.username}")
        print(f"💰 Initial balance: ₹{wallet.balance:,.2f}")
        print(f"📊 Available balance: ₹{wallet.available_balance:,.2f}")
    else:
        print(f"ℹ️  Virtual wallet already exists for {user.username}")
        print(f"💰 Current balance: ₹{wallet.balance:,.2f}")
        print(f"📊 Available balance: ₹{wallet.available_balance:,.2f}")
        print(f"📈 Total P&L: ₹{wallet.total_pnl:,.2f}")
        print(f"🎯 Win rate: {wallet.win_rate:.1f}%")
        print(f"📋 Total trades: {wallet.total_trades}")
    
    return True

if __name__ == "__main__":
    # You can specify a username as command line argument
    username = sys.argv[1] if len(sys.argv) > 1 else None
    create_virtual_wallet(username) 