#!/bin/bash
# UpTime Monitor Startup Script
# This script starts both the Python backend and React frontend

echo "🚀 Starting UpTime Monitor..."
echo ""

# Set up environment for macOS with Homebrew
export PATH="/opt/homebrew/bin:$PATH"

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the UpTimeMonitor directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected files: main.py, package.json"
    exit 1
fi

# Check if virtual environment exists and activate it
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found. Please run:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating Python virtual environment..."
source venv/bin/activate

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js not found. Please install Node.js via Homebrew:"
    echo "   brew install node"
    exit 1
fi

# Check if npm dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down UpTime Monitor..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "   Backend stopped (PID: $BACKEND_PID)"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "   Frontend stopped (PID: $FRONTEND_PID)"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "🐍 Starting Python backend (FastAPI)..."
python main.py &
BACKEND_PID=$!
echo "   Backend started with PID: $BACKEND_PID"

# Wait for backend to start and check if it's running
echo "⏳ Waiting for backend to start..."
sleep 5

# Check if backend is running
if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "❌ Backend failed to start. Check the logs above for errors."
    cleanup
fi

echo "✅ Backend is running on http://localhost:8000"

echo "⚛️  Starting React frontend..."
npm start &
FRONTEND_PID=$!
echo "   Frontend started with PID: $FRONTEND_PID"

echo ""
echo "✅ UpTime Monitor is starting up!"
echo "📊 Backend API: http://localhost:8000"
echo "🌐 Frontend UI: http://localhost:3000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Wait for both processes
wait 