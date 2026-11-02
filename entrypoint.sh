#!/usr/bin/env bash
set -e

echo "=================================================="
echo " Starting SubTracker Fullstack Application"
echo "=================================================="

# Function to handle shutdown signals gracefully
cleanup() {
    echo "Stopping all services..."
    if [ -n "$BACKEND_PID" ]; then
        kill -TERM "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill -TERM "$FRONTEND_PID" 2>/dev/null || true
    fi
    wait 2>/dev/null || true
    echo "Services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

# 1. Start FastAPI Backend
echo "Starting FastAPI backend on port 8091..."
cd /app/backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8091 &
BACKEND_PID=$!

# 2. Start Frontend Application
echo "Starting Frontend application on port 8080..."
cd /app/frontend
npm run dev -- --host 0.0.0.0 --port 8080 &
FRONTEND_PID=$!

echo "=================================================="
echo " SubTracker services are running:"
echo " - Frontend Web UI:  http://localhost:8080"
echo " - Backend REST API: http://localhost:8091"
echo " - API Documentation: http://localhost:8091/docs"
echo "=================================================="

# Wait for background processes
wait -n "$BACKEND_PID" "$FRONTEND_PID"
