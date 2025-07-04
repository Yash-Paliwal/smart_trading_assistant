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
    df_with_indicators.ta.rsi(length=14, append=True)
    df_with_indicators.ta.ema(length=20, append=True) # Add 20-day EMA for pullback strategy
    df_with_indicators.ta.ema(length=50, append=True)
    df_with_indicators.ta.ema(length=200, append=True)
    df_with_indicators.ta.macd(append=True)
    df_with_indicators.ta.bbands(append=True) # Add Bollinger Bands
    df_with_indicators.ta.ema(length=10, name="VOL_EMA_10", close='volume', append=True)

    # Extract latest and previous day's data
    latest = df_with_indicators.iloc[-1]
    previous = df_with_indicators.iloc[-2]

    # --- Extract Raw Indicator Values ---
    indicators['RSI'] = latest.get('RSI_14')
    indicators['EMA20'] = latest.get('EMA_20')
    indicators['EMA50'] = latest.get('EMA_50')
    indicators['EMA200'] = latest.get('EMA_200')
    indicators['MACD'] = latest.get('MACD_12_26_9')
    indicators['MACD_Signal'] = latest.get('MACDs_12_26_9')
    indicators['BB_Lower'] = latest.get('BBL_20_2.0') # Lower Bollinger Band
    indicators['BB_Upper'] = latest.get('BBU_20_2.0') # Upper Bollinger Band
    indicators['BB_Width'] = latest.get('BBB_20_2.0') # Bollinger Band Width
    indicators['Volume'] = latest.get('volume')
    indicators['Close'] = latest.get('close')
    indicators['Low'] = latest.get('low') # For pullback check

    # --- Generate Discrete Signals ---

    # Volume Spike Signal
    avg_volume = latest.get('VOL_EMA_10')
    indicators['Volume_Spike'] = bool(avg_volume and indicators['Volume'] and indicators['Volume'] > (avg_volume * 1.5))

    # EMA Crossover Signal
    indicators['Crossover'] = 'None'
    if all(k in indicators and indicators[k] is not None for k in ['EMA50', 'EMA200']) and all(k in previous and previous[k] is not None for k in ['EMA_50', 'EMA_200']):
        if previous['EMA_50'] <= previous['EMA_200'] and indicators['EMA50'] > indicators['EMA200']:
            indicators['Crossover'] = 'Golden'
        elif previous['EMA_50'] >= previous['EMA_200'] and indicators['EMA50'] < indicators['EMA200']:
            indicators['Crossover'] = 'Death'

    # MACD Crossover Signal
    indicators['MACD_Crossover'] = 'None'
    if all(k in indicators and indicators[k] is not None for k in ['MACD', 'MACD_Signal']) and all(k in previous and previous[k] is not None for k in ['MACD_12_26_9', 'MACDs_12_26_9']):
        if previous['MACD_12_26_9'] <= previous['MACDs_12_26_9'] and indicators['MACD'] > indicators['MACD_Signal']:
            indicators['MACD_Crossover'] = 'Bullish'
        elif previous['MACD_12_26_9'] >= previous['MACDs_12_26_9'] and indicators['MACD'] < indicators['MACD_Signal']:
            indicators['MACD_Crossover'] = 'Bearish'

    return indicators
