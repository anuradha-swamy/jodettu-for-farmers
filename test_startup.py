#!/usr/bin/env python3
"""
Test script to verify FastAPI startup without blocking
"""
import time
import subprocess
import sys
import requests
import os

def test_startup():
    print("🧪 Testing FastAPI startup without blocking...")
    
    # Kill any existing uvicorn processes
    if os.name != "nt":
        subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
    time.sleep(2)
    
    # Start the server in background
    print("🚀 Starting FastAPI server...")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "9090",
            "--app-dir",
            ".",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    # Wait a moment for startup
    time.sleep(5)
    
    try:
        # Test if server is responding
        response = requests.get("http://127.0.0.1:9090/health", timeout=10)
        if response.status_code == 200:
            print("✅ SUCCESS: Server started and is responding!")
            print(f"📊 Response: {response.json()}")
            return True
        else:
            print(f"❌ FAILED: Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ FAILED: Connection refused - server didn't start properly")
        return False
    except requests.exceptions.Timeout:
        print("❌ FAILED: Request timeout - server is hanging")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        return False
    finally:
        # Clean up
        process.terminate()
        process.wait()

if __name__ == "__main__":
    success = test_startup()
    sys.exit(0 if success else 1)
