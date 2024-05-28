import asyncio

import fanoutqa

from redel import Kanpai, events


async def query(q: str):
    ai = Kanpai()

    out = []
    async for event in ai.query(q):
        if isinstance(event, events.RootMessage):
            out.append(event.msg.text)

    await ai.close()
    return "\n\n".join(out), ai.logger.log_dir


async def run_dev():
    qs = fanoutqa.load_dev()
    for q in qs:
        result = await query(q.question)


async def main():
    await run_dev()


if __name__ == "__main__":
    asyncio.run(main())
