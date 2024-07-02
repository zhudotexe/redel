"""
Usage: python score_webarena.py [path/to/results.jsonl,...]
"""

import asyncio
import glob
import json
import sys
from pathlib import Path

from redel.utils import read_jsonl


def score_submission(fp: Path):
    """Read in the results file and return the proportion of successful runs."""
    results = list(read_jsonl(fp))
    split = fp.parent.name
    score = sum(r["score"] for r in results) / len(results)
    print(f"{split}: {score}")


async def main():
    paths = sys.argv[1:]
    if len(paths) == 1 and "*" in paths[0]:
        paths = glob.glob(paths[0], recursive=True)
    if not paths:
        print("no paths specified! Usage: python score_webarena.py [path/to/results.jsonl ...]")
    print(paths)
    for fp in paths:
        score_submission(Path(fp))


if __name__ == "__main__":
    asyncio.run(main())
