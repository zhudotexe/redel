import logging
from urllib.parse import urljoin

from kani import ChatMessage, Kani
from playwright.async_api import Locator, Page
from pydantic import BaseModel, RootModel

from .engines import long_engine

log = logging.getLogger(__name__)


class Link(BaseModel):
    content: str
    href: str


class Links(RootModel):
    root: list[Link]

    def __bool__(self):
        return bool(self.root)


async def get_links(elem: Page | Locator) -> Links:
    """Return a list of all links on a page or in an element."""
    page = elem if isinstance(elem, Page) else elem.page
    base_url = page.url
    links = []
    for loc in await elem.get_by_role("link").all():
        content = await loc.inner_text()
        href = await loc.get_attribute("href")
        if not href:
            continue
        # if the href is relative, resolve relative to the current page
        href = urljoin(base_url, href)
        links.append(Link(content=content or "", href=href))
    return Links(links)


async def web_summarize(content: str, task="Please summarize the main content of the webpage above."):
    """Summarize the contents of a webpage."""
    msg = ChatMessage.user(content)
    summarizer = Kani(long_engine, chat_history=[msg])
    token_len = summarizer.message_token_len(msg)
    log.info(f"Summarizing web content with length {len(content)} ({token_len} tokens)\n{content[:32]}...")
    # recursively summarize chunks if the content is *still* too long
    if token_len > long_engine.max_context_size - 256:
        half_len = len(content) // 2
        first_half = await web_summarize(content[:half_len])
        second_half = await web_summarize(content[half_len:])
        return f"{first_half}\n---\n{second_half}"
    return await summarizer.chat_round_str(task)
