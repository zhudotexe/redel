"""
This is the minimal configuration for a ReDel visualization server. This is useful for when you just want to
view saves without defining a full system configuration.
"""

import logging

from redel import AUTOGENERATE_TITLE
from .server import VizServer

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("redel-server")

# todo args for save dirs

# Define the configuration for each interactive session
redel_config = dict(title=AUTOGENERATE_TITLE)

log.info("Launching a minimal ReDel server with web browsing...")
log.info("Please open the URL below in your favorite web browser.")

# configure and start the server
server = VizServer(redel_kwargs=redel_config)
server.serve()
