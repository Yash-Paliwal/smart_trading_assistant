# trading_app/admin.py

from django.contrib import admin
# **FIX:** Import the new TradeLog model instead of the old TrackedStock model
from .models import RadarAlert, Instrument, TradeLog

@admin.register(RadarAlert)
class RadarAlertAdmin(admin.ModelAdmin):
    list_display = ('instrument_key', 'source_strategy', 'timestamp', 'get_score')
    list_filter = ('timestamp', 'source_strategy', 'instrument_key')
    search_fields = ('instrument_key',)

    @admin.display(description='Score')
    def get_score(self, obj):
        return obj.alert_details.get('score', 'N/A')


@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ('instrument_key', 'tradingsymbol', 'name', 'segment', 'exchange')
    list_filter = ('segment', 'exchange', 'instrument_type')
    search_fields = ('instrument_key', 'tradingsymbol', 'name')


# **FIX:** Register the new TradeLog model with the admin site
@admin.register(TradeLog)
class TradeLogAdmin(admin.ModelAdmin):
    list_display = ('instrument_key', 'status', 'trade_date', 'pnl')
    list_filter = ('status', 'trade_date')
    search_fields = ('instrument_key',)

