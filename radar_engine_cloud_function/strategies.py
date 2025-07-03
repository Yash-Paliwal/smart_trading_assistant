# strategies.py

import pattern_recognizer

# This is the master list of all available screening rules.
ALL_RULES = [
    {
        "name": "RSI Oversold",
        "type": "indicator", "signal": "bullish",
        "indicator": "RSI", "condition": "less_than", "value": 30,
        "message": "RSI is oversold at {RSI:.2f}.", "score": 1
    },
    {
        "name": "RSI Overbought",
        "type": "indicator", "signal": "bearish",
        "indicator": "RSI", "condition": "greater_than", "value": 70,
        "message": "RSI is overbought at {RSI:.2f}.", "score": 1
    },
    {
        "name": "Volume Spike",
        "type": "indicator", "signal": "neutral", # Can confirm both bullish and bearish moves
        "indicator": "Volume_Spike", "condition": "equals", "value": True,
        "message": "Significant volume spike detected.", "score": 1
    },
    {
        "name": "Golden Cross Event",
        "type": "indicator", "signal": "bullish",
        "indicator": "Crossover", "condition": "equals", "value": "Golden",
        "message": "Bullish 'Golden Cross' (50-EMA over 200-EMA) occurred.", "score": 2
    },
    {
        "name": "Death Cross Event",
        "type": "indicator", "signal": "bearish",
        "indicator": "Crossover", "condition": "equals", "value": "Death",
        "message": "Bearish 'Death Cross' (50-EMA under 200-EMA) occurred.", "score": 2
    },
    {
        "name": "Bullish MACD Cross",
        "type": "indicator", "signal": "bullish",
        "indicator": "MACD_Crossover", "condition": "equals", "value": "Bullish",
        "message": "Bullish MACD Crossover occurred.", "score": 1
    },
    {
        "name": "Bearish MACD Cross",
        "type": "indicator", "signal": "bearish",
        "indicator": "MACD_Crossover", "condition": "equals", "value": "Bearish",
        "message": "Bearish MACD Crossover occurred.", "score": 1
    },
    {
        "name": "Bullish Engulfing Pattern",
        "type": "pattern", "signal": "bullish",
        "function": pattern_recognizer.detect_bullish_engulfing,
        "message": "A 'Bullish Engulfing' pattern was detected.", "score": 1
    },
    {
        "name": "Hammer Pattern",
        "type": "pattern", "signal": "bullish",
        "function": pattern_recognizer.detect_hammer,
        "message": "A 'Hammer' reversal pattern was detected.", "score": 1
    }
]

# Here we define our new, specialized strategies.
STRATEGIES = {
    "Bullish_Scan": [
        rule['name'] for rule in ALL_RULES if rule['signal'] in ['bullish', 'neutral']
    ],
    "Bearish_Scan": [
        rule['name'] for rule in ALL_RULES if rule['signal'] in ['bearish', 'neutral']
    ],
    "Full_Scan": [rule['name'] for rule in ALL_RULES] # A fallback that uses all rules
}

def get_rules_for_strategy(strategy_name):
    """
    Returns the list of rule dictionaries for a given strategy name.
    """
    rule_names = STRATEGIES.get(strategy_name, [])
    rules_dict = {rule['name']: rule for rule in ALL_RULES}
    return [rules_dict[name] for name in rule_names if name in rules_dict]

