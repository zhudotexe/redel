"""
Usage: python score_fanoutqa.py [path/to/results.jsonl,...]

Outputs `score.json` files next to each input `results.jsonl` file.
"""

import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import List

import fanoutqa
from fanoutqa.eval.scorer import Scorer


def read_jsonl_answers(fp: Path) -> List[dict]:
    """Given a path to a JSONL file, return a list of the answers in that file."""
    answers = []
    with open(fp) as f:
        for ln in f:
            if not ln:
                continue
            ans = json.loads(ln)
            assert "id" in ans, "All generated answers must contain the 'id' key"
            assert "answer" in ans, "All generated answers must contain the 'answer' key"
            assert isinstance(ans["answer"], str), "All generated answers must be strings"
            answers.append(ans)
    return answers


async def eval_submission(fp: Path):
    """Read in the answers and generations and eval them all, then write the results file."""
    questions = fanoutqa.load_dev()

    print("Evaluating open book answers...")
    openbook_answers = read_jsonl_answers(fp)
    openbook_scorer = Scorer(questions, openbook_answers, llm_cache_key=fp.parent.name)
    openbook_results = asdict(await openbook_scorer.score())

    result_fp = fp.parent / "score.json"
    with open(result_fp, "w") as f:
        json.dump(openbook_results, f, indent=2)
    print(f"Written to {result_fp.resolve()}.")
    return result_fp


async def main():
    paths = sys.argv[1:]
    if not paths:
        print("no paths specified! Usage: python score_fanoutqa.py [path/to/results.jsonl ...]")
    for fp in paths:
        await eval_submission(Path(fp))


if __name__ == "__main__":
    asyncio.run(main())
