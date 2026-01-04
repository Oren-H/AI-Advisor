#!/usr/bin/env python3
"""
FastAPI server startup script for the Course Advisor API
"""

import uvicorn
import os
import sys

# Add the project root to Python path (go up one level from scripts folder)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Also add the template src (if present) so "app.api" resolves to our local app package.
# This allows `uvicorn.run("app.api:app", ...)` to work consistently.
template_src = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "template_langgraph_pr",
    "src"
)
if os.path.isdir(template_src):
    sys.path.insert(0, template_src)

if __name__ == "__main__":
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    print(f"🚀 Starting Course Advisor API server...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🔄 Reload: {reload}")
    print(f"📖 API Documentation: http://{host}:{port}/docs")
    print(f"🔧 Alternative docs: http://{host}:{port}/redoc")
    
    # Start the server
    uvicorn.run(
        "app.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    ) 