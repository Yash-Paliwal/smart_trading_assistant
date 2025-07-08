#!/usr/bin/env python3
"""
Production System for Smart Trading Assistant
Handles premarket scanning and real-time polling
"""

import argparse
import sys
import os
import time
import signal
from datetime import datetime, timedelta
import django

# Add Django project to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'django_api'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')
django.setup()

from trading_app.models import RadarAlert, Instrument
from premarket_scanner import run_premarket_scanner
from intraday_scanner import run_intraday_scanner
from real_time_poller import RealTimePoller

def check_market_hours():
    """Check if market is currently open"""
    now = datetime.now()
    current_day = now.weekday()  # Monday = 0, Sunday = 6
    
    # Market is closed on weekends
    if current_day >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Market hours: 9:15 AM to 3:30 PM IST
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    return market_open <= now <= market_close

def run_premarket_scan():
    """Run premarket scanner and return results"""
    print("🔍 Starting premarket scanner...")
    start_time = time.time()
    
    try:
        # Run premarket scanner
        alerts = run_premarket_scanner()
        
        scan_duration = time.time() - start_time
        stocks_scanned = 200  # Nifty 200 stocks
        
        print(f"✅ Premarket scan completed in {scan_duration:.2f}s")
        print(f"📊 Scanned {stocks_scanned} stocks")
        print(f"🚨 Found {len(alerts)} screening alerts")
        
        return {
            'success': True,
            'alerts_found': len(alerts),
            'stocks_scanned': stocks_scanned,
            'scan_duration': scan_duration
        }
        
    except Exception as e:
        print(f"❌ Premarket scan failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def run_intraday_scan():
    """Run intraday scanner and return results"""
    print("🔍 Starting intraday scanner...")
    start_time = time.time()
    
    try:
        # Get watchlist from database (top stocks from premarket scan)
        watchlist = list(RadarAlert.objects.filter(
            category='SCREENING',
            status='ACTIVE'
        ).values_list('instrument_key', flat=True)[:10])
        
        if not watchlist:
            print("⚠️ No watchlist found. Using default stocks.")
            watchlist = ['NSE:NIFTY50-INDEX', 'NSE:BANKNIFTY-INDEX']
        
        # Run intraday scanner
        alerts = run_intraday_scanner(watchlist=watchlist)
        
        scan_duration = time.time() - start_time
        
        print(f"✅ Intraday scan completed in {scan_duration:.2f}s")
        print(f"📊 Scanned {len(watchlist)} stocks")
        print(f"🚨 Found {len(alerts)} entry alerts")
        
        return {
            'success': True,
            'alerts_found': len(alerts),
            'stocks_scanned': len(watchlist),
            'scan_duration': scan_duration
        }
        
    except Exception as e:
        print(f"❌ Intraday scan failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def run_production_system():
    """Run the complete production system"""
    print("🚀 Starting Smart Trading Assistant Production System")
    print(f"⏰ Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if market is open
    if check_market_hours():
        print("📈 Market is OPEN - Running in production mode")
        run_mode = "production"
    else:
        print("📉 Market is CLOSED - Running in test mode")
        run_mode = "test"
    
    # Step 1: Run premarket scanner at 9:00 AM or if not run today
    print("\n" + "="*50)
    print("STEP 1: PREMARKET SCANNER")
    print("="*50)
    
    premarket_result = run_premarket_scan()
    
    if not premarket_result['success']:
        print("❌ Premarket scan failed. Exiting.")
        return 1
    
    # Step 2: Start real-time polling (only during market hours)
    if run_mode == "production":
        print("\n" + "="*50)
        print("STEP 2: REAL-TIME POLLING")
        print("="*50)
        
        poller = RealTimePoller()
        
        # Handle graceful shutdown
        def signal_handler(signum, frame):
            print("\n🛑 Shutdown signal received. Stopping poller...")
            poller.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            poller.start()
        except KeyboardInterrupt:
            print("\n🛑 Manual shutdown. Stopping poller...")
            poller.stop()
    
    print("\n✅ Production system completed successfully!")
    return 0

def main():
    parser = argparse.ArgumentParser(description='Smart Trading Assistant Production System')
    parser.add_argument('--premarket-scan', action='store_true', 
                       help='Run only premarket scanner')
    parser.add_argument('--intraday-scan', action='store_true', 
                       help='Run only intraday scanner')
    parser.add_argument('--production', action='store_true', 
                       help='Run complete production system')
    
    args = parser.parse_args()
    
    if args.premarket_scan:
        # Run only premarket scanner
        result = run_premarket_scan()
        if result['success']:
            print(f"{result['alerts_found']} alerts found")
            print(f"{result['stocks_scanned']} stocks scanned")
            print(f"{result['scan_duration']} scan duration")
        else:
            print(f"Scan failed: {result['error']}")
            return 1
        return 0
        
    elif args.intraday_scan:
        # Run only intraday scanner
        result = run_intraday_scan()
        if result['success']:
            print(f"{result['alerts_found']} alerts found")
            print(f"{result['stocks_scanned']} stocks scanned")
            print(f"{result['scan_duration']} scan duration")
        else:
            print(f"Scan failed: {result['error']}")
            return 1
        return 0
        
    elif args.production:
        # Run complete production system
        return run_production_system()
        
    else:
        # Default: run complete production system
        return run_production_system()

if __name__ == "__main__":
    sys.exit(main()) 