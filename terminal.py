import asyncio
import logging

from redel.app import ReDel


async def main():
    app = ReDel()
    await app.chat_in_terminal()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
