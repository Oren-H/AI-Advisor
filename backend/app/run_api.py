#!/usr/bin/env python3
"""
Convenience runner for the FastAPI app.

Usage:
  python scripts/run_api.py

Environment variables:
  HOST       - default "0.0.0.0"
  PORT       - default "8000"
  RELOAD     - "true" to enable autoreload (default "false")
  LOG_LEVEL  - uvicorn log level (default "info")
"""
import os
import sys
from pathlib import Path

import uvicorn


def main() -> None:
    # Ensure app directory is on sys.path
    app_dir = Path(__file__).resolve().parent
    project_root = app_dir.parent.parent
    # Add project root first so absolute imports like `backend.*` resolve
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    # Also add the app directory to import sibling modules like `main`
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")

    print(f"Starting AI Advisor API at http://{host}:{port} (reload={reload})")

    # Import after adding to path
    from backend.app.main import app

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )


if __name__ == "__main__":
    main()


