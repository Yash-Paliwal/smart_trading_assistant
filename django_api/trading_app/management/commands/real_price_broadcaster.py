import time
import sys
import os
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from trading_app.models import RadarAlert
import logging

# Add the radar engine path for Upstox client
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'radar_engine_cloud_function'))

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Broadcasts real-time price updates from Upstox API for current alert stocks."

    def handle(self, *args, **options):
        channel_layer = get_channel_layer()
        print("🚀 Starting real-time price broadcaster for alert stocks. Press Ctrl+C to stop.")
        
        try:
            # Import Upstox client
            import upstox_client_wrapper
        except ImportError as e:
            print(f"❌ Error importing Upstox client: {e}")
            print("Make sure the radar_engine_cloud_function is accessible")
            return
        
        # Fetch current alert stocks from the database
        alerts = RadarAlert.objects.filter(status='ACTIVE')
        tracked_instruments = []
        
        for alert in alerts:
            instrument_key = alert.instrument_key
            # Extract trading symbol from instrument key
            if '|' in instrument_key:
                tradingsymbol = instrument_key.split('|')[1]
            else:
                tradingsymbol = instrument_key
            
            tracked_instruments.append({
                "instrument_key": instrument_key,
                "tradingsymbol": tradingsymbol
            })
        
        if not tracked_instruments:
            print("⚠️ No active alert stocks found. Add some alerts to see live prices.")
            return
        
        print(f"📊 Tracking {len(tracked_instruments)} alert stocks for live prices:")
        for inst in tracked_instruments:
            print(f"   - {inst['tradingsymbol']} ({inst['instrument_key']})")
        
        # Price cache to avoid unnecessary API calls
        price_cache = {}
        
        try:
            while True:
                for inst in tracked_instruments:
                    try:
                        # Fetch latest intraday data (1-minute candles)
                        df = upstox_client_wrapper.fetch_intraday_data(
                            inst["instrument_key"], 
                            interval='1'
                        )
                        
                        if df is not None and not df.empty:
                            # Get the latest price
                            latest_price = df['close'].iloc[-1]
                            latest_volume = df['volume'].iloc[-1]
                            
                            # Calculate price change
                            price_change = 0
                            if len(df) > 1:
                                prev_price = df['close'].iloc[-2]
                                price_change = latest_price - prev_price
                                price_change_pct = (price_change / prev_price) * 100
                            else:
                                price_change_pct = 0
                            
                            data = {
                                "instrument_key": inst["instrument_key"],
                                "tradingsymbol": inst["tradingsymbol"],
                                "current_price": round(float(latest_price), 2),
                                "price_change": round(float(price_change), 2),
                                "price_change_pct": round(float(price_change_pct), 2),
                                "volume": int(latest_volume),
                                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            }
                            
                            # Only send if price changed significantly or it's a new stock
                            cache_key = inst["instrument_key"]
                            if (cache_key not in price_cache or 
                                abs(price_cache[cache_key] - latest_price) > 0.01):
                            
                                print(f"📡 Broadcasting price for {inst['tradingsymbol']}: ₹{latest_price:.2f}")
                                
                                async_to_sync(channel_layer.group_send)(
                                    "prices",
                                    {
                                        "type": "price_update",
                                        "data": data,
                                    }
                                )
                                print(f"✅ Sent price update to Redis channel layer for {inst['tradingsymbol']}")
                                
                                # Update cache
                                price_cache[cache_key] = latest_price
                                
                                # Log significant price changes
                                if abs(price_change_pct) > 0.5:
                                    print(f"📈 {inst['tradingsymbol']}: ₹{latest_price:.2f} ({price_change_pct:+.2f}%)")
                        
                        # Rate limiting to avoid API overload
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Error fetching price for {inst['tradingsymbol']}: {e}")
                        continue
                
                # Wait before next cycle
                time.sleep(5)  # Update every 5 seconds
                
        except KeyboardInterrupt:
            print("\n🛑 Real-time price broadcaster stopped.")
        except Exception as e:
            logger.error(f"Unexpected error in price broadcaster: {e}")
            print(f"❌ Error: {e}") 