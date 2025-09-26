#!/usr/bin/env python3
"""
Cryptographic utilities for Kaonic Serial Number System
Handles ECDSA signature verification and key management
"""

import base64
import hashlib
import logging
from typing import Optional, Tuple
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.exceptions import InvalidSignature
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_ecdsa_signature(public_key_pem: str, message: str, signature_base64: str) -> Tuple[bool, Optional[str]]:
    """
    Verify ECDSA signature using P-256 curve
    
    Args:
        public_key_pem: Public key in PEM format
        message: Message that was signed
        signature_base64: Base64 encoded signature
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Load public key
        public_key = serialization.load_pem_public_key(public_key_pem.encode())
        
        # Verify it's an EC public key
        if not isinstance(public_key, ec.EllipticCurvePublicKey):
            return False, "Public key is not an EC key"
        
        # Decode signature
        signature_bytes = base64.b64decode(signature_base64)
        
        # Verify signature
        public_key.verify(
            signature_bytes,
            message.encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )
        
        logger.info("ECDSA signature verification successful")
        return True, None
        
    except InvalidSignature:
        logger.warning("ECDSA signature verification failed: Invalid signature")
        return False, "Invalid signature"
    except Exception as e:
        logger.error(f"ECDSA signature verification error: {e}")
        return False, str(e)

def verify_hmac_signature(message: str, signature_base64: str, secret_key: str = "flutter_client_secret_key") -> Tuple[bool, Optional[str]]:
    """
    Verify HMAC signature for backward compatibility with Flutter clients
    
    Args:
        message: Message that was signed
        signature_base64: Base64 encoded HMAC signature
        secret_key: Secret key for HMAC
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        import hmac
        
        # Compute expected HMAC
        expected_signature = hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        
        # Decode received signature
        received_signature = base64.b64decode(signature_base64)
        
        # Compare signatures
        if hmac.compare_digest(expected_signature, received_signature):
            logger.info("HMAC signature verification successful")
            return True, None
        else:
            logger.warning("HMAC signature verification failed: Signature mismatch")
            return False, "Signature mismatch"
            
    except Exception as e:
        logger.error(f"HMAC signature verification error: {e}")
        return False, str(e)

def compute_file_hash(file_content: bytes) -> str:
    """
    Compute SHA-256 hash of file content
    
    Args:
        file_content: File content as bytes
        
    Returns:
        Hex digest of the hash
    """
    return hashlib.sha256(file_content).hexdigest()

def validate_public_key_format(public_key: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a public key is in the correct P-256 format
    
    Args:
        public_key: Public key string (base64 or PEM format)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # If it's base64, convert to PEM format
        if not public_key.startswith("-----BEGIN PUBLIC KEY-----"):
            # Clean the base64 string (remove any whitespace/newlines)
            clean_key = public_key.strip().replace('\n', '').replace('\r', '').replace(' ', '')
            
            # Validate base64 format
            try:
                import base64
                base64.b64decode(clean_key)
            except Exception:
                return False, "Invalid base64 format"
            
            public_key_pem = f"""-----BEGIN PUBLIC KEY-----
{clean_key}
-----END PUBLIC KEY-----"""
        else:
            public_key_pem = public_key
        
        # Load and validate the public key
        public_key_obj = serialization.load_pem_public_key(public_key_pem.encode())
        
        if not isinstance(public_key_obj, ec.EllipticCurvePublicKey):
            return False, "Public key is not an EC key"
        
        # Check if it's P-256 curve
        if public_key_obj.curve.name != 'secp256r1':
            return False, "Public key must use P-256 curve (secp256r1)"
        
        logger.info("Public key format validation successful")
        return True, None
        
    except Exception as e:
        logger.error(f"Public key format validation failed: {e}")
        return False, str(e)

def get_factory_public_key_from_db(factory_id: str, conn) -> Optional[str]:
    """
    Get factory's public key from database
    
    Args:
        factory_id: Factory identifier
        conn: Database connection
        
    Returns:
        Public key in PEM format or None
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT public_key FROM public_key_requests 
                WHERE factory_name = %s AND status = 'approved'
                ORDER BY approved_at DESC LIMIT 1
            """, (factory_id,))
            
            result = cursor.fetchone()
            if result:
                return result[0]
            return None
            
    except Exception as e:
        logger.error(f"Error retrieving public key for factory {factory_id}: {e}")
        return None

def create_signature_message(timestamp: str, file_hash: str) -> str:
    """
    Create the message that should be signed
    
    Args:
        timestamp: Unix timestamp
        file_hash: SHA-256 hash of the file
        
    Returns:
        Message string to be signed
    """
    return f"{timestamp}{file_hash}"

def log_signature_verification(factory_id: str, success: bool, error: Optional[str] = None):
    """
    Log signature verification attempts
    
    Args:
        factory_id: Factory identifier
        success: Whether verification was successful
        error: Error message if verification failed
    """
    if success:
        logger.info(f"Signature verified for factory {factory_id}")
    else:
        logger.error(f"Signature verification failed for factory {factory_id}: {error}")

def store_batch_metadata(batch_id: str, metadata: dict, conn) -> bool:
    """
    Store batch metadata in database
    
    Args:
        batch_id: Batch identifier
        metadata: Metadata dictionary
        conn: Database connection
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO batch_uploads (id, factory_id, test_run_count, total_serials, metadata)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    metadata = EXCLUDED.metadata,
                    test_run_count = EXCLUDED.test_run_count,
                    total_serials = EXCLUDED.total_serials
            """, (
                batch_id,
                metadata.get('factory_id'),
                metadata.get('test_run_count', 0),
                metadata.get('total_serials', 0),
                json.dumps(metadata)
            ))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error storing batch metadata: {e}")
        return False

def get_pending_uploads_count(factory_id: str, conn) -> int:
    """
    Get count of pending uploads for a factory
    
    Args:
        factory_id: Factory identifier
        conn: Database connection
        
    Returns:
        Number of pending uploads
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM offline_queue 
                WHERE factory_id = %s AND status = 'pending'
            """, (factory_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error getting pending uploads count: {e}")
        return 0

def get_failed_uploads_count(factory_id: str, conn) -> int:
    """
    Get count of failed uploads for a factory
    
    Args:
        factory_id: Factory identifier
        conn: Database connection
        
    Returns:
        Number of failed uploads
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM offline_queue 
                WHERE factory_id = %s AND status = 'failed'
            """, (factory_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error getting failed uploads count: {e}")
        return 0

def reset_failed_uploads(factory_id: str, conn) -> bool:
    """
    Reset failed uploads to pending status
    
    Args:
        factory_id: Factory identifier
        conn: Database connection
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE offline_queue 
                SET status = 'pending', retry_count = 0, error_message = NULL
                WHERE factory_id = %s AND status = 'failed'
            """, (factory_id,))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error resetting failed uploads: {e}")
        return False
