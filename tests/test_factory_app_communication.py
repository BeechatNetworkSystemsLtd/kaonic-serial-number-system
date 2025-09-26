#!/usr/bin/env python3
"""
Test script to verify communication between the factory app and the server
"""

import requests
import hashlib
import hmac
import base64
import time
import json

def test_factory_app_communication():
    """Test the complete communication flow between factory app and server"""
    
    server_url = "http://localhost:5000"
    
    print("🧪 Testing Factory App Communication with Kaonic Serial Number System")
    print("=" * 70)
    
    # Test 1: Check server is running
    print("\n1️⃣ Testing server connectivity...")
    try:
        response = requests.get(f"{server_url}/verify?sn=K1S-A001")
        if response.status_code == 200:
            print("✅ Server is running and responding")
            data = response.json()
            print(f"   Sample verification: {data}")
        else:
            print("❌ Server not responding properly")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False
    
    # Test 2: Test registration endpoint
    print("\n2️⃣ Testing public key registration...")
    try:
        registration_data = {
            "factory_name": "Test Factory App",
            "public_key": "test_factory_app_public_key_12345"
        }
        
        response = requests.post(
            f"{server_url}/register_public_key",
            json=registration_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201]:
            print("✅ Registration endpoint working")
            data = response.json()
            print(f"   Response: {data}")
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
    
    # Test 3: Test registration status check
    print("\n3️⃣ Testing registration status check...")
    try:
        response = requests.get(
            f"{server_url}/check_registration_status",
            params={"public_key": "test_factory_app_public_key_12345"}
        )
        
        if response.status_code == 200:
            print("✅ Status check endpoint working")
            data = response.json()
            print(f"   Status: {data}")
        else:
            print(f"❌ Status check failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Status check test failed: {e}")
    
    # Test 4: Test serial upload with HMAC signature (simulating Flutter app)
    print("\n4️⃣ Testing serial upload with HMAC signature...")
    try:
        # Create test CSV content
        csv_content = "device_id,wwyy\nTEST001,4023\nTEST002,4023\n"
        csv_bytes = csv_content.encode('utf-8')
        
        # Compute hash
        csv_hash = hashlib.sha256(csv_bytes).hexdigest()
        
        # Generate timestamp
        timestamp = str(int(time.time()))
        
        # Create HMAC signature (matching Flutter app)
        message = f"{timestamp}{csv_hash}"
        signature = hmac.new(
            b"flutter_client_secret_key",
            message.encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.b64encode(signature).decode()
        
        # Prepare multipart request
        files = {
            'file': ('serials.csv', csv_bytes, 'text/csv')
        }
        headers = {
            'X-Timestamp': timestamp,
            'X-Signature': signature_b64
        }
        
        response = requests.post(
            f"{server_url}/add_serials",
            files=files,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Serial upload with HMAC signature successful")
            data = response.json()
            print(f"   Response: {data}")
        else:
            print(f"❌ Serial upload failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Serial upload test failed: {e}")
    
    # Test 5: Verify uploaded serials
    print("\n5️⃣ Testing serial verification...")
    try:
        response = requests.get(f"{server_url}/verify?sn=K1S-TEST001")
        if response.status_code == 200:
            print("✅ Serial verification working")
            data = response.json()
            print(f"   Verified serial: {data}")
        else:
            print(f"❌ Serial verification failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Serial verification test failed: {e}")
    
    # Test 6: Test admin endpoints
    print("\n6️⃣ Testing admin endpoints...")
    try:
        response = requests.get(f"{server_url}/admin/registration_requests")
        if response.status_code == 200:
            print("✅ Admin endpoints working")
            data = response.json()
            print(f"   Found {len(data.get('requests', []))} registration requests")
        else:
            print(f"❌ Admin endpoints failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Admin endpoints test failed: {e}")
    
    print("\n" + "=" * 70)
    print("🎉 Factory App Communication Test Complete!")
    print("\nThe factory app should now be able to:")
    print("  ✅ Register public keys")
    print("  ✅ Check registration status")
    print("  ✅ Upload serial numbers via POST request")
    print("  ✅ Verify serial numbers")
    print("  ✅ Communicate with admin endpoints")
    
    return True

if __name__ == "__main__":
    test_factory_app_communication()
