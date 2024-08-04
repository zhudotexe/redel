"""
Usage: python score_webarena.py [path/to/results.jsonl,...]
"""

import asyncio
import glob
import json
import sys
from pathlib import Path

from redel.utils import read_jsonl

WA_ROOT = Path(__file__).parent / "experiments/webarena"
START_IDX = 0
END_IDX = 812
SKIP = 3  # 0, 812, 3 = 270 trials for small
EXPECTED = len(range(START_IDX, END_IDX, SKIP))


def get_config(idx: int) -> dict:
    fp = WA_ROOT / f"config/{idx}.json"
    with open(fp) as f:
        return json.load(f)


def score_submission(fp: Path):
    """Read in the results file and return the proportion of successful runs."""
    # read results
    results = list(read_jsonl(fp))
    # read configs, get achievable/unachievable idxs
    achievable_idxs = set()
    unachievable_idxs = set()
    for idx in range(START_IDX, END_IDX, SKIP):
        cfg = get_config(idx)
        ra = cfg["eval"].get("reference_answers")
        if ra and ra.get("fuzzy_match") == "N/A":
            unachievable_idxs.add(idx)
        else:
            achievable_idxs.add(idx)

    # total up results
    split = fp.parent.name
    total = 0
    total_achievable = 0
    total_unachievable = 0
    for r in results:
        total += r["score"]
        if r["id"] in achievable_idxs:
            total_achievable += r["score"]
        else:
            total_unachievable += r["score"]

    # print score
    n_success = len(results)
    score = total / EXPECTED
    score_achievable = total_achievable / len(achievable_idxs)
    score_unachievable = total_unachievable / len(unachievable_idxs)
    print(
        f"{split}: {score} -- {int(total)} / {EXPECTED} ({n_success} / {EXPECTED} result rows) --"
        f" {score_achievable} AC; {score_unachievable} UA"
    )


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
