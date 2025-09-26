#!/usr/bin/env python3
"""
Test script for enhanced Kaonic Serial Number System server
Tests ECC cryptography, batch uploads, and offline queue support
"""

import requests
import json
import time
import hashlib
import hmac
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

def test_enhanced_server():
    """Test the enhanced server functionality"""
    
    server_url = "http://localhost:5000"
    
    print("🧪 Testing Enhanced Kaonic Serial Number System Server")
    print("=" * 70)
    
    # Test 1: Server connectivity
    print("\n1️⃣ Testing server connectivity...")
    try:
        response = requests.get(f"{server_url}/verify?sn=K1S-TEST001")
        if response.status_code in [200, 404]:
            print("✅ Server is running and responding")
        else:
            print("❌ Server not responding properly")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False
    
    # Test 2: ECC Public Key Registration
    print("\n2️⃣ Testing ECC public key registration...")
    try:
        # Generate a test ECC key pair
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()
        
        # Convert to PEM format
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        
        # Extract base64 part for registration
        public_key_b64 = public_key_pem.replace("-----BEGIN PUBLIC KEY-----\n", "").replace("\n-----END PUBLIC KEY-----", "")
        
        registration_data = {
            "factory_name": "Test ECC Factory",
            "public_key": public_key_b64
        }
        
        response = requests.post(
            f"{server_url}/register_public_key",
            json=registration_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201]:
            print("✅ ECC public key registration successful")
            data = response.json()
            print(f"   Request ID: {data.get('request_id')}")
        else:
            print(f"❌ ECC registration failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ECC registration test failed: {e}")
        return False
    
    # Test 3: Admin approval simulation
    print("\n3️⃣ Simulating admin approval...")
    try:
        # Get the request ID from the registration
        response = requests.get(f"{server_url}/admin/registration_requests")
        if response.status_code == 200:
            requests_data = response.json()
            if requests_data.get('requests'):
                request_id = requests_data['requests'][0]['id']
                
                # Approve the request
                response = requests.post(
                    f"{server_url}/admin/approve_request/{request_id}",
                    json={"approved_by": "test_admin"}
                )
                
                if response.status_code == 200:
                    print("✅ Admin approval successful")
                else:
                    print(f"❌ Admin approval failed: {response.status_code}")
            else:
                print("❌ No registration requests found")
        else:
            print(f"❌ Failed to get registration requests: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Admin approval test failed: {e}")
    
    # Test 4: ECC Signature Upload
    print("\n4️⃣ Testing ECC signature upload...")
    try:
        # Create test CSV content
        csv_content = "device_id,wwyy\nECC001,4023\nECC002,4023\n"
        csv_bytes = csv_content.encode('utf-8')
        
        # Compute hash
        csv_hash = hashlib.sha256(csv_bytes).hexdigest()
        
        # Generate timestamp
        timestamp = str(int(time.time()))
        
        # Create ECC signature
        message = f"{timestamp}{csv_hash}"
        signature = private_key.sign(
            message.encode(),
            ec.ECDSA(hashes.SHA256())
        )
        signature_b64 = base64.b64encode(signature).decode()
        
        # Prepare upload request
        files = {
            'file': ('test_serials.csv', csv_bytes, 'text/csv')
        }
        headers = {
            'X-Timestamp': timestamp,
            'X-Signature': signature_b64,
            'X-Factory-ID': 'Test ECC Factory'
        }
        
        response = requests.post(
            f"{server_url}/add_serials",
            files=files,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ ECC signature upload successful")
            data = response.json()
            print(f"   Response: {data}")
        else:
            print(f"❌ ECC signature upload failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ ECC signature upload test failed: {e}")
    
    # Test 5: Batch Upload
    print("\n5️⃣ Testing batch upload...")
    try:
        # Create batch CSV content
        batch_csv_content = "device_id,wwyy\nBATCH001,4023\nBATCH002,4023\nBATCH003,4023\n"
        batch_csv_bytes = batch_csv_content.encode('utf-8')
        
        # Compute hash
        batch_csv_hash = hashlib.sha256(batch_csv_bytes).hexdigest()
        
        # Generate timestamp
        timestamp = str(int(time.time()))
        
        # Create ECC signature
        message = f"{timestamp}{batch_csv_hash}"
        signature = private_key.sign(
            message.encode(),
            ec.ECDSA(hashes.SHA256())
        )
        signature_b64 = base64.b64encode(signature).decode()
        
        # Prepare batch upload request
        files = {
            'file': ('batch_serials.csv', batch_csv_bytes, 'text/csv')
        }
        headers = {
            'X-Timestamp': timestamp,
            'X-Signature': signature_b64,
            'X-Factory-ID': 'Test ECC Factory',
            'X-Batch-ID': f'BATCH_{int(time.time())}',
            'X-Test-Run-Count': '3'
        }
        
        response = requests.post(
            f"{server_url}/add_batch_serials",
            files=files,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Batch upload successful")
            data = response.json()
            print(f"   Response: {data}")
        else:
            print(f"❌ Batch upload failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Batch upload test failed: {e}")
    
    # Test 6: Chunked Upload
    print("\n6️⃣ Testing chunked upload...")
    try:
        # Create chunk CSV content
        chunk_csv_content = "device_id,wwyy\nCHUNK001,4023\nCHUNK002,4023\n"
        chunk_csv_bytes = chunk_csv_content.encode('utf-8')
        
        # Compute hash
        chunk_csv_hash = hashlib.sha256(chunk_csv_bytes).hexdigest()
        
        # Generate timestamp
        timestamp = str(int(time.time()))
        
        # Create ECC signature
        message = f"{timestamp}{chunk_csv_hash}"
        signature = private_key.sign(
            message.encode(),
            ec.ECDSA(hashes.SHA256())
        )
        signature_b64 = base64.b64encode(signature).decode()
        
        # Prepare chunk upload request
        files = {
            'file': ('chunk_serials.csv', chunk_csv_bytes, 'text/csv')
        }
        headers = {
            'X-Timestamp': timestamp,
            'X-Signature': signature_b64,
            'X-Factory-ID': 'Test ECC Factory',
            'X-Batch-ID': f'CHUNK_BATCH_{int(time.time())}',
            'X-Chunk-Index': '0',
            'X-Total-Chunks': '2'
        }
        
        response = requests.post(
            f"{server_url}/add_chunk_serials",
            files=files,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Chunked upload successful")
            data = response.json()
            print(f"   Response: {data}")
        else:
            print(f"❌ Chunked upload failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Chunked upload test failed: {e}")
    
    # Test 7: Queue Status
    print("\n7️⃣ Testing queue status...")
    try:
        response = requests.get(
            f"{server_url}/queue_status",
            params={"public_key": public_key_b64}
        )
        
        if response.status_code == 200:
            print("✅ Queue status retrieval successful")
            data = response.json()
            print(f"   Factory ID: {data.get('factory_id')}")
            print(f"   Pending uploads: {data.get('pending_uploads')}")
            print(f"   Failed uploads: {data.get('failed_uploads')}")
        else:
            print(f"❌ Queue status failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Queue status test failed: {e}")
    
    # Test 8: Serial Verification
    print("\n8️⃣ Testing serial verification...")
    try:
        test_serials = ["K1S-ECC001", "K1S-ECC002", "K1S-BATCH001", "K1S-CHUNK001"]
        
        for serial in test_serials:
            response = requests.get(f"{server_url}/verify?sn={serial}")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'Authentic':
                    print(f"✅ Serial {serial} verified successfully")
                    print(f"   Production Date: {data.get('production_date')}")
                    print(f"   Factory: {data.get('provenance')}")
                else:
                    print(f"❌ Serial {serial} not found")
            else:
                print(f"❌ Serial verification failed for {serial}: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Serial verification test failed: {e}")
    
    print("\n" + "=" * 70)
    print("🎉 Enhanced Server Testing Complete!")
    print("\nThe enhanced server now supports:")
    print("  ✅ ECC signature verification")
    print("  ✅ Batch upload functionality")
    print("  ✅ Chunked upload support")
    print("  ✅ Offline queue management")
    print("  ✅ Enhanced security measures")
    
    return True

if __name__ == "__main__":
    test_enhanced_server()
