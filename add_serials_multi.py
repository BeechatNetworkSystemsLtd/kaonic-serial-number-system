import time
import base64
import hashlib
import requests
from ecdsa import SigningKey, NIST256p
import os
import sys

def compute_csv_hash(filename: str) -> str:
    """Compute the SHA256 hash of the CSV file."""
    hasher = hashlib.sha256()
    with open(filename, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def upload_serials(csv_filename, private_key_path, server_url="http://localhost:5000"):
    """Upload serials using the specified private key."""
    
    if not os.path.exists(csv_filename):
        raise FileNotFoundError(f"CSV file not found: {csv_filename}")
    
    if not os.path.exists(private_key_path):
        raise FileNotFoundError(f"Private key file not found: {private_key_path}")
    
    # Load Private Key
    with open(private_key_path, "rb") as key_file:
        sk = SigningKey.from_pem(key_file.read())
    
    # Generate timestamp
    timestamp = str(int(time.time()))
    
    # Compute hash of the CSV file
    csv_hash = compute_csv_hash(csv_filename)
    
    # Sign timestamp + CSV hash
    message = f"{timestamp}{csv_hash}".encode()
    signature = sk.sign(message)
    signature_b64 = base64.b64encode(signature).decode()
    
    # Upload CSV
    with open(csv_filename, "rb") as csv_file:
        files = {'file': csv_file}
        headers = {
            "X-Timestamp": timestamp,
            "X-Signature": signature_b64
        }
        
        try:
            response = requests.post(f"{server_url}/add_serials", files=files, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error uploading CSV: {e}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 add_serials_multi.py <csv_file> <private_key_path> [server_url]")
        print("Example: python3 add_serials_multi.py serials.csv keys/tokyo_factory_private.pem")
        print("Example: python3 add_serials_multi.py serials.csv keys/factory_a_private.pem http://localhost:5000")
        print()
        print("Note: The private key filename should match the factory alias used in genkeys_multi.py")
        print("For example, if you generated keys for 'TOKYO_FACTORY', use 'keys/tokyo_factory_private.pem'")
        sys.exit(1)
    
    csv_filename = sys.argv[1]
    private_key_path = sys.argv[2]
    server_url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:5000"
    
    try:
        result = upload_serials(csv_filename, private_key_path, server_url)
        print("✅ Upload successful!")
        print(f"Response: {result}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
