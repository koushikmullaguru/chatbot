#!/bin/bash

# Script to start the AI School Chat Application on localhost

echo "Starting AI School Chat Application on localhost..."
echo "=================================================="

# Check if we're in the correct directory
if [ ! -f "package.json" ] || [ ! -f "backend/start.py" ]; then
    echo "Error: Please run this script from the root directory of the project."
    exit 1
fi

# Function to kill background processes on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    echo "Servers stopped."
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Start the backend server
echo "Starting backend server on http://localhost:8000..."
cd backend
python start.py &
BACKEND_PID=$!
cd ..

# Wait a moment for the backend to start
sleep 3

# Start the frontend server
echo "Starting frontend server on http://localhost:3000..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=================================================="
echo "Servers are running:"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:8000"
echo "- API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."
echo "=================================================="

# Wait for processes
wait