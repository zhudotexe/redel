import asyncio
import logging

from redel.app import Kanpai


async def main():
    app = Kanpai()
    await app.chat_in_terminal()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
