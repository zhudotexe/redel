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
import sys
from pathlib import Path

import tqdm
from datasets import load_dataset
from kani import ChatRole
from kani.engines.openai import OpenAIEngine

from redel import Kanpai, events
from redel.delegation.delegate_one import Delegate1Mixin
from redel.tools.travelplanner.planner import TravelPlannerRootMixin
from redel.tools.travelplanner.search import TravelPlannerMixin
from redel.utils import read_jsonl

LOG_BASE = Path(__file__).parent / "experiments/travelplanner"
experiment_config = sys.argv[-1]
log = logging.getLogger("bench_travelplanner")

# ==== config ====
delegation_scheme = Delegate1Mixin
log_dir = LOG_BASE / "validation" / experiment_config
root_system_prompt = (
    "Based on the user's query, make the best travel plan for the user and save it. Do not ask follow-up questions."
)
# gross but whatever
# - **full**: no root FC, gpt-4o everything
if experiment_config == "full":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0)
    delegate_engine = root_engine
    root_has_tools = False
# - **root-fc**: root FC, gpt-4o everything
elif experiment_config == "root-fc":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0)
    delegate_engine = root_engine
    root_has_tools = True
# - **baseline**: root FC, no delegation, gpt-4o
elif experiment_config == "baseline":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0)
    delegate_engine = root_engine
    root_has_tools = True
    delegation_scheme = None
# - **small-leaf**: no root FC, gpt-4o root, gpt-3.5-turbo leaves
elif experiment_config == "small-leaf":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0)
    delegate_engine = OpenAIEngine(model="gpt-3.5-turbo", temperature=0)
    root_has_tools = False
#     - **small-all**: no root FC, gpt-3.5-turbo everything
elif experiment_config == "small-all":
    root_engine = OpenAIEngine(model="gpt-3.5-turbo", temperature=0)
    delegate_engine = root_engine
    root_has_tools = False
#     - **small-baseline**: root FC, no delegation, gpt-3.5-turbo
elif experiment_config == "small-baseline":
    root_engine = OpenAIEngine(model="gpt-3.5-turbo", temperature=0)
    delegate_engine = root_engine
    root_has_tools = True
    delegation_scheme = None
else:
    raise ValueError("invalid experiment config")

print("========== CONFIG ==========")
print("root engine:", root_engine.model)
print("root ctx:", root_engine.max_context_size)
print("root tools:", root_has_tools)
print("delegation scheme:", delegation_scheme)
if delegation_scheme:
    print("delegate engine:", delegate_engine.model)
    print("delegate ctx:", delegate_engine.max_context_size)
print("saving to:", log_dir.resolve())
print("============================")


# ==== main ====
async def query(q: dict, qid: str):
    ai = Kanpai(
        root_engine=root_engine,
        delegate_engine=delegate_engine,
        root_system_prompt=root_system_prompt,
        delegate_system_prompt=None,
        delegation_scheme=delegation_scheme,
        tool_configs={
            TravelPlannerMixin: {"always_include": True},
            TravelPlannerRootMixin: {"always_include_root": True},
        },
        root_has_tools=root_has_tools,
        title=f"travelplanner: {q['query']} ({qid})",
        log_dir=log_dir / qid,
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
    results_fp = log_dir / "results.jsonl"
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
    log_dir.mkdir(parents=True, exist_ok=True)
    await run()


if __name__ == "__main__":
    asyncio.run(main())
