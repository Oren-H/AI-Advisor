#!/bin/bash

# Development startup script for AI Advisor
# This script starts both the FastAPI backend and React frontend

echo "🚀 Starting AI Advisor Development Environment"
echo "=============================================="

# Function to cleanup background processes on exit
cleanup() {
    echo "🛑 Shutting down development environment..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if Python and Node.js are available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed or not in PATH"
    exit 1
fi

# Check if required directories exist
if [ ! -d "frontend" ]; then
    echo "❌ Frontend directory not found"
    exit 1
fi

# Install frontend dependencies if node_modules doesn't exist
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Activate virtual environment and start the FastAPI backend
echo "🔧 Starting FastAPI backend..."
if [ -d "rag_env" ]; then
    echo "  ✓ Activating virtual environment..."
    source rag_env/bin/activate
fi
python3 scripts/run_api.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ! curl -s http://localhost:8000/ > /dev/null; then
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Backend is running on http://localhost:8000"

# Start the React frontend
echo "🎨 Starting React frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 3

echo "✅ Frontend is starting (check terminal output for actual port)"
echo ""
echo "🌐 Access your application:"
echo "   Frontend: http://localhost:3000 (or next available port)"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for background processes
wait 