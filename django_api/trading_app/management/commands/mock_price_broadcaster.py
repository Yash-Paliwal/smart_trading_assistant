import time
import random
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from trading_app.models import RadarAlert

class Command(BaseCommand):
    help = "Broadcasts mock price updates to the 'prices' WebSocket group for current alert stocks."

    def handle(self, *args, **options):
        channel_layer = get_channel_layer()
        print("Starting mock price broadcaster for current alert stocks. Press Ctrl+C to stop.")
        
        # Fetch current alert stocks from the database
        alerts = RadarAlert.objects.all()
        tracked_instruments = [
            {
                "instrument_key": alert.instrument_key,
                "tradingsymbol": alert.instrument_key.split('|')[1] if '|' in alert.instrument_key else alert.instrument_key
            }
            for alert in alerts
        ]
        if not tracked_instruments:
            print("No alert stocks found. Add some alerts to see live prices.")
            return
        prices = {inst["instrument_key"]: random.uniform(1000, 3000) for inst in tracked_instruments}
        try:
            while True:
                for inst in tracked_instruments:
                    # Simulate price change
                    change = random.uniform(-5, 5)
                    prices[inst["instrument_key"]] += change
                    prices[inst["instrument_key"]] = max(1, prices[inst["instrument_key"]])
                    data = {
                        "instrument_key": inst["instrument_key"],
                        "tradingsymbol": inst["tradingsymbol"],
                        "current_price": round(prices[inst["instrument_key"]], 2),
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }
                    async_to_sync(channel_layer.group_send)(
                        "prices",
                        {
                            "type": "price_update",
                            "data": data,
                        }
                    )
                    print(f"Sent price update: {data}")
                time.sleep(2)
        except KeyboardInterrupt:
            print("Mock price broadcaster stopped.") 