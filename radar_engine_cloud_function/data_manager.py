# data_manager.py

import pandas as pd

# This dictionary will hold the historical data for each instrument.
# Key: instrument_key (str), Value: pandas DataFrame of historical candles.
market_data_history = {}

def initialize_history(instrument_key, historical_df):
    """Initializes or replaces the historical data for a given instrument."""
    if not historical_df.empty:
        market_data_history[instrument_key] = historical_df.copy()
    else:
        market_data_history[instrument_key] = pd.DataFrame()
        print(f"WARNING: Initial historical data for {instrument_key} is empty.")

def update_history_with_tick(instrument_key, tick_data):
    """
    Updates the historical DataFrame for an instrument with a new tick.
    This function appends the tick and keeps the DataFrame size limited.
    Returns the updated DataFrame.
    """
    if instrument_key not in market_data_history:
        print(f"WARNING: Cannot update history for {instrument_key}. No initial data.")
        return pd.DataFrame()

    df_history = market_data_history[instrument_key]

    # Convert tick data to a pandas Series and then to a single-row DataFrame
    new_series = pd.Series(tick_data).to_frame().T
    new_series['datetime'] = pd.to_datetime(new_series['datetime'])
    new_series.set_index('datetime', inplace=True)
    new_series = new_series.astype({
        'open': float, 'high': float, 'low': float, 'close': float, 'volume': float
    })

    # Append new data and handle duplicates by keeping the last entry for a given timestamp
    updated_df = pd.concat([df_history, new_series])
    updated_df = updated_df[~updated_df.index.duplicated(keep='last')]
    updated_df.sort_index(inplace=True)

    # Keep only the last 200 data points for performance
    updated_df = updated_df.tail(200)

    # Update the master dictionary
    market_data_history[instrument_key] = updated_df

    return updated_df

def get_history(instrument_key):
    """Retrieves the historical DataFrame for a given instrument."""
    return market_data_history.get(instrument_key, pd.DataFrame())
