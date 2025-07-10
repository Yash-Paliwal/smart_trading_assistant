# trading_app/models.py

from django.db import models
from django.contrib.auth.models import User
from datetime import date
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    upstox_user_id = models.CharField(max_length=100, unique=True, db_index=True)
    upstox_access_token = models.CharField(max_length=1000)

    def __str__(self):
        return self.user.username

class Instrument(models.Model):
    instrument_key = models.CharField(max_length=100, unique=True, primary_key=True)
    tradingsymbol = models.CharField(max_length=50)
    name = models.CharField(max_length=200, null=True, blank=True)
    exchange = models.CharField(max_length=10, null=True, blank=True)
    instrument_type = models.CharField(max_length=10, null=True, blank=True)
    segment = models.CharField(max_length=20, null=True, blank=True)
    expiry = models.DateField(null=True, blank=True)
    strike = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    lot_size = models.IntegerField(null=True, blank=True)
    average_volume = models.BigIntegerField(null=True, blank=True)
    sector = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.tradingsymbol} ({self.instrument_key})"

class TradeLog(models.Model):
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, null=True, blank=True)
    instrument_key = models.CharField(max_length=100, null=True, blank=True)  # Keep for backward compatibility
    trade_date = models.DateField(null=True, blank=True)
    entry_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    exit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    trade_type = models.CharField(max_length=10, choices=[('BUY', 'Buy'), ('SELL', 'Sell')], null=True, blank=True)
    pnl = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        symbol = self.instrument.tradingsymbol if self.instrument else self.instrument_key
        return f"{symbol} - {self.trade_type} - {self.trade_date}"

class RadarAlert(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('TRIGGERED', 'Triggered'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    ALERT_TYPE_CHOICES = [
        ('SCREENING', 'Screening'),
        ('ENTRY', 'Entry'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    instrument_key = models.CharField(max_length=100, db_index=True)
    source_strategy = models.CharField(max_length=50)
    alert_details = models.JSONField(default=dict)
    indicators = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    expires_at = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES, default='SCREENING')
    notified = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['instrument_key', 'source_strategy'], name='unique_instrument_strategy')
        ]

    def __str__(self):
        return f"{self.instrument_key} - {self.source_strategy} - {self.status}"

# --- Virtual Trading Models ---

class VirtualWallet(models.Model):
    """Virtual trading wallet with initial balance of 2 lakh rupees"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('200000.00'))  # 2 lakh initial
    total_invested = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_pnl = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet - ₹{self.balance}"

    @property
    def available_balance(self):
        """Available balance for new trades"""
        return self.balance - self.total_invested

    @property
    def win_rate(self):
        """Percentage of winning trades"""
        if self.total_trades == 0:
            return 0
        return (self.winning_trades / self.total_trades) * 100

    @property
    def total_value(self):
        """Total portfolio value (cash + invested)"""
        return self.balance

class VirtualTrade(models.Model):
    """Individual virtual trade based on alerts"""
    TRADE_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('EXECUTED', 'Executed'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    TRADE_TYPE_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]

    wallet = models.ForeignKey(VirtualWallet, on_delete=models.CASCADE, related_name='trades')
    alert = models.ForeignKey(RadarAlert, on_delete=models.CASCADE, related_name='virtual_trades')
    instrument_key = models.CharField(max_length=100)
    tradingsymbol = models.CharField(max_length=50)
    trade_type = models.CharField(max_length=10, choices=TRADE_TYPE_CHOICES)
    quantity = models.IntegerField()
    entry_price = models.DecimalField(max_digits=10, decimal_places=2)
    exit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    target_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stop_loss = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=TRADE_STATUS_CHOICES, default='PENDING')
    pnl = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pnl_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Risk management
    risk_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Amount risked
    risk_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('2.00'))  # 2% risk per trade

    def __str__(self):
        return f"{self.tradingsymbol} - {self.trade_type} - {self.status}"

    @property
    def is_profitable(self):
        """Check if trade is profitable"""
        if self.pnl is None:
            return None
        return self.pnl > 0

    @property
    def current_value(self):
        """Current value of the position"""
        if self.status == 'CLOSED':
            return Decimal('0.00')
        return self.quantity * (self.exit_price or self.entry_price)

    def calculate_pnl(self, current_price=None):
        """Calculate P&L based on current or exit price"""
        if current_price is None:
            current_price = self.exit_price
        
        if current_price is None:
            return None
            
        if self.trade_type == 'BUY':
            pnl = (current_price - self.entry_price) * self.quantity
        else:  # SELL
            pnl = (self.entry_price - current_price) * self.quantity
            
        return pnl

class VirtualPosition(models.Model):
    """Current open positions in the virtual wallet"""
    wallet = models.ForeignKey(VirtualWallet, on_delete=models.CASCADE, related_name='positions')
    instrument_key = models.CharField(max_length=100)
    tradingsymbol = models.CharField(max_length=50)
    quantity = models.IntegerField()
    avg_entry_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unrealized_pnl = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unrealized_pnl_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['wallet', 'instrument_key']

    def __str__(self):
        return f"{self.tradingsymbol} - {self.quantity} shares"

    def update_current_price(self, current_price):
        """Update current price and recalculate unrealized P&L"""
        self.current_price = current_price
        self.unrealized_pnl = (current_price - self.avg_entry_price) * self.quantity
        if self.avg_entry_price > 0:
            self.unrealized_pnl_percentage = (self.unrealized_pnl / (self.avg_entry_price * self.quantity)) * 100
        self.save()

@receiver(post_save, sender=User)
def create_virtual_wallet_for_user(sender, instance, created, **kwargs):
    """Automatically create a VirtualWallet for every new user"""
    from .models import VirtualWallet
    if created:
        VirtualWallet.objects.get_or_create(user=instance)
