#!/usr/bin/env python3
"""
Test script for real data fetching and storage system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'django_api'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')

import django
django.setup()

from historical_data_manager import HistoricalDataManager, IntradayDataGenerator
from trading_app.models import HistoricalData
import pandas as pd
from datetime import datetime

def test_historical_data_manager():
    """Test the historical data manager functionality."""
    print("🧪 Testing Historical Data Manager...")
    
    # Initialize manager
    manager = HistoricalDataManager()
    
    # Test symbols (using real Upstox instrument keys)
    test_symbols = [
        "NSE_EQ|INE002A01018",  # Reliance
        "NSE_EQ|INE019A01038",  # HDFC Bank
    ]
    
    print(f"\n📊 Testing with symbols: {test_symbols}")
    
    # Test 1: Fetch and store data
    print("\n1️⃣ Testing data fetch and storage...")
    for symbol in test_symbols:
        try:
            data = manager.fetch_and_store_historical_data(symbol, days=30, force_refresh=False)
            if not data.empty:
                print(f"✅ Successfully fetched {len(data)} days for {symbol}")
            else:
                print(f"❌ No data received for {symbol}")
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
    
    # Test 2: Retrieve from database
    print("\n2️⃣ Testing database retrieval...")
    for symbol in test_symbols:
        try:
            data = manager.get_stored_historical_data(symbol, days=30)
            if data is not None and not data.empty:
                print(f"✅ Retrieved {len(data)} days for {symbol} from database")
                print(f"   Date range: {data.index.min()} to {data.index.max()}")
                print(f"   Latest close: {data['close'].iloc[-1]:.2f}")
            else:
                print(f"❌ No data found for {symbol}")
        except Exception as e:
            print(f"❌ Error retrieving {symbol}: {e}")
    
    # Test 3: Check Django model
    print("\n3️⃣ Testing Django model...")
    try:
        total_records = HistoricalData.objects.count()
        print(f"✅ Total historical records in database: {total_records}")
        
        for symbol in test_symbols:
            symbol_records = HistoricalData.objects.filter(instrument_key=symbol).count()
            print(f"   {symbol}: {symbol_records} records")
            
    except Exception as e:
        print(f"❌ Error checking Django model: {e}")
    
    # Test 4: Intraday data generation
    print("\n4️⃣ Testing intraday data generation...")
    intraday_gen = IntradayDataGenerator()
    
    try:
        intraday_data = intraday_gen.generate_intraday_data(
            "RELIANCE", 
            datetime.now(), 
            interval_minutes=5, 
            scenario='volatile'
        )
        
        print(f"✅ Generated {len(intraday_data)} intraday candles")
        print(f"   Time range: {intraday_data.index.min()} to {intraday_data.index.max()}")
        print(f"   Price range: {intraday_data['low'].min():.2f} - {intraday_data['high'].max():.2f}")
        
    except Exception as e:
        print(f"❌ Error generating intraday data: {e}")

def test_data_quality():
    """Test the quality of fetched data."""
    print("\n🔍 Testing Data Quality...")
    
    manager = HistoricalDataManager()
    symbol = "NSE_EQ|INE002A01018"  # Reliance
    
    try:
        data = manager.get_stored_historical_data(symbol, days=30)
        
        if data is not None and not data.empty:
            print(f"📊 Data quality check for {symbol}:")
            print(f"   Total records: {len(data)}")
            print(f"   Date range: {data.index.min()} to {data.index.max()}")
            print(f"   Missing values: {data.isnull().sum().sum()}")
            print(f"   Price range: {data['low'].min():.2f} - {data['high'].max():.2f}")
            print(f"   Volume range: {data['volume'].min():,.0f} - {data['volume'].max():,.0f}")
            
            # Check for data consistency
            price_issues = []
            if (data['high'] < data['low']).any():
                price_issues.append("High < Low")
            if (data['open'] > data['high']).any():
                price_issues.append("Open > High")
            if (data['close'] > data['high']).any():
                price_issues.append("Close > High")
            
            if price_issues:
                print(f"   ⚠️  Data issues found: {', '.join(price_issues)}")
            else:
                print(f"   ✅ Data quality looks good")
        else:
            print(f"❌ No data available for quality check")
            
    except Exception as e:
        print(f"❌ Error in data quality check: {e}")

if __name__ == "__main__":
    print("🚀 Starting Real Data System Tests...")
    print("=" * 50)
    
    # Run tests
    test_historical_data_manager()
    test_data_quality()
    
    print("\n" + "=" * 50)
    print("✅ Real Data System Tests Completed!")
    print("\n📝 Summary:")
    print("   - Historical data manager tested")
    print("   - Database storage and retrieval tested")
    print("   - Django model integration tested")
    print("   - Intraday data generation tested")
    print("   - Data quality validation tested") 