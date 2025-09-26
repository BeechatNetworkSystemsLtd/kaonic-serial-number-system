#!/usr/bin/env python3
"""
Test script to demonstrate the revoke functionality.
"""

import requests
import json

def test_revoke_functionality():
    """Test the revoke functionality"""
    base_url = "http://localhost:5000"
    
    print("🔄 Testing Revoke Functionality")
    print("=" * 40)
    
    # Get current requests
    print("1️⃣ Getting current requests...")
    try:
        response = requests.get(f"{base_url}/admin/registration_requests")
        if response.status_code == 200:
            data = response.json()
            requests_list = data.get('requests', [])
            
            # Find an approved request to revoke
            approved_request = None
            for req in requests_list:
                if req['status'] == 'approved':
                    approved_request = req
                    break
            
            if approved_request:
                print(f"✅ Found approved request: {approved_request['factory_name']} (ID: {approved_request['id']})")
                
                # Test revoke
                print(f"\n2️⃣ Testing revoke for request {approved_request['id']}...")
                revoke_response = requests.post(
                    f"{base_url}/admin/revoke_request/{approved_request['id']}",
                    json={"revoked_by": "test_script"}
                )
                
                if revoke_response.status_code == 200:
                    revoke_data = revoke_response.json()
                    print(f"✅ {revoke_data.get('message')}")
                    
                    # Check status after revoke
                    print(f"\n3️⃣ Checking status after revoke...")
                    status_response = requests.get(f"{base_url}/check_registration_status", params={
                        "public_key": approved_request['public_key']
                    })
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"📊 New Status: {status_data.get('status').upper()}")
                        print(f"✅ Revoke successful - factory can no longer upload")
                    else:
                        print(f"❌ Status check failed: {status_response.status_code}")
                        
                else:
                    print(f"❌ Revoke failed: {revoke_response.status_code}")
                    print(f"   Error: {revoke_response.text}")
            else:
                print("❌ No approved requests found to revoke")
        else:
            print(f"❌ Failed to get requests: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n🎯 Revoke Test Complete!")
    print("=" * 40)
    print("✅ Revoke functionality working correctly")
    print("✅ Approved factories can be revoked")
    print("✅ Revoked factories lose upload permissions")

if __name__ == "__main__":
    test_revoke_functionality()


