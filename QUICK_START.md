# Kaonic Serial Number System - Quick Start Guide

## 🚀 **Quick Setup**

### Option 1: Automated Setup (Recommended)
```bash
# Run the setup script
./setup.sh

# Start the server
source venv/bin/activate
python server.py
```

### Option 2: Manual Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your database settings

# Initialize database
python -c "from db import initialize_db; initialize_db()"

# Start server
python server.py
```

## 🔧 **Configuration**

### 1. Database Setup
Edit the `.env` file with your PostgreSQL settings:
```env
DB_NAME=kaonic_serials
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 2. Factory Keys (Optional)
For multiple factories, add to `.env`:
```env
FACTORY_KEYS=TOKYO_FACTORY:keys/tokyo_factory_public.pem,SHANGHAI_FACTORY:keys/shanghai_factory_public.pem
```

## 🎯 **Usage**

### Start Server
```bash
source venv/bin/activate
python server.py
```
Server will start on `http://localhost:5000`

### Admin Terminal
```bash
source venv/bin/activate
python admin_terminal.py
```

### Generate Keys (Optional)
```bash
# Single factory
python genkeys.py

# Multiple factories
python genkeys_multi.py
```

## 📡 **API Endpoints**

- **GET** `/verify?sn=K1S-1234` - Verify serial number
- **POST** `/add_serials` - Upload serial numbers
- **POST** `/register_public_key` - Register factory
- **GET** `/check_registration_status` - Check status
- **GET** `/admin/registration_requests` - List requests

## 🧪 **Testing**

```bash
# Run tests
python tests/test_factory_app_communication.py
python tests/test_strict_rate_limit.py
python tests/test_network_connectivity.py
```

## 🆘 **Troubleshooting**

### Server won't start
- Check if virtual environment is activated: `source venv/bin/activate`
- Verify dependencies are installed: `pip list`
- Check database connection in `.env` file

### Database errors
- Ensure PostgreSQL is running
- Verify database credentials in `.env`
- Run database initialization: `python -c "from db import initialize_db; initialize_db()"`

### Port already in use
- Kill existing processes: `pkill -f "python.*server.py"`
- Use different port: `python server.py --port 5001`

## 📚 **Documentation**

- **[Complete README](README.md)** - Full documentation
- **[Admin Terminal Guide](ADMIN_TERMINAL_GUIDE.md)** - Admin interface
- **[Factory Name Guide](FACTORY_NAME_GUIDE.md)** - Factory management
- **[Comprehensive Analysis](COMPREHENSIVE_ANALYSIS.md)** - System analysis

## 🎉 **Success!**

If you see:
```
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:5000
* Running on http://[::1]:5000
```

Your server is running successfully! 🚀
