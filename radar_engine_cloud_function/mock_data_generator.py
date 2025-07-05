# mock_data_generator.py

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import json
import os

class MockDataGenerator:
    """
    Generates realistic mock market data for testing the scanner outside market hours.
    """
    
    def __init__(self):
        self.base_prices = {
            'RELIANCE': 2500,
            'TCS': 3800,
            'HDFCBANK': 1600,
            'INFY': 1400,
            'ICICIBANK': 1000,
            'HINDUNILVR': 2400,
            'ITC': 450,
            'SBIN': 650,
            'BHARTIARTL': 1100,
            'AXISBANK': 950
        }
        
        self.volatility_profiles = {
            'HIGH': {'daily_vol': 0.04, 'intraday_vol': 0.02},
            'MEDIUM': {'daily_vol': 0.025, 'intraday_vol': 0.015},
            'LOW': {'daily_vol': 0.015, 'intraday_vol': 0.01}
        }
        
        self.market_scenarios = {
            'BULL_MARKET': {'trend': 0.001, 'volatility': 'MEDIUM'},
            'BEAR_MARKET': {'trend': -0.001, 'volatility': 'HIGH'},
            'SIDEWAYS': {'trend': 0.0001, 'volatility': 'LOW'},
            'VOLATILE': {'trend': 0.0005, 'volatility': 'HIGH'}
        }
    
    def generate_daily_candles(self, symbol, days=100, scenario='SIDEWAYS', start_date=None):
        """
        Generates realistic daily OHLCV data for a given symbol.
        
        Args:
            symbol (str): Stock symbol
            days (int): Number of days to generate
            scenario (str): Market scenario (BULL_MARKET, BEAR_MARKET, SIDEWAYS, VOLATILE)
            start_date (datetime): Starting date for the data
            
        Returns:
            pd.DataFrame: OHLCV data with datetime index
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=days)
        
        base_price = self.base_prices.get(symbol, 1000)
        scenario_config = self.market_scenarios[scenario]
        vol_profile = self.volatility_profiles[scenario_config['volatility']]
        
        dates = pd.date_range(start=start_date, periods=days, freq='D')
        data = []
        
        current_price = base_price
        
        for i, date in enumerate(dates):
            # Skip weekends
            if date.weekday() >= 5:
                continue
                
            # Add trend component
            trend_change = scenario_config['trend'] * current_price
            
            # Generate daily volatility
            daily_return = np.random.normal(trend_change, vol_profile['daily_vol'] * current_price)
            new_price = current_price + daily_return
            
            # Generate OHLC from the new price
            high_low_range = vol_profile['intraday_vol'] * new_price
            high = new_price + abs(np.random.normal(0, high_low_range * 0.3))
            low = new_price - abs(np.random.normal(0, high_low_range * 0.3))
            open_price = current_price + np.random.normal(0, high_low_range * 0.2)
            close_price = new_price
            
            # Ensure OHLC relationships are valid
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            # Generate volume (correlated with price movement)
            base_volume = 1000000
            volume_multiplier = 1 + abs(daily_return) / (vol_profile['daily_vol'] * current_price)
            volume = int(base_volume * volume_multiplier * (0.8 + 0.4 * random.random()))
            
            data.append({
                'datetime': date,
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
    
    def generate_intraday_candles(self, symbol, date, scenario='SIDEWAYS', interval_minutes=5):
        """
        Generates realistic intraday OHLCV data for a given symbol and date.
        
        Args:
            symbol (str): Stock symbol
            date (datetime): Trading date
            scenario (str): Market scenario
            interval_minutes (int): Candle interval in minutes
            
        Returns:
            pd.DataFrame: Intraday OHLCV data
        """
        # Get the previous day's close as starting point
        prev_day_data = self.generate_daily_candles(symbol, days=2, scenario=scenario, 
                                                   start_date=date - timedelta(days=2))
        if prev_day_data.empty:
            return pd.DataFrame()
        
        start_price = prev_day_data['close'].iloc[-1]
        scenario_config = self.market_scenarios[scenario]
        vol_profile = self.volatility_profiles[scenario_config['volatility']]
        
        # Generate intraday data (9:15 AM to 3:30 PM = 375 minutes)
        total_minutes = 375
        num_candles = total_minutes // interval_minutes
        
        data = []
        current_price = start_price
        
        # Market open time
        market_open = date.replace(hour=9, minute=15, second=0, microsecond=0)
        
        for i in range(num_candles):
            candle_time = market_open + timedelta(minutes=i * interval_minutes)
            
            # Add trend and volatility
            trend_change = scenario_config['trend'] * current_price * (interval_minutes / 1440)  # Daily trend scaled to interval
            intraday_return = np.random.normal(trend_change, vol_profile['intraday_vol'] * current_price * 0.1)
            new_price = current_price + intraday_return
            
            # Generate OHLC
            high_low_range = vol_profile['intraday_vol'] * new_price * 0.05
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
            volume = int(base_volume * volume_multiplier * (0.5 + random.random()))
            
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
    
    def create_market_scenario(self, scenario_name, symbols=None, days=30):
        """
        Creates a complete market scenario with multiple symbols.
        
        Args:
            scenario_name (str): Name of the scenario
            symbols (list): List of symbols to include
            days (int): Number of days to generate
            
        Returns:
            dict: Scenario data with symbol keys and DataFrame values
        """
        if symbols is None:
            symbols = list(self.base_prices.keys())
        
        scenario_data = {}
        start_date = datetime.now() - timedelta(days=days)
        
        for symbol in symbols:
            scenario_data[symbol] = self.generate_daily_candles(
                symbol, days=days, scenario=scenario_name, start_date=start_date
            )
        
        return scenario_data
    
    def save_scenario(self, scenario_data, filename):
        """
        Saves a market scenario to a JSON file for later use.
        
        Args:
            scenario_data (dict): Scenario data
            filename (str): Output filename
        """
        # Convert DataFrames to JSON-serializable format
        serializable_data = {}
        for symbol, df in scenario_data.items():
            serializable_data[symbol] = {
                'data': df.reset_index().to_dict('records'),
                'columns': df.columns.tolist()
            }
        
        with open(filename, 'w') as f:
            json.dump(serializable_data, f, indent=2, default=str)
    
    def load_scenario(self, filename):
        """
        Loads a market scenario from a JSON file.
        
        Args:
            filename (str): Input filename
            
        Returns:
            dict: Scenario data with symbol keys and DataFrame values
        """
        with open(filename, 'r') as f:
            data = json.load(f)
        
        scenario_data = {}
        for symbol, symbol_data in data.items():
            df = pd.DataFrame(symbol_data['data'])
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            scenario_data[symbol] = df
        
        return scenario_data
    
    def generate_alert_scenario(self, symbol, alert_type='RSI_OVERSOLD'):
        """
        Generates data that will trigger specific alerts for testing.
        
        Args:
            symbol (str): Stock symbol
            alert_type (str): Type of alert to trigger
            
        Returns:
            pd.DataFrame: Data that will trigger the specified alert
        """
        base_price = self.base_prices.get(symbol, 1000)
        min_days = 100  # Ensure at least 100 trading days for all indicators
        
        if alert_type == 'RSI_OVERSOLD':
            # Generate declining price data to create oversold RSI
            data = []
            current_price = base_price
            days_generated = 0
            i = 0
            while days_generated < min_days:
                date = datetime.now() - timedelta(days=min_days-i)
                i += 1
                if date.weekday() >= 5:  # Skip weekends
                    continue
                # Steady decline
                decline = current_price * 0.02
                current_price -= decline
                high = current_price * 1.01
                low = current_price * 0.99
                open_price = current_price * 1.005
                close_price = current_price
                data.append({
                    'datetime': date,
                    'open': round(open_price, 2),
                    'high': round(high, 2),
                    'low': round(low, 2),
                    'close': round(close_price, 2),
                    'volume': 1000000
                })
                days_generated += 1
            df = pd.DataFrame(data)
            df.set_index('datetime', inplace=True)
            return df
        
        elif alert_type == 'GOLDEN_CROSS':
            # Generate data that will create a golden cross (EMA50 > EMA200)
            data = []
            current_price = base_price * 0.8  # Start lower
            days_generated = 0
            i = 0
            while days_generated < max(250, min_days):
                date = datetime.now() - timedelta(days=max(250, min_days)-i)
                i += 1
                if date.weekday() >= 5:
                    continue
                # Gradual uptrend
                if days_generated < 100:
                    current_price *= 1.001  # Slow rise
                else:
                    current_price *= 1.005  # Faster rise
                high = current_price * 1.02
                low = current_price * 0.98
                open_price = current_price * 0.999
                close_price = current_price
                data.append({
                    'datetime': date,
                    'open': round(open_price, 2),
                    'high': round(high, 2),
                    'low': round(low, 2),
                    'close': round(close_price, 2),
                    'volume': 1000000
                })
                days_generated += 1
            df = pd.DataFrame(data)
            df.set_index('datetime', inplace=True)
            return df
        
        # Default: return normal data
        return self.generate_daily_candles(symbol, days=max(min_days, 50), scenario='SIDEWAYS')


# Example usage and testing
if __name__ == "__main__":
    generator = MockDataGenerator()
    
    # Generate a bull market scenario
    print("Generating bull market scenario...")
    bull_scenario = generator.create_market_scenario('BULL_MARKET', ['RELIANCE', 'TCS'], days=30)
    
    # Save the scenario
    generator.save_scenario(bull_scenario, 'test_scenarios/bull_market.json')
    
    # Generate RSI oversold alert data
    print("Generating RSI oversold alert data...")
    rsi_data = generator.generate_alert_scenario('RELIANCE', 'RSI_OVERSOLD')
    print(f"Generated {len(rsi_data)} days of RSI oversold data")
    
    # Generate golden cross alert data
    print("Generating golden cross alert data...")
    golden_cross_data = generator.generate_alert_scenario('TCS', 'GOLDEN_CROSS')
    print(f"Generated {len(golden_cross_data)} days of golden cross data") 