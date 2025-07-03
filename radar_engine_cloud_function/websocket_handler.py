# websocket_handler.py

import json
import time
import websocket
import pandas as pd

# Import our custom modules
import data_manager
import indicator_calculator
import trade_analyzer

# Import the pre-compiled Protobuf message class
from upstox_client.feeder.proto import MarketDataFeedV3_pb2

# --- WebSocket Callback Functions ---

def on_message(ws, message):
    """Callback executed when a message is received from the WebSocket."""
    try:
        decoded_message = MarketDataFeedV3_pb2.FeedResponse()
        decoded_message.ParseFromString(message)

        if decoded_message.feeds:
            for instrument_key, feed in decoded_message.feeds.items():
                if feed.ltpc:
                    ltpc_data = feed.ltpc
                    tick_data = {
                        'datetime': pd.to_datetime(int(ltpc_data.ltp_timestamp) / 1000, unit='s', utc=True).tz_convert('Asia/Kolkata'),
                        'open': ltpc_data.open_price,
                        'high': ltpc_data.high,
                        'low': ltpc_data.low,
                        'close': ltpc_data.ltp,
                        'volume': ltpc_data.volume
                    }

                    # Update history and get the latest complete DataFrame
                    updated_df = data_manager.update_history_with_tick(instrument_key, tick_data)

                    if not updated_df.empty:
                        # Calculate indicators on the updated data
                        indicators = indicator_calculator.calculate_indicators(updated_df)
                        print(f"  Processed {instrument_key}: Close={indicators.get('Close'):.2f}, Indicators: RSI={indicators.get('RSI', 'N/A'):.2f}")
                        
                        # **FIX:** Pass the updated_df to the analyzer for pattern recognition
                        trade_analyzer.analyze_for_trade_setup(instrument_key, indicators, updated_df)

    except Exception as e:
        print(f"ERROR in on_message: {e}")

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket closed: Code={close_status_code}, Message={close_msg}")

def on_open(ws, instrument_keys_to_subscribe):
    """Callback executed when the WebSocket connection is opened."""
    print("WebSocket connection opened. Sending subscription request...")
    subscription_message = {
        "guid": str(int(time.time() * 1000)),
        "method": "sub",
        "mode": "ltpc",
        "instrumentKeys": instrument_keys_to_subscribe
    }
    ws.send(json.dumps(subscription_message))
    print(f"Subscription message sent for: {instrument_keys_to_subscribe}")

def start_websocket_feed(uri, instrument_keys):
    """Initializes and runs the WebSocket application."""
    print("Connecting to WebSocket...")
    ws_app = websocket.WebSocketApp(
        uri,
        on_open=lambda ws: on_open(ws, instrument_keys), # Use lambda to pass extra args
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    print("Starting WebSocket listener...")
    ws_app.run_forever()
