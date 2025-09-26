# Kaonic Serial Number System

A secure Flask-based web application for verifying Kaonic device serial numbers with cryptographic authentication for data uploads.

## Features

- **Secure Serial Verification**: Public API for verifying device serial numbers
- **Multi-Factory Support**: Support for multiple factories with separate cryptographic keys
- **Provenance Tracking**: Track which factory uploaded each serial number
- **Cryptographic Upload**: ECC-signed CSV uploads for adding new serial numbers
- **Modern Web Interface**: Clean, responsive UI with glassmorphism design
- **Rate Limiting**: Protection against abuse with configurable rate limits
- **Database Integrity**: PostgreSQL backend with proper constraints
- **Input Validation**: Comprehensive validation and sanitization
- **Admin Interface**: Terminal-based administration interface

## Serial Number Format

Serial numbers follow the format: `K1S-{device_id}`

- **Prefix**: `K1S-` (Kaonic Series 1)
- **Device ID**: Unique identifier for the device (1-10 alphanumeric characters)
- **Example**: `K1S-1234`, `K1S-ABC123`

The production date is stored separately in the database and not included in the serial number format.

## System Architecture

### Core Components

- **`server.py`** - Main Flask application with API endpoints
- **`db.py`** - Database connection and initialization utilities
- **`admin_terminal.py`** - Terminal-based admin interface
- **`add_serials.py`** - Client script for uploading serial numbers with cryptographic signatures
- **`add_serials_multi.py`** - Multi-factory upload script
- **`genkeys.py`** - ECC key pair generation utility (single factory)
- **`genkeys_multi.py`** - Multi-factory ECC key pair generation utility
- **`templates/index.html`** - Web interface for serial number verification
- **`static/logo-white.png`** - Company logo asset

### API Endpoints

#### 1. **GET `/verify`** - Public Serial Verification
- **Purpose**: Verify if a serial number exists in the database
- **Parameters**: `sn` (serial number)
- **Rate Limit**: 100 requests per minute per IP
- **Response**: JSON with status, serial number, production date, and provenance

**Example Request:**
```bash
curl "http://localhost:5000/verify?sn=K1S-1234"
```

**Example Response:**
```json
{
  "status": "Authentic",
  "serial_number": "K1S-1234",
  "production_date": "2025-02-17",
  "provenance": "FACTORY_A"
}
```

#### 2. **POST `/add_serials`** - Secure Serial Upload
- **Purpose**: Upload CSV file with new serial numbers
- **Authentication**: ECC signature verification required
- **Headers**: `X-Signature`, `X-Timestamp`
- **Security**: Cryptographic signature validation, timestamp verification

#### 3. **POST `/register_public_key`** - Factory Registration
- **Purpose**: Register a new factory's public key
- **Rate Limit**: 100 requests per minute per IP
- **Parameters**: `factory_name`, `public_key`

#### 4. **GET `/check_registration_status`** - Status Check
- **Purpose**: Check registration status of a public key
- **Parameters**: `public_key`

#### 5. **Admin Endpoints**
- **GET `/admin/registration_requests`** - List all registration requests
- **POST `/admin/approve_request/<id>`** - Approve a registration request
- **POST `/admin/deny_request/<id>`** - Deny a registration request
- **POST `/admin/revoke_request/<id>`** - Revoke an approved request

## Installation & Setup

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Git

### 1. Clone the Repository

```bash
git clone <repository-url>
cd kaonic-serial-server
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Database Setup

Create a PostgreSQL database and configure the connection:

```sql
CREATE DATABASE kaonic_serials;
```

### 5. Environment Configuration

Create a `.env` file in the project root. For multiple factories, use this format:

```env
# Database Configuration
DB_NAME=kaonic_serials
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Multiple Factory Public Keys (New Format - Recommended)
# Format: ALIAS1:path/to/key1.pem,ALIAS2:path/to/key2.pem,ALIAS3:path/to/key3.pem
FACTORY_KEYS=TOKYO_FACTORY:keys/tokyo_factory_public.pem,SHANGHAI_FACTORY:keys/shanghai_factory_public.pem,BERLIN_FACTORY:keys/berlin_factory_public.pem
```

**Note**: 
- You can use any alphanumeric alias you want (e.g., `TOKYO_FACTORY`, `SHANGHAI_FACTORY`, `BERLIN_FACTORY`)
- The system also supports the legacy format: `ECC_PUBLIC_KEY_FACTORY_A=keys/factory_a_public.pem`

### 6. Initialize Database

```bash
python -c "from db import initialize_db; initialize_db()"
```

### 7. Start the Server

```bash
python server.py
```

The server will start on `http://localhost:5000`

## Usage

### For Administrators

#### Admin Terminal Interface

The system includes a powerful terminal-based admin interface:

```bash
# Start the admin terminal
python admin_terminal.py
```

**Admin Terminal Features:**
- List all registration requests
- Select requests by ID for detailed processing
- Approve, deny, or revoke requests
- View summary statistics
- Real-time status updates

#### Key Management

```bash
# Generate keys for multiple factories
python genkeys_multi.py

# Generate keys for single factory (legacy)
python genkeys.py
```

### For Factory Operators

#### Upload Serial Numbers

```bash
# Upload with factory-specific authentication
python add_serials_multi.py serials.csv keys/tokyo_factory_private.pem

# Upload with single factory (legacy)
python add_serials.py
```

## Security Features

### Cryptographic Security
- **ECC (Elliptic Curve Cryptography)** using NIST P-256 curve
- **Digital signatures** for authenticating CSV uploads
- **SHA-256 hashing** for file integrity verification
- **Timestamp-based replay protection** (5-minute window)

### Application Security
- **Rate limiting**: 100 requests per minute per IP address
- **Input validation**: Regex pattern for serial number format
- **SQL injection protection**: Parameterized queries
- **Environment variable configuration**: Sensitive data in `.env` files

## Testing

The server includes comprehensive test suites:

```bash
# Run all tests
python -m pytest tests/

# Run specific tests
python tests/test_factory_app_communication.py
python tests/test_strict_rate_limit.py
python tests/test_network_connectivity.py
```

## Project Structure

```
kaonic-serial-server/
├── server.py              # Main Flask application
├── db.py                  # Database utilities
├── admin_terminal.py      # Admin terminal interface
├── add_serials.py         # CSV upload client (single factory)
├── add_serials_multi.py   # CSV upload client (multi-factory)
├── genkeys.py             # Key generation utility (single factory)
├── genkeys_multi.py       # Key generation utility (multi-factory)
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
├── env.example            # Example environment configuration
├── .gitignore            # Git ignore rules
├── LICENSE               # MIT License
├── README.md             # This file
├── keys/                 # Cryptographic keys (generated)
│   ├── factory_a_private.pem  # Factory A private key (DO NOT COMMIT)
│   ├── factory_a_public.pem   # Factory A public key
│   ├── factory_b_private.pem  # Factory B private key (DO NOT COMMIT)
│   ├── factory_b_public.pem   # Factory B public key
│   └── ...               # Additional factory keys
├── static/               # Web assets
│   └── logo-white.png    # Company logo
├── templates/            # HTML templates
│   └── index.html        # Main web interface
└── tests/                # Test suites
    ├── test_factory_app_communication.py
    ├── test_strict_rate_limit.py
    ├── test_network_connectivity.py
    └── demo_workflow.py
```

## Production Deployment

### Environment Variables

Ensure all required environment variables are set:

```env
DB_NAME=production_db_name
DB_USER=production_db_user
DB_PASSWORD=secure_password
DB_HOST=production_db_host
DB_PORT=5432
FACTORY_KEYS=TOKYO_FACTORY:/path/to/production/tokyo_factory_public.pem,SHANGHAI_FACTORY:/path/to/production/shanghai_factory_public.pem,BERLIN_FACTORY:/path/to/production/berlin_factory_public.pem
```

### Key Management

- **Private keys** should never be committed to version control
- **Public keys** can be safely committed
- Use proper key rotation strategies in production
- Store private keys securely (e.g., in secure key management systems)

## Documentation

- **API_SPECIFICATION.md** - Complete API reference
- **SECURITY.md** - Security guidelines and best practices
- **CONTRIBUTING.md** - Contribution guidelines
- **QUICK_START.md** - Quick start guide

## License

MIT License - see LICENSE file for details.