# indicator_calculator.py

import pandas as pd
import pandas_ta as ta

def calculate_indicators(df):
    """
    Calculates a comprehensive set of technical indicators from a DataFrame.
    """
    if df.empty or len(df) < 2:
        return {}

    indicators = {}
    df_with_indicators = df.copy()

    # --- Calculate All Indicators ---
    try:
        df_with_indicators.ta.rsi(length=14, append=True)
    except Exception:
        pass
    try:
        df_with_indicators.ta.ema(length=20, append=True) # Add 20-day EMA for pullback strategy
    except Exception:
        pass
    try:
        df_with_indicators.ta.ema(length=50, append=True)
    except Exception:
        pass
    try:
        df_with_indicators.ta.ema(length=200, append=True)
    except Exception:
        pass
    try:
        df_with_indicators.ta.macd(append=True)
    except Exception:
        pass
    try:
        df_with_indicators.ta.bbands(append=True) # Add Bollinger Bands
    except Exception:
        pass
    try:
        df_with_indicators.ta.ema(length=10, name="VOL_EMA_10", close='volume', append=True)
    except Exception:
        pass

    # Extract latest and previous day's data
    latest = df_with_indicators.iloc[-1]
    previous = df_with_indicators.iloc[-2]

    # --- Extract Raw Indicator Values ---
    def safe_get(val):
        try:
            if pd.isna(val):
                return None
            return float(val)
        except Exception:
            return None

    indicators['RSI'] = safe_get(latest.get('RSI_14'))
    indicators['EMA20'] = safe_get(latest.get('EMA_20'))
    indicators['EMA50'] = safe_get(latest.get('EMA_50'))
    indicators['EMA200'] = safe_get(latest.get('EMA_200'))
    indicators['MACD'] = safe_get(latest.get('MACD_12_26_9'))
    indicators['MACD_Signal'] = safe_get(latest.get('MACDs_12_26_9'))
    indicators['BB_Lower'] = safe_get(latest.get('BBL_20_2.0')) # Lower Bollinger Band
    indicators['BB_Upper'] = safe_get(latest.get('BBU_20_2.0')) # Upper Bollinger Band
    indicators['BB_Width'] = safe_get(latest.get('BBB_20_2.0')) # Bollinger Band Width
    indicators['Volume'] = safe_get(latest.get('volume'))
    indicators['Close'] = safe_get(latest.get('close'))
    indicators['Low'] = safe_get(latest.get('low')) # For pullback check

    # --- Generate Discrete Signals ---
    # Volume Spike Signal
    avg_volume = safe_get(latest.get('VOL_EMA_10'))
    indicators['Volume_Spike'] = bool(avg_volume and indicators['Volume'] and indicators['Volume'] > (avg_volume * 1.5)) if avg_volume and indicators['Volume'] else False

    # EMA Crossover Signal
    indicators['Crossover'] = 'None'
    # (Add more robust logic here if needed)

    return indicators
