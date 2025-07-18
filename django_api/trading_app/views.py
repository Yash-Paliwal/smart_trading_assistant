# trading_app/views.py

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.db.models import Q, Avg, Sum
from django.utils import timezone
from datetime import datetime, timedelta
import json
import requests
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .models import Instrument, TradeLog, RadarAlert, UserProfile, VirtualWallet, VirtualTrade, VirtualPosition
from .serializers import (
    InstrumentSerializer, TradeLogSerializer, RadarAlertSerializer,
    VirtualWalletSerializer, VirtualTradeSerializer, VirtualPositionSerializer,
    UserSerializer
)
import urllib.parse
import os
import sys
import subprocess
import time
from django.conf import settings
from decimal import Decimal
from collections import defaultdict, Counter
from django.db.models.functions import TruncDate

# Add this function after the existing imports and before the ViewSets

def get_current_market_price(instrument_key):
    """Get current market price for an instrument"""
    try:
        # Try to get price from Upstox API first
        user_profile = UserProfile.objects.filter(
            upstox_access_token__isnull=False
        ).first()
        
        if user_profile:
            headers = {
                'Authorization': f'Bearer {user_profile.upstox_access_token}',
                'Accept': 'application/json'
            }
            
            url = f'https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument_key}'
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and instrument_key in data['data']:
                    return Decimal(str(data['data'][instrument_key]['last_price']))
        
        # Fallback to mock price for testing
        numeric_part = sum(ord(c) for c in instrument_key) % 1000
        base_price = 100 + (numeric_part % 1900)
        import random
        variation = random.uniform(-0.05, 0.05)
        price = base_price * (1 + variation)
        return Decimal(f'{price:.2f}')
        
    except Exception as e:
        print(f"Error fetching price for {instrument_key}: {str(e)}")
        return None

# --- ViewSets ---

class InstrumentViewSet(viewsets.ModelViewSet):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentSerializer

class TradeLogViewSet(viewsets.ModelViewSet):
    queryset = TradeLog.objects.all()
    serializer_class = TradeLogSerializer

class RadarAlertViewSet(viewsets.ModelViewSet):
    queryset = RadarAlert.objects.all()
    serializer_class = RadarAlertSerializer
    
    def get_queryset(self):
        # Get status filter from query params
        status = self.request.query_params.get('status', 'ACTIVE')
        alert_category = self.request.query_params.get('category', 'ALL')  # SCREENING, ENTRY, ALL
        
        # Base queryset
        queryset = RadarAlert.objects.all()
        
        # Filter by alert category
        if alert_category == 'SCREENING':
            # Screening alerts: Bullish_Scan, Daily_Confluence_Scan, Full_Scan
            queryset = queryset.filter(source_strategy__in=['Bullish_Scan', 'Daily_Confluence_Scan', 'Full_Scan'])
        elif alert_category == 'ENTRY':
            # Entry alerts: RealTime_ORB (time-sensitive)
            queryset = queryset.filter(source_strategy='RealTime_ORB')
        
        # Filter by status
        if status == 'ACTIVE':
            queryset = queryset.filter(status='ACTIVE')
        elif status == 'EXPIRED':
            queryset = queryset.filter(status='EXPIRED')
        elif status == 'ALL':
            pass  # Show all alerts
        
        # Filter by strategy if specified
        strategy = self.request.query_params.get('strategy')
        if strategy:
            queryset = queryset.filter(source_strategy=strategy)
        
        # Filter by alert type if specified
        alert_type = self.request.query_params.get('alert_type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        return queryset.order_by('-timestamp')
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        alerts_data = response.data.get('results', [])
        if not alerts_data: 
            return response
            
        # Get instrument symbols
        instrument_keys = {a['instrument_key'] for a in alerts_data}
        instruments = Instrument.objects.filter(instrument_key__in=instrument_keys).values('instrument_key', 'tradingsymbol')
        symbol_map = {i['instrument_key']: i['tradingsymbol'] for i in instruments}
        
        for alert in alerts_data:
            alert['tradingsymbol'] = symbol_map.get(alert['instrument_key'], '')
            
            # Determine alert category
            if alert.get('source_strategy') == 'RealTime_ORB':
                alert['category'] = 'ENTRY'
                alert['is_time_sensitive'] = True
            else:
                alert['category'] = 'SCREENING'
                alert['is_time_sensitive'] = False
            
            # Add remaining time for time-sensitive alerts only
            if alert.get('is_time_sensitive') and alert.get('status') == 'ACTIVE' and alert.get('expires_at'):
                now = timezone.now()
                expires_at = timezone.datetime.fromisoformat(alert['expires_at'].replace('Z', '+00:00'))
                if now < expires_at:
                    delta = expires_at - now
                    alert['remaining_minutes'] = int(delta.total_seconds() / 60)
                else:
                    alert['remaining_minutes'] = 0
            else:
                alert['remaining_minutes'] = None
        
        response.data['results'] = alerts_data
        return response

class VirtualWalletViewSet(viewsets.ModelViewSet):
    queryset = VirtualWallet.objects.all()
    serializer_class = VirtualWalletSerializer
    
    def get_queryset(self):
        # Only show wallet for the current user
        if self.request.user.is_authenticated:
            return VirtualWallet.objects.filter(user=self.request.user)
        return VirtualWallet.objects.none()

class VirtualTradeViewSet(viewsets.ModelViewSet):
    queryset = VirtualTrade.objects.all()
    serializer_class = VirtualTradeSerializer
    
    def get_queryset(self):
        # Only show trades for the current user
        if self.request.user.is_authenticated:
            return VirtualTrade.objects.filter(wallet__user=self.request.user).order_by('-entry_time')
        return VirtualTrade.objects.none()

class VirtualPositionViewSet(viewsets.ModelViewSet):
    queryset = VirtualPosition.objects.all()
    serializer_class = VirtualPositionSerializer
    
    def get_queryset(self):
        # Only show positions for the current user
        if self.request.user.is_authenticated:
            return VirtualPosition.objects.filter(wallet__user=self.request.user)
        return VirtualPosition.objects.none()

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

@csrf_exempt
def user_logout(request):
    """Logs the current user out of the Django session."""
    logout(request)
    response = JsonResponse({"message": "Successfully logged out."})
    response["Access-Control-Allow-Credentials"] = "true"
    response["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return response

@csrf_exempt
def logout_view(request):
    """Alternative logout view"""
    logout(request)
    response = JsonResponse({"message": "Successfully logged out."})
    response["Access-Control-Allow-Credentials"] = "true"
    response["Access-Control-Allow-Origin"] = "http://localhost:3000"
    return response

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
    try:
        code = request.GET.get('code')
        if not code:
            return JsonResponse({"error": "Authorization code not found"}, status=400)

        print(f"DEBUG: Received code: {code[:10]}...")
        print(f"DEBUG: UPSTOX_API_KEY: {settings.UPSTOX_API_KEY}")
        print(f"DEBUG: UPSTOX_REDIRECT_URI: {settings.UPSTOX_REDIRECT_URI}")

        token_url = "https://api.upstox.com/v2/login/authorization/token"
        payload = {
            'code': code,
            'client_id': settings.UPSTOX_API_KEY,
            'client_secret': settings.UPSTOX_API_SECRET,
            'redirect_uri': settings.UPSTOX_REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        headers = {'accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}

        print(f"DEBUG: Making request to Upstox with payload: {payload}")

        response = requests.post(token_url, headers=headers, data=payload)
        print(f"DEBUG: Upstox response status: {response.status_code}")
        print(f"DEBUG: Upstox response: {response.text}")
        
        response.raise_for_status()
        token_data = response.json()
        
        print(f"DEBUG: Token data received: {token_data}")
        
        user, created = User.objects.get_or_create(
            username=token_data.get('email'),
            defaults={'email': token_data.get('email'), 'first_name': token_data.get('user_name')}
        )

        print(f"DEBUG: User created/retrieved: {user.username}")

        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                'upstox_user_id': token_data.get('user_id'),
                'upstox_access_token': token_data.get('access_token')
            }
        )
        
        print(f"DEBUG: UserProfile updated")
        
        # Log the user into the Django session framework.
        login(request, user)
        response = JsonResponse({"message": "Login successful"})
        response["Access-Control-Allow-Credentials"] = "true"
        return response

    except requests.exceptions.RequestException as e:
        print(f"DEBUG: RequestException: {e}")
        error_details = e.response.json() if e.response else str(e)
        return JsonResponse({"error": "Failed to exchange code for token", "details": error_details}, status=500)
    except Exception as e:
        print(f"DEBUG: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": "Unexpected error during login", "details": str(e)}, status=500)

# --- Legacy Views (for backward compatibility) ---

class RadarAlertListView(generics.ListAPIView):
    serializer_class = RadarAlertSerializer

    def get_queryset(self):
        # Get status filter from query params
        status = self.request.query_params.get('status', 'ACTIVE')
        alert_category = self.request.query_params.get('category', 'ALL')
        
        # Base queryset
        queryset = RadarAlert.objects.all()
        
        # Filter by alert category
        if alert_category == 'SCREENING':
            queryset = queryset.filter(source_strategy__in=['Bullish_Scan', 'Daily_Confluence_Scan', 'Full_Scan'])
        elif alert_category == 'ENTRY':
            queryset = queryset.filter(source_strategy='RealTime_ORB')
        
        # Filter by status
        if status == 'ACTIVE':
            queryset = queryset.filter(status='ACTIVE')
        elif status == 'EXPIRED':
            queryset = queryset.filter(status='EXPIRED')
        elif status == 'ALL':
            pass
        
        return queryset.order_by('-timestamp')

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        alerts_data = response.data.get('results', [])
        if not alerts_data: 
            return response
            
        instrument_keys = {a['instrument_key'] for a in alerts_data}
        instruments = Instrument.objects.filter(instrument_key__in=instrument_keys).values('instrument_key', 'tradingsymbol')
        symbol_map = {i['instrument_key']: i['tradingsymbol'] for i in instruments}
        
        for alert in alerts_data:
            alert['tradingsymbol'] = symbol_map.get(alert['instrument_key'], '')
            
            # Determine alert category
            if alert.get('source_strategy') == 'RealTime_ORB':
                alert['category'] = 'ENTRY'
                alert['is_time_sensitive'] = True
            else:
                alert['category'] = 'SCREENING'
                alert['is_time_sensitive'] = False
            
            # Add remaining time for time-sensitive alerts only
            if alert.get('is_time_sensitive') and alert.get('status') == 'ACTIVE' and alert.get('expires_at'):
                now = timezone.now()
                expires_at = timezone.datetime.fromisoformat(alert['expires_at'].replace('Z', '+00:00'))
                if now < expires_at:
                    delta = expires_at - now
                    alert['remaining_minutes'] = int(delta.total_seconds() / 60)
                else:
                    alert['remaining_minutes'] = 0
            else:
                alert['remaining_minutes'] = None
        
        response.data['results'] = alerts_data
        return response

class TradeLogListCreateView(generics.ListCreateAPIView):
    queryset = TradeLog.objects.all()
    serializer_class = TradeLogSerializer

class TradeLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TradeLog.objects.all()
    serializer_class = TradeLogSerializer

# --- New Scanning API ---

@api_view(['POST'])
@csrf_exempt
def trigger_scan(request):
    """
    Trigger actual scanning (screening + intraday) and return results
    """
    try:
        data = request.data
        scan_type = data.get('scan_type', 'comprehensive')  # comprehensive, screening, intraday
        market_hours = data.get('market_hours', False)
        
        # Get current alerts count before scan
        current_alerts_count = RadarAlert.objects.filter(
            status='ACTIVE',
            expires_at__gt=datetime.now()
        ).count()
        
        start_time = time.time()
        
        # Determine what to scan based on scan_type and market hours
        if scan_type == 'comprehensive':
            # Run both screening and intraday scans
            scan_commands = []
            
            # Always run screening scan
            scan_commands.append('screening')
            
            # Only run intraday scan during market hours
            if market_hours:
                scan_commands.append('intraday')
                
        elif scan_type == 'screening':
            scan_commands = ['screening']
        elif scan_type == 'intraday':
            if market_hours:
                scan_commands = ['intraday']
            else:
                return Response({
                    'error': 'Intraday scan only available during market hours'
                }, status=400)
        else:
            return Response({
                'error': 'Invalid scan_type. Use: comprehensive, screening, or intraday'
            }, status=400)
        
        # Run the actual scans
        scan_results = []
        stocks_scanned = 0
        
        for scan_command in scan_commands:
            try:
                # Run the scanner using the production system
                if scan_command == 'screening':
                    # Run premarket scanner
                    result = run_premarket_scanner()
                    scan_results.append({
                        'type': 'screening',
                        'success': result['success'],
                        'alerts_found': result.get('alerts_found', 0),
                        'stocks_scanned': result.get('stocks_scanned', 0),
                        'message': result.get('message', '')
                    })
                    stocks_scanned += result.get('stocks_scanned', 0)
                    
                elif scan_command == 'intraday':
                    # Run intraday scanner
                    result = run_intraday_scanner()
                    scan_results.append({
                        'type': 'intraday',
                        'success': result['success'],
                        'alerts_found': result.get('alerts_found', 0),
                        'stocks_scanned': result.get('stocks_scanned', 0),
                        'message': result.get('message', '')
                    })
                    stocks_scanned += result.get('stocks_scanned', 0)
                    
            except Exception as e:
                scan_results.append({
                    'type': scan_command,
                    'success': False,
                    'error': str(e)
                })
        
        scan_duration = round(time.time() - start_time, 2)
        
        # Get new alerts count after scan
        new_alerts_count = RadarAlert.objects.filter(
            status='ACTIVE',
            expires_at__gt=datetime.now()
        ).count()
        
        new_alerts = new_alerts_count - current_alerts_count
        
        # Return comprehensive scan results
        return Response({
            'success': True,
            'scan_type': scan_type,
            'market_hours': market_hours,
            'scan_duration': scan_duration,
            'stocks_scanned': stocks_scanned,
            'new_alerts': max(0, new_alerts),  # Ensure non-negative
            'total_alerts': new_alerts_count,
            'scan_results': scan_results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

def run_premarket_scanner():
    """
    Run the premarket scanner and return results
    """
    try:
        # Path to the production system script
        script_path = os.path.join(settings.BASE_DIR, '..', 'radar_engine_cloud_function', 'production_system.py')
        
        # Run the premarket scanner
        result = subprocess.run([
            sys.executable, script_path, '--premarket-scan'
        ], capture_output=True, text=True, cwd=os.path.dirname(script_path))
        
        if result.returncode == 0:
            # Parse the output to get results
            output_lines = result.stdout.strip().split('\n')
            alerts_found = 0
            stocks_scanned = 0
            
            for line in output_lines:
                if 'alerts found' in line.lower():
                    try:
                        alerts_found = int(line.split()[0])
                    except:
                        pass
                elif 'stocks scanned' in line.lower():
                    try:
                        stocks_scanned = int(line.split()[0])
                    except:
                        pass
            
            return {
                'success': True,
                'alerts_found': alerts_found,
                'stocks_scanned': stocks_scanned,
                'message': 'Premarket scan completed successfully'
            }
        else:
            return {
                'success': False,
                'error': result.stderr,
                'message': 'Premarket scan failed'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Error running premarket scanner'
        }

def run_intraday_scanner():
    """
    Run the intraday scanner and return results
    """
    try:
        # Path to the production system script
        script_path = os.path.join(settings.BASE_DIR, '..', 'radar_engine_cloud_function', 'production_system.py')
        
        # Run the intraday scanner
        result = subprocess.run([
            sys.executable, script_path, '--intraday-scan'
        ], capture_output=True, text=True, cwd=os.path.dirname(script_path))
        
        if result.returncode == 0:
            # Parse the output to get results
            output_lines = result.stdout.strip().split('\n')
            alerts_found = 0
            stocks_scanned = 0
            
            for line in output_lines:
                if 'alerts found' in line.lower():
                    try:
                        alerts_found = int(line.split()[0])
                    except:
                        pass
                elif 'stocks scanned' in line.lower():
                    try:
                        stocks_scanned = int(line.split()[0])
                    except:
                        pass
            
            return {
                'success': True,
                'alerts_found': alerts_found,
                'stocks_scanned': stocks_scanned,
                'message': 'Intraday scan completed successfully'
            }
        else:
            return {
                'success': False,
                'error': result.stderr,
                'message': 'Intraday scan failed'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Error running intraday scanner'
        }

@api_view(['GET'])
def virtual_trading_dashboard(request):
    """
    Get virtual trading dashboard data for the current user with real-time P&L calculations and advanced insights
    """
    if not request.user.is_authenticated:
        return Response(
            {'error': 'Authentication required. Please log in first.'},
            status=401
        )
    try:
        wallet = VirtualWallet.objects.get(user=request.user)
        # Get recent trades
        recent_trades = VirtualTrade.objects.filter(wallet=wallet).order_by('-entry_time')[:10]
        # Get open trades with real-time P&L calculations
        open_trades = VirtualTrade.objects.filter(wallet=wallet, status='EXECUTED')
        open_trades_data = []
        total_unrealized_pnl = Decimal('0.00')
        for trade in open_trades:
            current_price = get_current_market_price(trade.instrument_key)
            trade_data = VirtualTradeSerializer(trade).data
            if current_price:
                if trade.trade_type == 'BUY':
                    unrealized_pnl = (current_price - trade.entry_price) * trade.quantity
                else:
                    unrealized_pnl = (trade.entry_price - current_price) * trade.quantity
                unrealized_pnl_percentage = (unrealized_pnl / (trade.entry_price * trade.quantity)) * 100
                total_unrealized_pnl += unrealized_pnl
                trade_data.update({
                    'current_price': float(current_price),
                    'unrealized_pnl': float(unrealized_pnl),
                    'unrealized_pnl_percentage': float(unrealized_pnl_percentage),
                    'is_profitable': unrealized_pnl > 0
                })
            else:
                trade_data.update({
                    'current_price': None,
                    'unrealized_pnl': None,
                    'unrealized_pnl_percentage': None,
                    'is_profitable': None
                })
            open_trades_data.append(trade_data)
        # Get open positions (legacy)
        open_positions = VirtualPosition.objects.filter(wallet=wallet)
        # Get trade statistics
        closed_trades = VirtualTrade.objects.filter(wallet=wallet, status='CLOSED')
        profitable_trades = closed_trades.filter(pnl__gt=0).count()
        total_closed_trades = closed_trades.count()
        avg_profit = closed_trades.filter(pnl__gt=0).aggregate(avg=Avg('pnl'))['avg'] or 0
        avg_loss = closed_trades.filter(pnl__lt=0).aggregate(avg=Avg('pnl'))['avg'] or 0
        # Calculate total portfolio value (balance + unrealized P&L)
        total_portfolio_value = wallet.balance + total_unrealized_pnl
        # --- Advanced Insights ---
        # Best/Worst Trade
        best_trade = closed_trades.order_by('-pnl').first()
        worst_trade = closed_trades.order_by('pnl').first()
        # Per-strategy stats
        strategy_stats = defaultdict(lambda: {'count': 0, 'win': 0, 'loss': 0, 'total_pnl': 0})
        for trade in closed_trades:
            strategy = trade.alert.source_strategy if trade.alert else 'Unknown'
            strategy_stats[strategy]['count'] += 1
            if trade.pnl and trade.pnl > 0:
                strategy_stats[strategy]['win'] += 1
            elif trade.pnl and trade.pnl < 0:
                strategy_stats[strategy]['loss'] += 1
            strategy_stats[strategy]['total_pnl'] += float(trade.pnl or 0)
        strategy_insights = []
        for strat, stats in strategy_stats.items():
            win_rate = (stats['win'] / stats['count']) * 100 if stats['count'] else 0
            avg_pnl = stats['total_pnl'] / stats['count'] if stats['count'] else 0
            strategy_insights.append({
                'strategy': strat,
                'count': stats['count'],
                'win_rate': win_rate,
                'avg_pnl': avg_pnl
            })
        # Equity curve (daily balance)
        equity_curve = []
        daily = closed_trades.annotate(day=TruncDate('exit_time')).values('day').annotate(
            daily_pnl=Sum('pnl')
        ).order_by('day')
        balance = float(wallet.balance)
        for d in daily:
            balance += float(d['daily_pnl'] or 0)
            equity_curve.append({'date': d['day'], 'balance': balance})
        # Win/loss streaks
        streaks = {'current_win': 0, 'current_loss': 0, 'longest_win': 0, 'longest_loss': 0}
        last_result = None
        current_win = current_loss = longest_win = longest_loss = 0
        for trade in closed_trades.order_by('exit_time'):
            if trade.pnl is not None:
                if trade.pnl > 0:
                    if last_result == 'win':
                        current_win += 1
                    else:
                        current_win = 1
                    longest_win = max(longest_win, current_win)
                    current_loss = 0
                    last_result = 'win'
                elif trade.pnl < 0:
                    if last_result == 'loss':
                        current_loss += 1
                    else:
                        current_loss = 1
                    longest_loss = max(longest_loss, current_loss)
                    current_win = 0
                    last_result = 'loss'
        streaks['current_win'] = current_win
        streaks['current_loss'] = current_loss
        streaks['longest_win'] = longest_win
        streaks['longest_loss'] = longest_loss
        # Most traded stocks
        symbol_counts = Counter([t.tradingsymbol for t in closed_trades])
        most_traded = symbol_counts.most_common(5)
        # Fastest/slowest trade
        fastest_trade = slowest_trade = None
        min_duration = None
        max_duration = None
        for trade in closed_trades:
            if trade.entry_time and trade.exit_time:
                duration = (trade.exit_time - trade.entry_time).total_seconds()
                if min_duration is None or duration < min_duration:
                    min_duration = duration
                    fastest_trade = trade
                if max_duration is None or duration > max_duration:
                    max_duration = duration
                    slowest_trade = trade
        dashboard_data = {
            'wallet': VirtualWalletSerializer(wallet).data,
            'recent_trades': VirtualTradeSerializer(recent_trades, many=True).data,
            'open_trades': open_trades_data,
            'open_positions': VirtualPositionSerializer(open_positions, many=True).data,
            'statistics': {
                'total_unrealized_pnl': float(total_unrealized_pnl),
                'total_portfolio_value': float(total_portfolio_value),
                'profitable_trades': profitable_trades,
                'total_closed_trades': total_closed_trades,
                'avg_profit': avg_profit,
                'avg_loss': avg_loss,
                'profit_factor': abs(avg_profit / avg_loss) if avg_loss != 0 else 0,
                'open_positions_count': open_trades.count()
            },
            'insights': {
                'best_trade': VirtualTradeSerializer(best_trade).data if best_trade else None,
                'worst_trade': VirtualTradeSerializer(worst_trade).data if worst_trade else None,
                'strategy_stats': strategy_insights,
                'equity_curve': equity_curve,
                'streaks': streaks,
                'most_traded': [{'symbol': s, 'count': c} for s, c in most_traded],
                'fastest_trade': VirtualTradeSerializer(fastest_trade).data if fastest_trade else None,
                'slowest_trade': VirtualTradeSerializer(slowest_trade).data if slowest_trade else None
            }
        }
        return Response(dashboard_data)
    except VirtualWallet.DoesNotExist:
        return Response(
            {'error': 'Virtual wallet not found. Please create one first.'},
            status=404
        )
    except Exception as e:
        return Response(
            {'error': f'Error loading dashboard: {str(e)}'},
            status=500
        )

@api_view(['GET'])
def get_screener_with_entry_status(request):
    """
    Return the full premarket screener list for today, and for each screener stock, include a field indicating if an entry alert exists (and its ID/status if so).
    """
    today = timezone.now().date()
    # Get all screening alerts for today (all strategies)
    screening_alerts = RadarAlert.objects.filter(
        source_strategy__in=['Bullish_Scan', 'Daily_Confluence_Scan', 'Full_Scan'],
        timestamp__date=today
    ).order_by('-timestamp')

    # Get all entry alerts for today
    entry_alerts = RadarAlert.objects.filter(
        source_strategy__in=['RealTime_ORB', 'Intraday_ORB_Breakout'],
        timestamp__date=today
    )
    entry_alert_map = {}
    for entry in entry_alerts:
        entry_alert_map[entry.instrument_key] = {
            'id': entry.id,
            'status': entry.status,
            'expires_at': entry.expires_at,
            'priority': entry.priority,
            'alert_type': entry.alert_type,
            'source_strategy': entry.source_strategy
        }

    # Get instrument symbol map
    instrument_keys = set(a.instrument_key for a in screening_alerts)
    instruments = Instrument.objects.filter(instrument_key__in=instrument_keys).values('instrument_key', 'tradingsymbol')
    symbol_map = {i['instrument_key']: i['tradingsymbol'] for i in instruments}

    results = []
    for alert in screening_alerts:
        entry_status = 'waiting'
        entry_alert_info = None
        if alert.instrument_key in entry_alert_map:
            entry_status = 'triggered'
            entry_alert_info = entry_alert_map[alert.instrument_key]
        results.append({
            'id': alert.id,
            'instrument_key': alert.instrument_key,
            'tradingsymbol': symbol_map.get(alert.instrument_key, ''),
            'source_strategy': alert.source_strategy,
            'alert_details': alert.alert_details,
            'indicators': alert.indicators,
            'timestamp': alert.timestamp,
            'status': alert.status,
            'priority': alert.priority,
            'alert_type': alert.alert_type,
            'entry_status': entry_status,
            'entry_alert': entry_alert_info
        })
    return Response({'results': results})

@api_view(['GET'])
def trade_journal_dashboard(request):
    """
    Get trade journal analytics/insights for real trades (TradeLog) for the current user.
    """
    # Removed authentication check for public access
    try:
        trades = TradeLog.objects.filter(instrument__isnull=False)
        closed_trades = trades.filter(exit_price__isnull=False)
        total_trades = trades.count()
        win_trades = closed_trades.filter(pnl__gt=0).count()
        loss_trades = closed_trades.filter(pnl__lt=0).count()
        win_rate = (win_trades / closed_trades.count()) * 100 if closed_trades.count() else 0
        avg_profit = closed_trades.filter(pnl__gt=0).aggregate(avg=Avg('pnl'))['avg'] or 0
        avg_loss = closed_trades.filter(pnl__lt=0).aggregate(avg=Avg('pnl'))['avg'] or 0
        best_trade = closed_trades.order_by('-pnl').first()
        worst_trade = closed_trades.order_by('pnl').first()
        # Per-strategy stats (if strategy field exists)
        strategy_stats = defaultdict(lambda: {'count': 0, 'win': 0, 'loss': 0, 'total_pnl': 0})
        for trade in closed_trades:
            strategy = getattr(trade, 'strategy', 'Unknown')
            strategy_stats[strategy]['count'] += 1
            if trade.pnl and trade.pnl > 0:
                strategy_stats[strategy]['win'] += 1
            elif trade.pnl and trade.pnl < 0:
                strategy_stats[strategy]['loss'] += 1
            strategy_stats[strategy]['total_pnl'] += float(trade.pnl or 0)
        strategy_insights = []
        for strat, stats in strategy_stats.items():
            win_rate_s = (stats['win'] / stats['count']) * 100 if stats['count'] else 0
            avg_pnl = stats['total_pnl'] / stats['count'] if stats['count'] else 0
            strategy_insights.append({
                'strategy': strat,
                'count': stats['count'],
                'win_rate': win_rate_s,
                'avg_pnl': avg_pnl
            })
        # Equity curve (daily balance)
        equity_curve = []
        daily = closed_trades.annotate(day=TruncDate('trade_date')).values('day').annotate(
            daily_pnl=Sum('pnl')
        ).order_by('day')
        balance = 0
        for d in daily:
            balance += float(d['daily_pnl'] or 0)
            equity_curve.append({'date': d['day'], 'balance': balance})
        # Win/loss streaks
        streaks = {'current_win': 0, 'current_loss': 0, 'longest_win': 0, 'longest_loss': 0}
        last_result = None
        current_win = current_loss = longest_win = longest_loss = 0
        for trade in closed_trades.order_by('trade_date'):
            if trade.pnl is not None:
                if trade.pnl > 0:
                    if last_result == 'win':
                        current_win += 1
                    else:
                        current_win = 1
                    longest_win = max(longest_win, current_win)
                    current_loss = 0
                    last_result = 'win'
                elif trade.pnl < 0:
                    if last_result == 'loss':
                        current_loss += 1
                    else:
                        current_loss = 1
                    longest_loss = max(longest_loss, current_loss)
                    current_win = 0
                    last_result = 'loss'
        streaks['current_win'] = current_win
        streaks['current_loss'] = current_loss
        streaks['longest_win'] = longest_win
        streaks['longest_loss'] = longest_loss
        # Most traded stocks
        symbol_counts = Counter([t.instrument.tradingsymbol for t in closed_trades if t.instrument])
        most_traded = symbol_counts.most_common(5)
        # Fastest/slowest trade
        fastest_trade = slowest_trade = None
        min_duration = None
        max_duration = None
        for trade in closed_trades:
            if hasattr(trade, 'entry_time') and hasattr(trade, 'exit_time') and trade.entry_time and trade.exit_time:
                duration = (trade.exit_time - trade.entry_time).total_seconds()
                if min_duration is None or duration < min_duration:
                    min_duration = duration
                    fastest_trade = trade
                if max_duration is None or duration > max_duration:
                    max_duration = duration
                    slowest_trade = trade
        from .serializers import TradeLogSerializer
        return Response({
            'statistics': {
                'total_trades': total_trades,
                'win_trades': win_trades,
                'loss_trades': loss_trades,
                'win_rate': win_rate,
                'avg_profit': avg_profit,
                'avg_loss': avg_loss,
            },
            'insights': {
                'best_trade': TradeLogSerializer(best_trade).data if best_trade else None,
                'worst_trade': TradeLogSerializer(worst_trade).data if worst_trade else None,
                'strategy_stats': strategy_insights,
                'equity_curve': equity_curve,
                'streaks': streaks,
                'most_traded': [{'symbol': s, 'count': c} for s, c in most_traded],
                'fastest_trade': TradeLogSerializer(fastest_trade).data if fastest_trade else None,
                'slowest_trade': TradeLogSerializer(slowest_trade).data if slowest_trade else None
            }
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)
