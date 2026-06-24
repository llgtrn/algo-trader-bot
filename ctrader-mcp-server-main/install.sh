#!/bin/bash
# Installation script for cTrader MCP Server

set -e

echo "==================================================================="
echo "   cTrader MCP Server Installation"
echo "==================================================================="
echo ""

# Function to check internet connectivity
check_internet() {
    echo "Checking internet connectivity..."
    if ! ping -c 1 pypi.org &> /dev/null; then
        echo "⚠ Warning: Cannot reach pypi.org. Network issues may cause installation problems."
        echo "Please check your internet connection."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "✓ Internet connectivity confirmed"
    fi
    echo ""
}

# Check internet first
check_internet

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found. Please install Python 3.10 or higher."
    exit 1
fi

python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version detected"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo "✓ pip upgraded"
echo ""

# Clear pip cache to avoid corruption issues
echo "Clearing pip cache..."
pip cache purge --quiet 2>/dev/null || true
echo "✓ pip cache cleared"
echo ""

# Install requirements with retries and better error handling
echo "Installing dependencies..."
if ! pip install -r requirements.txt --no-cache-dir --timeout 60; then
    echo "✗ Initial installation failed. Trying with verbose output..."
    echo "Attempting to install dependencies one by one..."
    
    # Try installing core dependencies individually
    echo "Installing mcp..."
    pip install mcp>=0.9.0 --no-cache-dir --timeout 60
    
    echo "Installing ctrader-open-api..."
    pip install ctrader-open-api==0.9.2 --no-cache-dir --timeout 60
    
    echo "Installing twisted..."
    pip install twisted>=23.0.0 --no-cache-dir --timeout 60
    
    echo "Installing python-dotenv..."
    pip install python-dotenv>=1.0.0 --no-cache-dir --timeout 60
    
    echo "Installing pandas..."
    pip install pandas>=2.0.0 --no-cache-dir --timeout 60
    
    echo "Installing numpy..."
    pip install numpy>=1.24.0 --no-cache-dir --timeout 60
    
    echo "✓ Dependencies installed individually"
else
    echo "✓ Dependencies installed"
fi

# Install optional TLS enhancement
echo "Installing optional TLS enhancement..."
pip install service_identity --no-cache-dir --quiet || echo "⚠ service_identity installation failed (optional)"
echo "✓ TLS enhancement installed"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠ .env file not found!"
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠ IMPORTANT: Edit .env file with your cTrader credentials!"
    echo ""
    echo "You need to add:"
    echo "  - CLIENT_ID"
    echo "  - CLIENT_SECRET"
    echo "  - ACCESS_TOKEN"
    echo "  - ACCOUNT_ID"
    echo ""
    echo "Get credentials from: https://help.ctrader.com/open-api/creating-new-app/"
    echo ""
else
    echo "✓ .env file found"
    echo ""
fi

echo "==================================================================="
echo "   Installation Complete!"
echo "==================================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your cTrader API credentials:"
echo "   nano .env"
echo ""
echo "2. Test the server:"
echo "   source venv/bin/activate"
echo "   python test_server.py"
echo ""
echo "3. Configure your AI assistant (e.g., Claude Desktop)"
echo "   See docs/CONFIGURATION.md for details"
echo ""
echo "4. Start the MCP server:"
echo "   python server.py"
echo ""
echo "==================================================================="
