import contextlib
import logging
import tempfile
import urllib.parse
from typing import Optional, TYPE_CHECKING

import httpx
import pymupdf
import pymupdf4llm
from kani import ChatMessage, ChatRole, ai_function
from playwright.async_api import BrowserContext, TimeoutError as PlaywrightTimeoutError, async_playwright

from redel.base_kani import BaseKani
from .webutils import CHROME_UA, get_google_links, web_markdownify, web_summarize

if TYPE_CHECKING:
    from playwright.async_api import Page

log = logging.getLogger(__name__)


class BrowsingMixin(BaseKani):
    # app-global browser instance
    playwright = None
    browser = None
    browser_context = None

    def __init__(self, *args, max_webpage_len: int = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.http = httpx.AsyncClient(follow_redirects=True)
        self.page: Optional["Page"] = None

        # the max number of tokens before asking for a summary - default 1/3rd ctx len
        if max_webpage_len is None:
            max_webpage_len = self.engine.max_context_size // 3
        self.max_webpage_len = max_webpage_len

        # content handlers
        self.content_handlers = {
            "application/pdf": self.pdf_content,
            "application/json": self.json_content,
            "text/": self.html_content,
        }

    # === resources + app lifecycle ===
    # noinspection PyMethodMayBeStatic
    async def get_browser(self, **kwargs) -> BrowserContext:
        """Get the current active browser context, or launch it on the first call."""
        if BrowsingMixin.playwright is None:
            BrowsingMixin.playwright = await async_playwright().start()
        if BrowsingMixin.browser is None:
            BrowsingMixin.browser = await BrowsingMixin.playwright.chromium.launch(
                channel="chrome", args=[f"--user-agent={CHROME_UA}"], **kwargs
            )
            # Kanpai.browser = await Kanpai.playwright.firefox.launch(**kwargs)
        if BrowsingMixin.browser_context is None:
            BrowsingMixin.browser_context = await BrowsingMixin.browser.new_context()
        return BrowsingMixin.browser_context

    async def get_page(self, create=True) -> Optional["Page"]:
        """Get the current page.

        Returns None if the browser is not on a page unless `create` is True, in which case it creates a new page.
        """
        if self.page is None and create:
            context = await self.get_browser()
            self.page = await context.new_page()
        return self.page

    async def cleanup(self):
        await super().cleanup()
        if self.page is not None:
            await self.page.close()
            self.page = None

    async def close(self):
        await super().close()
        if BrowsingMixin.browser is not None:
            await BrowsingMixin.browser.close()
            BrowsingMixin.browser = None
        if BrowsingMixin.playwright is not None:
            await BrowsingMixin.playwright.stop()
            BrowsingMixin.playwright = None

    # ==== functions ====
    @ai_function()
    async def search(self, query: str):
        """Search a query on Google."""
        page = await self.get_page()
        query_enc = urllib.parse.quote_plus(query)
        await page.goto(f"https://www.google.com/search?q={query_enc}")
        # content
        try:
            # if the main content is borked, fallback
            search_html = await page.inner_html("#main", timeout=5000)
            search_text = web_markdownify(search_html, include_links=False)
            # links
            search_loc = page.locator("#search")
            links = await get_google_links(search_loc)
            return (
                f"{search_text.strip()}\n\nYou should visit some of these links for more information or delegate"
                f" helpers to visit multiple:\n\n===== Links =====\n{links.to_md_str()}"
            )
        except PlaywrightTimeoutError:
            content_html = await page.content()
            content = web_markdownify(content_html)
            return content

    @ai_function()
    async def visit_page(self, href: str):
        """Visit a web page and view its contents."""
        # first, let's do a HEAD request and get the content-type so we know how to actually process the info
        resp = await self.http.head(href)
        content_type = resp.headers.get("Content-Type", "").lower()

        # then delegate to the content type handler
        handler = next((f for t, f in self.content_handlers.items() if content_type.startswith(t)), None)
        if handler is None:
            log.warning(f"Could not find handler for content type: {content_type}")
            handler = self.html_content

        return await handler(href)

    # ==== content renderers ====
    async def pdf_content(self, href: str) -> str:
        """Handler for application/pdf content types."""
        with tempfile.NamedTemporaryFile() as f:
            # download into a tempfile
            async with self.http.stream("GET", href) as response:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)

            # then read it
            doc = pymupdf.open(f.name, filetype="pdf")
            content = pymupdf4llm.to_markdown(doc)

        # summarization
        content = await self.maybe_summarize(content)
        return content

    async def json_content(self, href: str) -> str:
        """Handler for application/json content types."""
        resp = await self.http.get(href)
        resp.raise_for_status()
        await resp.aread()
        return resp.text

    async def html_content(self, href: str) -> str:
        """Default handler for all other content types."""
        page = await self.get_page()
        await page.goto(href)
        with contextlib.suppress(PlaywrightTimeoutError):
            await page.wait_for_load_state("networkidle", timeout=10_000)
        # header
        title = await page.title()
        header = f"{title}\n{'=' * len(title)}\n{page.url}\n\n"

        content_html = await page.content()
        content = web_markdownify(content_html)
        # summarization
        content = await self.maybe_summarize(content)
        # result
        result = header + content
        return result

    # ==== helpers ====
    async def maybe_summarize(self, content, max_len=None):
        max_len = max_len or self.max_webpage_len
        if self.message_token_len(ChatMessage.function("visit_page", content)) > max_len:
            msg_ctx = "\n\n".join(
                m.text for m in self.chat_history if m.role != ChatRole.FUNCTION and m.text is not None
            )
            content = await web_summarize(
                content,
                parent=self,
                task=(
                    "Keep the current context in mind:\n"
                    f"<context>\n{msg_ctx}\n</context>\n\n"
                    "Keeping the context and task in mind, please summarize the main content above."
                ),
            )
        return content
