import asyncio
import logging

from kani import chat_in_terminal_async
from playwright.async_api import async_playwright

from kanpai import Kanpai
from kanpai.engines import engine
from kanpai.prompts import ROOT_KANPAI


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ai = Kanpai(engine, browser=browser, system_prompt=ROOT_KANPAI)
        await chat_in_terminal_async(ai)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
