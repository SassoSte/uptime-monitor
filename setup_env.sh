#!/bin/bash
# UpTime Monitor Environment Setup Script
# This script sets up the environment for the UpTime Monitor application

echo "🔧 Setting up UpTime Monitor environment..."
echo ""

# Set up environment for macOS with Homebrew
export PATH="/opt/homebrew/bin:$PATH"

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the UpTimeMonitor directory"
    echo "   Current directory: $(pwd)"
    exit 1
fi

echo "✅ Directory check passed"

# Check Python version
echo "🐍 Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Check Node.js
echo "📦 Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Installing via Homebrew..."
    brew install node
else
    echo "✅ Node.js found: $(node --version)"
fi

# Check npm
echo "📦 Checking npm..."
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install Node.js which includes npm"
    exit 1
else
    echo "✅ npm found: $(npm --version)"
fi

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "   Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install npm dependencies
echo "📦 Installing npm dependencies..."
npm install

echo ""
echo "✅ Environment setup complete!"
echo ""
echo "🚀 To start the application, run:"
echo "   ./start_app.sh"
echo ""
echo "📚 Available commands:"
echo "   ./start_app.sh     - Start the full application"
echo "   python main.py     - Start backend only"
echo "   npm start          - Start frontend only"
echo "" 