# radar_core.py

import requests
import json
import websocket
import threading
import time
import pandas as pd
import pandas_ta as ta

from decouple import config

from upstox_client.feeder.proto import MarketDataFeedV3_pb2
from upstox_client.api.history_v3_api import HistoryV3Api
from upstox_client import ApiClient, Configuration


UPSTOX_ACCESS_TOKEN = config('UPSTOX_ACCESS_TOKEN', default="YOUR_UPSTOX_ACCESS_TOKEN_HERE")
if UPSTOX_ACCESS_TOKEN == "YOUR_UPSTOX_ACCESS_TOKEN_HERE":
    print("WARNING: Please update UPSTOX_ACCESS_TOKEN in your .env file with your actual Upstox Access Token.")

rest_api_configuration = Configuration()
rest_api_configuration.api_key['Api-Version'] = '2.0'
rest_api_configuration.access_token = UPSTOX_ACCESS_TOKEN

rest_api_client = ApiClient(rest_api_configuration)
historical_candle_api = HistoryV3Api(rest_api_client)

AUTH_URL = "https://api.upstox.com/v2/feed/market-data-feed/authorize"

market_data_history = {}

def fetch_historical_data(instrument_key, interval=1, num_days=100): # Default interval to 1 (integer)
    today = pd.Timestamp.now(tz='Asia/Kolkata').date()
    from_date_str = (today - pd.Timedelta(days=num_days)).strftime('%Y-%m-%d')
    to_date_str = today.strftime('%Y-%m-%d')

    print(f"Fetching {interval} historical data for {instrument_key} from {from_date_str} to {to_date_str}...")
    try:
        # Corrected parameters based on the provided table:
        # unit='days' (lowercase string), interval=1 (integer)
        response = historical_candle_api.get_historical_candle_data1(
            instrument_key=instrument_key,
            unit='days',           # Changed unit to 'days' (lowercase per table)
            interval=interval,     # interval is 1 (integer) for 1 day
            to_date=to_date_str,
            from_date=from_date_str
        )

        if response and response.data and response.data.candles:
            candles_data = []
            for candle in response.data.candles:
                candles_data.append({
                    'datetime': pd.to_datetime(candle[0]),
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                })
            df = pd.DataFrame(candles_data)
            df.set_index('datetime', inplace=True)
            df.sort_index(inplace=True)
            print(f"Successfully fetched {len(df)} historical candles for {instrument_key}.")
            return df
        else:
            print(f"No historical data found for {instrument_key} for interval {interval}.")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching historical data for {instrument_key}: {e}")
        return pd.DataFrame()

def update_and_calculate_indicators(instrument_token, current_data_point, df_history):
    new_series = pd.Series(current_data_point).to_frame().T
    new_series['datetime'] = pd.to_datetime(new_series['datetime'])
    new_series.set_index('datetime', inplace=True)
    new_series = new_series.astype({'open': float, 'high': float, 'low': float, 'close': float, 'volume': float})

    updated_df = pd.concat([df_history, new_series])
    updated_df = updated_df.drop_duplicates(keep='last')
    updated_df.sort_index(inplace=True)
    updated_df = updated_df.tail(200)

    indicators = {}

    if len(updated_df) >= 14:
        rsi_series = ta.rsi(updated_df['close'], length=14)
        indicators['RSI'] = rsi_series.iloc[-1] if not rsi_series.empty else None

    if len(updated_df) >= 50:
        ema50_series = ta.ema(updated_df['close'], length=50)
        indicators['EMA50'] = ema50_series.iloc[-1] if not ema50_series.empty else None
    if len(updated_df) >= 200:
        ema200_series = ta.ema(updated_df['close'], length=200)
        indicators['EMA200'] = ema200_series.iloc[-1] if not ema200_series.empty else None

    indicators['Volume'] = current_data_point.get('volume')

    return updated_df, indicators

def analyze_for_trade_setup(instrument_token, indicators):
    setup_found = False
    details = []

    if indicators.get('RSI') is not None:
        if indicators['RSI'] < 30:
            details.append(f"RSI ({indicators['RSI']:.2f}) indicates oversold.")
            setup_found = True
        elif indicators['RSI'] > 70:
            details.append(f"RSI ({indicators['RSI']:.2f}) indicates overbought.")
            setup_found = True

    if indicators.get('EMA50') is not None and indicators.get('EMA200') is not None:
        if indicators['EMA50'] > indicators['EMA200']:
            details.append(f"EMA50 ({indicators['EMA50']:.2f}) is above EMA200 ({indicators['EMA50']:.2f}) - potentially bullish trend.")
            setup_found = True
        else:
            details.append(f"EMA50 ({indicators['EMA50']:.2f}) is below EMA200 ({indicators['EMA200']:.2f}) - potentially bearish trend.")
            setup_found = True

    if indicators.get('Volume') is not None and indicators['Volume'] > 0:
        details.append(f"Current Volume: {indicators['Volume']}.")

    if setup_found:
        print(f"\n--- RADAR ALERT for {instrument_token}! ---")
        for detail in details:
            print(f"- {detail}")
        print("--------------------------------------")

    return setup_found, details

def on_message(ws, message):
    try:
        decoded_message = MarketDataFeedV3_pb2.FeedResponse()
        decoded_message.ParseFromString(message)

        if decoded_message.feeds:
            for feed in decoded_message.feeds:
                if feed.ltpc_feed:
                    ltpc_data = feed.ltpc_feed
                    instrument_token = ltpc_data.instrument_token
                    current_ltp = ltpc_data.ltp

                    current_data_point = {
                        'datetime': pd.to_datetime(ltpc_data.timestamp, unit='ms', utc=True).tz_convert('Asia/Kolkata'),
                        'open': ltpc_data.open_price,
                        'high': ltpc_data.high,
                        'low': ltpc_data.low,
                        'close': ltpc_data.ltp,
                        'volume': ltpc_data.volume
                    }

                    if instrument_token not in market_data_history:
                        print(f"WARNING: Historical data for {instrument_token} not initialized during startup. Skipping indicator calculation for this tick.")
                        continue

                    updated_df, indicators = update_and_calculate_indicators(
                        instrument_token,
                        current_data_point,
                        market_data_history[instrument_token]
                    )
                    market_data_history[instrument_token] = updated_df

                    print(f"  Processed {instrument_token}: Current LTP={current_ltp}, Indicators: {indicators}")
                    analyze_for_trade_setup(instrument_token, indicators)

                elif feed.full_feed:
                    full_data = feed.full_feed
                    print(f"  Full Feed for Instrument Token {full_data.instrument_token}: LTP={full_data.ltp}, BidPrice={full_data.bid_price}, AskPrice={full_data.ask_price}, Vol={full_data.volume}")

        elif decoded_message.message_type:
            print(f"Control Message Type: {decoded_message.message_type}")
            if decoded_message.message_type == MarketDataFeedV3_pb2.FeedResponse.MESSAGE_TYPE_SUCCESS:
                print("Subscription successful acknowledgment received.")
            elif decoded_message.message_type == MarketDataFeedV3_pb2.FeedResponse.MESSAGE_TYPE_ERROR:
                print(f"Error message from feed: {decoded_message.error_message}")
            elif decoded_message.message_type == MarketDataFeedV3_pb2.FeedResponse.MESSAGE_TYPE_PING:
                print("Received PING from server.")
            elif decoded_message.message_type == MarketDataFeedV3_pb2.FeedResponse.MESSAGE_TYPE_PONG:
                print("Received PONG from server.")


    except Exception as e:
        print(f"Error decoding Protobuf message or processing data: {e}")

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket closed: Code={close_status_code}, Message={close_msg}")

def on_open(ws):
    print("WebSocket connection opened. Sending subscription request...")
    subscription_message = {
        "guid": str(int(time.time() * 1000)),
        "method": "sub",
        "mode": "ltpc",
        "instrumentKeys": [
            "NSE_EQ|INE002A01018",
            "NSE_EQ|INE019A01038"
        ]
    }
    ws.send(json.dumps(subscription_message))
    print(f"Subscription message sent for mode '{subscription_message['mode']}' and keys {subscription_message['instrumentKeys']}.")

def on_ping(ws, message):
    pass

def on_pong(ws, message):
    pass

def run_market_data_feed():
    subscribed_instrument_keys = [
        "NSE_EQ|INE002A01018",
        "NSE_EQ|INE019A01038"
    ]
    for key in subscribed_instrument_keys:
        df = fetch_historical_data(key, interval=1, num_days=100)
        if not df.empty:
            market_data_history[key] = df
        else:
            print(f"Initial historical data fetch failed for {key}. Indicators for this instrument might be inaccurate or unavailable.")

    if not UPSTOX_ACCESS_TOKEN or UPSTOX_ACCESS_TOKEN == "YOUR_UPSTOX_ACCESS_TOKEN_HERE":
        print("Error: UPSTOX_ACCESS_TOKEN not set or default. Please provide your Upstox API access token in .env.")
        return

    websocket_uri = None
    try:
        print("Attempting to obtain WebSocket authorization URI...")
        headers = {
            "Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}",
            "Accept": "application/json"
        }
        response = requests.get(AUTH_URL, headers=headers)
        response.raise_for_status()
        auth_data = response.json()
        websocket_uri = auth_data.get('data', {}).get('authorized_redirect_uri')
        if not websocket_uri:
            raise ValueError(f"authorized_redirect_uri not found in response: {auth_data}")
        print(f"Obtained WebSocket URI: {websocket_uri}")
    except requests.exceptions.RequestException as e:
        print(f"Error obtaining WebSocket URI: {e}. Please check your access token and network connection.")
        if hasattr(e, 'response') and e.response is not None:
            print(f"API Response: {e.response.text}")
        return
    except ValueError as e:
        print(f"Parsing error: {e}")
        return

    print("Connecting to WebSocket...")
    ws_app = websocket.WebSocketApp(
        websocket_uri,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_ping=on_ping,
        on_pong=on_pong
    )

    print("Starting WebSocket run_forever (this will block execution until closed)...")
    ws_app.run_forever()

if __name__ == "__main__":
    run_market_data_feed()
