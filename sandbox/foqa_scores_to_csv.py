"""Read all the FOQA scores and output them as CSV so I don't have to type them all."""

import glob
import json
import re
from pathlib import Path

from redel.utils import read_jsonl

REPO_ROOT = Path(__file__).parents[1]


def print_one(fp):
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
    print(",".join(map(str, (n_results, acc, perf, r1, r2, rL, bleurt, gptscore))))


for fp in glob.glob("experiments/fanoutqa/mistral/**/score.json", recursive=True):
    setting_match = re.search(r"(mistral/.+)/score\.json", fp)
    print(f"{setting_match[1]},", end="")
    print_one(fp)
