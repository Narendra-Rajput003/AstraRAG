#!/usr/bin/env python3
"""
AstraRAG Main Entry Point
Runs the Streamlit application.
"""

import subprocess
import sys
import os

def main():
    """Run the AstraRAG Streamlit application."""
    app_path = os.path.join("src", "frontend", "app.py")
    if not os.path.exists(app_path):
        print(f"Error: {app_path} not found.")
        sys.exit(1)

    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", app_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()