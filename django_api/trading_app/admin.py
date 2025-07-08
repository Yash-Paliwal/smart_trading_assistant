# trading_app/admin.py

from django.contrib import admin
from .models import Instrument, TradeLog, RadarAlert, VirtualWallet, VirtualTrade, VirtualPosition, UserProfile

@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ['tradingsymbol', 'instrument_key', 'exchange', 'sector', 'average_volume']
    list_filter = ['exchange', 'sector', 'instrument_type']
    search_fields = ['tradingsymbol', 'name', 'instrument_key']
    ordering = ['tradingsymbol']

@admin.register(TradeLog)
class TradeLogAdmin(admin.ModelAdmin):
    list_display = ['instrument', 'trade_date', 'trade_type', 'entry_price', 'exit_price', 'quantity', 'pnl']
    list_filter = ['trade_type', 'trade_date']
    search_fields = ['instrument__tradingsymbol', 'instrument__instrument_key']
    ordering = ['-trade_date']

@admin.register(RadarAlert)
class RadarAlertAdmin(admin.ModelAdmin):
    list_display = ['instrument_key', 'source_strategy', 'status', 'priority', 'alert_type', 'timestamp']
    list_filter = ['status', 'priority', 'alert_type', 'source_strategy', 'timestamp']
    search_fields = ['instrument_key', 'source_strategy']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']

@admin.register(VirtualWallet)
class VirtualWalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'total_invested', 'total_pnl', 'total_trades', 'win_rate']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(VirtualTrade)
class VirtualTradeAdmin(admin.ModelAdmin):
    list_display = ['tradingsymbol', 'trade_type', 'status', 'entry_price', 'exit_price', 'quantity', 'pnl', 'entry_time']
    list_filter = ['trade_type', 'status', 'entry_time']
    search_fields = ['tradingsymbol', 'instrument_key']
    ordering = ['-entry_time']
    readonly_fields = ['entry_time', 'exit_time']

@admin.register(VirtualPosition)
class VirtualPositionAdmin(admin.ModelAdmin):
    list_display = ['tradingsymbol', 'quantity', 'avg_entry_price', 'current_price', 'unrealized_pnl', 'unrealized_pnl_percentage']
    list_filter = ['created_at']
    search_fields = ['tradingsymbol', 'instrument_key']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'upstox_user_id']
    search_fields = ['user__username', 'user__email', 'upstox_user_id']

