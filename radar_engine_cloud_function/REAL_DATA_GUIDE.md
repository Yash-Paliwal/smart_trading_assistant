# Real Data System Guide

## Overview

The Real Data System allows you to fetch actual historical market data from Upstox and store it in your Django database for realistic testing and development of the radar scanner outside market hours.

## Features

- **Real Market Data**: Fetch actual OHLCV data from Upstox API
- **Database Storage**: Store data in Django database for persistence
- **Local Caching**: Fast access to frequently used data
- **Intraday Generation**: Generate realistic intraday data for testing
- **Data Quality Validation**: Ensure data integrity and consistency
- **Integration**: Seamless integration with existing scanner components

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Upstox API    │───▶│ Historical Data  │───▶│ Django Database │
│                 │    │    Manager       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ Local Cache      │
                       │ (JSON files)     │
                       └──────────────────┘
```

## Components

### 1. HistoricalDataManager

The main class that handles fetching, storing, and retrieving historical data.

**Key Methods:**
- `fetch_and_store_historical_data()`: Fetch from Upstox and store in DB
- `get_stored_historical_data()`: Retrieve data from DB or cache
- `fetch_multiple_symbols()`: Fetch data for multiple symbols
- `cleanup_old_data()`: Remove old cached data

### 2. IntradayDataGenerator

Generates realistic intraday data for testing scenarios.

**Key Methods:**
- `generate_intraday_data()`: Create intraday OHLCV data
- Supports different scenarios: normal, volatile, trending

### 3. Django Models

**HistoricalData Model:**
```python
class HistoricalData(models.Model):
    instrument_key = models.CharField(max_length=100, db_index=True)
    date = models.DateField(db_index=True)
    open_price = models.FloatField()
    high_price = models.FloatField()
    low_price = models.FloatField()
    close_price = models.FloatField()
    volume = models.BigIntegerField()
```

## Usage

### 1. Basic Data Fetching

```python
from historical_data_manager import HistoricalDataManager

# Initialize manager
manager = HistoricalDataManager()

# Fetch data for a symbol
symbol = "NSE_EQ|INE002A01018"  # Reliance
data = manager.fetch_and_store_historical_data(symbol, days=100)

# Retrieve stored data
data = manager.get_stored_historical_data(symbol, days=50)
```

### 2. Multiple Symbols

```python
# Fetch data for multiple symbols
symbols = [
    "NSE_EQ|INE002A01018",  # Reliance
    "NSE_EQ|INE019A01038",  # HDFC Bank
    "NSE_EQ|INE090A01021"   # ICICI Bank
]

results = manager.fetch_multiple_symbols(symbols, days=100)
```

### 3. Intraday Data Generation

```python
from historical_data_manager import IntradayDataGenerator

generator = IntradayDataGenerator()

# Generate intraday data
intraday_data = generator.generate_intraday_data(
    symbol="RELIANCE",
    date=datetime.now(),
    interval_minutes=5,
    scenario='volatile'
)
```

### 4. Testing with Real Data

```python
from scanner_tester import ScannerTester

# Initialize tester with real data
tester = ScannerTester(use_real_data=True)

# Run backtest with real data
result = tester.run_backtest("NSE_EQ|INE002A01018", scenario='recent', days=100)

# Fetch real data for testing
data_results = tester.fetch_real_data_for_testing(symbols, days=100)
```

## Command Line Tools

### 1. Quick Test Runner

```bash
# Test with real data
python quick_test_runner.py --test real --symbol "NSE_EQ|INE002A01018" --days 30

# Run all tests including real data
python quick_test_runner.py --test all
```

### 2. Real Data Test Script

```bash
# Test the real data system
python test_real_data.py
```

### 3. Development Dashboard

```bash
# Launch dashboard with real data management
python development_dashboard.py
```

## Database Operations

### 1. Django Model Usage

```python
from trading_app.models import HistoricalData

# Store DataFrame in database
HistoricalData.store_dataframe(symbol, df)

# Retrieve data from database
data = HistoricalData.get_data_for_symbol(symbol, days=100)

# Check total records
total_records = HistoricalData.objects.count()
```

### 2. Migration

```bash
# Create migration for HistoricalData model
python manage.py makemigrations trading_app --name add_historical_data

# Apply migration
python manage.py migrate
```

## Data Quality

### Validation Checks

The system includes automatic data quality validation:

1. **OHLC Relationships**: Ensures High ≥ Low, High ≥ Open, High ≥ Close
2. **Date Continuity**: Checks for missing trading days
3. **Price Reasonableness**: Validates price ranges
4. **Volume Validation**: Ensures volume data is reasonable

### Quality Metrics

```python
# Check data quality
def check_data_quality(data):
    issues = []
    
    # OHLC validation
    if (data['high'] < data['low']).any():
        issues.append("High < Low")
    
    # Missing values
    missing_count = data.isnull().sum().sum()
    if missing_count > 0:
        issues.append(f"Missing values: {missing_count}")
    
    return issues
```

## Caching Strategy

### 1. Database Storage
- Primary storage in Django database
- Persistent across sessions
- Supports complex queries

### 2. Local Cache
- JSON files for quick access
- Faster retrieval for frequently used data
- Automatic cleanup of old files

### 3. Cache Management

```python
# Clean up old cache files
manager.cleanup_old_data(days_old=30)

# Check cache status
manager.refresh_data_status()
```

## Error Handling

### Common Issues

1. **API Rate Limits**: Automatic retry with delays
2. **Network Errors**: Graceful fallback to cached data
3. **Data Format Issues**: Validation and correction
4. **Database Errors**: Transaction rollback and logging

### Error Recovery

```python
try:
    data = manager.fetch_and_store_historical_data(symbol, days=100)
except Exception as e:
    print(f"Error fetching data: {e}")
    # Fallback to cached data
    data = manager.get_stored_historical_data(symbol, days=100)
```

## Performance Optimization

### 1. Batch Operations
- Fetch multiple symbols in parallel
- Bulk database operations
- Efficient caching strategies

### 2. Memory Management
- Stream data processing for large datasets
- Automatic cleanup of old data
- Optimized DataFrame operations

### 3. Database Indexing
- Indexed fields for fast queries
- Composite indexes for common queries
- Regular index maintenance

## Best Practices

### 1. Data Fetching
- Use appropriate time periods (30-100 days for testing)
- Implement rate limiting to respect API limits
- Cache frequently used data

### 2. Testing
- Test with real data before market hours
- Validate data quality before use
- Use multiple symbols for comprehensive testing

### 3. Maintenance
- Regular cleanup of old cached data
- Monitor database size and performance
- Update data periodically

## Troubleshooting

### Common Problems

1. **No Data Received**
   - Check Upstox API credentials
   - Verify instrument keys are correct
   - Check network connectivity

2. **Database Errors**
   - Ensure Django migrations are applied
   - Check database permissions
   - Verify model relationships

3. **Performance Issues**
   - Clean up old cache files
   - Optimize database queries
   - Use appropriate data periods

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test with verbose output
manager = HistoricalDataManager()
data = manager.fetch_and_store_historical_data(symbol, days=30, force_refresh=True)
```

## Integration with Scanner

### 1. Scanner Tester Integration

The scanner tester automatically uses real data when available:

```python
# Use real data for testing
tester = ScannerTester(use_real_data=True)
result = tester.run_backtest(symbol, scenario='recent', days=100)
```

### 2. Development Dashboard

The dashboard includes a dedicated tab for real data management:
- Fetch data from Upstox
- Monitor data status
- Clean up old data
- View data quality metrics

### 3. Quick Tests

Real data testing is integrated into the quick test suite:

```bash
# Run real data test
python quick_test_runner.py --test real

# Run all tests including real data
python quick_test_runner.py --test all
```

## Future Enhancements

### Planned Features

1. **Real-time Data**: Live market data integration
2. **Advanced Caching**: Redis-based caching system
3. **Data Analytics**: Built-in data analysis tools
4. **Backtesting Engine**: Historical strategy testing
5. **Data Export**: Export data to various formats

### API Extensions

1. **REST API**: Web-based data access
2. **WebSocket**: Real-time data streaming
3. **GraphQL**: Flexible data querying
4. **Batch Processing**: Large-scale data operations

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review error logs
3. Test with different symbols
4. Verify API credentials
5. Check database connectivity

## Conclusion

The Real Data System provides a robust foundation for testing and developing the radar scanner with actual market data. By combining real historical data with synthetic data generation, you can thoroughly test your strategies and ensure they work correctly before deploying them during market hours. 