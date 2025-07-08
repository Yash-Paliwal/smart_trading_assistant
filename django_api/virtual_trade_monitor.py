#!/usr/bin/env python3
"""
Virtual Trade Monitor - Standalone script to automatically monitor and close virtual trades
"""

import os
import sys
import time
import subprocess
import signal
from datetime import datetime

# Add Django project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')

import django
django.setup()

def run_monitor_command():
    """Run the Django management command to monitor virtual trades"""
    try:
        result = subprocess.run([
            'python', 'manage.py', 'monitor_virtual_trades'
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            print(f"[{datetime.now()}] ✅ Monitor completed successfully")
            if result.stdout.strip():
                print(result.stdout.strip())
        else:
            print(f"[{datetime.now()}] ❌ Monitor failed: {result.stderr.strip()}")
            
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error running monitor: {str(e)}")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n[{datetime.now()}] 🛑 Shutting down virtual trade monitor...")
    sys.exit(0)

def main():
    """Main function - run monitor every minute"""
    print(f"[{datetime.now()}] 🚀 Starting Virtual Trade Monitor")
    print("Press Ctrl+C to stop")
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run initial check
    print(f"[{datetime.now()}] 🔍 Running initial trade check...")
    run_monitor_command()
    
    # Main loop - run every minute
    while True:
        try:
            time.sleep(60)  # Wait 60 seconds
            run_monitor_command()
            
        except KeyboardInterrupt:
            print(f"\n[{datetime.now()}] 🛑 Stopping monitor...")
            break
        except Exception as e:
            print(f"[{datetime.now()}] ❌ Unexpected error: {str(e)}")
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    main() 