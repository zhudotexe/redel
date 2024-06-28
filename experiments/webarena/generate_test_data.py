"""Replace the website placeholders with website domains from env_config
Generate the test data

Adapted from scripts/generate_test_data.py in the webarena repo.
"""

import json
from pathlib import Path

from browser_env import env_config

EXPERIMENTS_DIR = Path(__file__).parents[1]
(EXPERIMENTS_DIR / "webarena/config").mkdir(exist_ok=True)


def main() -> None:
    with open(EXPERIMENTS_DIR / "webarena/test.raw.json", "r") as f:
        raw = f.read()
    raw = raw.replace("__GITLAB__", env_config.GITLAB)
    raw = raw.replace("__REDDIT__", env_config.REDDIT)
    raw = raw.replace("__SHOPPING__", env_config.SHOPPING)
    raw = raw.replace("__SHOPPING_ADMIN__", env_config.SHOPPING_ADMIN)
    raw = raw.replace("__WIKIPEDIA__", env_config.WIKIPEDIA)
    raw = raw.replace("__MAP__", env_config.MAP)
    with open(EXPERIMENTS_DIR / "webarena/config/test.json", "w") as f:
        f.write(raw)
    # split to multiple files
    data = json.loads(raw)
    for idx, item in enumerate(data):
        with open(EXPERIMENTS_DIR / f"webarena/config/{idx}.json", "w") as f:
            json.dump(item, f, indent=2)


if __name__ == "__main__":
    main()
