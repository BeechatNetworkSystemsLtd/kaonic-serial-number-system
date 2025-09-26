#!/usr/bin/env python3
"""
Complete demonstration of the registration workflow.
This script shows the entire process from registration to approval.
"""

import requests
import json
import time

def demo_complete_workflow():
    """Demonstrate the complete registration workflow"""
    base_url = "http://localhost:5000"
    
    print("🔐 Kaonic Serial System - Complete Workflow Demo")
    print("=" * 60)
    
    # Step 1: Register a new factory
    print("\n1️⃣ FACTORY REGISTRATION")
    print("-" * 30)
    
    factory_name = "Demo Factory"
    public_key = "demo_public_key_12345_workflow_test"
    
    print(f"📱 Factory: {factory_name}")
    print(f"🔑 Public Key: {public_key[:30]}...")
    
    try:
        response = requests.post(f"{base_url}/register_public_key", json={
            "factory_name": factory_name,
            "public_key": public_key
        })
        
        if response.status_code in [200, 201]:
            data = response.json()
            request_id = data.get('request_id')
            print(f"✅ Registration successful! Request ID: {request_id}")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return
    
    # Step 2: Check status (should be pending)
    print("\n2️⃣ STATUS CHECK")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/check_registration_status", params={
            "public_key": public_key
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Status: {data.get('status').upper()}")
            print(f"📅 Created: {data.get('created_at')}")
        else:
            print(f"❌ Status check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Status check error: {e}")
    
    # Step 3: Admin approval simulation
    print("\n3️⃣ ADMIN APPROVAL")
    print("-" * 30)
    
    print("🔧 Admin would now use: python admin_terminal.py")
    print("   - Select option [2] to process pending requests")
    print("   - Choose [A] to approve the request")
    
    # Simulate admin approval
    print("\n🤖 Simulating admin approval...")
    try:
        response = requests.post(f"{base_url}/admin/approve_request/{request_id}", json={
            "approved_by": "demo_admin"
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data.get('message')}")
        else:
            print(f"❌ Approval failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Approval error: {e}")
        return
    
    # Step 4: Check status again (should be approved)
    print("\n4️⃣ FINAL STATUS CHECK")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/check_registration_status", params={
            "public_key": public_key
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Status: {data.get('status').upper()}")
            print(f"✅ Approved: {data.get('approved_at')}")
            print(f"👤 Approved by: {data.get('approved_by')}")
        else:
            print(f"❌ Status check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Status check error: {e}")
    
    # Step 5: Show summary
    print("\n5️⃣ SUMMARY")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/admin/registration_requests")
        
        if response.status_code == 200:
            data = response.json()
            request_list = data.get('requests', [])
            
            total = len(request_list)
            pending = len([r for r in request_list if r['status'] == 'pending'])
            approved = len([r for r in request_list if r['status'] == 'approved'])
            denied = len([r for r in request_list if r['status'] == 'denied'])
            
            print(f"📊 Total Requests: {total}")
            print(f"⏳ Pending: {pending}")
            print(f"✅ Approved: {approved}")
            print(f"❌ Denied: {denied}")
        else:
            print(f"❌ Failed to get summary: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Summary error: {e}")
    
    print("\n🎯 WORKFLOW COMPLETE!")
    print("=" * 60)
    print("✅ Factory registered successfully")
    print("✅ Admin approved the request")
    print("✅ Factory can now upload serial numbers")
    print("\n📱 Next: Test with Flutter app:")
    print("   1. Generate keys in Flutter app")
    print("   2. Register public key")
    print("   3. Wait for admin approval")
    print("   4. Upload CSV files")

if __name__ == "__main__":
    demo_complete_workflow()
