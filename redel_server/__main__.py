"""
This is the minimal configuration for a ReDel visualization server with web browsing.
"""

import logging

import uvicorn

from redel import AUTOGENERATE_TITLE
from redel.tools.browsing import BrowsingMixin
from .server import VizServer

# Define the configuration for each interactive session
redel_config = dict(
    title=AUTOGENERATE_TITLE,
    tool_configs={
        BrowsingMixin: {"always_include": True},
    },
)

# configure and start the server
server = VizServer(redel_kwargs=redel_config)

logging.basicConfig(level=logging.INFO)
uvicorn.run(server.fastapi)
