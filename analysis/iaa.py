"""
Pairwise inter-annotator agreement on GPT scores between model scorers.

Usage: python analysis/iaa.py path/to/experiments
e.g. python analysis/iaa.py experiments/fanoutqa/redel-rl-like/qwen3
"""

import argparse
import glob
import json
import os
from itertools import combinations


def cohen_kappa(scores_a, scores_b):
    """Compute Cohen's kappa for two lists of binary annotations."""
    assert len(scores_a) == len(scores_b)
    n = len(scores_a)

    # Observed agreement
    p_o = sum(a == b for a, b in zip(scores_a, scores_b)) / n

    # Expected agreement
    p_a1 = sum(scores_a) / n
    p_b1 = sum(scores_b) / n
    p_e = p_a1 * p_b1 + (1 - p_a1) * (1 - p_b1)

    if p_e == 1.0:
        return 1.0
    return (p_o - p_e) / (1 - p_e)


def percent_agreement(scores_a, scores_b):
    n = len(scores_a)
    return sum(a == b for a, b in zip(scores_a, scores_b)) / n


def load_scores(path):
    with open(path) as f:
        data = json.load(f)
    return data["gpt"], {r["question_id"]: r["gpt"] for r in data["raw"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("experiment_dir", help="Path to the experiment directory containing score-*.json files")
    args = parser.parse_args()

    score_dir = os.path.abspath(args.experiment_dir)
    if not os.path.isdir(score_dir):
        parser.error(f"Not a directory: {score_dir}")

    score_files = sorted(
        p for p in glob.glob(os.path.join(score_dir, "score-*.json")) if os.path.basename(p) != "score.json"
    )

    if not score_files:
        print("No score-*.json files found.")
        return

    # Load all scores, aligned by question_id
    all_scores = {}
    all_totals = {}
    for path in score_files:
        name = os.path.basename(path).removeprefix("score-").removesuffix(".json")
        all_totals[name], all_scores[name] = load_scores(path)

    print(f"Found {len(score_files)} scorer files:")
    for name, total in all_totals.items():
        print(f"  {name:<35} gpt={total:.4f}")
    print()

    # Align on common question IDs
    common_ids = sorted(set.intersection(*(set(s.keys()) for s in all_scores.values())))
    print(f"Common questions: {len(common_ids)}\n")

    names = list(all_scores.keys())
    print(f"{'Scorer A':<35} {'Scorer B':<35} {'% Agree':>8} {'Kappa':>8}")
    print("-" * 90)
    for name_a, name_b in combinations(names, 2):
        sa = [all_scores[name_a][qid] for qid in common_ids]
        sb = [all_scores[name_b][qid] for qid in common_ids]
        pct = percent_agreement(sa, sb)
        kappa = cohen_kappa(sa, sb)
        print(f"{name_a:<35} {name_b:<35} {pct:>8.3f} {kappa:>8.3f}")
        disagreements = [
            (qid, all_scores[name_a][qid], all_scores[name_b][qid])
            for qid in common_ids
            if all_scores[name_a][qid] != all_scores[name_b][qid]
        ]
        # print(f"  Disagreements ({len(disagreements)}):")
        # for qid, va, vb in disagreements:
        #     print(f"    {qid}  {name_a}={va}  {name_b}={vb}")
        # print()


if __name__ == "__main__":
    main()
