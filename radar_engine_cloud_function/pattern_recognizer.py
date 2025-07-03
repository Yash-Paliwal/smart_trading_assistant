# pattern_recognizer.py

import pandas as pd

def detect_bullish_engulfing(df):
    """
    Checks if the last candle in the DataFrame is a Bullish Engulfing pattern.
    This pattern occurs after a downtrend and suggests a potential reversal upwards.

    Args:
        df (pd.DataFrame): The DataFrame of historical data (must have at least 2 rows).
                           It requires 'open', 'high', 'low', 'close' columns.

    Returns:
        bool: True if a Bullish Engulfing pattern is detected, False otherwise.
    """
    if len(df) < 2:
        return False

    last_candle = df.iloc[-1]
    previous_candle = df.iloc[-2]

    # Rule 1: The last candle must be bullish (green).
    is_last_bullish = last_candle['close'] > last_candle['open']

    # Rule 2: The previous candle must be bearish (red).
    is_previous_bearish = previous_candle['close'] < previous_candle['open']

    # Rule 3: The body of the last (bullish) candle must completely "engulf" the
    # body of the previous (bearish) candle.
    engulfs = (last_candle['open'] <= previous_candle['close']) and \
              (last_candle['close'] >= previous_candle['open'])

    if is_last_bullish and is_previous_bearish and engulfs:
        return True
    
    return False


def detect_hammer(df):
    """
    Checks if the last candle is a Hammer pattern.
    This is a bullish reversal pattern that often appears at the bottom of a downtrend.

    Args:
        df (pd.DataFrame): The DataFrame of historical data.

    Returns:
        bool: True if a Hammer pattern is detected, False otherwise.
    """
    if len(df) < 1:
        return False

    last_candle = df.iloc[-1]
    
    # Calculate the size of the body, upper wick, and lower wick
    body_size = abs(last_candle['close'] - last_candle['open'])
    if body_size == 0: return False # Dojis are not hammers, avoid division by zero.

    upper_wick = last_candle['high'] - max(last_candle['open'], last_candle['close'])
    lower_wick = min(last_candle['open'], last_candle['close']) - last_candle['low']

    # Rule 1: The lower wick must be at least twice the size of the body.
    is_long_lower_wick = lower_wick >= 2 * body_size

    # Rule 2: The upper wick must be very small or non-existent.
    is_small_upper_wick = upper_wick < body_size
    
    if is_long_lower_wick and is_small_upper_wick:
        return True

    return False

# You can add more pattern detection functions here in the future.
