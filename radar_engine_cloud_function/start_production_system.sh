#!/bin/bash

# Production Trading Assistant Startup Script
# Follows the correct workflow: Pre-market scan -> Real-time polling

echo "🚀 Starting Production Trading Assistant System"
echo "================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if required packages are installed
python -c "import schedule, pandas, django" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing required packages..."
    pip install schedule pandas django
fi

# Set environment variables
export UPSTOX_API_KEY="5c517390-23f5-40dd-a317-959209f7904c"
export UPSTOX_SECRET_KEY="ubfgfq3kba"
export UPSTOX_REDIRECT_URI="http://localhost:3000/login/callback"
export UPSTOX_ACCESS_TOKEN="eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIzVUMzTFAiLCJqdGkiOiI2ODYzNjA2MDY2NWYzYjFiYjQzYWYyYmIiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzUxMzQzMjAwLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTE0MDcyMDB9.bACetq2fKfVkuxt8quxyMbA6sQQeZw5O8cdYYSnl3O4"

# Create logs directory if it doesn't exist
mkdir -p logs

echo ""
echo "📋 Production Workflow:"
echo "1. Pre-market scan (9:00 AM) - Find top 10 stocks"
echo "2. Real-time polling (9:15 AM - 3:30 PM) - Monitor for ORB setups"
echo ""

# Function to run pre-market scan
run_premarket_scan() {
    echo "🌅 Running Pre-Market Scan..."
    echo "   - Analyzing market context"
    echo "   - Scanning 200 stocks"
    echo "   - Finding top 10 setups"
    echo "   - Saving to database"
    
    python premarket_scanner.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Pre-market scan completed successfully"
        return 0
    else
        echo "❌ Pre-market scan failed"
        return 1
    fi
}

# Function to start real-time polling
start_realtime_polling() {
    echo "🔄 Starting Real-Time Polling System..."
    echo "   - Loading watchlist from pre-market results"
    echo "   - Monitoring for ORB setups"
    echo "   - 60-second polling intervals"
    echo "   - Real-time alerts"
    
    python production_realtime_poller.py --interval 60
}

# Check current time to determine what to run
current_hour=$(date +%H)
current_minute=$(date +%M)
current_time="$current_hour:$current_minute"

echo "🕐 Current time: $current_time"

# Determine what to run based on time
if [ "$current_hour" -eq 9 ] && [ "$current_minute" -lt 15 ]; then
    echo "📊 It's pre-market time. Running pre-market scan..."
    run_premarket_scan
    if [ $? -eq 0 ]; then
        echo ""
        echo "⏰ Waiting for market open (9:15 AM)..."
        sleep 60  # Wait 1 minute
        echo "🚀 Market opening! Starting real-time polling..."
        start_realtime_polling
    else
        echo "❌ Pre-market scan failed. Exiting."
        exit 1
    fi
elif [ "$current_hour" -ge 9 ] && [ "$current_hour" -lt 16 ]; then
    echo "📈 Market is open. Starting real-time polling..."
    start_realtime_polling
else
    echo "📴 Market is closed. Running in test mode..."
    echo "🧪 Starting test mode with 30-second intervals..."
    python production_realtime_poller.py --test --interval 30
fi

echo ""
echo "👋 Production system stopped." 