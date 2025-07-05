# historical_data_manager.py

import os
import sys
import django
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json

# Django setup
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'django_api'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')
django.setup()

from trading_app.models import Instrument, HistoricalData
import upstox_client_wrapper

class HistoricalDataManager:
    """
    Manages historical market data by fetching from Upstox and storing in Django database.
    """
    
    def __init__(self):
        self.cache_dir = "historical_data_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def fetch_and_store_historical_data(self, symbol, days=100, force_refresh=False):
        """
        Fetches historical data from Upstox and stores it in the database.
        
        Args:
            symbol (str): Stock symbol
            days (int): Number of days to fetch
            force_refresh (bool): Whether to force refresh existing data
            
        Returns:
            pd.DataFrame: Historical data
        """
        print(f"📊 Fetching historical data for {symbol} ({days} days)...")
        
        # Check if we have recent data in database
        if not force_refresh:
            existing_data = self.get_stored_historical_data(symbol, days)
            if existing_data is not None and len(existing_data) >= days * 0.8:  # 80% of requested days
                print(f"✅ Using cached data for {symbol} ({len(existing_data)} days)")
                return existing_data
        
        # Fetch from Upstox
        try:
            historical_data = upstox_client_wrapper.fetch_historical_data(
                instrument_key=symbol,
                interval=1,
                unit='days',
                num_periods=days
            )
            
            if historical_data.empty:
                print(f"❌ No data received for {symbol}")
                return pd.DataFrame()
            
            # Store in database
            self.store_historical_data(symbol, historical_data)
            
            print(f"✅ Fetched and stored {len(historical_data)} days of data for {symbol}")
            return historical_data
            
        except Exception as e:
            print(f"❌ Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def store_historical_data(self, symbol, data):
        """
        Stores historical data in the Django database.
        """
        try:
            # Store in Django database
            HistoricalData.store_dataframe(symbol, data)
            
            # Also keep a local cache for quick access
            data_json = data.reset_index().to_dict('records')
            filename = os.path.join(self.cache_dir, f"{symbol.replace('|', '_')}_historical.json")
            
            with open(filename, 'w') as f:
                json.dump({
                    'symbol': symbol,
                    'data': data_json,
                    'last_updated': datetime.now().isoformat(),
                    'data_points': len(data)
                }, f, indent=2, default=str)
            
            print(f"💾 Stored {len(data)} data points for {symbol} in database and cache")
            
        except Exception as e:
            print(f"❌ Error storing data for {symbol}: {e}")
    
    def get_stored_historical_data(self, symbol, days=None):
        """
        Retrieves stored historical data from the Django database.
        """
        try:
            # First try to get from Django database
            db_data = HistoricalData.get_data_for_symbol(symbol, days)
            
            if db_data.exists():
                # Convert to DataFrame
                df = pd.DataFrame(list(db_data))
                df['datetime'] = pd.to_datetime(df['date'])
                df.set_index('datetime', inplace=True)
                
                # Rename columns to match expected format
                df = df.rename(columns={
                    'open_price': 'open',
                    'high_price': 'high',
                    'low_price': 'low',
                    'close_price': 'close'
                })
                
                # Filter by days if requested
                if days:
                    df = df.tail(days)
                
                print(f"✅ Retrieved {len(df)} data points for {symbol} from database")
                return df
            
            # Fallback to local cache
            filename = os.path.join(self.cache_dir, f"{symbol.replace('|', '_')}_historical.json")
            
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    stored_data = json.load(f)
                
                # Check if data is recent (within 1 day)
                last_updated = datetime.fromisoformat(stored_data['last_updated'])
                if datetime.now() - last_updated > timedelta(days=1):
                    print(f"⚠️  Data for {symbol} is older than 1 day")
                    return None
                
                # Convert back to DataFrame
                df = pd.DataFrame(stored_data['data'])
                df['datetime'] = pd.to_datetime(df['datetime'])
                df.set_index('datetime', inplace=True)
                
                # Filter by days if requested
                if days:
                    df = df.tail(days)
                
                print(f"✅ Retrieved {len(df)} data points for {symbol} from cache")
                return df
            
            return None
            
        except Exception as e:
            print(f"❌ Error retrieving data for {symbol}: {e}")
            return None
    
    def fetch_multiple_symbols(self, symbols, days=100):
        """
        Fetches historical data for multiple symbols.
        
        Args:
            symbols (list): List of symbols to fetch
            days (int): Number of days to fetch
            
        Returns:
            dict: Dictionary with symbol as key and DataFrame as value
        """
        results = {}
        
        for i, symbol in enumerate(symbols):
            print(f"\n📈 Fetching {i+1}/{len(symbols)}: {symbol}")
            data = self.fetch_and_store_historical_data(symbol, days)
            if not data.empty:
                results[symbol] = data
            time.sleep(0.5)  # Rate limiting
        
        print(f"\n✅ Successfully fetched data for {len(results)}/{len(symbols)} symbols")
        return results
    
    def get_test_data(self, symbol, scenario='recent', days=100):
        """
        Gets test data for a symbol based on scenario.
        
        Args:
            symbol (str): Stock symbol
            scenario (str): 'recent', 'bull_market', 'bear_market', 'volatile'
            days (int): Number of days
            
        Returns:
            pd.DataFrame: Test data
        """
        if scenario == 'recent':
            # Use most recent data
            return self.fetch_and_store_historical_data(symbol, days)
        
        elif scenario in ['bull_market', 'bear_market', 'volatile']:
            # For now, use recent data but could be enhanced to find specific periods
            print(f"⚠️  Scenario '{scenario}' not implemented yet, using recent data")
            return self.fetch_and_store_historical_data(symbol, days)
        
        else:
            print(f"❌ Unknown scenario: {scenario}")
            return pd.DataFrame()
    
    def cleanup_old_data(self, days_old=30):
        """
        Removes historical data files older than specified days.
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        removed_count = 0
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('_historical.json'):
                filepath = os.path.join(self.cache_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_time < cutoff_date:
                    os.remove(filepath)
                    removed_count += 1
        
        print(f"🧹 Cleaned up {removed_count} old data files")


# Enhanced intraday data generator
class IntradayDataGenerator:
    """
    Generates realistic intraday data for testing.
    """
    
    def __init__(self):
        self.market_hours = {
            'open': '09:15',
            'close': '15:30'
        }
    
    def generate_intraday_data(self, symbol, date, interval_minutes=5, scenario='normal'):
        """
        Generates realistic intraday data for testing.
        
        Args:
            symbol (str): Stock symbol
            date (datetime): Trading date
            interval_minutes (int): Candle interval
            scenario (str): 'normal', 'volatile', 'trending'
            
        Returns:
            pd.DataFrame: Intraday OHLCV data
        """
        # Get the previous day's close as starting point
        base_price = 1000  # Default, could be enhanced to use real data
        
        # Generate intraday data (9:15 AM to 3:30 PM = 375 minutes)
        total_minutes = 375
        num_candles = total_minutes // interval_minutes
        
        data = []
        current_price = base_price
        
        # Market open time
        market_open = date.replace(hour=9, minute=15, second=0, microsecond=0)
        
        # Scenario-specific parameters
        if scenario == 'volatile':
            volatility = 0.02
            trend = 0.0001
        elif scenario == 'trending':
            volatility = 0.01
            trend = 0.001
        else:  # normal
            volatility = 0.015
            trend = 0.0005
        
        for i in range(num_candles):
            candle_time = market_open + timedelta(minutes=i * interval_minutes)
            
            # Add trend and volatility
            trend_change = trend * current_price * (interval_minutes / 1440)
            intraday_return = np.random.normal(trend_change, volatility * current_price * 0.1)
            new_price = current_price + intraday_return
            
            # Generate OHLC
            high_low_range = volatility * new_price * 0.05
            high = new_price + abs(np.random.normal(0, high_low_range))
            low = new_price - abs(np.random.normal(0, high_low_range))
            open_price = current_price + np.random.normal(0, high_low_range * 0.5)
            close_price = new_price
            
            # Ensure OHLC relationships
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            # Generate volume (higher during market open/close)
            base_volume = 50000
            if i < 10 or i > num_candles - 10:  # First and last 10 candles
                volume_multiplier = 2.0
            else:
                volume_multiplier = 1.0
            volume = int(base_volume * volume_multiplier * (0.5 + np.random.random()))
            
            data.append({
                'datetime': candle_time,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
            
            current_price = close_price
        
        df = pd.DataFrame(data)
        df.set_index('datetime', inplace=True)
        return df


# Example usage
if __name__ == "__main__":
    # Initialize managers
    historical_manager = HistoricalDataManager()
    intraday_generator = IntradayDataGenerator()
    
    # Test symbols
    test_symbols = [
        "NSE_EQ|INE002A01018",  # Reliance
        "NSE_EQ|INE019A01038",  # HDFC Bank
        "NSE_EQ|INE090A01021"   # ICICI Bank
    ]
    
    # Fetch historical data
    print("🚀 Fetching historical data for testing...")
    historical_data = historical_manager.fetch_multiple_symbols(test_symbols, days=100)
    
    # Generate intraday data
    print("\n📈 Generating intraday data...")
    intraday_data = intraday_generator.generate_intraday_data(
        "RELIANCE", 
        datetime.now(), 
        interval_minutes=5, 
        scenario='volatile'
    )
    
    print(f"✅ Historical data: {len(historical_data)} symbols")
    print(f"✅ Intraday data: {len(intraday_data)} candles") 