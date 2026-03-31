# Deployment script to restart the server with fixes (Windows)
import subprocess
import sys
import time
import os

def stop_server():
    """Stop any running server processes"""
    print("🛑 Stopping any running server...")
    try:
        # Kill uvicorn processes
        subprocess.run(['taskkill', '/F', '/IM', 'uvicorn.exe'], capture_output=True)
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True)
    except:
        pass
    
    time.sleep(2)

def start_server():
    """Start the production server"""
    print("🔄 Starting server with fixed animal_routes_fixed.py...")
    print("🔧 Look for this message in logs: '🔧✅ FIXED animal_routes_fixed.py loaded'")
    print("🔍 Look for debug messages when calling /all-animals endpoint")
    
    # Set environment variables
    env = os.environ.copy()
    env['HOST'] = '0.0.0.0'
    env['PORT'] = '8000'
    env['DEBUG'] = 'false'
    
    # Start the server
    try:
        subprocess.run([sys.executable, 'main_production.py'], env=env)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")

if __name__ == "__main__":
    print("🚀 DEPLOYING FIXED VERSION...")
    stop_server()
    start_server()
