#!/usr/bin/env python3
"""
Quick script to check database status and real data collection.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'django_api'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')

import django
django.setup()

from trading_app.models import HistoricalData
from datetime import datetime
from django.db import models

def check_database_status():
    """Check the current status of the database."""
    print("📊 Database Status Report")
    print("=" * 50)
    
    # Total records
    total_records = HistoricalData.objects.count()
    print(f"Total historical records: {total_records}")
    
    if total_records == 0:
        print("❌ No data found in database")
        return
    
    # Unique symbols (distinct)
    symbols = list(HistoricalData.objects.values_list('instrument_key', flat=True).distinct())
    print(f"Unique symbols: {len(symbols)}")
    
    # Data per symbol
    print("\n📈 Data per Symbol:")
    for symbol in symbols:
        count = HistoricalData.objects.filter(instrument_key=symbol).count()
        latest_date = HistoricalData.objects.filter(instrument_key=symbol).order_by('-date').first().date
        print(f"  {symbol}: {count} records (latest: {latest_date})")
    
    # Date range
    earliest = HistoricalData.objects.order_by('date').first().date
    latest = HistoricalData.objects.order_by('-date').first().date
    print(f"\n📅 Date Range: {earliest} to {latest}")
    
    # Data quality check
    print("\n🔍 Data Quality Check:")
    for symbol in symbols:
        data = HistoricalData.objects.filter(instrument_key=symbol).order_by('date')
        if data.exists():
            price_range = data.aggregate(
                min_price=models.Min('low_price'),
                max_price=models.Max('high_price')
            )
            print(f"  {symbol}: ₹{price_range['min_price']:.2f} - ₹{price_range['max_price']:.2f}")
    
    # Summary
    print(f"\n📋 Summary:")
    print(f"  • Total data points: {total_records:,}")
    print(f"  • Unique symbols: {len(symbols)}")
    print(f"  • Date coverage: {(latest - earliest).days} days")
    print(f"  • Average records per symbol: {total_records // len(symbols)}")
    
    print("\n✅ Database status check completed!")

if __name__ == "__main__":
    check_database_status() 