# trading_app/models.py

from django.db import models
from django.contrib.auth.models import User
from datetime import date

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    upstox_user_id = models.CharField(max_length=100, unique=True, db_index=True)
    upstox_access_token = models.CharField(max_length=1000)

    def __str__(self):
        return self.user.username


class RadarAlert(models.Model):
    id = models.AutoField(primary_key=True)
    instrument_key = models.CharField(max_length=100, db_index=True)
    source_strategy = models.CharField(max_length=100, db_index=True)
    alert_details = models.JSONField()
    indicators = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"'{self.source_strategy}' alert for {self.instrument_key}"

    class Meta:
        ordering = ['-timestamp']
        unique_together = ('instrument_key', 'source_strategy')


class Instrument(models.Model):
    instrument_key = models.CharField(max_length=100, unique=True, primary_key=True)
    exchange_token = models.CharField(max_length=50, null=True, blank=True)
    tradingsymbol = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    last_price = models.FloatField(null=True, blank=True)
    expiry = models.DateField(null=True, blank=True)
    strike = models.FloatField(null=True, blank=True)
    tick_size = models.FloatField(null=True, blank=True)
    lot_size = models.IntegerField(null=True, blank=True)
    instrument_type = models.CharField(max_length=50, null=True, blank=True)
    segment = models.CharField(max_length=50, null=True, blank=True)
    exchange = models.CharField(max_length=50, null=True, blank=True)
    average_volume = models.BigIntegerField(default=0, db_index=True)
    
    # **NEW FIELD:** Store the stock's sector (e.g., 'NIFTY BANK', 'NIFTY IT').
    sector = models.CharField(max_length=100, null=True, blank=True, db_index=True)

    def __str__(self):
        return self.tradingsymbol or self.instrument_key


class TradeLog(models.Model):
    class TradeStatus(models.TextChoices):
        PLANNED = 'PLANNED', 'Planned'
        ACTIVE = 'ACTIVE', 'Active'
        CLOSED = 'CLOSED', 'Closed'

    instrument_key = models.CharField(max_length=100, db_index=True)
    status = models.CharField(max_length=10, choices=TradeStatus.choices, default=TradeStatus.PLANNED)
    planned_entry_price = models.FloatField(null=True, blank=True)
    stop_loss_price = models.FloatField(null=True, blank=True)
    target_price = models.FloatField(null=True, blank=True)
    actual_entry_price = models.FloatField(null=True, blank=True)
    exit_price = models.FloatField(null=True, blank=True)
    pnl = models.FloatField(default=0.0)
    notes = models.TextField(blank=True, null=True)
    trade_date = models.DateField(default=date.today)

    def __str__(self):
        return f"{self.status} trade for {self.instrument_key} on {self.trade_date}"

    class Meta:
        ordering = ['-trade_date']


class HistoricalData(models.Model):
    """
    Model to store historical market data for testing and analysis.
    """
    instrument_key = models.CharField(max_length=100, db_index=True)
    date = models.DateField(db_index=True)
    open_price = models.FloatField()
    high_price = models.FloatField()
    low_price = models.FloatField()
    close_price = models.FloatField()
    volume = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('instrument_key', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['instrument_key', 'date']),
        ]
    
    def __str__(self):
        return f"{self.instrument_key} - {self.date}"
    
    @classmethod
    def get_data_for_symbol(cls, instrument_key, days=100):
        """
        Get historical data for a symbol.
        
        Args:
            instrument_key (str): The instrument key
            days (int): Number of days to retrieve
            
        Returns:
            QuerySet: Historical data ordered by date
        """
        return cls.objects.filter(
            instrument_key=instrument_key
        ).order_by('date').values(
            'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'
        )
    
    @classmethod
    def store_dataframe(cls, instrument_key, df):
        """
        Store a pandas DataFrame as historical data.
        
        Args:
            instrument_key (str): The instrument key
            df (pd.DataFrame): DataFrame with OHLCV data
        """
        # Convert DataFrame to list of dictionaries
        records = []
        for date, row in df.iterrows():
            records.append({
                'instrument_key': instrument_key,
                'date': date.date() if hasattr(date, 'date') else date,
                'open_price': row['open'],
                'high_price': row['high'],
                'low_price': row['low'],
                'close_price': row['close'],
                'volume': row['volume']
            })
        
        # Bulk create or update
        for record in records:
            cls.objects.update_or_create(
                instrument_key=record['instrument_key'],
                date=record['date'],
                defaults=record
            )
