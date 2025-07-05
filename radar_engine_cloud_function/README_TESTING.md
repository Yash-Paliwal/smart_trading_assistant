# 🧪 Radar Scanner Testing & Development Toolkit

This toolkit provides comprehensive testing and development tools for the radar scanner, allowing you to test and iterate on your trading strategies even when the market is closed.

## 🚀 Quick Start

### 1. Setup Environment (First Time Only)
```bash
# Make scripts executable
chmod +x setup_testing_env.sh run_tests.sh activate_env.sh

# Setup virtual environment and install dependencies
./setup_testing_env.sh
```

### 2. Activate Environment (Every Session)
```bash
# Activate virtual environment
./activate_env.sh

# Or manually:
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 3. Run Tests
```bash
# Run all tests
./run_tests.sh all

# Test specific alert types
./run_tests.sh alert RELIANCE

# Test strategy performance
./run_tests.sh strategy RELIANCE BULL_MARKET

# Test indicator calculations
./run_tests.sh indicator TCS

# Launch development dashboard
./run_tests.sh dashboard

# Or run directly (after activating environment):
python quick_test_runner.py --test all
python development_dashboard.py
python scanner_tester.py
```

## 🛠️ Tools Overview

### 1. **Mock Data Generator** (`mock_data_generator.py`)
Generates realistic market data for testing outside market hours.

**Features:**
- ✅ Realistic OHLCV data with proper relationships
- ✅ Multiple market scenarios (Bull, Bear, Sideways, Volatile)
- ✅ Alert-specific data generation (RSI oversold, Golden Cross, etc.)
- ✅ Configurable volatility and trend profiles
- ✅ Support for both daily and intraday data

**Usage:**
```python
from mock_data_generator import MockDataGenerator

generator = MockDataGenerator()

# Generate bull market data
bull_data = generator.generate_daily_candles('RELIANCE', days=100, scenario='BULL_MARKET')

# Generate RSI oversold alert data
rsi_data = generator.generate_alert_scenario('TCS', 'RSI_OVERSOLD')

# Create complete market scenario
scenario = generator.create_market_scenario('VOLATILE', ['RELIANCE', 'TCS', 'HDFCBANK'])
```

### 2. **Scanner Tester** (`scanner_tester.py`)
Comprehensive testing framework for the radar scanner.

**Features:**
- ✅ Backtesting with performance metrics
- ✅ Alert scenario validation
- ✅ Strategy performance comparison
- ✅ Detailed test reports
- ✅ Performance analytics (Sharpe ratio, drawdown, etc.)

**Usage:**
```python
from scanner_tester import ScannerTester

tester = ScannerTester()

# Run backtest
result = tester.run_backtest('RELIANCE', 'BULL_MARKET', days=100)

# Test alert scenarios
alert_results = tester.test_alert_scenarios()

# Run comprehensive test suite
comprehensive_results = tester.run_comprehensive_test()
```

### 3. **Development Dashboard** (`development_dashboard.py`)
Interactive GUI for real-time development and testing.

**Features:**
- ✅ Real-time simulation with adjustable speed
- ✅ Live indicator monitoring
- ✅ Alert history tracking
- ✅ Data generation controls
- ✅ Test execution interface
- ✅ Performance analytics

**Usage:**
```bash
python development_dashboard.py
```

### 4. **Quick Test Runner** (`quick_test_runner.py`)
Command-line tool for rapid testing during development.

**Features:**
- ✅ Single-command test execution
- ✅ Multiple test types (alert, strategy, indicator, data quality)
- ✅ Configurable parameters
- ✅ Quick validation of scanner components

## 📊 Testing Scenarios

### Market Scenarios
1. **BULL_MARKET**: Upward trending market with medium volatility
2. **BEAR_MARKET**: Downward trending market with high volatility
3. **SIDEWAYS**: Range-bound market with low volatility
4. **VOLATILE**: High volatility market with mixed trends

### Alert Types
1. **RSI_OVERSOLD**: Generates data that triggers RSI < 30
2. **GOLDEN_CROSS**: Generates data that creates EMA50 > EMA200 crossover
3. **VOLUME_SPIKE**: Generates data with volume spikes

### Test Types
1. **Data Quality**: Validates OHLC relationships and data consistency
2. **Indicator Calculation**: Verifies all technical indicators are calculated correctly
3. **Alert Detection**: Tests if the scanner can detect specific alert conditions
4. **Strategy Performance**: Evaluates strategy performance across different market conditions

## 🔧 Development Workflow

### During Market Hours
1. **Monitor Real Scanner**: Use the actual scanner with live data
2. **Quick Validation**: Use `quick_test_runner.py` to validate changes
3. **Dashboard Testing**: Use the development dashboard for real-time testing

### Outside Market Hours
1. **Mock Data Testing**: Generate realistic scenarios with `mock_data_generator.py`
2. **Comprehensive Testing**: Run full test suites with `scanner_tester.py`
3. **Strategy Development**: Use the dashboard for interactive development
4. **Performance Analysis**: Analyze strategy performance across different market conditions

## 📈 Performance Metrics

The testing framework calculates several performance metrics:

- **Total Return**: Overall percentage return
- **Annualized Return**: Return annualized to 252 trading days
- **Volatility**: Standard deviation of returns
- **Sharpe Ratio**: Risk-adjusted return measure
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable periods
- **Alert Frequency**: Number of alerts per trading period

## 🎯 Best Practices

### 1. **Regular Testing**
- Run quick tests before deploying changes
- Use comprehensive tests for major updates
- Validate alert scenarios after strategy modifications

### 2. **Data Quality**
- Always verify OHLC relationships
- Check for missing or invalid data
- Validate indicator calculations

### 3. **Performance Monitoring**
- Track strategy performance across different market conditions
- Monitor alert frequency and quality
- Analyze drawdown and risk metrics

### 4. **Development Process**
- Use mock data for initial development
- Validate with real data during market hours
- Maintain test scenarios for regression testing

## 📁 File Structure

```
radar_engine_cloud_function/
├── mock_data_generator.py      # Mock data generation
├── scanner_tester.py           # Comprehensive testing framework
├── development_dashboard.py    # Interactive development GUI
├── quick_test_runner.py        # Command-line quick tests
├── setup_testing_env.sh        # Environment setup script
├── run_tests.sh                # Test runner script
├── activate_env.sh             # Environment activation script
├── test_reports/               # Generated test reports
├── test_scenarios/             # Saved market scenarios
├── venv/                       # Virtual environment
└── README_TESTING.md           # This file
```

## 🚨 Troubleshooting

### Common Issues

1. **Virtual Environment Not Activated**
   ```bash
   # Always activate the virtual environment first
   source venv/bin/activate
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   
   # Or use the provided script
   ./activate_env.sh
   ```

2. **Import Errors**
   ```bash
   # Ensure you're in the correct directory
   cd radar_engine_cloud_function
   
   # Make sure virtual environment is activated
   source venv/bin/activate
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

3. **Missing Dependencies**
   ```bash
   # Run the setup script to install all dependencies
   ./setup_testing_env.sh
   
   # Or manually install
   pip install pandas numpy pandas-ta python-decouple websocket-client protobuf requests
   ```

3. **Data Generation Issues**
   - Check that symbol names match the base prices dictionary
   - Verify scenario names are correct
   - Ensure sufficient data points for indicator calculation

4. **Dashboard Issues**
   - Ensure tkinter is installed
   - Check for threading conflicts
   - Verify data manager initialization

### Getting Help

1. **Check Test Output**: Look for specific error messages in test output
2. **Validate Data**: Use data quality tests to verify mock data
3. **Review Logs**: Check console output for detailed error information
4. **Simplify Tests**: Start with basic tests and gradually increase complexity

## 🎉 Success Indicators

Your scanner is ready for market hours when:

- ✅ All quick tests pass
- ✅ Alert scenarios are detected correctly
- ✅ Indicator calculations are accurate
- ✅ Performance metrics are reasonable
- ✅ No data quality issues
- ✅ Dashboard simulation runs smoothly

## 🔄 Continuous Improvement

1. **Add New Test Scenarios**: Extend the mock data generator for new market conditions
2. **Enhance Performance Metrics**: Add new metrics to the testing framework
3. **Improve Dashboard**: Add new features to the development interface
4. **Automate Testing**: Set up automated test runs for continuous validation

---

**Happy Testing! 🚀**

Remember: The goal is to catch issues before they reach live trading, so test thoroughly and iterate quickly. 