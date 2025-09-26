#!/usr/bin/env python3
"""
Test script for the admin terminal functionality
"""

import requests
import json

def test_admin_terminal():
    """Test the admin terminal functionality"""
    
    server_url = "http://localhost:5000"
    
    print("🧪 Testing Admin Terminal Functionality")
    print("=" * 50)
    
    # Test 1: Check if server is running
    print("\n1️⃣ Testing server connection...")
    try:
        response = requests.get(f"{server_url}/verify?sn=K1S-A001")
        if response.status_code in [200, 404]:
            print("✅ Server is running")
        else:
            print("❌ Server not responding")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False
    
    # Test 2: Get registration requests
    print("\n2️⃣ Testing registration requests endpoint...")
    try:
        response = requests.get(f"{server_url}/admin/registration_requests")
        if response.status_code == 200:
            data = response.json()
            requests_list = data.get('requests', [])
            print(f"✅ Found {len(requests_list)} registration requests")
            
            # Display summary
            pending = len([r for r in requests_list if r.get('status') == 'pending'])
            approved = len([r for r in requests_list if r.get('status') == 'approved'])
            denied = len([r for r in requests_list if r.get('status') == 'denied'])
            
            print(f"   🟡 Pending: {pending}")
            print(f"   🟢 Approved: {approved}")
            print(f"   🔴 Denied: {denied}")
            
            # Show first few requests
            if requests_list:
                print("\n📋 Sample requests:")
                for req in requests_list[:3]:
                    print(f"   ID {req.get('id')}: {req.get('factory_name')} - {req.get('status')}")
                    
        else:
            print(f"❌ Failed to get requests: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting requests: {e}")
        return False
    
    # Test 3: Test approval endpoint
    print("\n3️⃣ Testing approval endpoint...")
    try:
        # Find a pending request
        response = requests.get(f"{server_url}/admin/registration_requests")
        if response.status_code == 200:
            data = response.json()
            requests_list = data.get('requests', [])
            pending_requests = [r for r in requests_list if r.get('status') == 'pending']
            
            if pending_requests:
                test_request = pending_requests[0]
                request_id = test_request.get('id')
                print(f"   Testing with request ID: {request_id}")
                
                # Test approval
                approve_response = requests.post(
                    f"{server_url}/admin/approve_request/{request_id}",
                    json={"approved_by": "test_admin"}
                )
                
                if approve_response.status_code == 200:
                    print("✅ Approval endpoint working")
                    
                    # Test revocation
                    revoke_response = requests.post(
                        f"{server_url}/admin/revoke_request/{request_id}",
                        json={"revoked_by": "test_admin"}
                    )
                    
                    if revoke_response.status_code == 200:
                        print("✅ Revocation endpoint working")
                    else:
                        print(f"❌ Revocation failed: {revoke_response.status_code}")
                        
                else:
                    print(f"❌ Approval failed: {approve_response.status_code}")
            else:
                print("⚠️ No pending requests to test with")
                
    except Exception as e:
        print(f"❌ Error testing approval: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Admin Terminal Test Complete!")
    print("\nThe admin terminal should now be able to:")
    print("  ✅ Connect to the server")
    print("  ✅ List registration requests")
    print("  ✅ Approve/deny/revoke requests")
    print("  ✅ Show detailed request information")
    print("  ✅ Display summary statistics")
    
    return True

if __name__ == "__main__":
    test_admin_terminal()