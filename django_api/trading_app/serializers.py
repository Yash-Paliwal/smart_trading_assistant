# trading_app/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Instrument, TradeLog, RadarAlert, VirtualWallet, VirtualTrade, VirtualPosition

class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = '__all__'

class TradeLogSerializer(serializers.ModelSerializer):
    instrument_symbol = serializers.CharField(source='instrument.tradingsymbol', read_only=True)
    
    class Meta:
        model = TradeLog
        fields = '__all__'

class RadarAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = RadarAlert
        fields = '__all__'

# Virtual Trading Serializers
class VirtualWalletSerializer(serializers.ModelSerializer):
    available_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    win_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = VirtualWallet
        fields = '__all__'

class VirtualTradeSerializer(serializers.ModelSerializer):
    is_profitable = serializers.BooleanField(read_only=True)
    current_value = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = VirtualTrade
        fields = '__all__'

class VirtualPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualPosition
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
