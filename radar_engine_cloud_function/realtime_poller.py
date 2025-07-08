#!/usr/bin/env python3
"""
Real-Time Market Polling System for Trading Assistant.
Runs continuously during market hours to provide real-time alerts.
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime, timedelta
import pandas as pd
import schedule
import threading

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
import upstox_client_wrapper
import intraday_scanner
import premarket_scanner
import trade_analyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('realtime_poller.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RealTimePoller:
    """
    Real-time market polling system that runs during market hours.
    """
    
    def __init__(self, polling_interval=60):  # 60 seconds = 1 minute
        self.polling_interval = polling_interval
        self.is_running = False
        self.watchlist = []
        self.alert_history = {}
        self.market_open_time = "09:15"
        self.market_close_time = "15:30"
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.stop()
    
    def is_market_open(self):
        """Check if market is currently open."""
        now = datetime.now()
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check market hours (9:15 AM to 3:30 PM IST)
        current_time = now.strftime("%H:%M")
        return self.market_open_time <= current_time <= self.market_close_time
    
    def load_watchlist(self):
        """Load the watchlist from pre-market scan alerts."""
        try:
            # Import Django models
            import django
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')
            django.setup()
            
            from trading_app.models import RadarAlert
            
            # Get the most recent alerts from pre-market scan
            alerts = RadarAlert.objects.filter(
                source_strategy="Full_Scan"
            ).order_by('-timestamp')[:50]  # Top 50 stocks
            
            self.watchlist = list(alerts.values_list('instrument_key', flat=True).distinct())
            logger.info(f"Loaded {len(self.watchlist)} stocks in watchlist")
            
        except Exception as e:
            logger.error(f"Error loading watchlist: {e}")
            # Fallback to default watchlist
            self.watchlist = [
                "NSE_EQ|INE002A01018",  # RELIANCE
                "NSE_EQ|INE467B01029",  # TCS
                "NSE_EQ|INE040A01034",  # HDFCBANK
                "NSE_EQ|INE009A01021",  # INFY
                "NSE_EQ|INE090A01021",  # ICICIBANK
            ]
    
    def run_premarket_scan(self):
        """Run pre-market scan to update watchlist."""
        logger.info("Running pre-market scan...")
        try:
            premarket_scanner.main()
            self.load_watchlist()
            logger.info("Pre-market scan completed and watchlist updated")
        except Exception as e:
            logger.error(f"Error in pre-market scan: {e}")
    
    def check_intraday_setups(self):
        """Check for intraday setups in the watchlist."""
        if not self.watchlist:
            logger.warning("No stocks in watchlist. Skipping intraday scan.")
            return
        
        logger.info(f"Checking intraday setups for {len(self.watchlist)} stocks...")
        
        alerts_found = 0
        for i, instrument_key in enumerate(self.watchlist):
            try:
                # Analyze each stock for ORB setups
                self.analyze_stock_realtime(instrument_key)
                alerts_found += 1
                
                # Rate limiting to avoid API overload
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error analyzing {instrument_key}: {e}")
                continue
        
        if alerts_found > 0:
            logger.info(f"Found {alerts_found} intraday setups")
        else:
            logger.info("No intraday setups found in this cycle")
    
    def analyze_stock_realtime(self, instrument_key):
        """Analyze a single stock for real-time setups."""
        try:
            # Fetch latest intraday data
            df = upstox_client_wrapper.fetch_intraday_data(instrument_key, interval='5')
            
            if df is None or len(df) < 12:
                return
            
            # Use the enhanced ORB analysis from intraday_scanner
            intraday_scanner.analyze_stock_for_orb(instrument_key)
            
        except Exception as e:
            logger.error(f"Error in real-time analysis for {instrument_key}: {e}")
    
    def send_notification(self, alert_data):
        """Send notification for new alerts."""
        # This can be extended to send emails, SMS, push notifications, etc.
        logger.info(f"🚨 NEW ALERT: {alert_data['instrument_key']}")
        logger.info(f"   Direction: {alert_data['indicators']['Direction']}")
        logger.info(f"   Entry: ₹{alert_data['indicators']['Entry_Price']:.2f}")
        logger.info(f"   Stop Loss: ₹{alert_data['indicators']['Stop_Loss']:.2f}")
        logger.info(f"   Target: ₹{alert_data['indicators']['Target']:.2f}")
        logger.info(f"   Risk-Reward: 1:{alert_data['indicators']['Risk_Reward']:.2f}")
        
        # TODO: Add email/SMS notification here
        # send_email_alert(alert_data)
        # send_sms_alert(alert_data)
    
    def run_market_open_tasks(self):
        """Tasks to run when market opens."""
        logger.info("Market opening - running pre-market scan...")
        self.run_premarket_scan()
    
    def run_market_close_tasks(self):
        """Tasks to run when market closes."""
        logger.info("Market closing - generating end-of-day report...")
        self.generate_eod_report()
    
    def generate_eod_report(self):
        """Generate end-of-day trading report."""
        try:
            # Count alerts generated today
            import django
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')
            django.setup()
            
            from trading_app.models import RadarAlert
            from datetime import date
            
            today = date.today()
            today_alerts = RadarAlert.objects.filter(
                timestamp__date=today
            ).count()
            
            logger.info(f"📊 End-of-Day Report:")
            logger.info(f"   Total alerts generated: {today_alerts}")
            logger.info(f"   Stocks monitored: {len(self.watchlist)}")
            logger.info(f"   Polling cycles completed: {self.get_polling_stats()}")
            
        except Exception as e:
            logger.error(f"Error generating EOD report: {e}")
    
    def get_polling_stats(self):
        """Get polling statistics."""
        # This can be enhanced to track more detailed stats
        return "Stats tracking to be implemented"
    
    def setup_schedule(self):
        """Set up the polling schedule."""
        # Pre-market scan at 9:00 AM
        schedule.every().day.at("09:00").do(self.run_market_open_tasks)
        
        # Intraday scanning every minute during market hours
        schedule.every(self.polling_interval).seconds.do(self.check_intraday_setups)
        
        # End-of-day report at 3:45 PM
        schedule.every().day.at("15:45").do(self.run_market_close_tasks)
        
        logger.info(f"Schedule set up with {self.polling_interval}-second polling interval")
    
    def start(self):
        """Start the real-time polling system."""
        logger.info("🚀 Starting Real-Time Market Polling System")
        logger.info(f"Polling interval: {self.polling_interval} seconds")
        
        self.is_running = True
        self.load_watchlist()
        self.setup_schedule()
        
        logger.info("System started. Press Ctrl+C to stop.")
        
        try:
            while self.is_running:
                # Check if market is open before running scheduled tasks
                if self.is_market_open():
                    schedule.run_pending()
                else:
                    logger.info("Market is closed. Waiting...")
                    time.sleep(300)  # Wait 5 minutes before checking again
                
                time.sleep(1)  # Small delay to prevent CPU overload
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt. Shutting down...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the polling system."""
        logger.info("Stopping Real-Time Market Polling System...")
        self.is_running = False
        logger.info("System stopped.")

def main():
    """Main function to run the real-time poller."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Real-Time Market Polling System')
    parser.add_argument('--interval', type=int, default=60, 
                       help='Polling interval in seconds (default: 60)')
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode (bypass market hours check)')
    
    args = parser.parse_args()
    
    # Create and start the poller
    poller = RealTimePoller(polling_interval=args.interval)
    
    if args.test:
        logger.info("Running in TEST MODE - bypassing market hours check")
        # Override market hours check for testing
        poller.is_market_open = lambda: True
    
    poller.start()

if __name__ == "__main__":
    main() 