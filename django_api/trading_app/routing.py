# trading_app/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/trading/(?P<user_id>[^/]+)/$', consumers.TradingConsumer.as_asgi()),
    re_path(r'ws/prices/$', consumers.PriceConsumer.as_asgi()),
] 