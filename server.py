"""
Example server for the ReDel web interface.

Environment Variables:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY (optional)

Configuration:
- root engine: gpt-4
- delegate engine: gpt-4
- tools:
    - Browsing (always included in delegates)
        - long engine: claude-3-opus (for summarizing long webpages, if ANTHROPIC_API_KEY is set)
"""

import logging
import os

from kani.engines.anthropic import AnthropicEngine
from kani.engines.openai import OpenAIEngine
from kani.ext.ratelimits import RatelimitedEngine

from redel import AUTOGENERATE_TITLE, ReDel
from redel.server import VizServer
from redel.tools.browsing import Browsing

# Define the engines
engine = OpenAIEngine(model="gpt-4", temperature=0.8, top_p=0.95)
if "ANTHROPIC_API_KEY" in os.environ:
    long_engine = RatelimitedEngine(
        AnthropicEngine(model="claude-3-opus-20240229", temperature=0.7, max_tokens=4096), max_concurrency=1
    )
else:
    long_engine = None

# Define the configuration for each interactive session
ai = ReDel(
    root_engine=engine,
    delegate_engine=engine,
    title=AUTOGENERATE_TITLE,
    tool_configs={
        Browsing: {
            "always_include": True,
            "kwargs": {"long_engine": long_engine},
        },
    },
)

# configure and start the server
server = VizServer(ai)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server.serve()
