# 🚨 Alert Lifecycle Management System

## 📋 **Overview**

The Alert Lifecycle Management System provides a complete solution for real-time market alerts with automatic expiration, priority management, and user interface updates.

## 🎯 **Complete Alert Flow**

### **1. Alert Generation (Production Real-Time Poller)**
```
Real-time Poller → ORB Detection → Alert Creation → Database Storage
```

**Location**: `radar_engine_cloud_function/production_realtime_poller.py`

**Process**:
- Monitors watchlist stocks every 60 seconds
- Detects Opening Range Breakouts (ORB)
- Creates alerts with 45-minute expiration
- Saves to database with lifecycle metadata

**Alert Data Structure**:
```python
{
    "instrument_key": "NSE_EQ|INE002A01018",
    "source_strategy": "RealTime_ORB",
    "alert_details": {
        "score": 2,
        "reasons": ["Enhanced ORB: Price broke UP the 30-min opening range"],
        "indicators": {
            "Entry_Price": 1488.33,
            "Stop_Loss": 1471.30,
            "Target": 1505.35,
            "Risk_Reward": 1.0,
            "Volume_Confirmation": true,
            "Direction": "UP"
        }
    },
    "status": "ACTIVE",
    "expires_at": "2025-07-05T10:30:00Z",
    "priority": "HIGH",
    "alert_type": "ORB",
    "notified": false
}
```

### **2. Database Storage (Django Models)**
```
RadarAlert Model → Lifecycle Fields → Automatic Expiration
```

**Location**: `django_api/trading_app/models.py`

**New Fields Added**:
- `status`: ACTIVE, EXPIRED, CANCELLED
- `expires_at`: When alert expires (45 minutes for ORB)
- `priority`: HIGH, MEDIUM, LOW (based on volume confirmation)
- `notified`: Whether user has been notified
- `alert_type`: ORB, BREAKOUT, REVERSAL, etc.

**Lifecycle Methods**:
```python
alert.is_expired()  # Check if expired
alert.mark_as_expired()  # Mark as expired
alert.get_remaining_time()  # Get minutes until expiration
```

### **3. Alert Cleanup (Django Management Command)**
```
Scheduled Task → Expire Old Alerts → Delete Old Expired → Database Cleanup
```

**Location**: `django_api/trading_app/management/commands/cleanup_expired_alerts.py`

**Commands**:
```bash
# Mark expired alerts
python manage.py cleanup_expired_alerts --expire-old

# Delete old expired alerts (24+ hours)
python manage.py cleanup_expired_alerts --delete-expired

# Show current status
python manage.py cleanup_expired_alerts
```

### **4. API Endpoints (Django Views)**
```
Frontend Request → Filtered Queries → Lifecycle Data → JSON Response
```

**Location**: `django_api/trading_app/views.py`

**Enhanced Features**:
- Filter by status: `?status=ACTIVE|EXPIRED|ALL`
- Filter by strategy: `?strategy=RealTime_ORB`
- Filter by alert type: `?alert_type=ORB`
- Automatic remaining time calculation
- Priority-based sorting

**API Response**:
```json
{
    "results": [
        {
            "id": 123,
            "instrument_key": "NSE_EQ|INE002A01018",
            "tradingsymbol": "RELIANCE",
            "status": "ACTIVE",
            "priority": "HIGH",
            "alert_type": "ORB",
            "remaining_minutes": 32,
            "expires_at": "2025-07-05T10:30:00Z",
            "alert_details": {...},
            "indicators": {...}
        }
    ]
}
```

### **5. Frontend Display (React Components)**
```
Real-time Updates → Lifecycle UI → Auto-refresh → Expiration Handling
```

**Location**: `react_frontend/src/pages/AlertsPage.js`

**Features**:
- **Auto-refresh**: 15s, 30s, 1m, 2m intervals
- **Real-time status**: Last update time
- **Priority sorting**: HIGH → MEDIUM → LOW
- **Time-based sorting**: Urgent alerts first
- **Automatic cleanup**: Remove expired alerts from UI

**Location**: `react_frontend/src/components/AlertCard.js`

**Features**:
- **Countdown timer**: Real-time remaining time
- **Priority badges**: Color-coded priority levels
- **Alert type badges**: ORB, BREAKOUT, etc.
- **Expiration handling**: Disable actions when expired
- **ORB-specific display**: Entry, Stop Loss, Target, Risk/Reward

## ⏰ **Alert Lifecycle Timeline**

### **Alert Generation (0 minutes)**
- Real-time poller detects ORB setup
- Alert created with 45-minute expiration
- Priority set based on volume confirmation
- Status: ACTIVE

### **Alert Display (0-45 minutes)**
- Frontend shows alert with countdown timer
- User can create trade plans
- Auto-refresh keeps data current
- Priority and urgency indicators

### **Alert Expiration (45 minutes)**
- Alert status changes to EXPIRED
- Frontend removes from active alerts
- Trade plan creation disabled
- Alert moved to expired list

### **Alert Cleanup (24+ hours)**
- Expired alerts deleted from database
- Database cleanup to prevent bloat
- Historical data preserved in logs

## 🎨 **User Interface Features**

### **Real-time Status Bar**
```
Last updated: 2:30:45 PM    [✓] Auto-refresh    [30s ▼]    [Refresh Now]
```

### **Alert Priority System**
- **🔴 HIGH**: Volume confirmation + strong breakout
- **🟡 MEDIUM**: Standard breakout
- **🔵 LOW**: Weak breakout

### **Countdown Timer**
- **🟢 Green**: >15 minutes remaining
- **🟠 Orange**: 5-15 minutes remaining  
- **🔴 Red**: <5 minutes remaining
- **⚫ Gray**: Expired

### **ORB-Specific Display**
```
Entry Price: ₹1488.33    Stop Loss: ₹1471.30    Target: ₹1505.35    Risk/Reward: 1:1.00
```

## 🔧 **Configuration Options**

### **Alert Expiration Times**
```python
# In production_realtime_poller.py
expires_at = timezone.now() + timedelta(minutes=45)  # ORB alerts
```

### **Cleanup Schedule**
```bash
# Cron job for automatic cleanup
*/5 * * * * python manage.py cleanup_expired_alerts --expire-old
0 2 * * * python manage.py cleanup_expired_alerts --delete-expired
```

### **Frontend Refresh Intervals**
```javascript
// In AlertsPage.js
const refreshIntervals = [15, 30, 60, 120]; // seconds
```

## 📊 **Monitoring & Analytics**

### **Alert Statistics**
```bash
# Check current alert status
python manage.py cleanup_expired_alerts

# Output:
Alert Status: 5 active, 12 expired, 17 total
2 alerts expiring in next 30 minutes
```

### **Database Queries**
```sql
-- Active alerts by priority
SELECT priority, COUNT(*) FROM RadarAlert 
WHERE status = 'ACTIVE' GROUP BY priority;

-- Alerts expiring soon
SELECT * FROM RadarAlert 
WHERE status = 'ACTIVE' 
AND expires_at < NOW() + INTERVAL '30 minutes';
```

## 🚀 **Production Deployment**

### **1. Database Migration**
```bash
cd django_api
python manage.py makemigrations
python manage.py migrate
```

### **2. Start Production System**
```bash
cd radar_engine_cloud_function
./start_production_system.sh
```

### **3. Setup Cleanup Cron Jobs**
```bash
# Add to crontab
crontab -e

# Add these lines:
*/5 * * * * cd /path/to/django_api && python manage.py cleanup_expired_alerts --expire-old
0 2 * * * cd /path/to/django_api && python manage.py cleanup_expired_alerts --delete-expired
```

### **4. Monitor Logs**
```bash
# Production poller logs
tail -f production_realtime_poller.log

# Django logs
tail -f django_api/logs/django.log
```

## 🎯 **Benefits of This System**

### **For Users**
- ✅ **Real-time alerts** with countdown timers
- ✅ **Priority-based sorting** for urgent setups
- ✅ **Automatic cleanup** of expired alerts
- ✅ **Visual indicators** for alert status
- ✅ **Trade plan integration** with alerts

### **For System**
- ✅ **Database efficiency** with automatic cleanup
- ✅ **Scalable architecture** handling 100+ alerts
- ✅ **Reliable expiration** preventing stale data
- ✅ **Performance optimization** with filtered queries
- ✅ **Monitoring capabilities** for system health

### **For Trading**
- ✅ **Time-sensitive alerts** for ORB setups
- ✅ **Risk management** with stop-loss and targets
- ✅ **Volume confirmation** for higher accuracy
- ✅ **Priority system** for best opportunities
- ✅ **Lifecycle tracking** for alert effectiveness

---

## 🏆 **System Status**

The Alert Lifecycle Management System is **production-ready** and provides:

- **Complete alert lifecycle** from generation to expiration
- **Real-time user interface** with auto-refresh
- **Automatic database cleanup** to prevent bloat
- **Priority-based sorting** for optimal trading decisions
- **Comprehensive monitoring** and analytics

**Ready for live trading! 🎯📈** 