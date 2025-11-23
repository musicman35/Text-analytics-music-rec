#!/bin/bash

# Multi-Agent Music Recommendation System - Setup Script

set -e

echo "=================================================="
echo "Music Recommendation System - Setup"
echo "=================================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ Pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
echo "(This may take a few minutes...)"
pip install -r requirements.txt > /dev/null 2>&1
echo "✓ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.template .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your API keys before running!"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Create data directories
echo "Creating data directories..."
mkdir -p data/cache
echo "✓ Data directories created"
echo ""

# Check if Qdrant is running
echo "Checking Qdrant..."
if docker ps | grep -q qdrant; then
    echo "✓ Qdrant is running"
else
    echo "⚠️  Qdrant is not running"
    echo ""
    echo "To start Qdrant with Docker:"
    echo "  docker run -p 6333:6333 qdrant/qdrant"
    echo ""
fi

echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your API keys:"
echo "   nano .env"
echo ""
echo "2. Start Qdrant (if not running):"
echo "   docker run -p 6333:6333 qdrant/qdrant"
echo ""
echo "3. Collect data (quick test with 100 songs):"
echo "   python collect_data.py --quick"
echo ""
echo "4. Start the application:"
echo "   streamlit run streamlit_app.py"
echo ""
echo "=================================================="
