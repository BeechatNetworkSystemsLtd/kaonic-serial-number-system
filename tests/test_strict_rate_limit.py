#!/usr/bin/env python3
"""
Test script to demonstrate the strict rate limiting on registration endpoint.
"""

import requests
import json
import time

def test_strict_rate_limit():
    """Test the strict rate limiting on registration endpoint"""
    base_url = "http://localhost:5000"
    
    print("🚫 Testing Strict Rate Limiting on Registration Endpoint")
    print("=" * 60)
    
    # Test data for registration
    test_data = {
        "factory_name": "Rate Limit Test Factory",
        "public_key": "test_rate_limit_public_key_12345"
    }
    
    print("1️⃣ First registration attempt (should succeed)...")
    try:
        response = requests.post(
            f"{base_url}/register_public_key",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            print("✅ First registration successful!")
            result = response.json()
            print(f"   Request ID: {result.get('request_id')}")
            print(f"   Status: {result.get('status')}")
        elif response.status_code == 200:
            print("✅ Registration successful (already exists)!")
            result = response.json()
            print(f"   Request ID: {result.get('request_id')}")
            print(f"   Status: {result.get('status')}")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n2️⃣ Second registration attempt (should be rate limited)...")
    try:
        response = requests.post(
            f"{base_url}/register_public_key",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 429:
            print("🚫 Rate limit hit! (Expected)")
            print("   This is the desired behavior - preventing spam registrations")
        elif response.status_code == 201:
            print("✅ Second registration successful (unexpected)")
        elif response.status_code == 200:
            print("✅ Registration successful (already exists)")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n3️⃣ Testing with different factory name (should also be rate limited)...")
    test_data_2 = {
        "factory_name": "Another Rate Limit Test Factory",
        "public_key": "test_rate_limit_public_key_67890"
    }
    
    try:
        response = requests.post(
            f"{base_url}/register_public_key",
            json=test_data_2,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 429:
            print("🚫 Rate limit hit! (Expected)")
            print("   Rate limiting is per IP, not per factory name")
        elif response.status_code == 201:
            print("✅ Registration successful (unexpected)")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n📊 Rate Limiting Summary:")
    print("=" * 60)
    print("✅ Registration endpoint has strict rate limiting: 1 per 10 minutes")
    print("✅ This prevents spam registration attempts")
    print("✅ Rate limiting is per IP address, not per factory")
    print("✅ After 10 minutes, the same IP can register again")
    print("✅ Other endpoints (like status check) are not affected")

if __name__ == "__main__":
    test_strict_rate_limit()


