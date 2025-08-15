#!/usr/bin/env python3
"""
Startup script for Interactive Story Game Backend
Installs dependencies and starts the Flask server
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"Python version: {sys.version.split()[0]}")

def install_dependencies():
    """Install required Python packages"""
    print("Installing dependencies...")
    
    requirements_file = os.path.join('backend', 'requirements.txt')
    
    if not os.path.exists(requirements_file):
        print(f"Requirements file not found: {requirements_file}")
        sys.exit(1)
    
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', requirements_file
        ], check=True)
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        print("Try running manually: pip install -r backend/requirements.txt")
        sys.exit(1)

def start_backend():
    """Start the Flask backend server"""
    print("Starting backend server...")
    
    backend_dir = os.path.join(os.getcwd(), 'backend')
    app_file = os.path.join(backend_dir, 'app.py')
    
    if not os.path.exists(app_file):
        print(f"Backend app not found: {app_file}")
        sys.exit(1)
    
    try:
        os.chdir(backend_dir)
        subprocess.run([sys.executable, 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\nBackend server stopped")
    except subprocess.CalledProcessError as e:
        print(f"Failed to start backend: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    print("Interactive Story Game Backend Startup")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Start backend
    start_backend()

if __name__ == '__main__':
    main()