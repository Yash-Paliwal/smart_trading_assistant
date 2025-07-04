# upstox_client_wrapper.py

import requests
import pandas as pd
from decouple import config
from datetime import datetime, timedelta
import io
import gzip
import json

from upstox_client import ApiClient, Configuration
from upstox_client.api.history_v3_api import HistoryV3Api

# --- Configuration ---
UPSTOX_ACCESS_TOKEN = config('UPSTOX_ACCESS_TOKEN', default="YOUR_UPSTOX_ACCESS_TOKEN_HERE")
AUTH_URL = "https://api.upstox.com/v2/feed/market-data-feed/authorize"

# --- Initialize API Clients ---
rest_api_configuration = Configuration()
rest_api_configuration.api_key['Api-Version'] = '2.0'
rest_api_configuration.access_token = UPSTOX_ACCESS_TOKEN

rest_api_client = ApiClient(rest_api_configuration)
historical_candle_api = HistoryV3Api(rest_api_client)


def get_websocket_auth_uri():
    """Obtains the WebSocket authorization URI from Upstox."""
    if UPSTOX_ACCESS_TOKEN == "YOUR_UPSTOX_ACCESS_TOKEN_HERE":
        print("ERROR: UPSTOX_ACCESS_TOKEN is not set in your .env file.")
        return None

    try:
        print("Attempting to obtain WebSocket authorization URI...")
        headers = {"Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}", "Accept": "application/json"}
        response = requests.get(AUTH_URL, headers=headers)
        response.raise_for_status()
        auth_data = response.json()
        websocket_uri = auth_data.get('data', {}).get('authorized_redirect_uri')
        if not websocket_uri:
            raise ValueError(f"authorized_redirect_uri not found in response: {auth_data}")
        print(f"Obtained WebSocket URI: {websocket_uri}")
        return websocket_uri
    except Exception as e:
        print(f"ERROR obtaining WebSocket URI: {e}")
        return None


def fetch_historical_data(instrument_key, interval=1, unit='days', num_periods=250):
    """Fetches historical candle data for a given instrument."""
    print(f"Fetching {interval} {unit} historical data for {instrument_key}...")
    today = pd.Timestamp.now(tz='Asia/Kolkata').date()
    from_date_str = (today - pd.Timedelta(days=num_periods)).strftime('%Y-%m-%d')
    to_date_str = today.strftime('%Y-%m-%d')
    try:
        if unit == 'days':
            response = historical_candle_api.get_historical_candle_data1(
                instrument_key=instrument_key,
                unit='days',
                interval=str(interval),
                to_date=to_date_str,
                from_date=from_date_str
            )
        else:
            print(f"ERROR: Unsupported unit '{unit}' in fetch_historical_data.")
            return pd.DataFrame()

        if response and response.data and response.data.candles:
            candles_data = [{'datetime': pd.to_datetime(c[0]), 'open': c[1], 'high': c[2], 'low': c[3], 'close': c[4], 'volume': c[5]} for c in response.data.candles]
            df = pd.DataFrame(candles_data)
            df.set_index('datetime', inplace=True)
            df.sort_index(inplace=True)
            # print(f"Successfully fetched {len(df)} historical candles for {instrument_key}.")
            return df
        else:
            # print(f"No historical data found for {instrument_key}.")
            return pd.DataFrame()
    except Exception as e:
        # print(f"ERROR fetching historical data for {instrument_key}: {e}")
        return pd.DataFrame()


def get_equity_instrument_keys():
    """
    Downloads the master list of all tradable equity instruments from Upstox.
    This function no longer relies on external NSE sources.
    Returns:
        list: A list of instrument keys for all tradable equity stocks.
    """
    # We will use the MTF list as it contains a broad range of liquid stocks.
    upstox_master_url = "https://assets.upstox.com/market-quote/instruments/exchange/MTF.json.gz"
    print(f"Downloading instrument master list from Upstox: {upstox_master_url}...")
    try:
        headers = {"Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}"}
        response = requests.get(upstox_master_url, headers=headers)
        response.raise_for_status()
        
        gzip_file = io.BytesIO(response.content)
        with gzip.open(gzip_file, 'rt') as f:
            instrument_list = json.load(f)
        
        upstox_df = pd.DataFrame(instrument_list)
        
        # Filter for standard equity instruments
        equity_df = upstox_df[upstox_df['instrument_type'] == 'EQUITY']

        print(f"Found {len(equity_df)} tradable equity stocks in the Upstox master list.")
        return equity_df['instrument_key'].tolist()

    except Exception as e:
        print(f"ERROR: Could not download or parse the Upstox master instrument list: {e}")
        return []
