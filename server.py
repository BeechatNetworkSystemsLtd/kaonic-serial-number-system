import os
import hashlib
import base64
import time
import logging
import re
import csv
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from ecdsa import VerifyingKey, NIST256p, BadSignatureError
import psycopg2
from db import get_db_connection

# Load environment variables
load_dotenv()

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

# Rate Limiting: 5 requests per minute per IP
limiter = Limiter(get_remote_address, app=app, default_limits=["5 per minute"])

# Regex pattern for serial validation
SERIAL_PATTERN = re.compile(r"^[A-Z0-9-]{5,20}$")

# Load ECC Public Key
ECC_PUBLIC_KEY_PATH = os.getenv("ECC_PUBLIC_KEY_PATH")
if not os.path.exists(ECC_PUBLIC_KEY_PATH):
    raise FileNotFoundError(f"Public key file not found: {ECC_PUBLIC_KEY_PATH}")

with open(ECC_PUBLIC_KEY_PATH, "rb") as f:
    ECC_PUBLIC_KEY = f.read().decode()

vk = VerifyingKey.from_pem(ECC_PUBLIC_KEY)

def convert_wwyy_to_date(wwyy: str) -> str:
    """ Converts WWYY (Week-Year) HEX format to a valid YYYY-MM-DD date. """
    try:
        # Convert from HEX to DECIMAL if needed
        if not wwyy.isdigit():  # If it's not a number, assume it's HEX
            wwyy = str(int(wwyy, 16))  # Convert HEX -> DECIMAL

        wwyy_str = str(wwyy).zfill(4)  # Ensure it's always 4 characters
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
@limiter.limit("5 per minute")
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
            cursor.execute("SELECT production_date FROM serials WHERE serial_number = %s;", (serial,))
            result = cursor.fetchone()

        if result:
            production_date_iso = convert_wwyy_to_iso(result[0])  # Now returns correct YYYY-MM-DD
            if production_date_iso is None:
                return jsonify({"error": "Invalid production date stored in database"}), 500

            return jsonify({
                "status": "Authentic",
                "serial_number": serial,
                "production_date": production_date_iso  # Now correctly formatted
            })
        else:
            return jsonify({"status": "Not Found"}), 404
    except Exception as e:
        logging.error(f"Database query error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        conn.close()


from datetime import datetime

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


def verify_ecc_signature(signature_b64: str, timestamp: str, csv_hash: str) -> bool:
    """ Verifies ECC Signature """
    try:
        signature = base64.b64decode(signature_b64)
        message = f"{timestamp}{csv_hash}".encode()
        vk.verify(signature, message)
        return True
    except (BadSignatureError, ValueError) as e:
        logging.error(f"Signature verification failed: {e}")
        return False

@app.route('/add_serials', methods=['POST'])
def add_serials():
    """ Accepts a CSV upload, validates, and adds serials securely """
    signature = request.headers.get("X-Signature")
    timestamp = request.headers.get("X-Timestamp")

    if not signature or not timestamp:
        return jsonify({"error": "Missing authentication headers"}), 403

    current_time = int(time.time())
    if abs(current_time - int(timestamp)) > 300:
        return jsonify({"error": "Request expired"}), 403

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    csv_hash = hashlib.sha256(file.stream.read()).hexdigest()
    file.stream.seek(0)

    if not verify_ecc_signature(signature, timestamp, csv_hash):
        logging.warning("Unauthorized attempt with invalid ECC signature.")
        return jsonify({"error": "Unauthorized"}), 403

    added_count = 0
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cursor:
            reader = csv.reader(file.stream.read().decode("utf-8").splitlines())
            next(reader, None)  # Skip header row

            for row in reader:  # ✅ Now inside the `with` block, so cursor remains open!
                if len(row) < 2:
                    logging.warning(f"Skipping invalid row: {row}")
                    continue

                device_id, wwyy = row[0].strip(), row[1].strip()

                # Convert WWYY to Hex for serial number
                try:
                    wwyy_int = int(wwyy)
                    wwyy_hex = hex(wwyy_int)[2:].upper()
                except ValueError:
                    logging.warning(f"Skipping serial {device_id} due to invalid WWYY: {wwyy}")
                    continue

                # Convert WWYY to YYYY-MM-DD format for production_date
                production_date = convert_wwyy_to_date(wwyy)  # Pass original decimal WWYY

                if not production_date:
                    logging.warning(f"Skipping serial {device_id} due to invalid WWYY: {wwyy}")
                    continue

                # Construct final serial number
                serial = f"K1S-{device_id}-{wwyy_hex}"

                try:
                    cursor.execute(
                            "INSERT INTO serials (serial_number, production_date) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                        (serial, production_date)
                    )
                    added_count += 1
                except Exception as e:
                    logging.error(f"Error inserting serial {serial}: {e}")

        conn.commit()  # ✅ Commit after the loop
        return jsonify({"message": f"{added_count} serial numbers added successfully."})

    except Exception as e:
        logging.error(f"Error processing CSV: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        conn.close()


from flask import render_template

@app.route('/')
def home():
    return render_template('index.html')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
