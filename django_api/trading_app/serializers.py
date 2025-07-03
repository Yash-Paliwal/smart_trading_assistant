# trading_app/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import RadarAlert, TradeLog, Instrument

# **NEW SERIALIZER:** This will format the built-in Django User model data into JSON.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name']


class RadarAlertSerializer(serializers.ModelSerializer):
    tradingsymbol = serializers.CharField(read_only=True)
    class Meta:
        model = RadarAlert
        fields = ['id', 'instrument_key', 'tradingsymbol', 'source_strategy', 'alert_details', 'indicators', 'timestamp']


class TradeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeLog
        fields = [
            'id', 'instrument_key', 'status', 'planned_entry_price', 
            'stop_loss_price', 'target_price', 'actual_entry_price', 
            'exit_price', 'pnl', 'notes', 'trade_date'
        ]
        read_only_fields = ['trade_date']
