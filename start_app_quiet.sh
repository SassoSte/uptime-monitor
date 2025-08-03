#!/bin/bash
# UpTime Monitor Quiet Startup Script
# This script starts the application in the background with minimal console output

echo "🚀 Starting UpTime Monitor in background..."
echo ""

# Set up environment for macOS with Homebrew
export PATH="/opt/homebrew/bin:$PATH"

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the UpTimeMonitor directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup_env.sh first"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Activate virtual environment
source venv/bin/activate

# Start backend in background with logs to file
echo "🐍 Starting backend (logs: logs/backend.log)..."
python main.py > logs/backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "❌ Backend failed to start. Check logs/backend.log"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend in background
echo "⚛️  Starting frontend (logs: logs/frontend.log)..."
npm start > logs/frontend.log 2>&1 &
FRONTEND_PID=$!

echo ""
echo "✅ UpTime Monitor is running in background!"
echo "📊 Backend API: http://localhost:8000"
echo "🌐 Frontend UI: http://localhost:3000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "📋 Process IDs:"
echo "   Backend: $BACKEND_PID"
echo "   Frontend: $FRONTEND_PID"
echo ""
echo "📄 Log files:"
echo "   Backend: logs/backend.log"
echo "   Frontend: logs/frontend.log"
echo ""
echo "🛑 To stop the application:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   or run: ./stop_app.sh"
echo "" 