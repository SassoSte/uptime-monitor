#!/bin/bash

echo "Starting UpTime Monitor..."
echo

echo "[1/3] Checking Python dependencies..."
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "Error: Failed to install Python dependencies"
    exit 1
fi

echo "[2/3] Checking Node.js dependencies..."
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install Node.js dependencies"
        exit 1
    fi
fi

echo "[3/3] Starting services..."
echo

echo "Starting backend server..."
python main.py &
BACKEND_PID=$!

sleep 5

echo "Starting frontend development server..."
npm start &
FRONTEND_PID=$!

echo
echo "UpTime Monitor is running!"
echo "- Backend API: http://localhost:8000"
echo "- Frontend UI: http://localhost:3000"
echo
echo "Press Ctrl+C to stop both services"

# Function to cleanup background processes
cleanup() {
    echo
    echo "Shutting down UpTime Monitor..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap SIGINT (Ctrl+C) to cleanup
trap cleanup SIGINT

# Wait for background processes
wait