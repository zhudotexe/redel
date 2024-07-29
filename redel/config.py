import os
from pathlib import Path

# ==== core ====
REDEL_HOME = Path(os.getenv("REDEL_HOME", "~/.redel")).expanduser()

# caching of embeddings, etc
REDEL_CACHE_DIR = Path(os.getenv("REDEL_CACHE", "~/.cache/redel")).expanduser()
REDEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# log instances to ~/.redel/instances by default
DEFAULT_LOG_DIR = REDEL_HOME / "instances"
DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True)
