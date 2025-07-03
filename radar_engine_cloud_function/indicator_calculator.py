# indicator_calculator.py

import pandas as pd
import pandas_ta as ta

def calculate_indicators(df):
    """
    Calculates technical indicators from a DataFrame of candle data.
    This now includes RSI, EMAs, Volume Spike, MACD, and EMA Crossover signals.

    Args:
        df (pd.DataFrame): The DataFrame containing OHLCV data.

    Returns:
        dict: A dictionary containing the calculated indicator values and signals.
    """
    if df.empty or len(df) < 2: # Need at least 2 data points for comparisons
        return {}

    indicators = {}
    
    # Use a copy to avoid SettingWithCopyWarning
    df_with_indicators = df.copy()

    # --- Standard Indicators ---
    df_with_indicators.ta.rsi(length=14, append=True)
    df_with_indicators.ta.ema(length=50, append=True)
    df_with_indicators.ta.ema(length=200, append=True)
    df_with_indicators.ta.macd(append=True)
    df_with_indicators.ta.ema(length=10, name="VOL_EMA_10", close='volume', append=True)

    # Extract latest and previous day's data
    latest = df_with_indicators.iloc[-1]
    previous = df_with_indicators.iloc[-2]

    # --- Extract Indicator Values ---
    indicators['RSI'] = latest.get('RSI_14')
    indicators['EMA50'] = latest.get('EMA_50')
    indicators['EMA200'] = latest.get('EMA_200')
    indicators['MACD'] = latest.get('MACD_12_26_9')
    indicators['MACD_Signal'] = latest.get('MACDs_12_26_9')
    indicators['Volume'] = latest.get('volume')
    indicators['Close'] = latest.get('close')

    # --- Signal 1: Volume Spike ---
    avg_volume = latest.get('VOL_EMA_10')
    if avg_volume and indicators['Volume'] and indicators['Volume'] > (avg_volume * 1.5):
        indicators['Volume_Spike'] = True
    else:
        indicators['Volume_Spike'] = False

    # --- Signal 2: EMA Crossover ---
    prev_ema50 = previous.get('EMA_50')
    prev_ema200 = previous.get('EMA_200')
    
    indicators['Crossover'] = 'None'
    if prev_ema50 is not None and prev_ema200 is not None and indicators['EMA50'] is not None and indicators['EMA200'] is not None:
        if prev_ema50 <= prev_ema200 and indicators['EMA50'] > indicators['EMA200']:
            indicators['Crossover'] = 'Golden'
        elif prev_ema50 >= prev_ema200 and indicators['EMA50'] < indicators['EMA200']:
            indicators['Crossover'] = 'Death'

    # --- Signal 3: MACD Crossover ---
    prev_macd = previous.get('MACD_12_26_9')
    prev_macd_signal = previous.get('MACDs_12_26_9')

    indicators['MACD_Crossover'] = 'None'
    if prev_macd is not None and prev_macd_signal is not None and indicators['MACD'] is not None and indicators['MACD_Signal'] is not None:
        if prev_macd <= prev_macd_signal and indicators['MACD'] > indicators['MACD_Signal']:
            indicators['MACD_Crossover'] = 'Bullish'
        elif prev_macd >= prev_macd_signal and indicators['MACD'] < indicators['MACD_Signal']:
            indicators['MACD_Crossover'] = 'Bearish'

    return indicators
