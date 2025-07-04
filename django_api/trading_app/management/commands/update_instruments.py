# django_api/trading_app/management/commands/update_instruments.py

from django.core.management.base import BaseCommand
from trading_app.models import Instrument
from decouple import config
import requests
import pandas as pd
import io
import json
import gzip
import time
from datetime import datetime, timedelta

# This command now needs to make authenticated API calls, so we import the Upstox SDK
from upstox_client import ApiClient, Configuration
from upstox_client.api.history_v3_api import HistoryV3Api

class Command(BaseCommand):
    help = 'Downloads the latest instrument list, maps them to sectors, calculates average volume, and saves all details to the database.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting instrument update process...'))

        # --- Initialize Upstox API Client ---
        try:
            access_token = config('UPSTOX_ACCESS_TOKEN')
            if not access_token:
                raise ValueError("UPSTOX_ACCESS_TOKEN not found in .env file.")
            
            configuration = Configuration()
            configuration.api_key['Api-Version'] = '2.0'
            configuration.access_token = access_token
            api_client = ApiClient(configuration)
            historical_api = HistoryV3Api(api_client)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to initialize Upstox client: {e}"))
            return

        # --- Step 1: Fetch Sector Data from NSE ---
        sector_map = self.get_sector_map()
        if not sector_map:
            self.stdout.write(self.style.ERROR("Could not build sector map. Aborting."))
            return

        # --- Step 2: Fetch the Full Instrument Master List from Upstox ---
        upstox_master_url = "https://assets.upstox.com/market-quote/instruments/exchange/MTF.json.gz"
        self.stdout.write(f"Downloading instrument master list from Upstox...")
        
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(upstox_master_url, headers=headers)
            response.raise_for_status()
            
            gzip_file = io.BytesIO(response.content)
            with gzip.open(gzip_file, 'rt') as f:
                instrument_list = json.load(f)
            
            upstox_df = pd.DataFrame(instrument_list)
            equity_df = upstox_df[upstox_df['instrument_type'] == 'EQ'].copy()
            equity_df.fillna(value=pd.NA, inplace=True)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Could not download or parse the Upstox master list: {e}'))
            return

        self.stdout.write(self.style.SUCCESS(f"Successfully fetched {len(equity_df)} equity instruments from Upstox."))

        # --- Step 3: Calculate Average Volume and Save to Database ---
        self.stdout.write("Calculating average volume and saving instruments (this may take several minutes)...")
        
        instruments_created = 0
        instruments_updated = 0
        
        for i, row in equity_df.iterrows():
            instrument_key = row['instrument_key']
            trading_symbol = row.get('trading_symbol')
            print(f"  Processing {i+1}/{len(equity_df)}: {trading_symbol}", end='\r')

            avg_vol = self.get_average_volume(historical_api, instrument_key)

            # Prepare data for saving, including the sector
            defaults = {
                'exchange_token': row.get('exchange_token'),
                'tradingsymbol': trading_symbol,
                'name': row.get('name'),
                'last_price': row.get('last_price') if pd.notna(row.get('last_price')) else None,
                'expiry': pd.to_datetime(row.get('expiry')).date() if pd.notna(row.get('expiry')) else None,
                'strike': row.get('strike') if pd.notna(row.get('strike')) else None,
                'tick_size': row.get('tick_size') if pd.notna(row.get('tick_size')) else None,
                'lot_size': row.get('lot_size') if pd.notna(row.get('lot_size')) else None,
                'instrument_type': row.get('instrument_type'),
                'segment': row.get('segment'),
                'exchange': row.get('exchange'),
                'average_volume': int(avg_vol),
                'sector': sector_map.get(trading_symbol, 'Other') # Assign sector from our map
            }
            
            _, created = Instrument.objects.update_or_create(
                instrument_key=instrument_key,
                defaults=defaults
            )
            if created:
                instruments_created += 1
            else:
                instruments_updated += 1
        
        self.stdout.write(self.style.SUCCESS(f'\nDatabase update complete. Created: {instruments_created}, Updated: {instruments_updated}.'))

    def get_sector_map(self):
        """Fetches constituent lists for major NSE sectoral indices and creates a symbol-to-sector map."""
        self.stdout.write("Fetching sectoral data from NSE...")
        sector_urls = {
            'NIFTY AUTO': 'https://archives.nseindia.com/content/indices/ind_niftyautolist.csv',
            'NIFTY BANK': 'https://archives.nseindia.com/content/indices/ind_niftybanklist.csv',
            'NIFTY FMCG': 'https://archives.nseindia.com/content/indices/ind_niftyfmcglist.csv',
            'NIFTY IT': 'https://archives.nseindia.com/content/indices/ind_niftyitlist.csv',
            'NIFTY MEDIA': 'https://archives.nseindia.com/content/indices/ind_niftymedialist.csv',
            'NIFTY METAL': 'https://archives.nseindia.com/content/indices/ind_niftymetallist.csv',
            'NIFTY PHARMA': 'https://archives.nseindia.com/content/indices/ind_niftypharmalist.csv',
            'NIFTY REALTY': 'https://archives.nseindia.com/content/indices/ind_niftyrealtylist.csv',
            'NIFTY PSU BANK': 'https://archives.nseindia.com/content/indices/ind_niftypsubanklist.csv',
            'NIFTY PVT BANK': 'https://archives.nseindia.com/content/indices/ind_niftyprivatebanklist.csv',
            'NIFTY FIN SERVICE': 'https://archives.nseindia.com/content/indices/ind_niftyfinancelist.csv',
            'NIFTY HEALTHCARE': 'https://archives.nseindia.com/content/indices/ind_niftyhealthcarelist.csv',
            'NIFTY CONSUMER DURABLES': 'https://archives.nseindia.com/content/indices/ind_niftyconsumerdurableslist.csv',
            'NIFTY OIL & GAS': 'https://archives.nseindia.com/content/indices/ind_niftyoilgaslist.csv',
        }
        
        symbol_to_sector = {}
        nse_headers = {'User-Agent': 'Mozilla/5.0'}

        for sector_name, url in sector_urls.items():
            try:
                response = requests.get(url, headers=nse_headers)
                response.raise_for_status()
                sector_df = pd.read_csv(io.StringIO(response.text))
                for symbol in sector_df['Symbol']:
                    symbol_to_sector[symbol] = sector_name
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not fetch data for sector {sector_name}: {e}"))
        
        return symbol_to_sector

    def get_average_volume(self, historical_api, instrument_key):
        """Fetches the last 30 days of data for an instrument and calculates its average volume."""
        try:
            to_date = datetime.now().strftime('%Y-%m-%d')
            from_date = (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d')
            
            api_response = historical_api.get_historical_candle_data1(
                instrument_key=instrument_key,
                unit='days',
                interval='1',
                to_date=to_date,
                from_date=from_date
            )
            
            if api_response.data and api_response.data.candles:
                volumes = [candle[5] for candle in api_response.data.candles]
                if volumes:
                    return sum(volumes) / len(volumes)
            
            time.sleep(0.4) # Respect API rate limits
        except Exception:
            return 0
        return 0
