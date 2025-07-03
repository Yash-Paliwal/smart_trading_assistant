# main.py

import upstox_client_wrapper
import data_manager
import websocket_handler
import time

def main():
    """
    The main function to orchestrate the radar engine.
    """
    # --- Step 1: Get the instrument keys for NIFTY 100 stocks ---
    print("--- Getting NIFTY 100 Instrument Keys ---")
    
    # **FIX:** Call the correct, updated function name.
    # This function will get symbols for NIFTY 50 & NIFTY NEXT 50, then find their keys.
    nifty100_keys = upstox_client_wrapper.get_nifty_instrument_keys(
        indices=['NIFTY 50', 'NIFTY NEXT 50']
    )

    if not nifty100_keys:
        print("FATAL: Could not retrieve NIFTY instrument list. Exiting.")
        return

    subscribed_instrument_keys = nifty100_keys
    print(f"\n--- Preparing to scan {len(subscribed_instrument_keys)} NIFTY 100 stocks ---")


    # --- Step 2: Initialize historical data for each instrument ---
    print("--- Initializing Historical Data ---")
    for key in subscribed_instrument_keys:
        df = upstox_client_wrapper.fetch_historical_data(
            instrument_key=key,
            interval=1,
            unit='days',
            num_periods=100
        )
        data_manager.initialize_history(key, df)
        time.sleep(0.5) # Add a small delay to respect API rate limits
    print("--- Historical Data Initialization Complete ---")


    # --- Step 3: Get the WebSocket URI ---
    websocket_uri = upstox_client_wrapper.get_websocket_auth_uri()


    # --- Step 4: Start the WebSocket feed if the URI was obtained ---
    if websocket_uri:
        websocket_handler.start_websocket_feed(websocket_uri, subscribed_instrument_keys)
    else:
        print("FATAL: Could not start WebSocket feed because the authorization URI was not obtained.")


if __name__ == "__main__":
    main()
