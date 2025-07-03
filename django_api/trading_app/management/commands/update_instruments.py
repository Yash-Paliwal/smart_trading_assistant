# django_api/trading_app/management/commands/update_instruments.py

from django.core.management.base import BaseCommand
from trading_app.models import Instrument
import requests
import pandas as pd
import io
import json

class Command(BaseCommand):
    help = 'Downloads the latest NIFTY 100 instrument list and saves it to the database.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting instrument update process...'))

        # --- Step 1: Fetch NIFTY 100 Symbols from NSE Website ---
        index_urls = {
            'NIFTY 50': 'https://archives.nseindia.com/content/indices/ind_nifty50list.csv',
            'NIFTY NEXT 50': 'https://archives.nseindia.com/content/indices/ind_niftynext50list.csv'
        }
        nifty_symbols = set()
        for index_name, url in index_urls.items():
            self.stdout.write(f"Fetching {index_name} constituents...")
            try:
                nse_headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=nse_headers)
                response.raise_for_status()
                index_df = pd.read_csv(io.StringIO(response.text))
                nifty_symbols.update(index_df['Symbol'].tolist())
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Could not fetch {index_name}: {e}"))
        
        if not nifty_symbols:
            self.stdout.write(self.style.ERROR('Failed to fetch any NIFTY index symbols. Aborting.'))
            return
            
        self.stdout.write(self.style.SUCCESS(f'Successfully fetched {len(nifty_symbols)} unique NIFTY 100 symbols.'))

        # --- Step 2: Fetch the Full Instrument Master List from a working source ---
        # We will use the MIS list as our master source, as we confirmed it works.
        master_url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE_MIS.json.gz"
        self.stdout.write("Downloading Upstox instrument master list...")
        try:
            # Note: This download does not seem to require an auth token.
            # If it fails in the future, an Authorization header might be needed.
            response = requests.get(master_url)
            response.raise_for_status()
            
            # This logic for reading the gzipped JSON is complex and should be here
            import gzip
            gzip_file = io.BytesIO(response.content)
            with gzip.open(gzip_file, 'rt') as f:
                instrument_list = json.load(f)
            upstox_df = pd.DataFrame(instrument_list)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Could not download Upstox master list: {e}'))
            return

        # --- Step 3: Filter and Save to Database ---
        # Filter the master list for only the NIFTY 100 stocks we fetched
        nifty100_df = upstox_df[upstox_df['trading_symbol'].isin(nifty_symbols)]
        self.stdout.write(f"Found {len(nifty100_df)} matching NIFTY 100 instruments in the Upstox master list.")

        # Use Django's update_or_create to efficiently add/update the database
        instruments_created = 0
        instruments_updated = 0
        for _, row in nifty100_df.iterrows():
            # The 'defaults' dictionary contains all the fields to update if the instrument already exists.
            defaults = {
                'exchange_token': row.get('exchange_token'),
                'tradingsymbol': row.get('trading_symbol'),
                'name': row.get('name'),
                'last_price': row.get('last_price'),
                'expiry': pd.to_datetime(row.get('expiry')).date() if pd.notna(row.get('expiry')) else None,
                'strike': row.get('strike'),
                'tick_size': row.get('tick_size'),
                'lot_size': row.get('lot_size'),
                'instrument_type': row.get('instrument_type'),
                'segment': row.get('segment'),
                'exchange': row.get('exchange'),
            }
            obj, created = Instrument.objects.update_or_create(
                instrument_key=row['instrument_key'],
                defaults=defaults
            )
            if created:
                instruments_created += 1
            else:
                instruments_updated += 1
        
        self.stdout.write(self.style.SUCCESS(f'Database update complete. Created: {instruments_created}, Updated: {instruments_updated}.'))

