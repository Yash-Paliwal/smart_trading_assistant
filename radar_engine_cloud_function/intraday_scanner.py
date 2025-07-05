# intraday_scanner.py

import os
import sys
import django
import time
import pandas as pd
from datetime import datetime


# --- Django Setup ---
# This allows this standalone script to use the Django database models.
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'django_api'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')
django.setup()
# --- End Django Setup ---

from trading_app.models import RadarAlert
import upstox_client_wrapper
import trade_analyzer

# --- Constants ---
STRATEGY_NAME = "Intraday_ORB_Breakout"
OPENING_RANGE_MINUTES = 30

def get_watchlist():
    """
    Fetches the instrument keys from the latest pre-market scan alerts
    to create our intraday watchlist.
    """
    print("Fetching watchlist from pre-market scan alerts...")
    try:
        # Get the most recent alerts from the "Daily_Confluence_Scan"
        alerts = RadarAlert.objects.filter(source_strategy="Daily_Confluence_Scan").order_by('-timestamp')
        # Get the unique instrument keys from these alerts
        watchlist = list(alerts.values_list('instrument_key', flat=True).distinct())
        print(f"Found {len(watchlist)} stocks in the watchlist.")
        return watchlist
    except Exception as e:
        print(f"ERROR fetching watchlist from database: {e}")
        return []

def analyze_stock_for_orb(instrument_key):
    """
    Analyzes a single stock for an Opening Range Breakout.
    """
    df = upstox_client_wrapper.fetch_intraday_data(instrument_key, interval='5')

    if df is None or len(df) < 6: # Need at least 6 5-min candles for a 30-min range
        return

    # 1. Define the opening range (first 30 minutes, which is the first 6 5-min candles)
    opening_range_df = df.head(6)
    opening_range_high = opening_range_df['high'].max()
    opening_range_low = opening_range_df['low'].min()
    
    # 2. Get the most recent candle
    last_candle = df.iloc[-1]
    
    # 3. Check for a breakout
    # A breakout occurs if the last candle's close is above the opening range high.
    if last_candle['close'] > opening_range_high:
        print(f"\n[BREAKOUT DETECTED] for {instrument_key}!")
        
        # 4. Create and save the alert
        reasons = [
            f"Price broke above the {OPENING_RANGE_MINUTES}-min opening range high of {opening_range_high:.2f}.",
            f"Current Price: {last_candle['close']:.2f}"
        ]
        
        alert_data = {
            "instrument_key": instrument_key,
            "score": 1, # Intraday alerts can have their own scoring system
            "reasons": reasons,
            "indicators": { # We can add relevant intraday indicators here later
                "ORB_High": opening_range_high,
                "ORB_Low": opening_range_low,
                "Last_Close": last_candle['close']
            }
        }
        
        # Use the existing save function, but just for this one alert
        trade_analyzer.save_alerts_to_db([alert_data], STRATEGY_NAME)

def main():
    """
    Main function to run the intraday scanner.
    """
    print(f"\n--- Running Intraday Scanner: {STRATEGY_NAME} ---")

    # 🛑 Exit if it's Saturday or Sunday
    today = datetime.now().weekday()  # Monday=0, Sunday=6
    if today >= 5:
        print("Market is closed today (Weekend). Exiting.")
        return

    # 🧪 Diagnostic check: print current time in IST
    now = pd.Timestamp.now(tz='Asia/Kolkata')
    print(f"Current IST Time: {now.time()}")

    market_open_time = pd.Timestamp(f"{now.date()} 09:15:00", tz='Asia/Kolkata')
    if now < market_open_time + pd.Timedelta(minutes=5):
        print(f"Market not open yet or opening range incomplete. Exiting.")
        return

    # ✅ Continue only if market is open
    watchlist = get_watchlist()
    if not watchlist:
        print("No stocks in the watchlist to scan. Exiting.")
        return

    for i, instrument_key in enumerate(watchlist):
        print(f"  Analyzing {i+1}/{len(watchlist)}: {instrument_key}", end='\r')
        analyze_stock_for_orb(instrument_key)
        time.sleep(0.5)

    print("\n--- Intraday Scan Complete ---")

if __name__ == "__main__":
    main()
