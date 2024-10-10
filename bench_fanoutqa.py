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

import fanoutqa
import tqdm
from fanoutqa.models import DevQuestion, TestQuestion
from kani import ChatRole

from bench_engines import get_experiment_config
from redel import ReDel, events
from redel.tools.fanoutqa.impl import FanOutQAMixin
from redel.utils import read_jsonl

log = logging.getLogger("bench_fanoutqa")


# ==== main ====
async def query(q: DevQuestion | TestQuestion, config):
    ai = ReDel(
        root_engine=config.root_engine,
        delegate_engine=config.delegate_engine,
        root_system_prompt=None,
        delegate_system_prompt=None,
        delegation_scheme=config.delegation_scheme,
        tool_configs={
            FanOutQAMixin: {
                "always_include": True,
                "kwargs": {"retrieval_type": "openai"},
            },
        },
        root_has_tools=config.root_has_tools,
        title=f"fanoutqa: {q.question} ({q.id})",
        log_dir=config.save_dir / q.id,
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
    results_fp = config.save_dir / "results.jsonl"
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
            result, result_log_dir = await asyncio.wait_for(query(q), timeout=config.engine_timeout)
            log.info(result)
            results_file.write(
                json.dumps(
                    {"id": q.id, "answer": result, "question": q.question, "log_dir": str(result_log_dir.resolve())}
                )
            )
            results_file.write("\n")
            results_file.flush()
        except Exception as e:
            log.exception(e)
    results_file.close()


async def main():
    logging.basicConfig(level=logging.WARNING)
    log.setLevel(logging.INFO)
    config.save_dir.mkdir(parents=True, exist_ok=True)
    await run()


if __name__ == "__main__":
    config = get_experiment_config()
    asyncio.run(main())
