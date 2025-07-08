# Scanning API Guide

## 🎯 **Overview**

The "Scan Now" button in the UI now triggers **actual scanning** of the market instead of just refreshing existing data. This provides real-time market analysis and generates fresh alerts based on current market conditions.

## 🔄 **How "Scan Now" Works**

### **1. Button States**
- **"Scan Now"** - Ready to scan
- **"Scanning..."** - Currently running scan
- **"Market Closed"** - Cannot scan entry alerts outside market hours
- **"Refreshing..."** - Loading results after scan

### **2. Scan Process**
1. **User clicks "Scan Now"**
2. **API call** to `/api/trigger-scan/`
3. **Actual scanning** runs (screening + intraday)
4. **Results displayed** with new alerts count
5. **UI refreshes** to show new alerts

## 🚀 **API Endpoint: `/api/trigger-scan/`**

### **Request Format**
```json
{
  "scan_type": "comprehensive",  // "comprehensive", "screening", "intraday"
  "market_hours": true           // true/false based on current time
}
```

### **Response Format**
```json
{
  "success": true,
  "scan_type": "comprehensive",
  "market_hours": true,
  "scan_duration": 45.2,
  "stocks_scanned": 210,
  "new_alerts": 5,
  "total_alerts": 15,
  "scan_results": [
    {
      "type": "screening",
      "success": true,
      "alerts_found": 3,
      "stocks_scanned": 200,
      "message": "Premarket scan completed successfully"
    },
    {
      "type": "intraday",
      "success": true,
      "alerts_found": 2,
      "stocks_scanned": 10,
      "message": "Intraday scan completed successfully"
    }
  ],
  "timestamp": "2024-01-15T10:30:00"
}
```

## 📊 **Scan Types**

### **1. Comprehensive Scan (`comprehensive`)**
- **Runs both** screening and intraday scans
- **Screening**: Always runs (200 stocks)
- **Intraday**: Only during market hours (watchlist stocks)
- **Best for**: Complete market analysis

### **2. Screening Only (`screening`)**
- **Runs only** premarket scanner
- **Scans**: 200 Nifty stocks
- **Generates**: Screening alerts (static)
- **Best for**: Market trend analysis

### **3. Intraday Only (`intraday`)**
- **Runs only** intraday scanner
- **Scans**: Watchlist stocks (top 10 from screening)
- **Generates**: Entry alerts (time-sensitive)
- **Best for**: Real-time trading opportunities
- **Note**: Only available during market hours

## 🔧 **Technical Implementation**

### **1. Django View (`trigger_scan`)**
```python
@api_view(['POST'])
def trigger_scan(request):
    # Get scan parameters
    scan_type = data.get('scan_type', 'comprehensive')
    market_hours = data.get('market_hours', False)
    
    # Count alerts before scan
    current_alerts_count = RadarAlert.objects.filter(
        status='ACTIVE',
        expires_at__gt=datetime.now()
    ).count()
    
    # Run scans based on type
    if scan_type == 'comprehensive':
        # Run both screening and intraday
        scan_commands = ['screening']
        if market_hours:
            scan_commands.append('intraday')
    
    # Execute scans and collect results
    scan_results = []
    for scan_command in scan_commands:
        if scan_command == 'screening':
            result = run_premarket_scanner()
        elif scan_command == 'intraday':
            result = run_intraday_scanner()
    
    # Calculate new alerts
    new_alerts_count = RadarAlert.objects.filter(
        status='ACTIVE',
        expires_at__gt=datetime.now()
    ).count()
    new_alerts = new_alerts_count - current_alerts_count
    
    return Response({
        'success': True,
        'new_alerts': max(0, new_alerts),
        'scan_results': scan_results,
        # ... other fields
    })
```

### **2. Production System Integration**
```python
# Command-line interface for individual scans
python production_system.py --premarket-scan
python production_system.py --intraday-scan
python production_system.py --production
```

### **3. Scanner Functions**
```python
def run_premarket_scanner():
    """Run premarket scanner and return results"""
    alerts = run_premarket_scanner()  # From premarket_scanner.py
    return {
        'success': True,
        'alerts_found': len(alerts),
        'stocks_scanned': 200,
        'scan_duration': scan_duration
    }

def run_intraday_scanner():
    """Run intraday scanner and return results"""
    watchlist = get_watchlist_from_database()
    alerts = run_intraday_scanner(watchlist=watchlist)
    return {
        'success': True,
        'alerts_found': len(alerts),
        'stocks_scanned': len(watchlist),
        'scan_duration': scan_duration
    }
```

## 🎨 **UI Integration**

### **1. React Component Updates**
```javascript
// Enhanced refresh function
const handleManualRefresh = async () => {
  if (isRefreshDisabled()) return;
  
  setIsRefreshing(true);
  setLoading(true);
  
  // Trigger actual scan instead of just refreshing data
  await triggerScan();
};

// Scan trigger function
const triggerScan = async () => {
  setIsScanning(true);
  setScanResults(null);
  
  try {
    const response = await fetch('/api/trigger-scan/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scan_type: 'comprehensive',
        market_hours: marketStatus.isOpen
      })
    });
    
    const scanData = await response.json();
    setScanResults(scanData);
    
    // Refresh alerts after scan
    await fetchPageData();
    
  } catch (err) {
    setError(`Scan failed: ${err.message}`);
  } finally {
    setIsScanning(false);
  }
};
```

### **2. Scan Results Display**
```javascript
{/* Scan Results Notification */}
{scanResults && (
  <div className="mb-8">
    <div className={`glass p-4 rounded-xl border max-w-2xl mx-auto ${
      scanResults.new_alerts > 0 
        ? 'border-green-500 bg-green-900/20' 
        : 'border-blue-500 bg-blue-900/20'
    }`}>
      <div className="flex items-center justify-center space-x-3">
        {scanResults.new_alerts > 0 ? (
          <svg className="w-6 h-6 text-green-400">✓</svg>
        ) : (
          <svg className="w-6 h-6 text-blue-400">ℹ</svg>
        )}
        <div className="text-center">
          <p className="font-semibold text-green-400">Scan Completed</p>
          <p className="text-sm text-gray-400">
            {scanResults.new_alerts > 0 
              ? `${scanResults.new_alerts} new alerts found` 
              : 'No new alerts found'
            }
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Scanned {scanResults.stocks_scanned} stocks in {scanResults.scan_duration}s
          </p>
        </div>
      </div>
    </div>
  </div>
)}
```

## 📈 **Performance Considerations**

### **1. Scan Duration**
- **Screening scan**: ~30-60 seconds (200 stocks)
- **Intraday scan**: ~10-20 seconds (10 stocks)
- **Comprehensive scan**: ~40-80 seconds total

### **2. Rate Limiting**
- **Manual scans**: No limit (user-controlled)
- **Auto-refresh**: Every 30 seconds (configurable)
- **Market-aware**: Only during market hours for entry alerts

### **3. Error Handling**
- **Timeout**: 2 minutes for API calls
- **Retry logic**: Automatic retry on failure
- **Fallback**: Graceful degradation if scan fails

## 🧪 **Testing**

### **1. Test Script**
```bash
# Run test script
python test_scan_api.py
```

### **2. Manual Testing**
```bash
# Test individual scans
python radar_engine_cloud_function/production_system.py --premarket-scan
python radar_engine_cloud_function/production_system.py --intraday-scan

# Test API endpoint
curl -X POST http://localhost:8000/api/trigger-scan/ \
  -H "Content-Type: application/json" \
  -d '{"scan_type": "comprehensive", "market_hours": true}'
```

## 🎯 **Use Cases**

### **1. Market Open (9:15 AM - 3:30 PM)**
- **Comprehensive scan**: Screening + intraday alerts
- **Screening scan**: Market trend analysis
- **Intraday scan**: Real-time trading opportunities

### **2. Market Closed**
- **Screening scan**: Available (static analysis)
- **Intraday scan**: Disabled (requires live data)
- **Comprehensive scan**: Screening only

### **3. Weekend**
- **All scans**: Available in test mode
- **Data source**: Historical data
- **Purpose**: Strategy testing and validation

## 🔄 **Workflow Integration**

### **1. Production System**
- **9:00 AM**: Automatic premarket scan
- **9:15 AM**: Market opens, real-time polling starts
- **Manual scans**: Available throughout the day
- **3:30 PM**: Market closes, entry scans disabled

### **2. User Workflow**
1. **Check market status** (navbar indicator)
2. **Click "Scan Now"** for fresh analysis
3. **View scan results** (notification)
4. **Review new alerts** (automatically loaded)
5. **Create trade plans** (for promising setups)

## 🚀 **Benefits**

1. **Real-time Analysis**: Fresh market data and insights
2. **User Control**: Manual scanning when needed
3. **Market Awareness**: Smart behavior based on market hours
4. **Performance**: Efficient scanning with progress feedback
5. **Integration**: Seamless UI/API integration
6. **Reliability**: Error handling and fallback mechanisms

This scanning API provides a powerful way to get fresh market insights and generate new trading opportunities on demand! 🎯 