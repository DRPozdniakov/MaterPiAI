"""MasterPi AI — Application entrypoint.

Usage:
    python run.py              # Start API server (default: 0.0.0.0:8000)
    python run.py --reload     # Start with auto-reload for development
"""

import sys

import uvicorn

from config.settings import settings


def main() -> None:
    reload = "--reload" in sys.argv
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
