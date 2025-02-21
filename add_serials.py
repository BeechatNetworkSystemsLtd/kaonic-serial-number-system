import time
import base64
import hashlib
import requests
from ecdsa import SigningKey, NIST256p
import os

# Load Private Key from File (Instead of Hardcoding)
PRIVATE_KEY_PATH = "keys/private.pem"
if not os.path.exists(PRIVATE_KEY_PATH):
    raise FileNotFoundError(f"Private key file not found: {PRIVATE_KEY_PATH}")

with open(PRIVATE_KEY_PATH, "rb") as key_file:
    sk = SigningKey.from_pem(key_file.read())

def compute_csv_hash(filename: str) -> str:
    """Compute the SHA256 hash of the CSV file."""
    hasher = hashlib.sha256()
    with open(filename, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

# Generate timestamp
timestamp = str(int(time.time()))

# Compute hash of the CSV file
csv_filename = "kaonic_serials.csv"
if not os.path.exists(csv_filename):
    raise FileNotFoundError(f"CSV file not found: {csv_filename}")

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
        response = requests.post("http://161.35.45.220:5000/add_serials", files=files, headers=headers)
#        response = requests.post("http://localhost:5000/add_serials", files=files, headers=headers)
        response.raise_for_status()
        print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"❌ Error uploading CSV: {e}")

print("✅ Upload complete.")
