"""
Run the fanoutqa experiments.

Usage: python bench_fanoutqa.py <full|root-fc|baseline|small-leaf|small-all|small-baseline|short-context|short-baseline>

- **full**: no root FC, gpt-4o everything
- **root-fc**: root FC, gpt-4o everything
- **baseline**: root FC, no delegation, gpt-4o
- **small-leaf**: no root FC, gpt-4o root, gpt-3.5-turbo leaves
    - **small-all**: no root FC, gpt-3.5-turbo everything
    - **small-baseline**: root FC, no delegation, gpt-3.5-turbo
- **short-context**: no root FC, gpt-4o everything, limit to 8192 ctx
    - **short-baseline**: root FC, no delegation, gpt-4o, 8192 ctx
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

import fanoutqa
import tqdm
from fanoutqa.models import DevQuestion, TestQuestion
from kani import ChatRole
from kani.engines.openai import OpenAIEngine

from redel import Kanpai, events
from redel.delegation.delegate_one import Delegate1Mixin
from redel.tools.fanoutqa.impl import FanOutQAConfig, FanOutQAMixin
from redel.utils import read_jsonl

LOG_BASE = Path(__file__).parent / "experiments/fanoutqa"
experiment_config = sys.argv[-1]
log = logging.getLogger("bench_fanoutqa")

# ==== config ====
delegation_scheme = Delegate1Mixin
do_long_engine_upgrade = False
log_dir = LOG_BASE / "test" / experiment_config
# gross but whatever
# - **full**: no root FC, gpt-4o everything
if experiment_config == "full":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0)
    delegate_engine = root_engine
    long_engine = root_engine
    root_has_tools = False
# - **root-fc**: root FC, gpt-4o everything
elif experiment_config == "root-fc":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0)
    delegate_engine = root_engine
    long_engine = root_engine
    root_has_tools = True
# - **baseline**: root FC, no delegation, gpt-4o
elif experiment_config == "baseline":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0)
    delegate_engine = root_engine
    long_engine = root_engine
    root_has_tools = True
    delegation_scheme = None
# - **small-leaf**: no root FC, gpt-4o root, gpt-3.5-turbo leaves
elif experiment_config == "small-leaf":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0)
    delegate_engine = OpenAIEngine(model="gpt-3.5-turbo", temperature=0)
    long_engine = root_engine
    root_has_tools = False
#     - **small-all**: no root FC, gpt-3.5-turbo everything
elif experiment_config == "small-all":
    root_engine = OpenAIEngine(model="gpt-3.5-turbo", temperature=0)
    delegate_engine = root_engine
    long_engine = root_engine
    root_has_tools = False
#     - **small-baseline**: root FC, no delegation, gpt-3.5-turbo
elif experiment_config == "small-baseline":
    root_engine = OpenAIEngine(model="gpt-3.5-turbo", temperature=0)
    delegate_engine = root_engine
    long_engine = root_engine
    root_has_tools = True
    delegation_scheme = None
# - **short-context**: no root FC, gpt-4o everything, limit to 8192 ctx
elif experiment_config == "short-context":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0, max_context_size=8192)
    delegate_engine = root_engine
    long_engine = root_engine
    root_has_tools = False
#     - **short-baseline**: root FC, no delegation, gpt-4o, 8192 ctx
elif experiment_config == "short-baseline":
    root_engine = OpenAIEngine(model="gpt-4o", temperature=0, max_context_size=8192)
    delegate_engine = root_engine
    long_engine = root_engine
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
async def query(q: DevQuestion | TestQuestion):
    ai = Kanpai(
        root_engine=root_engine,
        delegate_engine=delegate_engine,
        long_engine=long_engine,
        root_system_prompt=None,
        delegate_system_prompt=None,
        delegation_scheme=delegation_scheme,
        tool_configs={
            FanOutQAMixin: {
                "always_include": True,
                "kwargs": {
                    "foqa_config": FanOutQAConfig(
                        do_long_engine_upgrade=do_long_engine_upgrade, retrieval_type="openai"
                    )
                },
            },
        },
        root_has_tools=root_has_tools,
        title=f"fanoutqa: {q.question} ({q.id})",
        log_dir=log_dir / q.id,
        clear_existing_log=True,
    )

    out = []
    async for event in ai.query(q.question):
        if isinstance(event, events.RootMessage) and event.msg.role == ChatRole.ASSISTANT:
            log.info(event.msg)
            if event.msg.text:
                out.append(event.msg.text)

    await ai.close()
    return "\n\n".join(out), ai.logger.log_dir


async def run():
    # check for existing results
    results_fp = log_dir / "results.jsonl"
    existing_results = set()
    if results_fp.exists():
        for r in read_jsonl(results_fp):
            existing_results.add(r["id"])

    # run on dev set questions
    results_file = open(results_fp, "a")
    qs = fanoutqa.load_dev()
    for q in tqdm.tqdm(qs):
        # skip if already set
        if q.id in existing_results:
            continue

        # run query
        log.info(q.question)
        try:
            result, result_log_dir = await asyncio.wait_for(query(q), timeout=600)
            log.info(result)
            results_file.write(
                json.dumps(
                    {"id": q.id, "answer": result, "question": q.question, "log_dir": str(result_log_dir.resolve())}
                )
            )
            results_file.write("\n")
        except Exception as e:
            log.exception(e)
    results_file.close()


async def main():
    logging.basicConfig(level=logging.WARNING)
    log.setLevel(logging.INFO)
    log_dir.mkdir(parents=True, exist_ok=True)
    await run()


if __name__ == "__main__":
    asyncio.run(main())
