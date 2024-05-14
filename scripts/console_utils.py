"""This file has utilities for poking playwright in a REPL environment."""

import asyncio

from playwright.async_api import async_playwright

from kanpai.mixins.browsing.webutils import CHROME_UA, get_google_links, web_markdownify


#  from playwright.sync_api import sync_playwright
#
#  playwright = sync_playwright().start()
#  browser = playwright.chromium.launch(headless=False)
#  page = browser.new_page()


async def start_playwright():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True, channel="chrome", args=[f"--user-agent={CHROME_UA}"])
    context = await browser.new_context()
    page = await context.new_page()

    # await page.goto(f"https://www.dndbeyond.com/races/16-dragonborn")
    # print(await page.content())

    # content
    search_html = await page.inner_html("#main")
    search_text = web_markdownify(search_html, include_links=False)
    # links
    search_loc = page.locator("#search")
    links = await get_google_links(search_loc)
    return f"{search_text.strip()}\n\n===== Links =====\n{links.to_md_str()}"


if __name__ == "__main__":
    asyncio.run(start_playwright())
