#!/bin/bash

echo "🌱 Starting Remedi Backend..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch venv/.installed
fi

# Start the server
echo ""
echo "✅ Backend starting on http://0.0.0.0:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
python main.py
