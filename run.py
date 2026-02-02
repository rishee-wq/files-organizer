import subprocess
import sys
import os
import threading
import time

def install_requirements():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def run_http_server():
    """Start HTTP server on port 8000"""
    print("📡 Starting HTTP server on port 8000...")
    os.system("python -m http.server 8000")

def run_app():
    """Start the RishFlow app"""
    print("🎨 Starting RishFlow application...")
    time.sleep(2)  # Wait for HTTP server to start
    os.system("python app.py")

if __name__ == "__main__":
    print("🚀 Starting RishFlow v2.0...")
    install_requirements()
    
    # Run the app directly (HTTP server not needed anymore)
    run_app()