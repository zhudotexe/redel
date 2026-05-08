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
from fanoutqa.models import DevQuestion, TestQuestion
from kani import ChatRole
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from bench_engines import get_experiment_config
from redel import ReDel, events
from redel.delegation.delegate_and_wait_v2 import DelegateWait2
from redel.prompts import REDEL_RL_SYSTEM_PROMPT_V3
from redel.tools.fanoutqa.impl import FanOutQAMixin
from redel.utils import read_jsonl

log = logging.getLogger("bench_fanoutqa")


# ==== main ====
async def query(q: DevQuestion | TestQuestion):
    ai = ReDel(
        root_engine=config.root_engine,
        delegate_engine=config.delegate_engine,
        root_system_prompt=REDEL_RL_SYSTEM_PROMPT_V3,
        delegate_system_prompt=REDEL_RL_SYSTEM_PROMPT_V3,
        delegation_scheme=config.delegation_scheme,
        max_delegation_depth=3,
        tool_configs={
            FanOutQAMixin: {
                "always_include": True,
            },
        },
        root_has_tools=config.root_has_tools,
        title=f"fanoutqa: {q.question} ({q.id})",
        log_dir=config.save_dir / q.id,
        clear_existing_log=True,
    )

    out = ""
    async for event in ai.query(q.question):
        if isinstance(event, events.RootMessage) and event.msg.role == ChatRole.ASSISTANT:
            log.info(event.msg)
            if event.msg.text:
                out = event.msg.text

    await ai.close()
    return out, ai.logger.log_dir


async def run():
    # check for existing results
    results_fp = config.save_dir / "results.jsonl"
    existing_results = set()
    if results_fp.exists():
        for r in read_jsonl(results_fp):
            existing_results.add(r["id"])

    # run on dev set questions
    results_file = open(results_fp, "a")
    results_lock = asyncio.Lock()
    parallel_sem = asyncio.Semaphore(5)
    qs = fanoutqa.load_dev("fanoutqa-test-answers.json")
    tasks = []
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    )
    progress.start()
    ptask = progress.add_task("Generating...")

    async def task(q):
        async with parallel_sem:
            # run query
            log.info(q.question)
            try:
                result, result_log_dir = await asyncio.wait_for(query(q), timeout=config.engine_timeout)
                log.info(result)
                async with results_lock:
                    results_file.write(
                        json.dumps({
                            "id": q.id,
                            "answer": result,
                            "question": q.question,
                            "log_dir": str(result_log_dir.resolve()),
                        })
                    )
                    results_file.write("\n")
                    results_file.flush()
            except Exception as e:
                log.exception(e)
            finally:
                progress.update(ptask, advance=1)

    for q_ in qs:
        # skip if already set
        if q_.id in existing_results:
            continue
        tasks.append(asyncio.create_task(task(q_)))
    progress.update(ptask, total=len(tasks))
    await asyncio.gather(*tasks)

    results_file.close()
    progress.stop()


async def main():
    if hasattr(config.root_engine, "server"):
        await config.root_engine.server.wait_for_healthy()
    logging.basicConfig(level=logging.WARNING)
    log.setLevel(logging.INFO)
    config.save_dir.mkdir(parents=True, exist_ok=True)
    await run()
    await config.root_engine.close()
    if config.delegate_engine is not config.root_engine:
        await config.delegate_engine.close()


if __name__ == "__main__":
    config = get_experiment_config(delegation_scheme=DelegateWait2)
    asyncio.run(main())
