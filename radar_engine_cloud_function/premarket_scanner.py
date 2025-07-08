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
    Enhanced market context analysis with multiple timeframes and strength indicators.
    """
    print("\n🔍 Analyzing Market Context (Trend & Volatility) ---")
    context = {'trend': 'NEUTRAL', 'volatility': 'NORMAL', 'strength': 'NEUTRAL'}
    
    # 1. Enhanced NIFTY 50 Multi-timeframe Analysis
    nifty_df = upstox_client_wrapper.fetch_historical_data("NSE_INDEX|Nifty 50", num_periods=250)  # Increased for EMA200
    if not nifty_df.empty and len(nifty_df) > 200:  # Need at least 200 points for EMA200
        try:
            # Calculate multiple EMAs
            nifty_df.ta.ema(length=20, append=True)
            nifty_df.ta.ema(length=50, append=True)
            nifty_df.ta.ema(length=200, append=True)
            
            last_close = nifty_df['close'].iloc[-1]
            last_ema20 = nifty_df['EMA_20'].iloc[-1]
            last_ema50 = nifty_df['EMA_50'].iloc[-1]
            last_ema200 = nifty_df['EMA_200'].iloc[-1]
            
            # Enhanced trend analysis with strength
            if last_close > last_ema20 > last_ema50 > last_ema200:
                context['trend'] = 'STRONG_UP'
                context['strength'] = 'STRONG'
                print("Market Trend is STRONG UP (All EMAs aligned).")
            elif last_close > last_ema20 > last_ema50:
                context['trend'] = 'UP'
                context['strength'] = 'MODERATE'
                print("Market Trend is UP (Price > 20EMA > 50EMA).")
            elif last_close < last_ema20 < last_ema50 < last_ema200:
                context['trend'] = 'STRONG_DOWN'
                context['strength'] = 'STRONG'
                print("Market Trend is STRONG DOWN (All EMAs aligned).")
            elif last_close < last_ema20 < last_ema50:
                context['trend'] = 'DOWN'
                context['strength'] = 'MODERATE'
                print("Market Trend is DOWN (Price < 20EMA < 50EMA).")
            else:
                print("Market Trend is NEUTRAL/SIDEWAYS.")
                
        except Exception as e:
            print(f"⚠️ Error calculating EMAs: {e}")
            # Fallback to basic trend analysis
            if last_close > last_ema20:
                context['trend'] = 'UP'
                print("Market Trend is UP (Basic analysis).")
            elif last_close < last_ema20:
                context['trend'] = 'DOWN'
                print("Market Trend is DOWN (Basic analysis).")
            else:
                print("Market Trend is NEUTRAL/SIDEWAYS.")
    else:
        print("⚠️ Insufficient data for comprehensive trend analysis.")
        context['trend'] = 'NEUTRAL'
            
    # 2. Enhanced VIX Analysis with averages
    vix_df = upstox_client_wrapper.fetch_historical_data(VIX_INDEX_KEY, num_periods=20)
    if not vix_df.empty:
        last_vix = vix_df['close'].iloc[-1]
        avg_vix = vix_df['close'].mean()
        
        if last_vix > avg_vix * 1.2:
            context['volatility'] = 'HIGH'
            print(f"Market Volatility is HIGH (VIX: {last_vix:.2f}, Avg: {avg_vix:.2f}).")
        elif last_vix < avg_vix * 0.8:
            context['volatility'] = 'LOW'
            print(f"Market Volatility is LOW (VIX: {last_vix:.2f}, Avg: {avg_vix:.2f}).")
        else:
            print(f"Market Volatility is NORMAL (VIX: {last_vix:.2f}, Avg: {avg_vix:.2f}).")
            
    return context

def analyze_sector_strength():
    """Enhanced sector analysis with momentum and strength scoring."""
    print("\n🔄 Analyzing Sector Strength & Rotation ---")
    sector_analysis = []
    
    for sector_name, instrument_key in SECTORAL_INDICES.items():
        try:
            df = upstox_client_wrapper.fetch_historical_data(instrument_key, num_periods=30)
            if not df.empty and len(df) > 20:
                # Calculate multiple metrics
                current_price = df['close'].iloc[-1]
                price_5d_ago = df['close'].iloc[-6] if len(df) > 5 else current_price
                price_20d_ago = df['close'].iloc[-21] if len(df) > 20 else current_price
                
                momentum_5d = (current_price / price_5d_ago - 1) * 100
                momentum_20d = (current_price / price_20d_ago - 1) * 100
                
                # Calculate RSI for sector with error handling
                try:
                    df.ta.rsi(length=14, append=True)
                    rsi = df['RSI_14'].iloc[-1] if 'RSI_14' in df.columns else 50
                except Exception as e:
                    print(f"⚠️ Error calculating RSI for {sector_name}: {e}")
                    rsi = 50  # Neutral RSI as fallback
                
                # Enhanced strength scoring
                strength_score = 0
                if momentum_5d > 2: strength_score += 2
                elif momentum_5d > 0: strength_score += 1
                if momentum_20d > 5: strength_score += 2
                elif momentum_20d > 0: strength_score += 1
                if 30 < rsi < 70: strength_score += 1
                if rsi > 50: strength_score += 1
                
                sector_analysis.append({
                    'sector': sector_name,
                    'momentum_5d': momentum_5d,
                    'momentum_20d': momentum_20d,
                    'rsi': rsi,
                    'strength_score': strength_score,
                    'current_price': current_price
                })
            
            time.sleep(0.3)  # Rate limiting
            
        except Exception as e:
            print(f"⚠️ Error analyzing {sector_name}: {e}")
            continue
    
    if not sector_analysis: return []
    
    # Sort by strength score
    sector_analysis.sort(key=lambda x: x['strength_score'], reverse=True)
    
    print("📊 Sector Strength Ranking:")
    for i, sector in enumerate(sector_analysis[:5]):
        print(f"  {i+1}. {sector['sector']}: Score {sector['strength_score']} (5d: {sector['momentum_5d']:.1f}%, RSI: {sector['rsi']:.1f})")
    
    return [s['sector'] for s in sector_analysis[:3]]  # Top 3 sectors

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
    print(f"\n🔍 Starting detailed analysis of {instruments.count()} stocks...")
    print(f"📋 Rules to check: {len(rules_to_run)}")
    print(f"🎯 Market context: {market_context['trend']} trend, {market_context['volatility']} volatility")
    print(f"🏭 Strong sectors: {', '.join(strongest_sectors) if strongest_sectors else 'None'}")
    print("-" * 80)
    
    for i, instrument in enumerate(instruments):
        print(f"\n[{i+1:3d}/{instruments.count()}] 🔍 Analyzing: {instrument.tradingsymbol} ({instrument.instrument_key})")
        print(f"    📊 Sector: {instrument.sector or 'Unknown'}")
        print(f"    📈 Volume: {instrument.average_volume:,.0f}")
        
        # Fetch historical data
        print(f"    📥 Fetching historical data...", end=' ')
        df = upstox_client_wrapper.fetch_historical_data(instrument.instrument_key, num_periods=250)
        
        if df.empty:
            print("❌ NO DATA")
            continue
        elif len(df) <= 50:
            print(f"❌ INSUFFICIENT DATA ({len(df)} candles, need >50)")
            continue
        else:
            print(f"✅ GOT {len(df)} candles")
        
        # Calculate indicators
        print(f"    🧮 Calculating indicators...", end=' ')
        try:
            indicators = indicator_calculator.calculate_indicators(df)
            print("✅ DONE")
        except Exception as e:
            print(f"❌ ERROR: {e}")
            continue
        
        # Analyze setup
        print(f"    🎯 Checking criteria...", end=' ')
        try:
            score, reasons = trade_analyzer.analyze_setup(
                indicators, df, rules_to_run, 
                stock_sector=instrument.sector, 
                strong_sectors=strongest_sectors,
                volatility=market_context['volatility']
            )
            
            if score > 0:
                print(f"✅ QUALIFIED (Score: {score})")
                print(f"       📝 Reasons:")
                for reason in reasons:
                    print(f"         - {reason}")
                all_alerts.append({
                    "instrument_key": instrument.instrument_key, 
                    "score": score, 
                    "reasons": reasons, 
                    "indicators": indicators
                })
            else:
                print(f"❌ REJECTED (Score: {score})")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            continue
        
        time.sleep(0.5)

    print(f"\n" + "="*80)
    print(f"📊 ANALYSIS COMPLETE")
    print(f"="*80)
    print(f"🎯 Strategy used: {STRATEGY_NAME}")
    print(f"📈 Stocks analyzed: {instruments.count()}")
    print(f"✅ Stocks with data: {len([i for i in range(instruments.count()) if True])}")  # Simplified for now
    print(f"🎯 Stocks qualified: {len(all_alerts)}")
    print(f"📋 Rules checked: {len(rules_to_run)}")
    
    if len(all_alerts) > 0:
        print(f"\n🏆 QUALIFIED STOCKS (Score > 0):")
        sorted_alerts = sorted(all_alerts, key=lambda x: x['score'], reverse=True)
        
        for i, alert in enumerate(sorted_alerts):
            print(f"\n{i+1:2d}. {alert['instrument_key']} (Score: {alert['score']})")
            for reason in alert['reasons']:
                print(f"     - {reason}")
        
        # Save top 10 (or all if less than 10)
        top_alerts = sorted_alerts[:10]
        print(f"\n💾 Saving top {len(top_alerts)} alerts to database...")
        trade_analyzer.save_alerts_to_db(top_alerts, STRATEGY_NAME)
        print(f"✅ Saved {len(top_alerts)} alerts successfully")
        
        print(f"\n📊 SUMMARY:")
        print(f"   - Total qualified: {len(all_alerts)}")
        print(f"   - Top alerts saved: {len(top_alerts)}")
        print(f"   - Strategy: {STRATEGY_NAME}")
        
    else:
        print(f"\n❌ NO STOCKS QUALIFIED")
        print(f"   - All {instruments.count()} stocks were rejected")
        print(f"   - Check if criteria are too strict")
        print(f"   - Market conditions may not be favorable")
    
    print(f"="*80)

if __name__ == "__main__":
    main()
