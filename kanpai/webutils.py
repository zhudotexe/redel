import logging
from urllib.parse import urljoin, urldefrag, urlparse, parse_qs, urlencode

import trafilatura
from kani import ChatMessage
from playwright.async_api import Locator, Page
from pydantic import BaseModel, RootModel

from .base_kani import BaseKani, RunState

log = logging.getLogger(__name__)


# links
class Link(BaseModel):
    content: str
    href: str


class Links(RootModel):
    root: list[Link]

    def __bool__(self):
        return bool(self.root)

    def to_md_str(self):
        return "\n".join(f"[{link.content}]({link.href})" for link in self.root)


async def get_google_links(elem: Page | Locator) -> Links:
    """Return a list of all links on a page or in an element."""
    page = elem if isinstance(elem, Page) else elem.page
    base_url = page.url
    seen_links = set()
    links = []
    for loc in await elem.get_by_role("link").all():
        content = await loc.inner_text()
        href = await loc.get_attribute("href")
        if not href:
            continue
        parts = urlparse(href)
        # if the href is relative, resolve relative to the current page
        href = urljoin(base_url, href)
        # clean up google urls (unimportant query params etc)
        if parts.netloc.endswith("google.com") and parts.path == "/search":
            query = parse_qs(parts.query)
            parts.query = urlencode({"q": query["q"]})
            href = parts.geturl()
        href = urldefrag(href).url  # and clean up hashes
        # only report a link once
        if href in seen_links:
            continue
        seen_links.add(href)
        links.append(Link(content=content or "", href=href))
    return Links(links)


# summarization
async def web_summarize(content: str, parent: BaseKani, task="Please summarize the main content of the webpage above."):
    """Summarize the contents of a webpage."""
    app = parent.app
    msg = ChatMessage.user(content)
    summarizer = BaseKani(app.long_engine, chat_history=[msg], app=app, parent=parent, id=f"{parent.id}-summarizer")
    token_len = summarizer.message_token_len(msg) + summarizer.message_token_len(ChatMessage.user(task))
    log.info(f"Summarizing web content with length {len(content)} ({token_len} tokens)\n{content[:32]}...")

    # if we can use base gpt-4 to summarize, do that; otherwise use 32k with rate limit controls
    if token_len + summarizer.always_len <= app.engine.max_context_size:
        summarizer.engine = app.engine

    with parent.set_state(RunState.WAITING):
        # recursively summarize chunks if the content is *still* too long
        if token_len + summarizer.always_len > summarizer.engine.max_context_size:
            half_len = len(content) // 2
            first_half = await web_summarize(f"{content[:half_len + 10]}\n[...]", task=task, parent=summarizer)
            second_half = await web_summarize(f"[...]\n{content[half_len - 10:]}", task=task, parent=summarizer)
            result = f"{first_half}\n---\n{second_half}"
        else:
            result = await summarizer.chat_round_str(task)
        return result


def web_markdownify(html: str, **kwargs):
    kwargs = {
        "include_links": True,
        "include_formatting": True,
        "include_tables": True,
        "favor_recall": True,
        "deduplicate": True,
        **kwargs,
    }
    return trafilatura.extract(html, **kwargs)
