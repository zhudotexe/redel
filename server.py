"""
Default server for the ReDel web interface.

Default configuration:
- root engine: gpt-4
- delegate engine: gpt-4
- tools:
    - Browsing (always included in delegates)
        - long engine: claude-3-opus (for summarizing long webpages)
"""

import logging
from pathlib import Path

from kani.engines.anthropic import AnthropicEngine
from kani.engines.openai import OpenAIEngine
from kani.ext.ratelimits import RatelimitedEngine

from redel import AUTOGENERATE_TITLE
from redel.eventlogger import DEFAULT_LOG_DIR
from redel.tools.browsing import BrowsingMixin
from server import VizServer

# Host saves from the experiments
EXPERIMENTS_DIR = Path(__file__).parent / "experiments"

# Define the engines
engine = OpenAIEngine(model="gpt-4", temperature=0.8, top_p=0.95)
long_engine = RatelimitedEngine(
    AnthropicEngine(model="claude-3-opus-20240229", temperature=0.7, max_tokens=4096), max_concurrency=1
)

# Define the configuration for each interactive session
redel_config = dict(
    root_engine=engine,
    delegate_engine=engine,
    title=AUTOGENERATE_TITLE,
    tool_configs={
        BrowsingMixin: {
            "always_include": True,
            "kwargs": {"long_engine": long_engine},
        },
    },
)

# configure and start the server
server = VizServer(save_dirs=(DEFAULT_LOG_DIR, EXPERIMENTS_DIR), redel_kwargs=redel_config)

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(server.fastapi)
