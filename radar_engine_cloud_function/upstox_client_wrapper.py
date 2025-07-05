# upstox_client_wrapper.py

import requests
import pandas as pd
from decouple import config
from datetime import datetime, timedelta
import io
import gzip
import json
import logging

# --- Upstox Client Imports ---
from upstox_client import ApiClient, Configuration
from upstox_client.api.history_v3_api import HistoryV3Api
from upstox_client.rest import ApiException

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
UPSTOX_ACCESS_TOKEN = config('UPSTOX_ACCESS_TOKEN', default="YOUR_UPSTOX_ACCESS_TOKEN_HERE")

# --- Initialize API Clients ---
try:
    rest_api_configuration = Configuration()
    rest_api_configuration.api_key['Api-Version'] = '2.0'
    rest_api_configuration.access_token = UPSTOX_ACCESS_TOKEN
    api_client = ApiClient(rest_api_configuration)
    historical_api = HistoryV3Api(api_client)
except Exception as e:
    logging.error(f"Failed to initialize Upstox API client: {e}")
    historical_api = None


def fetch_historical_data(instrument_key: str, interval: str = '1', unit: str = 'days', num_periods: int = 250) -> pd.DataFrame:
    """
    Fetches historical daily candle data for a given instrument.
    """
    if not historical_api:
        logging.error("Historical API client is not initialized. Cannot fetch data.")
        return pd.DataFrame()

    logging.info(f"Fetching historical data for {instrument_key}...")
    
    today = pd.Timestamp.now(tz='Asia/Kolkata').date()
    from_date_str = (today - pd.Timedelta(days=num_periods)).strftime('%Y-%m-%d')
    to_date_str = today.strftime('%Y-%m-%d')
    
    try:
        response = historical_api.get_historical_candle_data1(
            instrument_key=instrument_key,
            unit=unit,
            interval=interval,
            to_date=to_date_str,
            from_date=from_date_str
        )
        if response and response.data and response.data.candles:
            candles_data = [{'datetime': pd.to_datetime(c[0]), 'open': c[1], 'high': c[2], 'low': c[3], 'close': c[4], 'volume': c[5]} for c in response.data.candles]
            df = pd.DataFrame(candles_data)
            df.set_index('datetime', inplace=True)
            df.sort_index(inplace=True)
            return df
        else:
            return pd.DataFrame()
    except ApiException as e:
        logging.warning(f"Upstox API error fetching historical data for {instrument_key}: {e.status} - {e.reason}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"An unexpected error occurred fetching historical data for {instrument_key}: {e}")
        return pd.DataFrame()


def fetch_intraday_data(instrument_key: str, unit: str = 'minutes', interval: str = '5') -> pd.DataFrame:
    """
    Fetches intraday candle data for the current day for a given instrument.

    Args:
        instrument_key (str): The Upstox instrument key (format: EXCHANGE|SYMBOL).
        unit (str): The time unit ('minutes', 'hours', or 'days').
        interval (str): The time interval (e.g., '5').

    Returns:
        pd.DataFrame: Intraday OHLCV data.
    """
    if not historical_api:
        logging.error("Historical API client is not initialized. Cannot fetch data.")
        return pd.DataFrame()

    # Validate input
    valid_units = {'minutes': range(1, 301), 'hours': range(1, 6), 'days': [1]}
    if unit not in valid_units:
        logging.error(f"[fetch_intraday_data] Invalid unit '{unit}'. Must be one of {list(valid_units.keys())}.")
        return pd.DataFrame()

    try:
        interval_int = int(interval)
    except ValueError:
        logging.error(f"[fetch_intraday_data] Interval '{interval}' is not a valid integer.")
        return pd.DataFrame()

    if interval_int not in valid_units[unit]:
        logging.error(f"[fetch_intraday_data] Invalid interval '{interval}' for unit '{unit}'.")
        return pd.DataFrame()

    try:
        logging.info(f"[fetch_intraday_data] Fetching intraday data for {instrument_key} ({interval} {unit})...")
        api_response = historical_api.get_intra_day_candle_data(
            instrument_key=instrument_key,
            unit=unit,
            interval=interval
        )

        if api_response and api_response.data and api_response.data.candles:
            candles_data = [
                {
                    'datetime': pd.to_datetime(c[0]),
                    'open': c[1],
                    'high': c[2],
                    'low': c[3],
                    'close': c[4],
                    'volume': c[5]
                }
                for c in api_response.data.candles
            ]
            df = pd.DataFrame(candles_data)
            df.set_index('datetime', inplace=True)
            df.sort_index(inplace=True)
            return df
        else:
            logging.warning(f"[fetch_intraday_data] No data returned for {instrument_key}.")
            return pd.DataFrame()

    except ApiException as e:
        logging.warning(f"[fetch_intraday_data] Upstox API error for {instrument_key}: {e.status} - {e.reason}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"[fetch_intraday_data] Unexpected error for {instrument_key}: {e}")
        return pd.DataFrame()




def get_equity_instrument_keys() -> list:
    """
    Downloads the master list of all tradable equity instruments from Upstox.
    """
    upstox_master_url = "https://assets.upstox.com/market-quote/instruments/exchange/MTF.json.gz"
    logging.info(f"Downloading instrument master list from Upstox: {upstox_master_url}")
    try:
        headers = {"Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}"}
        response = requests.get(upstox_master_url, headers=headers)
        response.raise_for_status()
        
        gzip_file = io.BytesIO(response.content)
        with gzip.open(gzip_file, 'rt') as f:
            instrument_list = json.load(f)
        
        upstox_df = pd.DataFrame(instrument_list)
        equity_df = upstox_df[upstox_df['instrument_type'] == 'EQ']

        logging.info(f"Found {len(equity_df)} tradable equity stocks in the Upstox master list.")
        return equity_df['instrument_key'].tolist()
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error downloading master instrument list: {e}")
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred parsing the master instrument list: {e}")
        return []
