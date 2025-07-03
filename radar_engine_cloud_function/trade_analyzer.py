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

def analyze_setup(indicators, df_history, rules):
    """
    A generic "Rules Engine" that analyzes indicators and patterns
    based on a provided list of rules.
    """
    if not indicators:
        return 0, []

    score = 0
    reasons = []

    # Loop through each rule and evaluate it
    for rule in rules:
        rule_triggered = False
        
        # --- Process Indicator-based Rules ---
        if rule['type'] == 'indicator':
            indicator_value = indicators.get(rule['indicator'])
            if indicator_value is not None:
                if rule['condition'] == 'less_than' and indicator_value < rule['value']:
                    rule_triggered = True
                elif rule['condition'] == 'greater_than' and indicator_value > rule['value']:
                    rule_triggered = True
                elif rule['condition'] == 'equals' and indicator_value == rule['value']:
                    rule_triggered = True
        
        # --- Process Pattern-based Rules ---
        elif rule['type'] == 'pattern':
            # The rule dictionary contains the actual function to call from the pattern_recognizer module
            if rule['function'](df_history):
                rule_triggered = True
        
        # If the rule was triggered, update the score and reasons
        if rule_triggered:
            score += rule.get('score', 1) # Use the score from the rule, default to 1
            # Use .format(**indicators) to fill in values like {RSI} into the message
            reasons.append(rule['message'].format(**indicators))

    return score, reasons

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
