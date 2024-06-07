import asyncio
from pathlib import Path

import fanoutqa
from fanoutqa.models import DevQuestion

from redel import Kanpai, events
from redel.tools.fanoutqa import FanOutQAConfig, FanOutQAMixin

LOG_BASE = Path(__file__).parent / "experiments/fanoutqa"


async def query(q: DevQuestion):
    ai = Kanpai(
        root_system_prompt=None,
        delegate_system_prompt=None,
        tool_configs={
            FanOutQAMixin: {
                "always_include": True,
                "kwargs": {"foqa_config": FanOutQAConfig(do_long_engine_upgrade=True)},
            },
        },
        title=f"fanoutqa: {q.question} ({q.id})",
        log_dir=LOG_BASE / q.id,
    )

    out = []
    async for event in ai.query(q.question):
        if isinstance(event, events.RootMessage):
            out.append(event.msg.text)

    await ai.close()
    return "\n\n".join(out), ai.logger.log_dir


async def run_dev():
    qs = fanoutqa.load_dev()
    for q in qs:
        result = await query(q)


async def main():
    await run_dev()


if __name__ == "__main__":
    asyncio.run(main())
