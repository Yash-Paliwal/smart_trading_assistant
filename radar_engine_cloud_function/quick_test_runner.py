# quick_test_runner.py

import argparse
import sys
import os
import time
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
import mock_data_generator
import historical_data_manager
import scanner_tester
import indicator_calculator
import trade_analyzer
import data_manager

def quick_alert_test(symbol="RELIANCE", alert_type="RSI_OVERSOLD"):
    """
    Quick test to verify that specific alerts are working.
    
    Args:
        symbol (str): Stock symbol to test
        alert_type (str): Type of alert to test
    """
    print(f"\n🔍 Quick Alert Test: {symbol} - {alert_type}")
    print("=" * 50)
    
    generator = mock_data_generator.MockDataGenerator()
    
    # Generate alert-specific data
    data = generator.generate_alert_scenario(symbol, alert_type)
    
    if data.empty:
        print("❌ Failed to generate test data")
        return False
    
    # Initialize data manager
    data_manager.initialize_history(symbol, data)
    
    # Test the last few days
    test_days = data.tail(5)
    alerts_found = 0
    
    for i, (date, row) in enumerate(test_days.iterrows()):
        current_data = data.iloc[:len(data)-len(test_days)+i+1]
        
        # Calculate indicators
        indicators = indicator_calculator.calculate_indicators(current_data)
        
        # Check for trade setup
        setup_found, details = trade_analyzer.analyze_for_trade_setup(
            symbol, indicators, current_data
        )
        
        if setup_found:
            alerts_found += 1
            print(f"✅ Alert found on {date.strftime('%Y-%m-%d')}: {details}")
        else:
            print(f"⏭️  No alert on {date.strftime('%Y-%m-%d')}")
    
    print(f"\n📊 Results: {alerts_found}/{len(test_days)} days triggered alerts")
    return alerts_found > 0

def quick_strategy_test(symbol="RELIANCE", scenario="BULL_MARKET", days=30):
    """
    Quick test to verify strategy performance in different market conditions.
    
    Args:
        symbol (str): Stock symbol to test
        scenario (str): Market scenario
        days (int): Number of days to simulate
    """
    print(f"\n📈 Quick Strategy Test: {symbol} - {scenario}")
    print("=" * 50)
    
    generator = mock_data_generator.MockDataGenerator()
    tester = scanner_tester.ScannerTester()
    
    # Run backtest
    result = tester.run_backtest(symbol, scenario, days)
    
    if 'error' in result:
        print(f"❌ Test failed: {result['error']}")
        return False
    
    # Display results
    print(f"📊 Total alerts generated: {result['alerts_generated']}")
    
    if 'performance_metrics' in result:
        metrics = result['performance_metrics']
        print(f"📈 Total return: {metrics.get('total_return', 0):.2%}")
        print(f"📊 Sharpe ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"📉 Max drawdown: {metrics.get('max_drawdown', 0):.2%}")
    
    # Show recent alerts
    if result['alerts']:
        print(f"\n🚨 Recent alerts:")
        for alert in result['alerts'][-3:]:  # Last 3 alerts
            print(f"  {alert['date'].strftime('%Y-%m-%d')}: {alert['details']}")
    
    return True

def quick_indicator_test(symbol="RELIANCE"):
    """
    Quick test to verify indicator calculations are working correctly.
    
    Args:
        symbol (str): Stock symbol to test
    """
    print(f"\n📊 Quick Indicator Test: {symbol}")
    print("=" * 50)
    
    generator = mock_data_generator.MockDataGenerator()
    
    # Generate data (need at least 200 trading days for EMA200, so use 400 calendar days)
    data = generator.generate_daily_candles(symbol, days=400, scenario='SIDEWAYS')
    
    if data.empty:
        print("❌ Failed to generate test data")
        return False
    
    # Calculate indicators
    indicators = indicator_calculator.calculate_indicators(data)
    
    # Display indicator values
    print("📈 Current Indicator Values:")
    for key, value in indicators.items():
        if value is not None:
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        else:
            print(f"  {key}: None")
    
    # Verify key indicators are present
    required_indicators = ['RSI', 'EMA50', 'EMA200', 'Close']
    missing_indicators = [ind for ind in required_indicators if ind not in indicators or indicators[ind] is None]
    
    if missing_indicators:
        print(f"⚠️  Missing indicators: {missing_indicators}")
        return False
    else:
        print("✅ All required indicators calculated successfully")
        return True

def quick_data_quality_test():
    """
    Quick test to verify data generation quality.
    """
    print(f"\n🔍 Quick Data Quality Test")
    print("=" * 50)
    
    generator = mock_data_generator.MockDataGenerator()
    
    # Test different scenarios
    scenarios = ['BULL_MARKET', 'BEAR_MARKET', 'SIDEWAYS', 'VOLATILE']
    symbols = ['RELIANCE', 'TCS', 'HDFCBANK']
    
    for scenario in scenarios:
        print(f"\n📊 Testing {scenario} scenario:")
        
        for symbol in symbols:
            data = generator.generate_daily_candles(symbol, days=30, scenario=scenario)
            
            if data.empty:
                print(f"  ❌ {symbol}: Failed to generate data")
                continue
            
            # Check data quality
            price_range = data['close'].max() - data['close'].min()
            avg_price = data['close'].mean()
            price_change = (data['close'].iloc[-1] / data['close'].iloc[0]) - 1
            
            print(f"  ✅ {symbol}: {len(data)} days, Price range: {price_range:.2f}, Change: {price_change:.2%}")
            
            # Verify OHLC relationships
            invalid_ohlc = ((data['high'] < data['low']) | 
                           (data['high'] < data['open']) | 
                           (data['high'] < data['close']) |
                           (data['low'] > data['open']) | 
                           (data['low'] > data['close'])).sum()
            
            if invalid_ohlc > 0:
                print(f"    ⚠️  {invalid_ohlc} invalid OHLC relationships")
            else:
                print(f"    ✅ All OHLC relationships valid")
    
    return True

def quick_real_data_test(symbol="NSE_EQ|INE002A01018", days=30):
    """
    Quick test using real historical data from Upstox.
    
    Args:
        symbol (str): Stock symbol (Upstox instrument key)
        days (int): Number of days to test
    """
    print(f"\n📊 Quick Real Data Test: {symbol}")
    print("=" * 50)
    
    try:
        # Initialize historical data manager
        manager = historical_data_manager.HistoricalDataManager()
        
        # Fetch real data
        print(f"📥 Fetching {days} days of real data...")
        data = manager.fetch_and_store_historical_data(symbol, days=days, force_refresh=False)
        
        if data.empty:
            print("❌ No data received from Upstox")
            return False
        
        print(f"✅ Fetched {len(data)} days of real data")
        print(f"   Date range: {data.index.min()} to {data.index.max()}")
        print(f"   Price range: {data['low'].min():.2f} - {data['high'].max():.2f}")
        print(f"   Latest close: {data['close'].iloc[-1]:.2f}")
        
        # Test indicators on real data
        print(f"\n📈 Testing indicators on real data...")
        indicators = indicator_calculator.calculate_indicators(data)
        
        # Display key indicators
        key_indicators = ['RSI', 'EMA50', 'EMA200', 'Close']
        for indicator in key_indicators:
            if indicator in indicators and indicators[indicator] is not None:
                print(f"   {indicator}: {indicators[indicator]:.2f}")
            else:
                print(f"   {indicator}: Not available")
        
        # Test trade analysis
        print(f"\n🔍 Testing trade analysis...")
        setup_found, details = trade_analyzer.analyze_for_trade_setup(
            symbol, indicators, data
        )
        
        if setup_found:
            print(f"✅ Trade setup detected: {details}")
        else:
            print(f"⏭️  No trade setup detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in real data test: {e}")
        return False

def run_comprehensive_quick_test():
    """
    Runs all quick tests in sequence.
    """
    print("🚀 Starting Comprehensive Quick Test Suite")
    print("=" * 60)
    
    start_time = time.time()
    test_results = []
    
    # Test 1: Data Quality
    print("\n1️⃣ Testing Data Quality...")
    data_quality_ok = quick_data_quality_test()
    test_results.append(('Data Quality', data_quality_ok))
    
    # Test 2: Indicator Calculation
    print("\n2️⃣ Testing Indicator Calculation...")
    indicator_ok = quick_indicator_test()
    test_results.append(('Indicator Calculation', indicator_ok))
    
    # Test 3: Alert Detection
    print("\n3️⃣ Testing Alert Detection...")
    alert_ok = quick_alert_test()
    test_results.append(('Alert Detection', alert_ok))
    
    # Test 4: Strategy Performance
    print("\n4️⃣ Testing Strategy Performance...")
    strategy_ok = quick_strategy_test()
    test_results.append(('Strategy Performance', strategy_ok))
    
    # Test 5: Real Data (if available)
    print("\n5️⃣ Testing Real Data...")
    real_data_ok = quick_real_data_test()
    test_results.append(('Real Data', real_data_ok))
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n📋 Test Summary")
    print("=" * 60)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(test_results)} tests passed")
    print(f"⏱️  Duration: {duration:.2f} seconds")
    
    if passed == len(test_results):
        print("🎉 All tests passed! Scanner is ready for market hours.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == len(test_results)

def main():
    """
    Main function to handle command line arguments and run tests.
    """
    parser = argparse.ArgumentParser(description='Quick test runner for the radar scanner')
    parser.add_argument('--test', choices=['alert', 'strategy', 'indicator', 'data', 'real', 'all'], 
                       default='all', help='Type of test to run')
    parser.add_argument('--symbol', default='RELIANCE', help='Stock symbol to test')
    parser.add_argument('--scenario', default='SIDEWAYS', 
                       choices=['BULL_MARKET', 'BEAR_MARKET', 'SIDEWAYS', 'VOLATILE'],
                       help='Market scenario to test')
    parser.add_argument('--alert-type', default='RSI_OVERSOLD',
                       choices=['RSI_OVERSOLD', 'GOLDEN_CROSS', 'VOLUME_SPIKE'],
                       help='Type of alert to test')
    parser.add_argument('--days', type=int, default=30, help='Number of days to simulate')
    
    args = parser.parse_args()
    
    print(f"🔧 Radar Scanner Quick Test Runner")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.test == 'all':
        success = run_comprehensive_quick_test()
    elif args.test == 'alert':
        success = quick_alert_test(args.symbol, args.alert_type)
    elif args.test == 'strategy':
        success = quick_strategy_test(args.symbol, args.scenario, args.days)
    elif args.test == 'indicator':
        success = quick_indicator_test(args.symbol)
    elif args.test == 'data':
        success = quick_data_quality_test()
    elif args.test == 'real':
        success = quick_real_data_test(args.symbol, args.days)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 