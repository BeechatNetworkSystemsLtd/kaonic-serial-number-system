#!/usr/bin/env python3
"""
Test network connectivity for the factory app
"""

import requests
import socket
import sys

def test_network_connectivity():
    """Test network connectivity to the server"""
    
    server_url = "http://192.168.1.232:5000"
    
    print("🌐 Testing Network Connectivity for Factory App")
    print("=" * 50)
    
    # Test 1: Basic socket connection
    print(f"\n1️⃣ Testing socket connection to 192.168.1.232:5000...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('192.168.1.232', 5000))
        sock.close()
        
        if result == 0:
            print("✅ Socket connection successful")
        else:
            print(f"❌ Socket connection failed (error code: {result})")
            return False
    except Exception as e:
        print(f"❌ Socket connection error: {e}")
        return False
    
    # Test 2: HTTP GET request
    print(f"\n2️⃣ Testing HTTP GET request...")
    try:
        response = requests.get(f"{server_url}/verify?sn=K1S-A001", timeout=10)
        if response.status_code == 200:
            print("✅ HTTP GET request successful")
            data = response.json()
            print(f"   Response: {data}")
        else:
            print(f"❌ HTTP GET failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectTimeout:
        print("❌ Connection timeout - server may not be accessible")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ HTTP GET error: {e}")
        return False
    
    # Test 3: Registration endpoint
    print(f"\n3️⃣ Testing registration endpoint...")
    try:
        response = requests.post(
            f"{server_url}/register_public_key",
            json={"factory_name": "Network Test", "public_key": "test_network_key"},
            timeout=10
        )
        if response.status_code in [200, 201]:
            print("✅ Registration endpoint accessible")
        else:
            print(f"❌ Registration endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Registration endpoint error: {e}")
    
    # Test 4: Check local IP addresses
    print(f"\n4️⃣ Checking local network configuration...")
    try:
        import subprocess
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        if result.returncode == 0:
            ips = result.stdout.strip().split()
            print(f"   Local IP addresses: {', '.join(ips)}")
            
            if '192.168.1.232' in ips:
                print("✅ Server IP matches local network")
            else:
                print("⚠️ Server IP may not be on the same network")
        else:
            print("⚠️ Could not determine local IP addresses")
    except Exception as e:
        print(f"⚠️ Error checking local IPs: {e}")
    
    print(f"\n" + "=" * 50)
    print("🎉 Network Connectivity Test Complete!")
    print(f"\nFor the factory app, use this server URL:")
    print(f"   {server_url}")
    print(f"\nIf connection is still refused, check:")
    print(f"   1. Server is running: python3 server.py")
    print(f"   2. Firewall allows port 5000")
    print(f"   3. Both devices are on the same network")
    print(f"   4. Install the updated APK with network security fix")
    
    return True

if __name__ == "__main__":
    test_network_connectivity()


