# 🚀 API Polling System Setup Guide

## Overview

The API Polling System provides real-time market alerts by continuously monitoring your watchlist during market hours. It's designed to be reliable, efficient, and easy to deploy.

## 🎯 **Key Features**

- **Real-time Monitoring**: Polls every 60 seconds during market hours
- **Smart Scheduling**: Automatically runs pre-market scans and end-of-day reports
- **Enhanced ORB Detection**: Advanced Opening Range Breakout analysis
- **Volume Confirmation**: Validates breakouts with volume analysis
- **Risk-Reward Calculation**: Automatic target and stop-loss recommendations
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Graceful Shutdown**: Handles interruptions safely

## 📋 **System Requirements**

- Python 3.8+
- Virtual environment with required packages
- Upstox API credentials (for production)
- Stable internet connection

## 🛠️ **Installation & Setup**

### 1. **Install Dependencies**
```bash
# Activate virtual environment
source venv/bin/activate

# Install required packages
pip install schedule pandas numpy
```

### 2. **Configure Environment**
```bash
# For production, set your Upstox credentials
export UPSTOX_API_KEY="your_api_key"
export UPSTOX_SECRET_KEY="your_secret_key"
export UPSTOX_REDIRECT_URI="your_redirect_uri"
```

## 🚀 **Usage Options**

### **Option 1: Simple Test Mode (Recommended for Testing)**
```bash
# Run with 30-second intervals in test mode
python simple_realtime_poller.py --test --interval 30
```

### **Option 2: Production Mode**
```bash
# Run with 60-second intervals during market hours
python realtime_poller.py --interval 60
```

### **Option 3: Custom Intervals**
```bash
# Run with 2-minute intervals
python realtime_poller.py --interval 120
```

### **Option 4: Using Startup Script**
```bash
# Use the provided startup script
./start_realtime_poller.sh
```

## 📊 **What the System Does**

### **Pre-Market (9:00 AM)**
- Runs comprehensive pre-market scan
- Updates watchlist with top 50 stocks
- Prepares for intraday monitoring

### **During Market Hours (9:15 AM - 3:30 PM)**
- Monitors watchlist every 60 seconds
- Detects Opening Range Breakouts (ORB)
- Validates breakouts with volume analysis
- Generates real-time alerts with:
  - Entry price
  - Stop loss
  - Target price
  - Risk-reward ratio
  - Volume confirmation

### **End of Day (3:45 PM)**
- Generates comprehensive end-of-day report
- Summarizes alerts and performance
- Prepares for next trading day

## 🎯 **Alert Types**

### **Enhanced ORB (Opening Range Breakout)**
- **Detection**: Price breaks above/below 30-minute opening range
- **Confirmation**: Volume > 120% of average volume
- **Targets**: 1:1 risk-reward ratio by default
- **Stop Loss**: Opposite end of opening range

### **Alert Information**
```
🚨 NEW ALERT: RELIANCE
   Direction: UP
   Entry: ₹1488.33
   Stop Loss: ₹1471.30
   Target: ₹1505.35
   Risk-Reward: 1:1.00
   Volume: ✅ Confirmed
```

## 📈 **Performance Monitoring**

### **Log Files**
- `simple_realtime_poller.log` - Test mode logs
- `realtime_poller.log` - Production mode logs

### **Key Metrics**
- Total alerts generated per day
- Stocks monitored
- Polling cycles completed
- Alert accuracy tracking

## 🔧 **Configuration Options**

### **Polling Intervals**
- **30 seconds**: High-frequency monitoring (test mode)
- **60 seconds**: Standard monitoring (recommended)
- **120 seconds**: Conservative monitoring
- **300 seconds**: Low-frequency monitoring

### **Market Hours**
- **Open**: 9:15 AM IST
- **Close**: 3:30 PM IST
- **Pre-market scan**: 9:00 AM IST
- **End-of-day report**: 3:45 PM IST

## 🚨 **Alert Notifications**

### **Current Implementation**
- Console logging with detailed information
- File-based logging for persistence
- Alert history tracking

### **Future Enhancements**
- Email notifications
- SMS alerts
- Push notifications
- Webhook integrations

## 🛡️ **Safety Features**

### **Rate Limiting**
- 0.5-second delay between stock analysis
- Prevents API overload
- Respects exchange rate limits

### **Error Handling**
- Graceful handling of API failures
- Automatic retry mechanisms
- Fallback to default watchlist

### **Market Hours Check**
- Only runs during market hours
- Respects weekends and holidays
- Automatic shutdown outside trading hours

## 📱 **Integration Options**

### **With Django Backend**
```python
# The full version integrates with Django models
from trading_app.models import RadarAlert

# Store alerts in database
alert = RadarAlert.objects.create(
    instrument_key=instrument_key,
    source_strategy="RealTime_ORB",
    alert_data=alert_data
)
```

### **Standalone Mode**
```python
# Simple version works without Django
# Perfect for testing and development
```

## 🔍 **Troubleshooting**

### **Common Issues**

1. **Import Errors**
   ```bash
   # Ensure virtual environment is activated
   source venv/bin/activate
   ```

2. **API Rate Limits**
   ```bash
   # Increase polling interval
   python realtime_poller.py --interval 120
   ```

3. **Market Hours Issues**
   ```bash
   # Use test mode to bypass market hours
   python simple_realtime_poller.py --test
   ```

### **Log Analysis**
```bash
# Monitor logs in real-time
tail -f simple_realtime_poller.log

# Search for specific alerts
grep "NEW ALERT" simple_realtime_poller.log
```

## 🎯 **Best Practices**

### **For Testing**
1. Use `--test` flag to bypass market hours
2. Start with 30-second intervals
3. Monitor logs for alert generation
4. Verify alert accuracy

### **For Production**
1. Use 60-second intervals for optimal performance
2. Set up proper environment variables
3. Monitor system resources
4. Implement notification system

### **For Development**
1. Use simple version for quick testing
2. Modify alert logic as needed
3. Test with mock data first
4. Gradually integrate with real data

## 📊 **Expected Performance**

### **Processing Speed**
- **5 stocks**: ~3 seconds per cycle
- **50 stocks**: ~25 seconds per cycle
- **100 stocks**: ~50 seconds per cycle

### **Alert Frequency**
- **High volatility**: 5-10 alerts per day
- **Normal market**: 2-5 alerts per day
- **Low volatility**: 0-2 alerts per day

### **Resource Usage**
- **CPU**: Low (< 5% on average)
- **Memory**: ~50MB
- **Network**: ~1MB per cycle

## 🚀 **Next Steps**

1. **Test the system** with mock data
2. **Configure notifications** (email/SMS)
3. **Set up production deployment**
4. **Monitor and optimize** performance
5. **Add custom strategies** as needed

## 📞 **Support**

For issues or questions:
1. Check the logs for error messages
2. Verify environment setup
3. Test with simple mode first
4. Review this guide for configuration options

---

**Happy Trading! 🎯📈** 