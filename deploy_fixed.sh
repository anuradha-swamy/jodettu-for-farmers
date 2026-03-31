#!/bin/bash
# Deployment script to restart the server with fixes

echo "🚀 DEPLOYING FIXED VERSION..."

# Stop any running server
echo "🛑 Stopping any running server..."
pkill -f "uvicorn.*main_production" || true
pkill -f "python.*main_production" || true

# Wait a moment for processes to stop
sleep 2

# Start the server with the fixed code
echo "🔄 Starting server with fixed animal_routes_fixed.py..."
echo "🔧 Look for this message in logs: '🔧✅ FIXED animal_routes_fixed.py loaded'"
echo "🔍 Look for debug messages when calling /all-animals endpoint"

# Start the production server
export HOST=0.0.0.0
export PORT=8000
export DEBUG=false

python main_production.py
