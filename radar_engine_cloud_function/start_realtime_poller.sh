#!/bin/bash

# Real-Time Market Polling System Startup Script
# This script starts the real-time polling system for market alerts

echo "🚀 Starting Real-Time Market Polling System"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if required packages are installed
python -c "import schedule" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing required packages..."
    pip install schedule
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the real-time poller
echo "✅ Starting poller with 60-second interval..."
echo "📝 Logs will be saved to realtime_poller.log"
echo "🛑 Press Ctrl+C to stop the system"
echo ""

# Run the poller
python realtime_poller.py --interval 60

echo ""
echo "👋 Real-Time Polling System stopped." 