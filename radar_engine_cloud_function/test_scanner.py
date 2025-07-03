# test_scanner.py

import pandas as pd
import time

# Import our custom modules
import upstox_client_wrapper
import indicator_calculator
import trade_analyzer

def run_backtest(instrument_key):
    """
    Runs a historical backtest for a single instrument to test the scanner logic.
    """
    print(f"\n--- Starting Backtest for {instrument_key} ---")

    # 1. Fetch a good amount of historical data to serve as our test bed
    # We fetch more data initially (e.g., 300 days) so that our indicators (like EMA 200)
    # have enough data to be accurate even on the first day of our test period.
    historical_df = upstox_client_wrapper.fetch_historical_data(
        instrument_key=instrument_key,
        interval=1,
        unit='days',
        num_periods=300
    )

    if historical_df.empty or len(historical_df) < 200:
        print(f"Not enough historical data to perform a meaningful backtest for {instrument_key}. Exiting.")
        return

    # We will simulate the last 100 days
    test_period_df = historical_df.tail(100)

    # The initial 'history' for our indicators will be the data *before* our test period begins
    initial_history_df = historical_df.head(len(historical_df) - 100)
    
    print(f"Simulating the last {len(test_period_df)} trading days...")

    # 2. Loop through each day in our test period
    for index, today_candle in test_period_df.iterrows():
        # 'today_candle' represents the data for the current day we are simulating.
        # It includes the 'open', 'high', 'low', 'close', and 'volume'.

        # The history for calculation is everything up to the day *before* the current simulated day
        history_for_calc = initial_history_df.copy()

        # Calculate indicators based on the history available *before* today's candle
        indicators = indicator_calculator.calculate_indicators(history_for_calc)

        # Analyze these indicators for a trade setup
        # We pass the full history (including today's candle) for pattern recognition
        trade_analyzer.analyze_for_trade_setup(
            instrument_key,
            indicators,
            pd.concat([history_for_calc, today_candle.to_frame().T])
        )

        # After analysis, add today's candle to the history for the next day's simulation
        initial_history_df = pd.concat([initial_history_df, today_candle.to_frame().T])

    print(f"--- Backtest for {instrument_key} Complete ---")


def main():
    """
    Main function to run tests on a list of stocks.
    """
    # Let's test our logic on a few interesting stocks
    stocks_to_test = [
        "NSE_EQ|INE002A01018",  # Reliance
        "NSE_EQ|INE019A01038",  # HDFC Bank
        "NSE_EQ|INE090A01021"   # ICICI Bank
    ]

    for instrument in stocks_to_test:
        run_backtest(instrument)
        time.sleep(1) # Pause between tests to respect API rate limits


if __name__ == "__main__":
    main()

