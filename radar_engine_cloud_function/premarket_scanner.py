# premarket_scanner.py

import os
import sys
import django
import time
import pandas_ta as ta

# --- Django Setup ---
# This block allows this standalone script to use the Django database models.
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'django_api'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')
django.setup()
# --- End Django Setup ---

from trading_app.models import Instrument
import indicator_calculator
import trade_analyzer
import upstox_client_wrapper
import strategies

def get_market_trend():
    """
    Determines the overall market trend by checking the NIFTY 50 index
    against its 50-day EMA.
    Returns:
        str: 'UP', 'DOWN', or 'SIDEWAYS'
    """
    print("Determining overall market trend...")
    # The instrument key for the NIFTY 50 Index
    nifty_key = "NSE_INDEX|Nifty 50"
    df = upstox_client_wrapper.fetch_historical_data(nifty_key, num_periods=100)

    if df.empty or len(df) < 50:
        print("Warning: Could not fetch NIFTY 50 data. Defaulting to a full scan.")
        return 'SIDEWAYS' # Default to a neutral state if we can't determine the trend

    # Calculate the 50-day EMA for the NIFTY 50
    df.ta.ema(length=50, append=True)
    
    last_close = df['close'].iloc[-1]
    last_ema50 = df['EMA_50'].iloc[-1]

    if last_close > last_ema50:
        print("Market Trend is UP (NIFTY 50 is above its 50-day EMA).")
        return 'UP'
    else:
        print("Market Trend is DOWN (NIFTY 50 is below its 50-day EMA).")
        return 'DOWN'

def main():
    """
    Main function to run the pre-market scan using the Market Trend Filter.
    """
    # 1. Determine the market trend to decide which strategy to run
    market_trend = get_market_trend()

    if market_trend == 'UP':
        STRATEGY_NAME = "Bullish_Scan"
    elif market_trend == 'DOWN':
        STRATEGY_NAME = "Bearish_Scan"
    else: # If trend is sideways or couldn't be determined
        STRATEGY_NAME = "Full_Scan"
    
    print(f"\n--- Starting Pre-Market Radar Scan: '{STRATEGY_NAME}' ---")

    # 2. Get the rules for the selected strategy
    rules_to_run = strategies.get_rules_for_strategy(STRATEGY_NAME)
    if not rules_to_run:
        print(f"ERROR: Strategy '{STRATEGY_NAME}' has no rules. Exiting.")
        return

    # 3. Get the list of stocks to scan from our database
    instrument_keys = list(Instrument.objects.values_list('instrument_key', flat=True))
    if not instrument_keys:
        print("ERROR: No instruments found in the database.")
        return

    print(f"\nAnalyzing {len(instrument_keys)} stocks with {len(rules_to_run)} rules...")
    all_alerts = []

    # 4. Analyze each stock
    for key in instrument_keys:
        df = upstox_client_wrapper.fetch_historical_data(key, num_periods=250)
        
        if not df.empty and len(df) > 50:
            indicators = indicator_calculator.calculate_indicators(df)
            score, reasons = trade_analyzer.analyze_setup(indicators, df, rules_to_run)

            if score > 0:
                all_alerts.append({
                    "instrument_key": key,
                    "score": score,
                    "reasons": reasons,
                    "indicators": indicators
                })
        
        time.sleep(0.5)

    print(f"\n--- Analysis Complete. Found {len(all_alerts)} potential setups. ---")

    # 5. Rank and save the top 10 alerts
    if all_alerts:
        sorted_alerts = sorted(all_alerts, key=lambda x: x['score'], reverse=True)
        top_10_alerts = sorted_alerts[:10]
        
        print("\n--- Top 10 Setups for Today ---")
        for i, alert in enumerate(top_10_alerts):
            print(f"{i+1}. {alert['instrument_key']} (Score: {alert['score']})")
            for reason in alert['reasons']:
                print(f"   - {reason}")
        
        trade_analyzer.save_alerts_to_db(top_10_alerts, STRATEGY_NAME)
    else:
        print("\nNo setups meeting any of our criteria were found for today.")


if __name__ == "__main__":
    main()
