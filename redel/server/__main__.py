"""
This is the minimal configuration for a ReDel visualization server. This is useful for when you just want to
view saves without defining a full system configuration.
"""

import argparse
import logging
from pathlib import Path

from redel import AUTOGENERATE_TITLE, ReDel
from redel.config import DEFAULT_LOG_DIR
from .server import VizServer

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("redel-server")

# args for save dirs
parser = argparse.ArgumentParser()
parser.add_argument(
    "--save-dir",
    action="append",
    default=[],
    help="A directory containing ReDel saves to index. Will search recursively for saves.",
)
parser.add_argument(
    "--no-default-save-dir",
    action="store_true",
    help="Do not automatically append $REDEL_HOME/instances to the save dir list.",
)
args = parser.parse_args()

# get save dirs from args
save_dirs = tuple(Path(d) for d in args.save_dir)
if not args.no_default_save_dir:
    save_dirs = (DEFAULT_LOG_DIR, *save_dirs)

# Define the configuration for each interactive session
proto = ReDel(
    title=AUTOGENERATE_TITLE,
    delegation_scheme=None,
)

print("Launching a minimal ReDel server with web browsing.")
print()
print("This is useful for quickly looking at replays, but the interactive system won't do much by default!")
print("To configure an interactive system with tools, see https://redel.readthedocs.io/en/latest/viz.html")
print()
print(f"Loading saves from the following paths: {save_dirs}")
print("Please open the URL below in your favorite web browser.")

# configure and start the server
server = VizServer(proto, save_dirs=save_dirs)
server.serve()
