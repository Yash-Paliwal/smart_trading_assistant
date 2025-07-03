# smart_trading_assistant_api/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Add this line to include the URLs from our trading_app
    # All URLs from trading_app will now be prefixed with 'api/'
    path('api/', include('trading_app.urls')),
    path('', include('trading_app.urls')),
]
