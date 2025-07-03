# trading_app/urls.py

from django.urls import path
from .views import (
    RadarAlertListView, 
    TradeLogListCreateView, 
    TradeLogDetailView, 
    upstox_login,
    upstox_callback,
    CurrentUserView, # Import new view
    user_logout      # Import new view
)

urlpatterns = [
    # Auth URLs
    path('auth/upstox/login/', upstox_login, name='upstox-login'),
    path('auth/upstox/callback/', upstox_callback, name='upstox-callback'),
    path('auth/user/', CurrentUserView.as_view(), name='current-user'),
    path('auth/logout/', user_logout, name='user-logout'),
    
    # Data URLs
    path('alerts/', RadarAlertListView.as_view(), name='radar-alert-list'),
    path('tradelogs/', TradeLogListCreateView.as_view(), name='tradelog-list-create'),
    path('tradelogs/<int:pk>/', TradeLogDetailView.as_view(), name='tradelog-detail'),
]
