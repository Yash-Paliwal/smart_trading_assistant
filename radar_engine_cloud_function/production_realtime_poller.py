#!/usr/bin/env python3
"""
Production Real-Time Market Polling System for Trading Assistant.
Optimized for production use with efficient Django integration.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_realtime_poller.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductionRealTimePoller:
    """
    Production-ready real-time market polling system.
    """
    
    def __init__(self, polling_interval=60):
        self.polling_interval = polling_interval
        self.is_running = False
        self.watchlist = []
        self.alert_history = {}
        self.market_open_time = "09:15"
        self.market_close_time = "15:30"
        self.django_initialized = False
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.stop()
    
    def initialize_django(self):
        """Initialize Django with proper error handling."""
        try:
            # Set Django settings
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_trading_assistant_api.settings')
            
            # Add Django project path
            django_path = os.path.join(os.path.dirname(__file__), '..', 'django_api')
            sys.path.insert(0, django_path)
            
            # Initialize Django
            import django
            django.setup()
            
            self.django_initialized = True
            logger.info("✅ Django initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Django initialization failed: {e}")
            logger.info("🔄 Falling back to standalone mode")
            return False
    
    def is_market_open(self):
        """Check if market is currently open."""
        import pytz
        
        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            logger.debug(f"Market closed: Weekend (weekday={now.weekday()})")
            return False
        
        # Check market hours (9:15 AM to 3:30 PM IST)
        current_time = now.strftime("%H:%M")
        is_open = self.market_open_time <= current_time <= self.market_close_time
        
        logger.debug(f"Market hours check: {current_time} between {self.market_open_time}-{self.market_close_time} = {is_open}")
        return is_open
    
    def load_watchlist_from_database(self):
        """Load watchlist from Django database."""
        if not self.django_initialized:
            logger.warning("Django not initialized. Using default watchlist.")
            return self.load_default_watchlist()
        
        try:
            from trading_app.models import RadarAlert
            from django.utils import timezone
            from datetime import timedelta
            
            # Get today's date
            today = timezone.now().date()
            
            # Check total screening alerts for today
            today_screening_alerts = RadarAlert.objects.filter(
                source_strategy__in=['Bullish_Scan', 'Bearish_Scan', 'Full_Scan'],
                timestamp__date=today,
                status='ACTIVE'
            )
            
            total_screening_alerts = today_screening_alerts.count()
            logger.info(f"📊 Found {total_screening_alerts} screening alerts for today ({today})")
            
            # Show breakdown by strategy
            for strategy in ['Bullish_Scan', 'Bearish_Scan', 'Full_Scan']:
                count = today_screening_alerts.filter(source_strategy=strategy).count()
                if count > 0:
                    logger.info(f"   - {strategy}: {count} alerts")
            
            # Get watchlist from Full_Scan (or most recent strategy)
            alerts = RadarAlert.objects.filter(
                source_strategy="Full_Scan",
                timestamp__date=today,
                status='ACTIVE'
            ).values_list('instrument_key', flat=True).distinct()[:50]  # Top 50 stocks
            
            self.watchlist = list(alerts)
            logger.info(f"✅ Loaded {len(self.watchlist)} stocks for real-time monitoring")
            
            if not self.watchlist:
                logger.warning("No stocks found in database. Using default watchlist.")
                return self.load_default_watchlist()
                
        except Exception as e:
            logger.error(f"Error loading watchlist from database: {e}")
            return self.load_default_watchlist()
    
    def load_default_watchlist(self):
        """Load default watchlist for fallback."""
        self.watchlist = [
            "NSE_EQ|INE002A01018",  # RELIANCE
            "NSE_EQ|INE467B01029",  # TCS
            "NSE_EQ|INE040A01034",  # HDFCBANK
            "NSE_EQ|INE009A01021",  # INFY
            "NSE_EQ|INE090A01021",  # ICICIBANK
        ]
        logger.info(f"✅ Loaded {len(self.watchlist)} stocks in default watchlist")
    
    def load_watchlist(self):
        """Load watchlist with fallback options."""
        if self.django_initialized:
            self.load_watchlist_from_database()
        else:
            self.load_default_watchlist()
    
    def run_premarket_scan(self):
        """Run pre-market scan to update watchlist."""
        logger.info("🔄 Running pre-market scan...")
        try:
            if self.django_initialized:
                # Import and run premarket scanner
                import premarket_scanner
                premarket_scanner.main()
                
                # Enhanced logging after scan
                from trading_app.models import RadarAlert
                from django.utils import timezone
                today = timezone.now().date()
                
                # Check results after scan
                today_alerts = RadarAlert.objects.filter(
                    source_strategy__in=['Bullish_Scan', 'Bearish_Scan', 'Full_Scan'],
                    timestamp__date=today,
                    status='ACTIVE'
                )
                
                total_alerts = today_alerts.count()
                logger.info(f"📊 Pre-market scan completed: {total_alerts} screening alerts created for today")
                
                # Show breakdown
                for strategy in ['Bullish_Scan', 'Bearish_Scan', 'Full_Scan']:
                    count = today_alerts.filter(source_strategy=strategy).count()
                    if count > 0:
                        logger.info(f"   - {strategy}: {count} alerts")
                
                self.load_watchlist()
                logger.info("✅ Watchlist updated with screening results")
            else:
                logger.info("⚠️  Django not available. Skipping pre-market scan.")
                self.load_default_watchlist()
                
        except Exception as e:
            logger.error(f"Error in pre-market scan: {e}")
            self.load_default_watchlist()
    
    def analyze_stock_for_orb(self, instrument_key):
        """
        Enhanced Opening Range Breakout analysis for production.
        """
        try:
            # Import required modules
            import upstox_client_wrapper
            
            # Fetch latest intraday data with timeout
            df = upstox_client_wrapper.fetch_intraday_data(instrument_key, interval='5')
            
            if df is None or len(df) < 12:
                logger.debug(f"Insufficient data for {instrument_key}: {len(df) if df is not None else 0} candles")
                return None

            # 1. Define the opening range (first 30 minutes = 6 candles)
            opening_range_df = df.head(6)
            opening_range_high = opening_range_df['high'].max()
            opening_range_low = opening_range_df['low'].min()
            
            # 2. Get the most recent candle
            last_candle = df.iloc[-1]
            current_price = last_candle['close']
            current_volume = last_candle['volume']
            avg_volume = df['volume'].tail(6).mean()
            
            # 3. Enhanced breakout detection with volume confirmation
            breakout_up = current_price > opening_range_high
            breakout_down = current_price < opening_range_low
            volume_confirmation = current_volume > avg_volume * 1.2
            
            if breakout_up or breakout_down:
                direction = "UP" if breakout_up else "DOWN"
                
                # Calculate targets and stop loss
                if breakout_up:
                    stop_loss = opening_range_low
                    target = current_price + (current_price - opening_range_low)
                else:
                    stop_loss = opening_range_high
                    target = current_price - (opening_range_high - current_price)
                
                # Calculate risk-reward ratio
                risk = abs(current_price - stop_loss)
                reward = abs(target - current_price)
                rr_ratio = reward / risk if risk > 0 else 0
                
                # Create alert data
                alert_data = {
                    "instrument_key": instrument_key,
                    "score": 2 if volume_confirmation else 1,
                    "reasons": [
                        f"Enhanced ORB: Price broke {direction} the 30-min opening range",
                        f"Entry: ₹{current_price:.2f}, Stop: ₹{stop_loss:.2f}, Target: ₹{target:.2f}",
                        f"Risk-Reward: 1:{rr_ratio:.2f}",
                        f"Volume: {'High' if volume_confirmation else 'Normal'}"
                    ],
                    "indicators": {
                        "ORB_High": opening_range_high,
                        "ORB_Low": opening_range_low,
                        "Entry_Price": current_price,
                        "Stop_Loss": stop_loss,
                        "Target": target,
                        "Risk_Reward": rr_ratio,
                        "Volume_Confirmation": volume_confirmation,
                        "Direction": direction
                    }
                }
                
                return alert_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing {instrument_key}: {e}")
            return None
    
    def save_alert_to_database(self, alert_data):
        """Save alert to Django database with lifecycle management."""
        if not self.django_initialized:
            logger.warning("Django not available. Alert not saved to database.")
            return
        
        try:
            from trading_app.models import RadarAlert
            from django.utils import timezone
            from datetime import timedelta
            import json
            
            # Calculate expiration time (ORB alerts typically valid for 45 minutes)
            expires_at = timezone.now() + timedelta(minutes=45)
            
            # Determine alert priority based on volume confirmation
            priority = 'HIGH' if alert_data['indicators'].get('Volume_Confirmation', False) else 'MEDIUM'
            
            # Convert data to JSON-serializable format
            def make_json_serializable(obj):
                if isinstance(obj, dict):
                    return {k: make_json_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [make_json_serializable(item) for item in obj]
                elif isinstance(obj, bool):
                    return obj  # Keep boolean as is
                elif isinstance(obj, (int, float, str, type(None))):
                    return obj
                else:
                    return str(obj)  # Convert other types to string
            
            # Prepare serializable data
            serializable_alert_details = make_json_serializable(alert_data)
            serializable_indicators = make_json_serializable(alert_data['indicators'])
            
            # Create or update alert
            alert, created = RadarAlert.objects.update_or_create(
                instrument_key=alert_data['instrument_key'],
                source_strategy="RealTime_ORB",
                defaults={
                    'alert_details': serializable_alert_details,
                    'indicators': serializable_indicators,
                    'status': 'ACTIVE',
                    'expires_at': expires_at,
                    'priority': priority,
                    'alert_type': 'ORB',
                    'notified': False
                }
            )
            
            action = "Created" if created else "Updated"
            logger.info(f"✅ {action} alert in database: {alert_data['instrument_key']} (expires in 45 minutes)")
            
        except Exception as e:
            logger.error(f"Error saving alert to database: {e}")
            logger.error(f"Alert data: {alert_data}")
    
    def check_intraday_setups(self):
        """Check for intraday setups in the watchlist."""
        if not self.watchlist:
            logger.warning("No stocks in watchlist. Skipping intraday scan.")
            return
        
        logger.info(f"🔍 Checking intraday setups for {len(self.watchlist)} stocks...")
        
        alerts_found = 0
        start_time = time.time()
        
        for i, instrument_key in enumerate(self.watchlist):
            try:
                # Add timeout protection
                if time.time() - start_time > 300:  # 5 minutes max
                    logger.warning("Timeout reached. Stopping current cycle.")
                    break
                
                # Analyze each stock for ORB setups
                alert = self.analyze_stock_for_orb(instrument_key)
                
                if alert:
                    alerts_found += 1
                    self.send_notification(alert)
                    self.save_alert_to_database(alert)
                
                # Rate limiting to avoid API overload
                time.sleep(1.0)  # Increased to 1 second for better API compliance
                
            except Exception as e:
                logger.error(f"Error analyzing {instrument_key}: {e}")
                time.sleep(0.5)  # Brief pause on error
                continue
        
        cycle_time = time.time() - start_time
        logger.info(f"⏱️  Cycle completed in {cycle_time:.1f} seconds")
        
        if alerts_found > 0:
            logger.info(f"🎯 Found {alerts_found} intraday setups")
        else:
            logger.info("📊 No intraday setups found in this cycle")
    
    def send_notification(self, alert_data):
        """Send notification for new alerts."""
        logger.info(f"🚨 NEW ALERT: {alert_data['instrument_key']}")
        logger.info(f"   Direction: {alert_data['indicators']['Direction']}")
        logger.info(f"   Entry: ₹{alert_data['indicators']['Entry_Price']:.2f}")
        logger.info(f"   Stop Loss: ₹{alert_data['indicators']['Stop_Loss']:.2f}")
        logger.info(f"   Target: ₹{alert_data['indicators']['Target']:.2f}")
        logger.info(f"   Risk-Reward: 1:{alert_data['indicators']['Risk_Reward']:.2f}")
        
        # Store alert in history
        alert_key = f"{alert_data['instrument_key']}_{datetime.now().strftime('%H%M')}"
        self.alert_history[alert_key] = alert_data
        
        # TODO: Add email/SMS notification here
        # send_email_alert(alert_data)
        # send_sms_alert(alert_data)
    
    def run_market_open_tasks(self):
        """Tasks to run when market opens."""
        logger.info("🌅 Market opening - running pre-market scan...")
        self.run_premarket_scan()
    
    def run_market_close_tasks(self):
        """Tasks to run when market closes."""
        logger.info("🌆 Market closing - generating end-of-day report...")
        self.generate_eod_report()
    
    def generate_eod_report(self):
        """Generate end-of-day trading report."""
        try:
            if self.django_initialized:
                # Count alerts generated today
                from trading_app.models import RadarAlert
                from datetime import date
                
                today = date.today()
                today_alerts = RadarAlert.objects.filter(
                    timestamp__date=today,
                    source_strategy="RealTime_ORB"
                ).count()
                
                logger.info(f"📊 End-of-Day Report:")
                logger.info(f"   Total alerts generated: {today_alerts}")
                logger.info(f"   Stocks monitored: {len(self.watchlist)}")
                logger.info(f"   Polling cycles completed: {self.get_polling_stats()}")
            else:
                logger.info(f"📊 End-of-Day Report (Standalone):")
                logger.info(f"   Total alerts generated: {len(self.alert_history)}")
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
        
        logger.info(f"📅 Schedule set up with {self.polling_interval}-second polling interval")
    
    def start(self):
        """Start the real-time polling system."""
        logger.info("🚀 Starting Production Real-Time Market Polling System")
        logger.info(f"⏱️  Polling interval: {self.polling_interval} seconds")
        
        # Initialize Django
        self.initialize_django()
        
        self.is_running = True
        self.load_watchlist()
        self.setup_schedule()
        
        logger.info("✅ System started. Press Ctrl+C to stop.")
        
        try:
            while self.is_running:
                # Check if market is open before running scheduled tasks
                if self.is_market_open():
                    schedule.run_pending()
                else:
                    logger.info("📴 Market is closed. Waiting...")
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
        logger.info("🛑 Stopping Production Real-Time Market Polling System...")
        self.is_running = False
        logger.info("✅ System stopped.")

def main():
    """Main function to run the production real-time poller."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Production Real-Time Market Polling System')
    parser.add_argument('--interval', type=int, default=60, 
                       help='Polling interval in seconds (default: 60)')
    
    args = parser.parse_args()
    
    # Create and start the poller
    poller = ProductionRealTimePoller(polling_interval=args.interval)
    poller.start()

if __name__ == "__main__":
    main() 