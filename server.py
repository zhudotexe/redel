"""
Example server for the ReDel web interface.

Configuration:
- root engine: gpt-4o
- delegate engine: gpt-4o
- delegation scheme: DelegateOne
- tools:
    - Browsing (always included in delegates)
"""

import argparse
import logging
from pathlib import Path

from kani.engines.openai import OpenAIEngine

from redel import AUTOGENERATE_TITLE, DEFAULT_LOG_DIR, ReDel
from redel.delegation import DelegateOne
from redel.server import VizServer
from redel.tools.browsing import Browsing

# CLI args for Docker
parser = argparse.ArgumentParser()
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", default=8000)
args = parser.parse_args()

# Host saves from the experiments
EXPERIMENTS_DIR = Path(__file__).parent / "experiments"

# Define the engines -- see https://kani.readthedocs.io/en/latest/engines.html for a list of available engines
engine = OpenAIEngine(model="gpt-4o", temperature=0.8)

# Define the configuration for each interactive session --
# see the paper or https://redel.readthedocs.io/en/latest/redel.html#the-redel-class for more info
ai = ReDel(
    root_engine=engine,
    delegate_engine=engine,
    title=AUTOGENERATE_TITLE,
    delegation_scheme=DelegateOne,
    tool_configs={
        Browsing: {"always_include": True},
    },
)

# configure and start the server
server = VizServer(ai, save_dirs=(DEFAULT_LOG_DIR, EXPERIMENTS_DIR))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server.serve(host=args.host, port=args.port)
