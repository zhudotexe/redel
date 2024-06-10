import asyncio
import json
import logging
from pathlib import Path

import fanoutqa
import tqdm
from fanoutqa.models import DevQuestion
from kani.engines.openai import OpenAIEngine

from redel import Kanpai, events
from redel.delegation.delegate_one import Delegate1Mixin
from redel.tools.fanoutqa.impl import FanOutQAConfig, FanOutQAMixin

LOG_BASE = Path(__file__).parent / "experiments/fanoutqa"

# ==== config ====
root_engine = OpenAIEngine(model="gpt-4", temperature=0)
delegate_engine = root_engine
long_engine = root_engine
delegation_scheme = Delegate1Mixin
root_has_tools = False
do_long_engine_upgrade = False
log_dir = LOG_BASE / "dev/1-gpt-4-all-no-root-tools"


async def query(q: DevQuestion, log_dir: Path):
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
                        do_long_engine_upgrade=do_long_engine_upgrade, retrieval_type="bm25"
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
        if isinstance(event, events.RootMessage) and event.msg.text:
            out.append(event.msg.text)

    await ai.close()
    return "\n\n".join(out), ai.logger.log_dir


async def run_dev():
    results_file = open(log_dir / "results.jsonl", "w")
    qs = fanoutqa.load_dev()
    for q in tqdm.tqdm(qs):
        result, result_log_dir = await query(q, log_dir=log_dir)
        results_file.write(json.dumps({"id": q.id, "answer": result, "question": q.question}))
        results_file.write("\n")
    results_file.close()


async def main():
    logging.basicConfig(level=logging.INFO)
    log_dir.mkdir(parents=True, exist_ok=True)
    await run_dev()


if __name__ == "__main__":
    asyncio.run(main())
