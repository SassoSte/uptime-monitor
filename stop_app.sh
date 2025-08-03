#!/bin/bash
# UpTime Monitor Stop Script
# This script stops the running UpTime Monitor application

echo "🛑 Stopping UpTime Monitor..."

# Find and kill Python backend process
BACKEND_PID=$(ps aux | grep "python main.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$BACKEND_PID" ]; then
    echo "   Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID
    sleep 2
    # Force kill if still running
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "   Force stopping backend..."
        kill -9 $BACKEND_PID
    fi
else
    echo "   Backend not found running"
fi

# Find and kill Node.js frontend process
FRONTEND_PID=$(ps aux | grep "npm start" | grep -v grep | awk '{print $2}')
if [ ! -z "$FRONTEND_PID" ]; then
    echo "   Stopping frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID
    sleep 2
    # Force kill if still running
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "   Force stopping frontend..."
        kill -9 $FRONTEND_PID
    fi
else
    echo "   Frontend not found running"
fi

# Kill any remaining React development server processes
REACT_PIDS=$(ps aux | grep "react-scripts start" | grep -v grep | awk '{print $2}')
if [ ! -z "$REACT_PIDS" ]; then
    echo "   Stopping React development servers..."
    echo $REACT_PIDS | xargs kill
fi

echo "✅ UpTime Monitor stopped successfully!"
echo "" 