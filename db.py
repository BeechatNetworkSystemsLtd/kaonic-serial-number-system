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
    """Ensure the database tables exist."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                # Create serials table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS serials (
                        serial_number VARCHAR(20) PRIMARY KEY,
                        production_date DATE NOT NULL,
                        provenance VARCHAR(50) NOT NULL,
                        batch_id VARCHAR(255),
                        chunk_index INTEGER,
                        test_run_id VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Check if serials table exists and add new columns if needed
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'serials' AND column_name = 'batch_id'
                """)
                batch_id_exists = cursor.fetchone() is not None
                
                if not batch_id_exists:
                    # Add new columns to existing serials table
                    cursor.execute("ALTER TABLE serials ADD COLUMN batch_id VARCHAR(255);")
                    cursor.execute("ALTER TABLE serials ADD COLUMN chunk_index INTEGER;")
                    cursor.execute("ALTER TABLE serials ADD COLUMN test_run_id VARCHAR(255);")
                    cursor.execute("ALTER TABLE serials ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
                    logging.info("Added new columns to existing serials table")
                else:
                    logging.info("Serials table already has new columns")
                
                # Public key requests table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS public_key_requests (
                        id SERIAL PRIMARY KEY,
                        factory_name VARCHAR(100) NOT NULL,
                        public_key TEXT NOT NULL,
                        status VARCHAR(20) DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        approved_at TIMESTAMP NULL,
                        approved_by VARCHAR(50) NULL
                    );
                """)
                
                # Batch uploads tracking table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS batch_uploads (
                        id VARCHAR(255) PRIMARY KEY,
                        factory_id VARCHAR(255) NOT NULL,
                        test_run_count INTEGER NOT NULL,
                        total_serials INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status VARCHAR(50) DEFAULT 'processing',
                        metadata JSON,
                        completed_at TIMESTAMP NULL
                    );
                """)
                
                # Batch chunks tracking table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS batch_chunks (
                        id SERIAL PRIMARY KEY,
                        batch_id VARCHAR(255) NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        total_chunks INTEGER NOT NULL,
                        serial_count INTEGER NOT NULL,
                        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status VARCHAR(50) DEFAULT 'uploaded',
                        UNIQUE(batch_id, chunk_index)
                    );
                """)
                
                # Offline queue table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS offline_queue (
                        id SERIAL PRIMARY KEY,
                        factory_id VARCHAR(255) NOT NULL,
                        batch_id VARCHAR(255),
                        serial_data JSON NOT NULL,
                        status VARCHAR(50) DEFAULT 'pending',
                        retry_count INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 5,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_attempt TIMESTAMP NULL,
                        error_message TEXT NULL
                    );
                """)
                
                # Create indexes for performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_serials_batch_id ON serials(batch_id);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_serials_provenance ON serials(provenance);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_batch_uploads_status ON batch_uploads(status);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_batch_chunks_batch_id ON batch_chunks(batch_id);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_offline_queue_factory_status ON offline_queue(factory_id, status);
                """)
                
                conn.commit()
                logging.info("Database initialized successfully with enhanced schema.")
        except Exception as e:
            logging.error(f"Error creating database tables: {e}")
        finally:
            conn.close()
