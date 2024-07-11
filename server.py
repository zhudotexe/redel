"""
Visualized UI for interacting with kanpai.
"""

import logging

from server import VizServer

server = VizServer()

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(server.fastapi)
