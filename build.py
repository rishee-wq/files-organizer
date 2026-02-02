#!/usr/bin/env python
"""
Build script for RishFlow Windows Desktop App
Generates an executable with logo.ico as the app icon
"""

import os
import subprocess
import sys
from pathlib import Path

def build_app():
    """Build RishFlow as a Windows desktop application"""
    
    print("🚀 Building RishFlow v2.0 Windows Desktop App...")
    
    # Check if logo.ico exists
    if not os.path.exists("logo.ico"):
        print("❌ Error: logo.ico not found!")
        return False
    
    # PyInstaller command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=RishFlow",
        "--onefile",
        "--windowed",
        f"--icon=logo.ico",
        "--add-data=stitch_rishflow_dashboard_home (1);stitch_rishflow_dashboard_home (1)",
        "--add-data=Logo.jpg;.",
        "--add-data=dark_theme.qss;.",
        "--add-data=requirements.txt;.",
        "--hidden-import=cv2",
        "--hidden-import=pytesseract",
        "--hidden-import=PIL",
        "--hidden-import=numpy",
        "--hidden-import=imagehash",
        "--collect-all=webview",
        "app.py"
    ]
    
    try:
        print("\n📦 Running PyInstaller...")
        result = subprocess.run(cmd, check=True)
        
        print("\n✅ Build successful!")
        print("\n📁 Your executable is ready:")
        exe_path = os.path.join("dist", "RishFlow.exe")
        print(f"   {os.path.abspath(exe_path)}")
        print("\n🎉 You can now run RishFlow.exe directly!")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return build_app()

if __name__ == "__main__":
    success = build_app()
    sys.exit(0 if success else 1)
