"""Read all the FOQA scores and output them as CSV so I don't have to type them all."""

import collections
import glob
import json
import re
from pathlib import Path

from redel.utils import read_jsonl

REPO_ROOT = Path(__file__).parents[1]
SETTINGS = (
    "full",
    "root-fc",
    "baseline",
    "small-leaf",
    "small-all",
    "small-baseline",
    "short-context",
    "short-baseline",
)


def score_one(fp):
    fp = Path(fp)
    with open(fp) as f:
        scores = json.load(f)
    n_results = sum(1 for _ in read_jsonl(fp.parent / "results.jsonl"))
    acc = scores["acc"]["loose"]
    perf = scores["acc"]["strict"]
    r1p = scores["rouge"]["rouge1"]["precision"]
    r1r = scores["rouge"]["rouge1"]["recall"]
    r1f = scores["rouge"]["rouge1"]["fscore"]
    r2p = scores["rouge"]["rouge2"]["precision"]
    r2r = scores["rouge"]["rouge2"]["recall"]
    r2f = scores["rouge"]["rouge2"]["fscore"]
    rLp = scores["rouge"]["rougeL"]["precision"]
    rLr = scores["rouge"]["rougeL"]["recall"]
    rLf = scores["rouge"]["rougeL"]["fscore"]
    bleurt = scores["bleurt"]
    gptscore = scores["gpt"]
    r1 = f"{r1p:.3f}/{r1r:.3f}/{r1f:.3f}"
    r2 = f"{r2p:.3f}/{r2r:.3f}/{r2f:.3f}"
    rL = f"{rLp:.3f}/{rLr:.3f}/{rLf:.3f}"
    return ",".join(map(str, (n_results, acc, perf, r1, r2, rL, bleurt, gptscore)))


# model_family -> setting -> csv
results = collections.defaultdict(lambda: collections.defaultdict(str))

# collect the results
for fp in glob.glob("experiments/fanoutqa/*/*/score.json", recursive=True):
    setting_match = re.search(r"experiments/fanoutqa/(.+)/(.+)/score\.json", fp)
    model_family = setting_match[1]
    setting = setting_match[2]
    results[model_family][setting] = score_one(fp)
    # print(f"{model_family}/{setting},", end="")

# print them
for model_family, model_results in results.items():
    print(f"====== {model_family} ======")
    for setting in SETTINGS:
        print(f"{model_family}/{setting},{model_results[setting]}")
