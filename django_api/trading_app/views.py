# trading_app/views.py

from django.http import JsonResponse, HttpResponseRedirect
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import login, logout # Import login/logout functions
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import RadarAlert, TradeLog, Instrument, UserProfile
from .serializers import RadarAlertSerializer, TradeLogSerializer, UserSerializer # Import new UserSerializer
import urllib.parse
import requests

# --- Authentication Views ---

class CurrentUserView(APIView):
    """
    API view to get the currently authenticated user.
    If the user is logged in, it returns their data. Otherwise, it returns an error.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

def user_logout(request):
    """Logs the current user out of the Django session."""
    logout(request)
    return JsonResponse({"message": "Successfully logged out."})


def upstox_login(request):
    """
    Redirects the user to the Upstox login page to start the OAuth2 flow.
    """
    client_id = settings.UPSTOX_API_KEY 
    redirect_uri = settings.UPSTOX_REDIRECT_URI
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'state': 'RANDOM_STATE_STRING'
    }
    auth_url = f"https://api.upstox.com/v2/login/authorization/dialog?{urllib.parse.urlencode(params)}"
    return HttpResponseRedirect(auth_url)


def upstox_callback(request):
    """
    Handles the callback from Upstox, exchanges the code for a token,
    and logs the user into our application.
    """
    code = request.GET.get('code')
    if not code:
        return JsonResponse({"error": "Authorization code not found"}, status=400)

    token_url = "https://api.upstox.com/v2/login/authorization/token"
    payload = {
        'code': code,
        'client_id': settings.UPSTOX_API_KEY,
        'client_secret': settings.UPSTOX_API_SECRET,
        'redirect_uri': settings.UPSTOX_REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    headers = {'accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}

    try:
        response = requests.post(token_url, headers=headers, data=payload)
        response.raise_for_status()
        token_data = response.json()
        
        user, created = User.objects.get_or_create(
            username=token_data.get('email'),
            defaults={'email': token_data.get('email'), 'first_name': token_data.get('user_name')}
        )

        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                'upstox_user_id': token_data.get('user_id'),
                'upstox_access_token': token_data.get('access_token')
            }
        )
        
        # **NEW:** Log the user into the Django session framework.
        # This creates a session cookie in the user's browser.
        login(request, user)
        # Instead of redirecting, return a response so browser stores session
        response = JsonResponse({"message": "Login successful"})
        response["Access-Control-Allow-Credentials"] = "true"  # Ensure frontend can use the cookie
        return response

    except requests.exceptions.RequestException as e:
        error_details = e.response.json() if e.response else str(e)
        return JsonResponse({"error": "Failed to exchange code for token", "details": error_details}, status=500)


# --- Data Views ---

class RadarAlertListView(generics.ListAPIView):
    queryset = RadarAlert.objects.all()
    serializer_class = RadarAlertSerializer

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        alerts_data = response.data.get('results', [])
        if not alerts_data: return response
        instrument_keys = {a['instrument_key'] for a in alerts_data}
        instruments = Instrument.objects.filter(instrument_key__in=instrument_keys).values('instrument_key', 'tradingsymbol')
        symbol_map = {i['instrument_key']: i['tradingsymbol'] for i in instruments}
        for alert in alerts_data:
            alert['tradingsymbol'] = symbol_map.get(alert['instrument_key'], '')
        response.data['results'] = alerts_data
        return response


class TradeLogListCreateView(generics.ListCreateAPIView):
    queryset = TradeLog.objects.all()
    serializer_class = TradeLogSerializer


class TradeLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TradeLog.objects.all()
    serializer_class = TradeLogSerializer
