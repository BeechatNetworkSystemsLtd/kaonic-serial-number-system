import os
import hashlib
import base64
import time
import logging
import re
import csv
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from ecdsa import VerifyingKey, NIST256p, BadSignatureError
import psycopg2
from db import get_db_connection
from crypto_utils import (
    verify_ecdsa_signature, verify_hmac_signature, compute_file_hash,
    validate_public_key_format, get_factory_public_key_from_db,
    create_signature_message, log_signature_verification,
    store_batch_metadata, get_pending_uploads_count, get_failed_uploads_count,
    reset_failed_uploads
)

# Load environment variables
load_dotenv()

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

# Rate Limiting: 100 requests per minute per IP
limiter = Limiter(get_remote_address, app=app, default_limits=["100 per minute"])

# Regex pattern for serial validation (K1S-XXXX format)
SERIAL_PATTERN = re.compile(r"^K1S-[A-Z0-9]{1,10}$")

# Load Multiple ECC Public Keys with Aliases
def load_public_keys():
    """Load multiple public keys from environment configuration."""
    public_keys = {}
    
    # First try the new FACTORY_KEYS format
    factory_keys = os.getenv("FACTORY_KEYS")
    if factory_keys:
        try:
            # Parse format: ALIAS1:path/to/key1.pem,ALIAS2:path/to/key2.pem
            for key_entry in factory_keys.split(','):
                if ':' in key_entry:
                    alias, key_path = key_entry.strip().split(':', 1)
                    if os.path.exists(key_path):
                        try:
                            with open(key_path, "rb") as f:
                                key_data = f.read().decode()
                            public_keys[alias] = VerifyingKey.from_pem(key_data)
                            logging.info(f"Loaded public key for factory: {alias}")
                        except Exception as e:
                            logging.error(f"Failed to load public key for {alias}: {e}")
                    else:
                        logging.warning(f"Public key file not found for {alias}: {key_path} (will be loaded from database)")
        except Exception as e:
            logging.error(f"Error parsing FACTORY_KEYS: {e}")
    
    # Fallback to legacy ECC_PUBLIC_KEY_* format
    if not public_keys:
        for key, value in os.environ.items():
            if key.startswith("ECC_PUBLIC_KEY_"):
                # Extract alias from key name (e.g., ECC_PUBLIC_KEY_FACTORY_A -> FACTORY_A)
                alias = key.replace("ECC_PUBLIC_KEY_", "")
                
                if os.path.exists(value):
                    try:
                        with open(value, "rb") as f:
                            key_data = f.read().decode()
                        public_keys[alias] = VerifyingKey.from_pem(key_data)
                        logging.info(f"Loaded public key for factory: {alias}")
                    except Exception as e:
                        logging.error(f"Failed to load public key for {alias}: {e}")
                else:
                    logging.warning(f"Public key file not found for {alias}: {value} (will be loaded from database)")
    
    # If no keys found in files, that's OK - we'll load them from database when needed
    if not public_keys:
        logging.warning("No public keys found in files. Keys will be loaded from database as needed.")
    
    return public_keys

# Load all public keys
PUBLIC_KEYS = load_public_keys()

def convert_wwyy_to_date(wwyy: str) -> str:
    """ Converts WWYY (Week-Year) format to a valid YYYY-MM-DD date. """
    try:
        wwyy_str = str(wwyy).zfill(4)  # Ensure it's always 4 digits
        week = int(wwyy_str[:2])  # First 2 digits = Week
        year = 2000 + int(wwyy_str[2:])  # Last 2 digits = Year

        # Convert week number into an actual date (first day of the given week)
        date_obj = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w")
        return date_obj.date()  # Return as YYYY-MM-DD
    except ValueError:
        logging.error(f"Failed to convert WWYY to date: {wwyy}")
        return None  # Return None for invalid values

def convert_wwyy_to_iso(production_date: str) -> str:
    """ Ensures the date format is ISO-8601. If already correct, return it. """
    try:
        # If the date is already in YYYY-MM-DD format, return it as ISO
        return str(production_date)
    except ValueError:
        logging.error(f"Failed to convert production date to ISO: {production_date}")
        return None  # Return None for invalid values




@app.route('/verify', methods=['GET'])
@limiter.limit("100 per minute")
def verify_serial():
    """ Public API to verify a serial number """
    serial = request.args.get("sn", "").strip().upper()

    if not SERIAL_PATTERN.match(serial):
        logging.warning(f"Invalid serial format attempt: {serial}")
        return jsonify({"error": "Invalid serial format"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT production_date, provenance FROM serials WHERE serial_number = %s;", (serial,))
            result = cursor.fetchone()

        if result:
            production_date, provenance = result
            production_date_iso = convert_wwyy_to_iso(production_date)  # Now returns correct YYYY-MM-DD
            if production_date_iso is None:
                return jsonify({"error": "Invalid production date stored in database"}), 500

            return jsonify({
                "status": "Authentic",
                "serial_number": serial,
                "production_date": production_date_iso,
                "provenance": provenance
            })
        else:
            return jsonify({"status": "Not Found"}), 404
    except Exception as e:
        logging.error(f"Database query error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        conn.close()


def verify_signature_with_factory_key(signature_b64: str, timestamp: str, csv_hash: str, factory_id: str) -> tuple[bool, str]:
    """ Verifies signature using factory's specific public key.
    Returns (is_valid, factory_alias) tuple.
    """
    conn = get_db_connection()
    if not conn:
        return False, None
    
    try:
        # Get factory's public key from database
        public_key_pem = get_factory_public_key_from_db(factory_id, conn)
        if not public_key_pem:
            logging.error(f"No public key found for factory: {factory_id}")
            return False, None
        
        # Create message to verify
        message = create_signature_message(timestamp, csv_hash)
        
        # Try ECDSA verification first
        is_valid, error = verify_ecdsa_signature(public_key_pem, message, signature_b64)
        if is_valid:
            log_signature_verification(factory_id, True)
            return True, factory_id
        
        # Try HMAC verification for backward compatibility
        is_valid, error = verify_hmac_signature(message, signature_b64)
        if is_valid:
            log_signature_verification(factory_id, True)
            return True, factory_id
        
        log_signature_verification(factory_id, False, error)
        return False, None
        
    except Exception as e:
        logging.error(f"Signature verification error for factory {factory_id}: {e}")
        return False, None
    finally:
        conn.close()

@app.route('/add_serials', methods=['POST'])
@limiter.limit("100 per minute")
def add_serials():
    """ Accepts a CSV upload, validates, and adds serials securely """
    signature = request.headers.get("X-Signature")
    timestamp = request.headers.get("X-Timestamp")
    factory_id = request.headers.get("X-Factory-ID")

    if not signature or not timestamp:
        return jsonify({"error": "Missing authentication headers"}), 403

    if not factory_id:
        return jsonify({"error": "Missing factory ID header"}), 400

    current_time = int(time.time())
    if abs(current_time - int(timestamp)) > 300:
        return jsonify({"error": "Request expired"}), 403

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    file_content = file.stream.read()
    csv_hash = compute_file_hash(file_content)
    file.stream.seek(0)

    # Verify signature using factory's specific key
    is_valid, factory_alias = verify_signature_with_factory_key(signature, timestamp, csv_hash, factory_id)
    
    if not is_valid:
        logging.warning(f"Unauthorized attempt with invalid signature from factory: {factory_id}")
        return jsonify({"error": "Unauthorized"}), 403

    added_count = 0
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cursor:
            reader = csv.reader(file_content.decode("utf-8").splitlines())
            next(reader, None)  # Skip header row

            for row in reader:
                if len(row) < 2:
                    logging.warning(f"Skipping invalid row: {row}")
                    continue

                device_id, wwyy = row[0].strip(), row[1].strip()

                # Convert WWYY to YYYY-MM-DD format for production_date
                production_date = convert_wwyy_to_date(wwyy)

                if not production_date:
                    logging.warning(f"Skipping serial {device_id} due to invalid WWYY: {wwyy}")
                    continue

                # Construct final serial number (without date component)
                serial = f"K1S-{device_id}"

                try:
                    cursor.execute(
                        "INSERT INTO serials (serial_number, production_date, provenance) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;",
                        (serial, production_date, factory_alias)
                    )
                    added_count += 1
                except Exception as e:
                    logging.error(f"Error inserting serial {serial}: {e}")

        conn.commit()
        return jsonify({"message": f"{added_count} serial numbers added successfully."})

    except Exception as e:
        logging.error(f"Error processing CSV: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        conn.close()


@app.route('/register_public_key', methods=['POST'])
@limiter.limit("100 per minute")  # Updated limit: 100 registrations per minute per IP
def register_public_key():
    """ Register a new public key request from a factory """
    try:
        data = request.get_json()
        factory_name = data.get('factory_name')
        public_key = data.get('public_key')
        
        if not factory_name or not public_key:
            return jsonify({"error": "factory_name and public_key are required"}), 400
        
        # Validate public key format (P-256 ECC)
        is_valid, error = validate_public_key_format(public_key)
        if not is_valid:
            return jsonify({"error": f"Invalid public key format: {error}"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        try:
            with conn.cursor() as cursor:
                # Check if this public key is already registered
                cursor.execute(
                    "SELECT id, status FROM public_key_requests WHERE public_key = %s",
                    (public_key,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    request_id, status = existing
                    return jsonify({
                        "message": "Public key already registered",
                        "request_id": request_id,
                        "status": status
                    }), 200
                
                # Insert new registration request
                cursor.execute("""
                    INSERT INTO public_key_requests (factory_name, public_key, status)
                    VALUES (%s, %s, 'pending')
                    RETURNING id
                """, (factory_name, public_key))
                
                request_id = cursor.fetchone()[0]
                conn.commit()
                
                logging.info(f"New public key registration request: {factory_name} (ID: {request_id})")
                
                return jsonify({
                    "message": "Public key registration request submitted",
                    "request_id": request_id,
                    "status": "pending"
                }), 201
                
        except Exception as e:
            logging.error(f"Database error during registration: {e}")
            return jsonify({"error": "Internal Server Error"}), 500
        finally:
            conn.close()
            
    except Exception as e:
        logging.error(f"Registration error: {e}")
        return jsonify({"error": "Invalid request"}), 400

@app.route('/check_registration_status', methods=['GET'])
def check_registration_status():
    """ Check the status of a public key registration """
    public_key = request.args.get('public_key')
    
    if not public_key:
        return jsonify({"error": "public_key parameter required"}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, factory_name, status, created_at, approved_at, approved_by
                FROM public_key_requests 
                WHERE public_key = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (public_key,))
            
            result = cursor.fetchone()
            
            if result:
                request_id, factory_name, status, created_at, approved_at, approved_by = result
                return jsonify({
                    "request_id": request_id,
                    "factory_name": factory_name,
                    "status": status,
                    "created_at": created_at.isoformat() if created_at else None,
                    "approved_at": approved_at.isoformat() if approved_at else None,
                    "approved_by": approved_by
                })
            else:
                return jsonify({"error": "Public key not found"}), 404
                
    except Exception as e:
        logging.error(f"Database error during status check: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        conn.close()

@app.route('/admin/registration_requests', methods=['GET'])
def list_registration_requests():
    """ List all public key registration requests (admin endpoint) """
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, factory_name, public_key, status, created_at, approved_at, approved_by
                FROM public_key_requests 
                ORDER BY created_at DESC
            """)
            
            requests = []
            for row in cursor.fetchall():
                request_id, factory_name, public_key, status, created_at, approved_at, approved_by = row
                requests.append({
                    "id": request_id,
                    "factory_name": factory_name,
                    "public_key": public_key[:50] + "..." if len(public_key) > 50 else public_key,
                    "public_key_full": public_key,
                    "status": status,
                    "created_at": created_at.isoformat() if created_at else None,
                    "approved_at": approved_at.isoformat() if approved_at else None,
                    "approved_by": approved_by
                })
            
            return jsonify({"requests": requests})
                
    except Exception as e:
        logging.error(f"Database error during request listing: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        conn.close()

@app.route('/admin/approve_request/<int:request_id>', methods=['POST'])
def approve_registration_request(request_id):
    """ Approve a public key registration request (admin endpoint) """
    try:
        data = request.get_json() or {}
        approved_by = data.get('approved_by', 'admin')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        try:
            with conn.cursor() as cursor:
                # Update the request status
                cursor.execute("""
                    UPDATE public_key_requests 
                    SET status = 'approved', approved_at = CURRENT_TIMESTAMP, approved_by = %s
                    WHERE id = %s
                    RETURNING factory_name, public_key
                """, (approved_by, request_id))
                
                result = cursor.fetchone()
                if not result:
                    return jsonify({"error": "Request not found"}), 404
                
                factory_name, public_key = result
                conn.commit()
                
                logging.info(f"Approved registration request {request_id} for factory: {factory_name}")
                
                return jsonify({
                    "message": "Registration request approved",
                    "request_id": request_id,
                    "factory_name": factory_name
                })
                
        except Exception as e:
            logging.error(f"Database error during approval: {e}")
            return jsonify({"error": "Internal Server Error"}), 500
        finally:
            conn.close()
            
    except Exception as e:
        logging.error(f"Approval error: {e}")
        return jsonify({"error": "Invalid request"}), 400

@app.route('/admin/deny_request/<int:request_id>', methods=['POST'])
def deny_registration_request(request_id):
    """ Deny a public key registration request (admin endpoint) """
    try:
        data = request.get_json() or {}
        denied_by = data.get('denied_by', 'admin')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        try:
            with conn.cursor() as cursor:
                # Update the request status
                cursor.execute("""
                    UPDATE public_key_requests 
                    SET status = 'denied', approved_at = CURRENT_TIMESTAMP, approved_by = %s
                    WHERE id = %s
                    RETURNING factory_name
                """, (denied_by, request_id))
                
                result = cursor.fetchone()
                if not result:
                    return jsonify({"error": "Request not found"}), 404
                
                factory_name = result[0]
                conn.commit()
                
                logging.info(f"Denied registration request {request_id} for factory: {factory_name}")
                
                return jsonify({
                    "message": "Registration request denied",
                    "request_id": request_id,
                    "factory_name": factory_name
                })
                
        except Exception as e:
            logging.error(f"Database error during denial: {e}")
            return jsonify({"error": "Internal Server Error"}), 500
        finally:
            conn.close()
            
    except Exception as e:
        logging.error(f"Denial error: {e}")
        return jsonify({"error": "Invalid request"}), 400

@app.route('/admin/revoke_request/<int:request_id>', methods=['POST'])
def revoke_registration_request(request_id):
    """ Revoke an approved public key registration request (admin endpoint) """
    try:
        data = request.get_json() or {}
        revoked_by = data.get('revoked_by', 'admin')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        try:
            with conn.cursor() as cursor:
                # Update the request status back to pending
                cursor.execute("""
                    UPDATE public_key_requests 
                    SET status = 'pending', approved_at = NULL, approved_by = NULL
                    WHERE id = %s AND status = 'approved'
                    RETURNING factory_name
                """, (request_id,))
                
                result = cursor.fetchone()
                if not result:
                    return jsonify({"error": "Request not found or not approved"}), 404
                
                factory_name = result[0]
                conn.commit()
                
                logging.info(f"Revoked registration request {request_id} for factory: {factory_name}")
                
                return jsonify({
                    "message": "Registration request revoked - status reset to pending",
                    "request_id": request_id,
                    "factory_name": factory_name
                })
                
        except Exception as e:
            logging.error(f"Database error during revocation: {e}")
            return jsonify({"error": "Internal Server Error"}), 500
        finally:
            conn.close()
            
    except Exception as e:
        logging.error(f"Revocation error: {e}")
        return jsonify({"error": "Invalid request"}), 400

# Batch Upload Endpoints

@app.route('/add_batch_serials', methods=['POST'])
@limiter.limit("100 per minute")
def add_batch_serials():
    """Handle batch upload of serial numbers from multiple test runs"""
    signature = request.headers.get("X-Signature")
    timestamp = request.headers.get("X-Timestamp")
    factory_id = request.headers.get("X-Factory-ID")
    batch_id = request.headers.get("X-Batch-ID")
    test_run_count = request.headers.get("X-Test-Run-Count")

    if not all([signature, timestamp, factory_id, batch_id]):
        return jsonify({"error": "Missing required headers"}), 400

    current_time = int(time.time())
    if abs(current_time - int(timestamp)) > 300:
        return jsonify({"error": "Request expired"}), 403

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    file_content = file.stream.read()
    csv_hash = compute_file_hash(file_content)
    file.stream.seek(0)

    # Verify signature
    is_valid, factory_alias = verify_signature_with_factory_key(signature, timestamp, csv_hash, factory_id)
    if not is_valid:
        return jsonify({"error": "Unauthorized"}), 403

    # Process batch metadata
    metadata = {
        'factory_id': factory_id,
        'test_run_count': int(test_run_count) if test_run_count else 0,
        'total_serials': 0,
        'batch_id': batch_id
    }

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cursor:
            # Store batch metadata
            store_batch_metadata(batch_id, metadata, conn)
            
            # Process CSV
            reader = csv.reader(file_content.decode("utf-8").splitlines())
            next(reader, None)  # Skip header row
            
            serials = []
            for row in reader:
                if len(row) < 2:
                    continue
                
                device_id, wwyy = row[0].strip(), row[1].strip()
                production_date = convert_wwyy_to_date(wwyy)
                
                if not production_date:
                    continue
                
                serial = f"K1S-{device_id}"
                serials.append((serial, production_date, factory_alias, batch_id))
            
            # Insert serials with batch information
            for serial, prod_date, provenance, batch in serials:
                cursor.execute("""
                    INSERT INTO serials (serial_number, production_date, provenance, batch_id)
                    VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING
                """, (serial, prod_date, provenance, batch))
            
            # Update batch metadata with actual count
            cursor.execute("""
                UPDATE batch_uploads SET total_serials = %s, status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (len(serials), batch_id))
            
            conn.commit()
            
            return jsonify({
                "message": f"Batch {batch_id} uploaded successfully",
                "uploaded_count": len(serials),
                "batch_id": batch_id
            })
            
    except Exception as e:
        logging.error(f"Error processing batch upload: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        conn.close()

@app.route('/add_chunk_serials', methods=['POST'])
@limiter.limit("100 per minute")
def add_chunk_serials():
    """Handle chunked upload for large batches"""
    signature = request.headers.get("X-Signature")
    timestamp = request.headers.get("X-Timestamp")
    factory_id = request.headers.get("X-Factory-ID")
    batch_id = request.headers.get("X-Batch-ID")
    chunk_index = request.headers.get("X-Chunk-Index")
    total_chunks = request.headers.get("X-Total-Chunks")

    if not all([signature, timestamp, factory_id, batch_id, chunk_index, total_chunks]):
        return jsonify({"error": "Missing required headers"}), 400

    current_time = int(time.time())
    if abs(current_time - int(timestamp)) > 300:
        return jsonify({"error": "Request expired"}), 403

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    file_content = file.stream.read()
    csv_hash = compute_file_hash(file_content)
    file.stream.seek(0)

    # Verify signature
    is_valid, factory_alias = verify_signature_with_factory_key(signature, timestamp, csv_hash, factory_id)
    if not is_valid:
        return jsonify({"error": "Unauthorized"}), 403

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cursor:
            # Process chunk
            reader = csv.reader(file_content.decode("utf-8").splitlines())
            next(reader, None)  # Skip header row
            
            serials = []
            for row in reader:
                if len(row) < 2:
                    continue
                
                device_id, wwyy = row[0].strip(), row[1].strip()
                production_date = convert_wwyy_to_date(wwyy)
                
                if not production_date:
                    continue
                
                serial = f"K1S-{device_id}"
                serials.append((serial, production_date, factory_alias, batch_id, int(chunk_index)))
            
            # Insert serials with chunk information
            for serial, prod_date, provenance, batch, chunk in serials:
                cursor.execute("""
                    INSERT INTO serials (serial_number, production_date, provenance, batch_id, chunk_index)
                    VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
                """, (serial, prod_date, provenance, batch, chunk))
            
            # Store chunk metadata
            cursor.execute("""
                INSERT INTO batch_chunks (batch_id, chunk_index, total_chunks, serial_count)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (batch_id, chunk_index) DO UPDATE SET
                    serial_count = EXCLUDED.serial_count,
                    status = 'uploaded'
            """, (batch_id, int(chunk_index), int(total_chunks), len(serials)))
            
            conn.commit()
            
            return jsonify({
                "message": f"Chunk {chunk_index}/{total_chunks} uploaded",
                "chunk_index": int(chunk_index),
                "total_chunks": int(total_chunks),
                "uploaded_count": len(serials)
            })
            
    except Exception as e:
        logging.error(f"Error processing chunk upload: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        conn.close()

# Offline Queue Support Endpoints

@app.route('/queue_status', methods=['GET'])
def get_queue_status():
    """Get offline queue status for a factory"""
    public_key = request.args.get('public_key')
    if not public_key:
        return jsonify({"error": "public_key parameter required"}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        with conn.cursor() as cursor:
            # Get factory ID from public key
            cursor.execute("""
                SELECT factory_name FROM public_key_requests 
                WHERE public_key = %s AND status = 'approved'
                ORDER BY approved_at DESC LIMIT 1
            """, (public_key,))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({"error": "Factory not found"}), 404
            
            factory_id = result[0]
            
            # Get queue statistics
            pending_count = get_pending_uploads_count(factory_id, conn)
            failed_count = get_failed_uploads_count(factory_id, conn)
            
            # Get last upload time
            cursor.execute("""
                SELECT MAX(created_at) FROM serials WHERE provenance = %s
            """, (factory_id,))
            last_upload = cursor.fetchone()[0]
            
            return jsonify({
                "factory_id": factory_id,
                "pending_uploads": pending_count,
                "failed_uploads": failed_count,
                "last_upload": last_upload.isoformat() if last_upload else None
            })
            
    except Exception as e:
        logging.error(f"Error getting queue status: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        conn.close()

@app.route('/retry_failed_uploads', methods=['POST'])
def retry_failed_uploads():
    """Retry failed uploads for a factory"""
    data = request.get_json()
    public_key = data.get('public_key')
    
    if not public_key:
        return jsonify({"error": "public_key required"}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        with conn.cursor() as cursor:
            # Get factory ID from public key
            cursor.execute("""
                SELECT factory_name FROM public_key_requests 
                WHERE public_key = %s AND status = 'approved'
                ORDER BY approved_at DESC LIMIT 1
            """, (public_key,))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({"error": "Factory not found"}), 404
            
            factory_id = result[0]
            
            # Reset failed uploads
            success = reset_failed_uploads(factory_id, conn)
            if success:
                return jsonify({
                    "message": "Failed uploads reset to pending",
                    "factory_id": factory_id
                })
            else:
                return jsonify({"error": "Failed to reset uploads"}), 500
                
    except Exception as e:
        logging.error(f"Error retrying failed uploads: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        conn.close()

@app.route('/')
def home():
    return render_template('index.html')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
