
#!/bin/bash

set -e

echo "========================================"
echo "  DragonAI Backend - Starting Service"
echo "========================================"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "[WARNING] .env file not found!"
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo "Please edit .env file with your configuration!"
    echo ""
fi

# Create required directories
mkdir -p storage
mkdir -p chroma_db
mkdir -p logs

# Check Python
if ! command -v python3 &amp;&gt; /dev/null; then
    echo "[ERROR] Python 3 not found! Please install Python 3.13+"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
echo "Installing/updating dependencies..."
pip install -r requirements.txt

# Initialize database
echo ""
echo "Initializing database..."
python3 scripts/init_db.py

# Start the server
echo ""
echo "========================================"
echo "  Starting DragonAI Server..."
echo "========================================"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo "Health Check:      http://localhost:8000/health"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

