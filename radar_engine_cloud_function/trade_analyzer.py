# trade_analyzer.py

import psycopg2
from decouple import config
import json
import pandas as pd
import traceback

# --- Database Configuration ---
DB_HOST = config('DB_HOST')
DB_NAME = config('DB_NAME')
DB_USER = config('DB_USER')
DB_PASSWORD = config('DB_PASSWORD')
DB_PORT = config('DB_PORT')

def analyze_setup(indicators, df_history, rules, stock_sector=None, strong_sectors=None, volatility='NORMAL'):
    """
    A generic "Rules Engine" that analyzes indicators and patterns,
    now including contextual filters for sector strength and market volatility.
    """
    if not indicators:
        return 0, []

    score = 0
    reasons = []

    # --- Contextual Scoring ---
    # 1. Sector Strength Bonus: Give a point if the stock is in a top-performing sector.
    if stock_sector and strong_sectors and stock_sector in strong_sectors:
        score += 1
        reasons.append(f"Relative Strength: Stock is in a top-performing sector ({stock_sector}).")

    # --- Rule-Based Scoring ---
    # Loop through the base rules and evaluate them
    for rule in rules:
        rule_triggered = False
        
        if rule['type'] == 'indicator':
            indicator_value = indicators.get(rule['indicator'])
            if indicator_value is not None:
                if rule['condition'] == 'less_than' and indicator_value < rule['value']:
                    rule_triggered = True
                elif rule['condition'] == 'greater_than' and indicator_value > rule['value']:
                    rule_triggered = True
                elif rule['condition'] == 'equals' and indicator_value == rule['value']:
                    rule_triggered = True
        
        elif rule['type'] == 'pattern':
            # The pattern_recognizer module must be imported where this function is called
            if rule['function'](df_history):
                rule_triggered = True
        
        elif rule['type'] == 'custom':
            if rule['function'](indicators):
                rule_triggered = True
        
        if rule_triggered:
            rule_score = rule.get('score', 1)
            
            # 2. Volatility-Adjusted Scoring
            # If volatility is HIGH, give a bonus to mean-reversion signals like RSI
            if volatility == 'HIGH' and rule['name'] in ['RSI Oversold', 'RSI Overbought']:
                rule_score += 1
                reasons.append("Volatility Bonus: Signal confirmed in high-volatility market.")
            # If volatility is LOW, give a bonus to trend-following signals like crossovers
            elif volatility == 'LOW' and rule['name'] in ['Golden Cross Event', 'Death Cross Event', 'Bullish MACD Cross']:
                rule_score += 1
                reasons.append("Volatility Bonus: Signal confirmed in low-volatility market.")

            score += rule_score
            reasons.append(rule['message'].format(**indicators))

    return score, reasons

def analyze_for_trade_setup(instrument_token, indicators, df_history=None):
    """
    Enhanced trade setup analyzer with target and stop loss recommendations.
    Returns (setup_found, details, trade_recommendations) tuple.
    """
    setup_found = False
    details = []
    trade_recommendations = {}

    # Enhanced RSI analysis
    if indicators.get('RSI') is not None:
        rsi = indicators['RSI']
        if rsi < 30:
            details.append(f"RSI ({rsi:.2f}) indicates oversold - potential bounce setup.")
            setup_found = True
            trade_recommendations['direction'] = 'BUY'
            trade_recommendations['setup_type'] = 'RSI_OVERSOLD'
        elif rsi > 70:
            details.append(f"RSI ({rsi:.2f}) indicates overbought - potential reversal setup.")
            setup_found = True
            trade_recommendations['direction'] = 'SELL'
            trade_recommendations['setup_type'] = 'RSI_OVERBOUGHT'

    # Enhanced EMA trend analysis
    if indicators.get('EMA50') is not None and indicators.get('EMA200') is not None:
        ema50 = indicators['EMA50']
        ema200 = indicators['EMA200']
        if ema50 > ema200:
            details.append(f"EMA50 ({ema50:.2f}) is above EMA200 ({ema200:.2f}) - bullish trend confirmed.")
            if not trade_recommendations.get('direction'):
                trade_recommendations['direction'] = 'BUY'
            trade_recommendations['trend'] = 'BULLISH'
        else:
            details.append(f"EMA50 ({ema50:.2f}) is below EMA200 ({ema200:.2f}) - bearish trend confirmed.")
            if not trade_recommendations.get('direction'):
                trade_recommendations['direction'] = 'SELL'
            trade_recommendations['trend'] = 'BEARISH'

    # Volume analysis
    if indicators.get('Volume') is not None and indicators['Volume'] > 0:
        volume = indicators['Volume']
        details.append(f"Current Volume: {volume:,.0f}.")
        
        # Check for volume spike
        if df_history is not None and len(df_history) > 20:
            avg_volume = df_history['volume'].tail(20).mean()
            if volume > avg_volume * 1.5:
                details.append(f"Volume spike detected ({volume/avg_volume:.1f}x average)")
                trade_recommendations['volume_confirmation'] = True

    # Calculate targets and stop loss if setup found
    if setup_found and df_history is not None:
        current_price = indicators.get('Close', 0)
        if current_price > 0:
            trade_recommendations.update(calculate_trade_levels(current_price, trade_recommendations.get('direction', 'BUY'), df_history))

    if setup_found:
        print(f"\n🎯 ENHANCED RADAR ALERT for {instrument_token}!")
        for detail in details:
            print(f"- {detail}")
        
        if trade_recommendations:
            print(f"\n📊 Trade Recommendations:")
            print(f"   Direction: {trade_recommendations.get('direction', 'N/A')}")
            if 'entry_price' in trade_recommendations:
                print(f"   Entry: ₹{trade_recommendations['entry_price']:.2f}")
            if 'stop_loss' in trade_recommendations:
                print(f"   Stop Loss: ₹{trade_recommendations['stop_loss']:.2f}")
            if 'target_1' in trade_recommendations:
                print(f"   Target 1: ₹{trade_recommendations['target_1']:.2f}")
            if 'risk_reward' in trade_recommendations:
                print(f"   Risk-Reward: 1:{trade_recommendations['risk_reward']:.2f}")
        print("--------------------------------------")

    return setup_found, details, trade_recommendations

def calculate_trade_levels(current_price, direction, df_history):
    """
    Calculate entry, stop loss, and target levels for trade setup.
    """
    if len(df_history) < 20:
        return {}
    
    # Calculate ATR for volatility measurement
    high = df_history['high'].tail(14)
    low = df_history['low'].tail(14)
    close = df_history['close'].tail(14).shift(1)
    
    tr1 = high - low
    tr2 = abs(high - close)
    tr3 = abs(low - close)
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=14).mean().iloc[-1]
    
    # Calculate support/resistance levels
    recent_high = df_history['high'].tail(20).max()
    recent_low = df_history['low'].tail(20).min()
    
    trade_levels = {
        'entry_price': current_price,
        'atr': atr
    }
    
    if direction.upper() == 'BUY':
        # Bullish trade levels
        trade_levels['stop_loss'] = current_price - (atr * 1.5)
        trade_levels['target_1'] = current_price + (atr * 1.5)  # 1:1 risk-reward
        trade_levels['target_2'] = current_price + (atr * 3)    # 1:2 risk-reward
        trade_levels['target_3'] = recent_high                   # Recent high
        trade_levels['risk_reward'] = 1.0
    else:
        # Bearish trade levels
        trade_levels['stop_loss'] = current_price + (atr * 1.5)
        trade_levels['target_1'] = current_price - (atr * 1.5)  # 1:1 risk-reward
        trade_levels['target_2'] = current_price - (atr * 3)    # 1:2 risk-reward
        trade_levels['target_3'] = recent_low                    # Recent low
        trade_levels['risk_reward'] = 1.0
    
    return trade_levels

def save_alerts_to_db(alerts_to_save, strategy_name):
    """Saves a batch of alerts to the PostgreSQL database, tagging them with a strategy name."""
    if not alerts_to_save:
        print("No alerts to save.")
        return

    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT)
        cur = conn.cursor()

        # This SQL command will INSERT a new alert. If an alert for the same
        # instrument_key and source_strategy already exists, it will UPDATE it.
        sql = """
            INSERT INTO trading_app_radaralert (
                instrument_key, source_strategy, alert_details, indicators, timestamp,
                status, priority, alert_type, notified, expires_at
            )
            VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s)
            ON CONFLICT (instrument_key, source_strategy) DO UPDATE SET
                alert_details = EXCLUDED.alert_details,
                indicators = EXCLUDED.indicators,
                timestamp = NOW(),
                status = EXCLUDED.status,
                priority = EXCLUDED.priority,
                alert_type = EXCLUDED.alert_type,
                notified = EXCLUDED.notified,
                expires_at = EXCLUDED.expires_at;
        """
        
        for alert in alerts_to_save:
            alert_details_with_score = {"score": alert['score'], "reasons": alert['reasons']}
            alert_details_json = json.dumps(alert_details_with_score)
            indicators_json = json.dumps(alert['indicators'], default=str, indent=2)

            # Set defaults for required fields if not present
            status = alert.get('status', 'ACTIVE')
            priority = alert.get('priority', 'MEDIUM')
            alert_type = alert.get('alert_type', 'SCREENING')
            notified = alert.get('notified', False)
            expires_at = alert.get('expires_at', None)
            # psycopg2 will convert None to NULL for expires_at

            values = (
                alert['instrument_key'], strategy_name, alert_details_json, indicators_json,
                status, priority, alert_type, notified, expires_at
            )
            cur.execute(sql, values)

        conn.commit()
        print(f"SUCCESS: Saved/Updated {len(alerts_to_save)} alerts for strategy '{strategy_name}' in the database.")
        print("[DEBUG] Database commit successful.")
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"ERROR saving alerts to database: {error}")
        traceback.print_exc()
    finally:
        if conn is not None:
            conn.close()
            print("[DEBUG] Database connection closed.")
