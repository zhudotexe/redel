"""
Visualized UI for interacting with kanpai.
"""

import logging
from pathlib import Path

from redel.eventlogger import DEFAULT_LOG_DIR
from server import VizServer

EXPERIMENTS_DIR = Path(__file__).parent / "experiments"

server = VizServer(save_dirs=(DEFAULT_LOG_DIR, EXPERIMENTS_DIR))

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(server.fastapi)
