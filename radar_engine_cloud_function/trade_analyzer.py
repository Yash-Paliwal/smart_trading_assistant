# trade_analyzer.py

import psycopg2
from decouple import config
import json

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
    Simple trade setup analyzer that checks basic indicator conditions.
    Returns (setup_found, details) tuple.
    """
    setup_found = False
    details = []

    if indicators.get('RSI') is not None:
        if indicators['RSI'] < 30:
            details.append(f"RSI ({indicators['RSI']:.2f}) indicates oversold.")
            setup_found = True
        elif indicators['RSI'] > 70:
            details.append(f"RSI ({indicators['RSI']:.2f}) indicates overbought.")
            setup_found = True

    if indicators.get('EMA50') is not None and indicators.get('EMA200') is not None:
        if indicators['EMA50'] > indicators['EMA200']:
            details.append(f"EMA50 ({indicators['EMA50']:.2f}) is above EMA200 ({indicators['EMA200']:.2f}) - potentially bullish trend.")
            setup_found = True
        else:
            details.append(f"EMA50 ({indicators['EMA50']:.2f}) is below EMA200 ({indicators['EMA200']:.2f}) - potentially bearish trend.")
            setup_found = True

    if indicators.get('Volume') is not None and indicators['Volume'] > 0:
        details.append(f"Current Volume: {indicators['Volume']:,.0f}.")

    if setup_found:
        print(f"\n--- RADAR ALERT for {instrument_token}! ---")
        for detail in details:
            print(f"- {detail}")
        print("--------------------------------------")

    return setup_found, details

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
            INSERT INTO trading_app_radaralert (instrument_key, source_strategy, alert_details, indicators, timestamp)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (instrument_key, source_strategy) DO UPDATE SET
                alert_details = EXCLUDED.alert_details,
                indicators = EXCLUDED.indicators,
                timestamp = NOW();
        """
        
        for alert in alerts_to_save:
            alert_details_with_score = {"score": alert['score'], "reasons": alert['reasons']}
            alert_details_json = json.dumps(alert_details_with_score)
            indicators_json = json.dumps(alert['indicators'], default=str, indent=2)
            
            values = (alert['instrument_key'], strategy_name, alert_details_json, indicators_json)
            cur.execute(sql, values)

        conn.commit()
        print(f"SUCCESS: Saved/Updated {len(alerts_to_save)} alerts for strategy '{strategy_name}' in the database.")
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"ERROR saving alerts to database: {error}")
    finally:
        if conn is not None:
            conn.close()
