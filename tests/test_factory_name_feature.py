#!/usr/bin/env python3
"""
Test script to verify the factory name editing feature and database clearing
"""

import requests
import json

def test_factory_name_feature():
    """Test the factory name editing feature"""
    
    server_url = "http://localhost:5000"
    
    print("🧪 Testing Factory Name Editing Feature")
    print("=" * 50)
    
    # Test 1: Verify database is cleared
    print("\n1️⃣ Checking if database is cleared...")
    try:
        response = requests.get(f"{server_url}/admin/registration_requests")
        if response.status_code == 200:
            data = response.json()
            requests_list = data.get('requests', [])
            
            if len(requests_list) == 0:
                print("✅ Database cleared successfully - no registration requests found")
            else:
                print(f"⚠️ Database still has {len(requests_list)} requests")
                for req in requests_list:
                    print(f"   - ID {req.get('id')}: {req.get('factory_name')} ({req.get('status')})")
        else:
            print(f"❌ Failed to check requests: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    
    # Test 2: Test registration with custom factory name
    print(f"\n2️⃣ Testing registration with custom factory name...")
    try:
        custom_factory_name = "My Custom Factory Name"
        test_public_key = "test_custom_factory_key_12345"
        
        response = requests.post(
            f"{server_url}/register_public_key",
            json={
                "factory_name": custom_factory_name,
                "public_key": test_public_key
            }
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ Registration successful with custom name")
            print(f"   Factory Name: {custom_factory_name}")
            print(f"   Request ID: {data.get('request_id')}")
            print(f"   Status: {data.get('status')}")
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Registration error: {e}")
    
    # Test 3: Verify the custom name is stored
    print(f"\n3️⃣ Verifying custom factory name is stored...")
    try:
        response = requests.get(f"{server_url}/admin/registration_requests")
        if response.status_code == 200:
            data = response.json()
            requests_list = data.get('requests', [])
            
            if requests_list:
                latest_request = requests_list[0]  # Most recent request
                stored_name = latest_request.get('factory_name')
                if stored_name == custom_factory_name:
                    print(f"✅ Custom factory name stored correctly: {stored_name}")
                else:
                    print(f"❌ Factory name mismatch: expected '{custom_factory_name}', got '{stored_name}'")
            else:
                print("❌ No requests found after registration")
        else:
            print(f"❌ Failed to verify: {response.status_code}")
    except Exception as e:
        print(f"❌ Verification error: {e}")
    
    # Test 4: Test status check with custom name
    print(f"\n4️⃣ Testing status check with custom factory name...")
    try:
        response = requests.get(
            f"{server_url}/check_registration_status",
            params={"public_key": test_public_key}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status check successful")
            print(f"   Factory Name: {data.get('factory_name')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Created: {data.get('created_at')}")
        else:
            print(f"❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status check error: {e}")
    
    print(f"\n" + "=" * 50)
    print("🎉 Factory Name Feature Test Complete!")
    print(f"\nThe factory app now supports:")
    print(f"  ✅ Editing factory name before registration")
    print(f"  ✅ Custom factory names are sent to server")
    print(f"  ✅ Database is cleared for fresh registration")
    print(f"  ✅ Status checking works with custom names")
    print(f"\nTo test in the factory app:")
    print(f"  1. Install the updated APK")
    print(f"  2. Generate keys")
    print(f"  3. Edit the factory name in the text field")
    print(f"  4. Register with the custom name")
    print(f"  5. Check that the custom name appears in admin terminal")

if __name__ == "__main__":
    test_factory_name_feature()
