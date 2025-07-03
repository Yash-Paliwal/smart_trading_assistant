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


def fetch_historical_data(instrument_key, interval=1, unit='days', num_periods=100):
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
            print(f"Successfully fetched {len(df)} historical candles for {instrument_key}.")
            return df
        else:
            print(f"No historical data found for {instrument_key}.")
            return pd.DataFrame()
    except Exception as e:
        print(f"ERROR fetching historical data for {instrument_key}: {e}")
        if hasattr(e, 'body'):
            print(f"HTTP response body: {e.body}")
        return pd.DataFrame()


def get_nifty_instrument_keys(indices=['NIFTY 50', 'NIFTY NEXT 50']):
    """
    Downloads the master list of all tradable instruments and filters it
    to include only the constituents of the specified NIFTY indices.
    Args:
        indices (list): A list of NIFTY indices to get constituents for.
    Returns:
        list: A list of instrument keys for the stocks in the specified indices.
    """
    # URLs for official NSE index constituent lists
    index_urls = {
        'NIFTY 50': 'https://archives.nseindia.com/content/indices/ind_nifty50list.csv',
        'NIFTY NEXT 50': 'https://archives.nseindia.com/content/indices/ind_niftynext50list.csv'
    }

    # **FIX:** Use the MTF instruments list as the master list, as we have confirmed it works.
    upstox_master_url = "https://assets.upstox.com/market-quote/instruments/exchange/MTF.json.gz"
    print(f"Downloading full Upstox instrument master from {upstox_master_url}...")
    try:
        headers = {"Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}"}
        response = requests.get(upstox_master_url, headers=headers)
        response.raise_for_status()
        gzip_file = io.BytesIO(response.content)
        with gzip.open(gzip_file, 'rt') as f:
            instrument_list = json.load(f)
        upstox_df = pd.DataFrame(instrument_list)
    except Exception as e:
        print(f"ERROR: Could not download or parse the Upstox master instrument list: {e}")
        return []

    # Now, fetch the symbols from the requested NIFTY indices
    nifty_symbols = set()
    for index_name in indices:
        if index_name in index_urls:
            url = index_urls[index_name]
            print(f"Fetching {index_name} constituents from {url}...")
            try:
                # NSE website requires a browser-like User-Agent header
                nse_headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=nse_headers)
                response.raise_for_status()
                index_df = pd.read_csv(io.StringIO(response.text))
                # Add all symbols from the 'Symbol' column to our set
                nifty_symbols.update(index_df['Symbol'].tolist())
            except Exception as e:
                print(f"Warning: Could not fetch constituents for {index_name}: {e}")

    if not nifty_symbols:
        print("ERROR: Failed to fetch any NIFTY index constituents.")
        return []

    print(f"Total unique symbols from specified NIFTY indices: {len(nifty_symbols)}")

    # Filter the Upstox master list to find instruments matching the NIFTY symbols
    filtered_df = upstox_df[upstox_df['trading_symbol'].isin(nifty_symbols)]
    
    print(f"Found {len(filtered_df)} matching instruments in Upstox master for the specified NIFTY indices.")
    return filtered_df['instrument_key'].tolist()
