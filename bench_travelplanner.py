"""
Run the travelplanner experiments.

Usage: python bench_travelplanner.py <full|root-fc|baseline|small-leaf|small-all|small-baseline>

- **full**: no root FC, gpt-4o everything
- **root-fc**: root FC, gpt-4o everything
- **baseline**: root FC, no delegation, gpt-4o
- **small-leaf**: no root FC, gpt-4o root, gpt-3.5-turbo leaves
    - **small-all**: no root FC, gpt-3.5-turbo everything
    - **small-baseline**: root FC, no delegation, gpt-3.5-turbo
- no short-ctx since this benchmark doesn't test long-ctx
"""

import asyncio
import hashlib
import json
import logging

import tqdm
from datasets import load_dataset
from kani import ChatRole

from bench_engines import get_experiment_config
from redel import ReDel, events
from redel.tools.travelplanner.planner import TravelPlannerRootMixin
from redel.tools.travelplanner.search import TravelPlannerMixin
from redel.utils import read_jsonl

log = logging.getLogger("bench_travelplanner")

# ==== config ====
root_system_prompt = (
    "Based on the user's query, make the best travel plan for the user and save it. Do not ask follow-up questions."
)

config = get_experiment_config()


# ==== main ====
async def query(q: dict, qid: str):
    ai = ReDel(
        root_engine=config.root_engine,
        delegate_engine=config.delegate_engine,
        root_system_prompt=root_system_prompt,
        delegate_system_prompt=None,
        delegation_scheme=config.delegation_scheme,
        tool_configs={
            TravelPlannerMixin: {"always_include": True},
            TravelPlannerRootMixin: {"always_include_root": True},
        },
        root_has_tools=config.root_has_tools,
        title=f"travelplanner: {q['query']} ({qid})",
        log_dir=config.save_dir / qid,
        clear_existing_log=True,
    )

    out = []
    async for event in ai.query(q["query"]):
        if isinstance(event, events.RootMessage) and event.msg.role == ChatRole.ASSISTANT:
            log.info(event.msg)
            if event.msg.text:
                out.append(event.msg.text)

    plan = ai.root_kani.get_tool(TravelPlannerRootMixin).current_plan

    await ai.close()
    return "\n\n".join(out), plan, ai.logger.log_dir


async def run():
    # check for existing results
    results_fp = config.save_dir / "results.jsonl"
    existing_results = set()
    if results_fp.exists():
        for r in read_jsonl(results_fp):
            existing_results.add(r["id"])

    # run on dev set questions
    results_file = open(results_fp, "a")
    data = load_dataset("osunlp/TravelPlanner", "validation")["validation"]
    for idx, q in tqdm.tqdm(enumerate(data)):
        # skip if already set
        qid = hashlib.sha256(q["query"].encode()).hexdigest()[:16]
        if qid in existing_results:
            continue

        # run query
        log.info(q["query"])
        try:
            result, plan, result_log_dir = await asyncio.wait_for(query(q, qid), timeout=600)
        except Exception as e:
            log.exception(e)
        else:
            log.info(result)
            results_file.write(
                json.dumps({
                    "id": qid,
                    "idx": idx,
                    "plan": plan,
                    "answer": result,
                    "question": q["query"],
                    "log_dir": str(result_log_dir.resolve()),
                })
            )
            results_file.write("\n")
            results_file.flush()
    results_file.close()


async def main():
    logging.basicConfig(level=logging.WARNING)
    log.setLevel(logging.INFO)
    config.save_dir.mkdir(parents=True, exist_ok=True)
    await run()


if __name__ == "__main__":
    asyncio.run(main())
