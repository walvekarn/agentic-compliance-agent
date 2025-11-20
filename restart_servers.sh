#!/bin/bash
# Restart Script for Agentic Compliance Agent
# This script stops existing servers and starts fresh ones

echo "🛑 Stopping existing servers..."

# Kill processes on ports 8000 and 8501
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8501 | xargs kill -9 2>/dev/null

sleep 2

echo "✅ Ports cleared"
echo ""
echo "🚀 Starting servers..."
echo ""

# Start backend in background
echo "Starting backend on port 8000..."
cd "$(dirname "$0")"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"
echo "Logs: tail -f backend.log"
echo ""

# Wait a moment for backend to start
sleep 3

# Start frontend in background
echo "Starting frontend on port 8501..."
streamlit run frontend/Home.py --server.port 8501 > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"
echo "Logs: tail -f frontend.log"
echo ""

echo "✅ Servers started!"
echo ""
echo "📍 Access points:"
echo "   Backend API: http://localhost:8000"
echo "   Frontend: http://localhost:8501"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "To stop servers:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   or: pkill -f 'uvicorn backend.main'"
echo "   or: pkill -f 'streamlit run'"

