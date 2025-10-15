#!/usr/bin/env python3
"""Test script to check Python formatting setup."""

import subprocess
import sys

def check_black():
    """Check if black is available."""
    try:
        result = subprocess.run([sys.executable, "-m", "black", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Black is available: {result.stdout.strip()}")
            return True
        else:
            print("❌ Black is not available")
            return False
    except Exception as e:
        print(f"❌ Error checking Black: {e}")
        return False

def check_isort():
    """Check if isort is available."""
    try:
        result = subprocess.run([sys.executable, "-m", "isort", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ isort is available: {result.stdout.strip()}")
            return True
        else:
            print("❌ isort is not available")
            return False
    except Exception as e:
        print(f"❌ Error checking isort: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Checking Python formatting setup...")
    print(f"Python interpreter: {sys.executable}")
    print()
    
    black_ok = check_black()
    isort_ok = check_isort()
    
    print()
    if black_ok and isort_ok:
        print("🎉 Python formatting tools are ready!")
        print("VS Code should be able to format Python files on save.")
    else:
        print("💥 Some tools are missing. Please install them:")
        print("pip install black isort")
