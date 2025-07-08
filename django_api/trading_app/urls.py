# trading_app/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import CurrentUserView

router = DefaultRouter()
router.register(r'instruments', views.InstrumentViewSet)
router.register(r'trade-logs', views.TradeLogViewSet)
router.register(r'alerts', views.RadarAlertViewSet)
router.register(r'virtual-wallets', views.VirtualWalletViewSet)
router.register(r'virtual-trades', views.VirtualTradeViewSet)
router.register(r'virtual-positions', views.VirtualPositionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/upstox/login/', views.upstox_login, name='upstox_login'),
    path('auth/upstox/callback/', views.upstox_callback, name='upstox_callback'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('trigger-scan/', views.trigger_scan, name='trigger_scan'),
    path('virtual-trading-dashboard/', views.virtual_trading_dashboard, name='virtual_trading_dashboard'),
    path('auth/user/', CurrentUserView.as_view(), name='current-user'),
    # Legacy routes for backward compatibility
    path('alerts/', views.RadarAlertListView.as_view(), name='radar-alert-list'),
    path('tradelogs/', views.TradeLogListCreateView.as_view(), name='tradelog-list-create'),
    path('tradelogs/<int:pk>/', views.TradeLogDetailView.as_view(), name='tradelog-detail'),
]
