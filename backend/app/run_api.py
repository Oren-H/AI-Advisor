#!/usr/bin/env python3
"""
FastAPI server startup script for the Course Advisor API
"""

import uvicorn
import os
import sys
from datetime import datetime

# Add the project root to Python path (go up one level from scripts folder)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TeeOutput:
    """Write to both file and terminal"""
    def __init__(self, file_path, original_stream):
        self.file = open(file_path, 'a')
        self.original = original_stream

    def write(self, data):
        self.file.write(data)
        self.file.flush()
        self.original.write(data)
        self.original.flush()

    def flush(self):
        self.file.flush()
        self.original.flush()

    def isatty(self):
        return self.original.isatty()

    def fileno(self):
        return self.original.fileno()

if __name__ == "__main__":
    # Set up logging to file
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "api.log")

    # Redirect stdout and stderr to both file and terminal
    sys.stdout = TeeOutput(log_file, sys.stdout)
    sys.stderr = TeeOutput(log_file, sys.stderr)

    print(f"\n{'='*60}")
    print(f"Server started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"

    print(f"Starting Course Advisor API server...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Reload: {reload}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"Alternative docs: http://{host}:{port}/redoc")
    print(f"Logging to: {log_file}")

    # Start the server
    uvicorn.run(
        "app.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    ) 