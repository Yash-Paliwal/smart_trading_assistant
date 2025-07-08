#!/usr/bin/env python3
"""
Test script for the new scanning API endpoint
"""

import requests
import json
import time

def test_scan_api():
    """Test the new scanning API endpoint"""
    
    # API endpoint
    url = "http://localhost:8000/api/trigger-scan/"
    
    # Test data
    test_cases = [
        {
            "name": "Comprehensive Scan (Market Hours)",
            "data": {
                "scan_type": "comprehensive",
                "market_hours": True
            }
        },
        {
            "name": "Screening Only",
            "data": {
                "scan_type": "screening",
                "market_hours": False
            }
        },
        {
            "name": "Intraday Only (Market Hours)",
            "data": {
                "scan_type": "intraday",
                "market_hours": True
            }
        },
        {
            "name": "Intraday Only (Market Closed)",
            "data": {
                "scan_type": "intraday",
                "market_hours": False
            }
        }
    ]
    
    print("🧪 Testing Scanning API Endpoint")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\n📋 Test: {test_case['name']}")
        print("-" * 30)
        
        try:
            start_time = time.time()
            
            response = requests.post(
                url,
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=120  # 2 minutes timeout
            )
            
            duration = time.time() - start_time
            
            print(f"⏱️ Response time: {duration:.2f}s")
            print(f"📊 Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Success!")
                print(f"   Scan type: {data.get('scan_type')}")
                print(f"   Market hours: {data.get('market_hours')}")
                print(f"   Scan duration: {data.get('scan_duration')}s")
                print(f"   Stocks scanned: {data.get('stocks_scanned')}")
                print(f"   New alerts: {data.get('new_alerts')}")
                print(f"   Total alerts: {data.get('total_alerts')}")
                
                # Show scan results
                scan_results = data.get('scan_results', [])
                for result in scan_results:
                    print(f"   {result['type']}: {'✅' if result['success'] else '❌'} - {result.get('alerts_found', 0)} alerts")
                
            else:
                print("❌ Failed!")
                print(f"   Error: {response.text}")
                
        except requests.exceptions.Timeout:
            print("⏰ Timeout - Scan took too long")
        except requests.exceptions.ConnectionError:
            print("🔌 Connection Error - Make sure Django server is running")
        except Exception as e:
            print(f"💥 Unexpected error: {e}")
        
        print()

if __name__ == "__main__":
    test_scan_api() 