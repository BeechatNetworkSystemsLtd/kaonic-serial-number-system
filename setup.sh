#!/bin/bash
# Kaonic Serial Number System - Server Setup Script

echo "🚀 Setting up Kaonic Serial Number System Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your database configuration before starting the server"
fi

# Initialize database
echo "🗄️ Initializing database..."
python -c "from db import initialize_db; initialize_db()"

echo "✅ Setup complete!"
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  python server.py"
echo ""
echo "To run admin terminal:"
echo "  source venv/bin/activate"
echo "  python admin_terminal.py"
