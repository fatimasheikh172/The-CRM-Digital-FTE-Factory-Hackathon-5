"""
Test script to verify the ticket ID bug fix.

This script:
1. Submits a new web form
2. Gets the ticket ID from response
3. Calls GET /support/ticket/{ticket_id}
4. Verifies it returns 200 with ticket details
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_ticket_flow():
    """Test the complete ticket flow."""
    print("=" * 70)
    print("Testing Ticket ID Bug Fix")
    print("=" * 70)
    
    # Step 1: Submit a new form
    print("\n1. Submitting web form...")
    form_data = {
        "name": "Test User",
        "email": "test.bugfix@example.com",
        "subject": "Bug Fix Test Ticket",
        "category": "General",
        "priority": "medium",
        "message": "This is a test to verify the ticket ID bug is fixed."
    }
    
    try:
        response = requests.post(f"{BASE_URL}/support/submit", json=form_data)
        print(f"   Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ERROR: Form submission failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        result = response.json()
        ticket_id = result.get('ticket_id')
        print(f"   Ticket ID returned: {ticket_id}")
        
        if not ticket_id:
            print("   ERROR: No ticket_id in response")
            return False
            
    except Exception as e:
        print(f"   ERROR: {e}")
        print("   Make sure the API server is running on localhost:8000")
        return False
    
    # Step 2: Get the ticket by ID
    print(f"\n2. Getting ticket {ticket_id}...")
    try:
        response = requests.get(f"{BASE_URL}/support/ticket/{ticket_id}")
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            ticket = response.json()
            print(f"   ✓ SUCCESS! Ticket found:")
            print(f"      - ID: {ticket.get('ticket_id')}")
            print(f"      - Status: {ticket.get('status')}")
            print(f"      - Subject: {ticket.get('subject')}")
            print(f"      - Category: {ticket.get('category')}")
            print(f"      - Messages: {len(ticket.get('messages', []))}")
            return True
        elif response.status_code == 404:
            print(f"   ✗ FAILED: Ticket {ticket_id} not found (404)")
            print("   This means the bug is NOT fixed!")
            return False
        else:
            print(f"   ERROR: Unexpected status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_ticket_flow()
    
    print("\n" + "=" * 70)
    if success:
        print("✓ BUG FIX VERIFIED: Ticket ID lookup is working correctly!")
    else:
        print("✗ BUG NOT FIXED: Ticket ID lookup still failing!")
    print("=" * 70)
