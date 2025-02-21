import os
import psycopg2
from psycopg2 import OperationalError, sql
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Database Configuration
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

def get_db_connection():
    """Establish and return a database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except OperationalError as e:
        logging.error(f"Database connection error: {e}")
        return None

def initialize_db():
    """Ensure the database table exists."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS serials (
                        serial_number VARCHAR(20) PRIMARY KEY,
                        production_date DATE NOT NULL
                    );
                """)
                conn.commit()
            logging.info("Database initialized successfully.")
        except Exception as e:
            logging.error(f"Error creating database table: {e}")
        finally:
            conn.close()
