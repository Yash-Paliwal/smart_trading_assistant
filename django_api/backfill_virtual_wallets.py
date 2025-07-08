#!/usr/bin/env python3
"""
Backfill virtual wallets for all existing users who don't have one
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')
django.setup()

from django.contrib.auth.models import User
from trading_app.models import VirtualWallet

def backfill_wallets():
    users = User.objects.all()
    created_count = 0
    for user in users:
        wallet, created = VirtualWallet.objects.get_or_create(
            user=user,
            defaults={
                'balance': Decimal('200000.00'),
                'total_invested': Decimal('0.00'),
                'total_pnl': Decimal('0.00'),
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0
            }
        )
        if created:
            print(f"✅ Created wallet for {user.username}")
            created_count += 1
        else:
            print(f"ℹ️  Wallet already exists for {user.username}")
    print(f"\nDone. {created_count} wallets created.")

if __name__ == "__main__":
    backfill_wallets() 