#!/bin/bash
# UpTime Monitor Startup Script
# This script starts both the Python backend and React frontend

echo "🚀 Starting UpTime Monitor..."
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "📦 Activating Python virtual environment..."
    source venv/bin/activate
fi

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down UpTime Monitor..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "🐍 Starting Python backend (FastAPI)..."
python main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

echo "⚛️  Starting React frontend..."
npm start &
FRONTEND_PID=$!

echo ""
echo "✅ UpTime Monitor is starting up!"
echo "📊 Backend API: http://localhost:8000"
echo "🌐 Frontend UI: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Wait for both processes
wait 