import os
import secrets
import sys
from ecdsa import SigningKey, NIST256p

# Define the folder to store keys
KEYS_DIR = "keys"

# Ensure the directory exists
os.makedirs(KEYS_DIR, exist_ok=True)

def generate_keypair(factory_alias):
    """Generate a key pair for a specific factory."""
    # Generate private key using secure entropy
    sk = SigningKey.generate(curve=NIST256p, entropy=secrets.token_bytes)
    
    # Get the public key
    vk = sk.verifying_key
    
    # Clean alias for filename (remove special characters, convert to lowercase)
    clean_alias = ''.join(c.lower() if c.isalnum() else '_' for c in factory_alias)
    
    # Define file paths
    private_key_path = os.path.join(KEYS_DIR, f"{clean_alias}_private.pem")
    public_key_path = os.path.join(KEYS_DIR, f"{clean_alias}_public.pem")
    
    # Save private key
    with open(private_key_path, "wb") as f:
        f.write(sk.to_pem())
    
    # Save public key
    with open(public_key_path, "wb") as f:
        f.write(vk.to_pem())
    
    print(f"✔ Private key saved to {private_key_path}")
    print(f"✔ Public key saved to {public_key_path}")
    
    return private_key_path, public_key_path, factory_alias

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 genkeys_multi.py <factory_alias> [factory_alias2] ...")
        print("Example: python3 genkeys_multi.py TOKYO_FACTORY SHANGHAI_FACTORY BERLIN_FACTORY")
        print("Example: python3 genkeys_multi.py FACTORY_A FACTORY_B")
        sys.exit(1)
    
    factory_aliases = sys.argv[1:]
    
    print(f"Generating key pairs for {len(factory_aliases)} factories...")
    print()
    
    generated_keys = {}
    
    for alias in factory_aliases:
        print(f"Generating keys for factory: {alias}")
        private_path, public_path, original_alias = generate_keypair(alias)
        generated_keys[original_alias] = public_path
        print()
    
    print("=" * 60)
    print("ENVIRONMENT CONFIGURATION")
    print("=" * 60)
    print("Add this line to your .env file:")
    print()
    
    # Create the new FACTORY_KEYS format
    factory_keys_config = ",".join([f"{alias}:{path}" for alias, path in generated_keys.items()])
    print(f"FACTORY_KEYS={factory_keys_config}")
    
    print()
    print("Complete .env configuration example:")
    print("DB_NAME=kaonic_serials")
    print("DB_USER=kaonic_user")
    print("DB_PASSWORD=change_this_password")
    print("DB_HOST=localhost")
    print("DB_PORT=5432")
    print(f"FACTORY_KEYS={factory_keys_config}")
    
    print()
    print("Alternative: You can also use the legacy format:")
    for alias, public_path in generated_keys.items():
        print(f"ECC_PUBLIC_KEY_{alias}={public_path}")

if __name__ == "__main__":
    main()
