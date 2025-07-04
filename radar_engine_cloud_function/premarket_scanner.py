# premarket_scanner.py

import os
import sys
import django
import time
import pandas as pd
import pandas_ta as ta

# --- Django Setup ---
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'django_api'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')
django.setup()
# --- End Django Setup ---

from trading_app.models import Instrument
import indicator_calculator
import trade_analyzer
import upstox_client_wrapper
import strategies

# --- Constants ---
SECTORAL_INDICES = {
    'NIFTY AUTO': 'NSE_INDEX|Nifty Auto',
    'NIFTY BANK': 'NSE_INDEX|Nifty Bank',
    'NIFTY FMCG': 'NSE_INDEX|Nifty FMCG',
    'NIFTY IT': 'NSE_INDEX|Nifty IT',
    'NIFTY MEDIA': 'NSE_INDEX|Nifty Media',
    'NIFTY METAL': 'NSE_INDEX|Nifty Metal',
    'NIFTY PHARMA': 'NSE_INDEX|Nifty Pharma',
    'NIFTY REALTY': 'NSE_INDEX|Nifty Realty',
}
VIX_INDEX_KEY = "NSE_INDEX|India VIX"

def get_market_context():
    """
    Analyzes the NIFTY 50 for trend and the India VIX for volatility.
    Returns a dictionary with the market context.
    """
    print("\n--- Analyzing Market Context (Trend & Volatility) ---")
    context = {'trend': 'NEUTRAL', 'volatility': 'NORMAL'}
    
    # 1. Analyze NIFTY 50 Trend
    nifty_df = upstox_client_wrapper.fetch_historical_data("NSE_INDEX|Nifty 50", num_periods=100)
    if not nifty_df.empty and len(nifty_df) > 50:
        nifty_df.ta.ema(length=20, append=True)
        nifty_df.ta.ema(length=50, append=True)
        last_close = nifty_df['close'].iloc[-1]
        last_ema20 = nifty_df['EMA_20'].iloc[-1]
        last_ema50 = nifty_df['EMA_50'].iloc[-1]
        
        if last_close > last_ema20 and last_ema20 > last_ema50:
            context['trend'] = 'UP'
            print("Market Trend is UP (Price > 20EMA > 50EMA).")
        elif last_close < last_ema20 and last_ema20 < last_ema50:
            context['trend'] = 'DOWN'
            print("Market Trend is DOWN (Price < 20EMA < 50EMA).")
        else:
            print("Market Trend is NEUTRAL/SIDEWAYS.")
            
    # 2. Analyze India VIX for Volatility
    vix_df = upstox_client_wrapper.fetch_historical_data(VIX_INDEX_KEY, num_periods=10)
    if not vix_df.empty:
        last_vix = vix_df['close'].iloc[-1]
        if last_vix > 20:
            context['volatility'] = 'HIGH'
            print(f"Market Volatility is HIGH (VIX: {last_vix:.2f}).")
        elif last_vix < 15:
            context['volatility'] = 'LOW'
            print(f"Market Volatility is LOW (VIX: {last_vix:.2f}).")
        else:
            print(f"Market Volatility is NORMAL (VIX: {last_vix:.2f}).")
            
    return context

def analyze_sector_strength():
    """Ranks sectors by recent performance."""
    print("\n--- Analyzing Sector Strength ---")
    sector_performance = []
    for sector_name, instrument_key in SECTORAL_INDICES.items():
        df = upstox_client_wrapper.fetch_historical_data(instrument_key, num_periods=20)
        if not df.empty and len(df) > 5:
            perf = (df['close'].iloc[-1] / df['close'].iloc[-6] - 1) * 100
            sector_performance.append({'sector': sector_name, 'performance': perf})
        time.sleep(0.5)
    
    if not sector_performance: return []
    strongest_sectors = sorted(sector_performance, key=lambda x: x['performance'], reverse=True)
    print("Sector Performance Ranking (5-Day Change):")
    for sector in strongest_sectors:
        print(f"  - {sector['sector']}: {sector['performance']:.2f}%")
    return [s['sector'] for s in strongest_sectors[:3]]

def main():
    """Main function to run the pre-market scan with contextual filters."""
    # 1. Get the full market context before starting
    market_context = get_market_context()
    strongest_sectors = analyze_sector_strength()
    
    # 2. Choose the right strategy based on the market trend
    if market_context['trend'] == 'UP':
        STRATEGY_NAME = "Bullish_Scan"
    elif market_context['trend'] == 'DOWN':
        STRATEGY_NAME = "Bearish_Scan"
    else:
        STRATEGY_NAME = "Full_Scan"
        
    print(f"\n--- Starting Pre-Market Radar Scan: '{STRATEGY_NAME}' ---")
    
    # 3. Get instruments and rules
    rules_to_run = strategies.get_rules_for_strategy(STRATEGY_NAME)
    instruments = Instrument.objects.order_by('-average_volume')[:200]
    if not instruments.exists():
        print("ERROR: No instruments found in the database.")
        return

    print(f"\nAnalyzing {instruments.count()} stocks with {len(rules_to_run)} rules...")
    all_alerts = []

    # 4. Analyze each stock, passing the full context to the analyzer
    for i, instrument in enumerate(instruments):
        print(f"  Scanning {i+1}/{instruments.count()}: {instrument.tradingsymbol}", end='\r')
        df = upstox_client_wrapper.fetch_historical_data(instrument.instrument_key, num_periods=250)
        if not df.empty and len(df) > 50:
            indicators = indicator_calculator.calculate_indicators(df)
            score, reasons = trade_analyzer.analyze_setup(
                indicators, df, rules_to_run, 
                stock_sector=instrument.sector, 
                strong_sectors=strongest_sectors,
                volatility=market_context['volatility']
            )
            if score > 0:
                all_alerts.append({"instrument_key": instrument.instrument_key, "score": score, "reasons": reasons, "indicators": indicators})
        time.sleep(0.5)

    print(f"\n\n--- Analysis Complete. Found {len(all_alerts)} potential setups. ---")

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
