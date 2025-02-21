import os
import secrets
from ecdsa import SigningKey, NIST256p

# Define the folder to store keys
KEYS_DIR = "keys"

# Ensure the directory exists
os.makedirs(KEYS_DIR, exist_ok=True)

# Generate private key using secure entropy
sk = SigningKey.generate(curve=NIST256p, entropy=secrets.token_bytes)

# Get the public key
vk = sk.verifying_key

# Define file paths
private_key_path = os.path.join(KEYS_DIR, "private.pem")
public_key_path = os.path.join(KEYS_DIR, "public.pem")

# Save private key
with open(private_key_path, "wb") as f:
    f.write(sk.to_pem())

# Save public key
with open(public_key_path, "wb") as f:
    f.write(vk.to_pem())

print(f"✔ Private key saved to {private_key_path}")
print(f"✔ Public key saved to {public_key_path}")

# Display keys (optional, remove if not needed)
print("\nPrivate Key (PEM):")
print(sk.to_pem().decode())

print("\nPublic Key (PEM):")
print(vk.to_pem().decode())
