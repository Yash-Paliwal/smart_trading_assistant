# trading_app/management/commands/monitor_virtual_trades.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import requests
import time
from trading_app.models import VirtualTrade, VirtualWallet, UserProfile
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Monitor and automatically close virtual trades based on target/stoploss'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually closing trades',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Monitor trades for specific user only',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        user_id = options.get('user_id')
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting virtual trade monitoring... {"(DRY RUN)" if dry_run else ""}')
        )
        
        # Get open trades
        open_trades = VirtualTrade.objects.filter(status='EXECUTED')
        if user_id:
            open_trades = open_trades.filter(wallet__user_id=user_id)
        
        if not open_trades.exists():
            self.stdout.write(self.style.WARNING('No open virtual trades found.'))
            return
        
        self.stdout.write(f'Found {open_trades.count()} open trades to monitor.')
        
        closed_count = 0
        error_count = 0
        
        for trade in open_trades:
            try:
                result = self.process_trade(trade, dry_run)
                if result == 'closed':
                    closed_count += 1
                elif result == 'error':
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing trade {trade.id}: {str(e)}')
                )
                error_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Monitoring complete. Closed: {closed_count}, Errors: {error_count}'
            )
        )

    def process_trade(self, trade, dry_run=False):
        """Process a single trade - check if it should be closed"""
        
        # Get current market price
        current_price = self.get_current_price(trade.instrument_key)
        if current_price is None:
            return 'error'
        
        # Check if trade should be closed
        should_close, exit_price, exit_reason = self.should_close_trade(trade, current_price)
        
        if not should_close:
            return 'no_action'
        
        if dry_run:
            self.stdout.write(
                f'[DRY RUN] Would close trade {trade.id} ({trade.tradingsymbol}) '
                f'at {exit_price} - {exit_reason}'
            )
            return 'would_close'
        
        # Close the trade
        with transaction.atomic():
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
            
            # Recalculate total invested (remove this trade's investment)
            wallet.total_invested -= (trade.entry_price * trade.quantity)
            wallet.balance += pnl  # Add P&L to balance
            
            wallet.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Closed trade {trade.id} ({trade.tradingsymbol}) '
                    f'at {exit_price} - P&L: ₹{pnl:.2f} ({trade.pnl_percentage:.2f}%)'
                )
            )
            
        return 'closed'

    def should_close_trade(self, trade, current_price):
        """Determine if a trade should be closed based on current price"""
        
        # Check target price
        if trade.target_price and current_price >= trade.target_price:
            return True, trade.target_price, 'Target hit'
        
        # Check stop loss
        if trade.stop_loss and current_price <= trade.stop_loss:
            return True, trade.stop_loss, 'Stop loss hit'
        
        # Check if trade has been open for too long (optional - 24 hours)
        time_open = timezone.now() - trade.entry_time
        if time_open.total_seconds() > 24 * 60 * 60:  # 24 hours
            return True, current_price, 'Time limit exceeded (24h)'
        
        return False, None, None

    def get_current_price(self, instrument_key):
        """Get current market price for an instrument"""
        try:
            # Try to get price from Upstox API first
            price = self.get_upstox_price(instrument_key)
            if price is not None:
                return price
            
            # Fallback to mock price for testing
            return self.get_mock_price(instrument_key)
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Error fetching price for {instrument_key}: {str(e)}')
            )
            return None

    def get_upstox_price(self, instrument_key):
        """Get price from Upstox API"""
        try:
            # Get a user with Upstox access token
            user_profile = UserProfile.objects.filter(
                upstox_access_token__isnull=False
            ).first()
            
            if not user_profile:
                return None
            
            # Make API call to Upstox
            headers = {
                'Authorization': f'Bearer {user_profile.upstox_access_token}',
                'Accept': 'application/json'
            }
            
            # Get LTP (Last Traded Price)
            url = f'https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument_key}'
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and instrument_key in data['data']:
                    return Decimal(str(data['data'][instrument_key]['last_price']))
            
            return None
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Upstox API error: {str(e)}')
            )
            return None

    def get_mock_price(self, instrument_key):
        """Get mock price for testing (when Upstox API is not available)"""
        # Simple mock price generation based on instrument key
        # In production, this would be replaced with real market data
        
        # Extract some numeric value from instrument key for consistent mock pricing
        numeric_part = sum(ord(c) for c in instrument_key) % 1000
        
        # Generate a price between 100 and 2000
        base_price = 100 + (numeric_part % 1900)
        
        # Add some random variation (±5%)
        import random
        variation = random.uniform(-0.05, 0.05)
        price = base_price * (1 + variation)
        
        return Decimal(f'{price:.2f}') 