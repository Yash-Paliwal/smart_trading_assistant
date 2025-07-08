#!/usr/bin/env python3
"""
Quick script to check database status and alerts
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')
django.setup()

from trading_app.models import RadarAlert, Instrument
from datetime import datetime

def check_database():
    print("🔍 Checking Database Status...")
    print("=" * 50)
    
    # Check instruments
    instruments_count = Instrument.objects.count()
    print(f"📊 Instruments in database: {instruments_count}")
    
    if instruments_count > 0:
        print("📋 Sample instruments:")
        for inst in Instrument.objects.all()[:5]:
            print(f"   - {inst.tradingsymbol} ({inst.instrument_key})")
    
    # Check alerts
    alerts_count = RadarAlert.objects.count()
    print(f"\n🚨 Total alerts in database: {alerts_count}")
    
    if alerts_count > 0:
        print("📋 Sample alerts:")
        for alert in RadarAlert.objects.all()[:5]:
            print(f"   - {alert.instrument_key} | {alert.source_strategy} | {alert.status} | {alert.timestamp}")
    
    # Check active alerts
    active_alerts = RadarAlert.objects.filter(status='ACTIVE')
    active_count = active_alerts.count()
    print(f"\n✅ Active alerts: {active_count}")
    
    if active_count > 0:
        print("📋 Active alerts:")
        for alert in active_alerts[:5]:
            print(f"   - {alert.instrument_key} | {alert.source_strategy} | {alert.timestamp}")
    
    # Check expired alerts
    expired_alerts = RadarAlert.objects.filter(status='EXPIRED')
    expired_count = expired_alerts.count()
    print(f"\n❌ Expired alerts: {expired_count}")
    
    print("\n" + "=" * 50)
    
    if alerts_count == 0:
        print("⚠️  No alerts found in database!")
        print("💡 This could mean:")
        print("   1. The scanner has never been run")
        print("   2. The scanner ran but didn't find any setups")
        print("   3. There's an issue with the scanner logic")
        print("   4. The scanner is not saving alerts to database")
    
    return alerts_count, active_count

if __name__ == "__main__":
    check_database() 