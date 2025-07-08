#!/usr/bin/env python3
"""
Test script to send a test message to the prices WebSocket group
"""

import os
import sys
import django
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')
django.setup()

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_test_price():
    """Send a test price update to the prices group"""
    channel_layer = get_channel_layer()
    
    test_data = {
        "instrument_key": "NSE_EQ|INE002A01018",
        "tradingsymbol": "RELIANCE",
        "current_price": 2500.50,
        "price_change": 25.50,
        "price_change_pct": 1.03,
        "volume": 1500000,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    
    print(f"📡 Sending test price update: {test_data}")
    
    async_to_sync(channel_layer.group_send)(
        "prices",
        {
            "type": "price_update",
            "data": test_data,
        }
    )
    
    print("✅ Test message sent to prices group")

if __name__ == "__main__":
    print("🧪 Testing WebSocket price broadcasting...")
    send_test_price()
    print("🎯 Check your browser console for the test message") 