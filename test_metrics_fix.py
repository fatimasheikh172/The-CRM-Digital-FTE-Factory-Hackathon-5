"""
Test script to verify the metrics bug fix.

This script:
1. Calls GET /metrics/summary
2. Verifies no ERROR in response
3. Returns proper data
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_metrics_summary():
    """Test the metrics summary endpoint."""
    print("=" * 70)
    print("Testing Metrics Summary Bug Fix")
    print("=" * 70)
    
    # Call GET /metrics/summary
    print("\n1. Calling GET /metrics/summary...")
    
    try:
        response = requests.get(f"{BASE_URL}/metrics/summary")
        print(f"   Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ERROR: Request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        result = response.json()
        print(f"   ✓ SUCCESS! Response received:")
        print(f"      - total_tickets_today: {result.get('total_tickets_today')}")
        print(f"      - resolved_rate: {result.get('resolved_rate')}")
        print(f"      - avg_response_time_ms: {result.get('avg_response_time_ms')}")
        print(f"      - escalation_rate: {result.get('escalation_rate')}")
        print(f"      - busiest_channel: {result.get('busiest_channel')}")
        
        # Verify all expected fields are present
        required_fields = [
            'total_tickets_today',
            'resolved_rate',
            'avg_response_time_ms',
            'escalation_rate',
            'busiest_channel'
        ]
        
        for field in required_fields:
            if field not in result:
                print(f"   ✗ ERROR: Missing field '{field}'")
                return False
        
        print(f"\n   ✓ All required fields present!")
        return True
        
    except Exception as e:
        print(f"   ERROR: {e}")
        print("   Make sure the API server is running on localhost:8000")
        return False

def test_metrics_channels():
    """Test the metrics channels endpoint."""
    print("\n" + "=" * 70)
    print("Testing Metrics Channels")
    print("=" * 70)
    
    print("\n1. Calling GET /metrics/channels...")
    
    try:
        response = requests.get(f"{BASE_URL}/metrics/channels")
        print(f"   Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ERROR: Request failed with status {response.status_code}")
            return False
        
        result = response.json()
        print(f"   ✓ SUCCESS! Response received:")
        
        # Check for each channel
        for channel in ['email', 'whatsapp', 'web_form']:
            if channel in result:
                channel_data = result[channel]
                print(f"      {channel}:")
                print(f"         - total_conversations: {channel_data.get('total_conversations')}")
                print(f"         - avg_latency_ms: {channel_data.get('avg_latency_ms')}")
            else:
                print(f"   ✗ ERROR: Missing channel '{channel}'")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("METRICS BUG FIX VERIFICATION")
    print("=" * 70)
    
    success1 = test_metrics_summary()
    success2 = test_metrics_channels()
    
    print("\n" + "=" * 70)
    if success1 and success2:
        print("✓ BUG FIX VERIFIED: Metrics endpoints working correctly!")
        print("  No 'column latency_ms does not exist' errors!")
    else:
        print("✗ BUG NOT FIXED: Metrics endpoints still failing!")
    print("=" * 70)
