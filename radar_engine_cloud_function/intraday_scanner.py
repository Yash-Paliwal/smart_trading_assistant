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
    Enhanced Opening Range Breakout analysis with multiple entry strategies.
    """
    df = upstox_client_wrapper.fetch_intraday_data(instrument_key, interval='5')

    if df is None or len(df) < 12: # Need at least 12 5-min candles for 1 hour analysis
        return

    # 1. Define the opening range (first 30 minutes = 6 candles)
    opening_range_df = df.head(6)
    opening_range_high = opening_range_df['high'].max()
    opening_range_low = opening_range_df['low'].min()
    
    # 2. Get the most recent candle
    last_candle = df.iloc[-1]
    current_price = last_candle['close']
    current_volume = last_candle['volume']
    avg_volume = df['volume'].tail(6).mean()
    
    # 3. Enhanced breakout detection with volume confirmation
    breakout_up = current_price > opening_range_high
    breakout_down = current_price < opening_range_low
    volume_confirmation = current_volume > avg_volume * 1.2
    
    if breakout_up or breakout_down:
        direction = "UP" if breakout_up else "DOWN"
        breakout_level = opening_range_high if breakout_up else opening_range_low
        
        # Calculate targets and stop loss
        if breakout_up:
            stop_loss = opening_range_low
            target = current_price + (current_price - opening_range_low)
        else:
            stop_loss = opening_range_high
            target = current_price - (opening_range_high - current_price)
        
        # Calculate risk-reward ratio
        risk = abs(current_price - stop_loss)
        reward = abs(target - current_price)
        rr_ratio = reward / risk if risk > 0 else 0
        
        print(f"\n🎯 [ENHANCED ORB DETECTED] for {instrument_key}!")
        print(f"   Direction: {direction}")
        print(f"   Entry: ₹{current_price:.2f}")
        print(f"   Stop Loss: ₹{stop_loss:.2f}")
        print(f"   Target: ₹{target:.2f}")
        print(f"   Risk-Reward: 1:{rr_ratio:.2f}")
        print(f"   Volume: {'✅ Confirmed' if volume_confirmation else '❌ Weak'}")
        
        # 4. Create enhanced alert
        reasons = [
            f"Enhanced ORB: Price broke {direction} the {OPENING_RANGE_MINUTES}-min opening range",
            f"Entry: ₹{current_price:.2f}, Stop: ₹{stop_loss:.2f}, Target: ₹{target:.2f}",
            f"Risk-Reward: 1:{rr_ratio:.2f}",
            f"Volume: {'High' if volume_confirmation else 'Normal'}"
        ]
        
        alert_data = {
            "instrument_key": instrument_key,
            "score": 2 if volume_confirmation else 1,
            "reasons": reasons,
            "indicators": {
                "ORB_High": opening_range_high,
                "ORB_Low": opening_range_low,
                "Entry_Price": current_price,
                "Stop_Loss": stop_loss,
                "Target": target,
                "Risk_Reward": rr_ratio,
                "Volume_Confirmation": volume_confirmation,
                "Direction": direction
            }
        }
        
        # Save enhanced alert
        trade_analyzer.save_alerts_to_db([alert_data], STRATEGY_NAME)

def main():
    """
    Main function to run the intraday scanner.
    """
    print(f"\n--- Running Intraday Scanner: {STRATEGY_NAME} ---")

    # Check if it's a weekday
    today = datetime.now().weekday()  # Monday=0, Sunday=6
    if today >= 5:
        print("Market is closed today (Weekend). Exiting.")
        return
    
    # Check market hours (9:15 AM to 3:30 PM IST)
    import pytz
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%H:%M")
    
    if not ("09:15" <= current_time <= "15:30"):
        print(f"Market is closed. Current time: {current_time}")
        return

    print(f"Current IST Time: {now.time()}")
    print("Market is open. Starting intraday scan...")

    # Get watchlist and scan
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
