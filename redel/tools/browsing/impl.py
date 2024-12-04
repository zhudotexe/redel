import asyncio
import logging
import tempfile
from typing import Optional, TYPE_CHECKING

from duckduckgo_search import AsyncDDGS
from kani import ChatMessage, ChatRole, ai_function
from kani.engines import BaseEngine

try:
    import httpx
    import pymupdf
    import pymupdf4llm
except ImportError:
    raise ImportError(
        "You are missing required dependencies to use the bundled tools. Please install ReDel using `pip install"
        ' "redel[bundled]"`.'
    ) from None

from redel.tools import ToolBase
from .webutils import web_markdownify, web_summarize

if TYPE_CHECKING:
    from playwright.async_api import Page

log = logging.getLogger(__name__)


class Browsing(ToolBase):
    """
    A tool that provides tools to search Google and visit webpages.

    Renders webpages in Markdown and has basic support for reading PDFs.
    """

    def __init__(
        self,
        *args,
        long_engine: BaseEngine = None,
        max_webpage_len: int = None,
        page_concurrency_sem: asyncio.Semaphore | None = None,
        **kwargs,
    ):
        """
        :param long_engine: If a webpage is longer than *max_webpage_len*, send it to this engine to summarize it. If
            not supplied, uses the kani's engine.
        :param max_webpage_len: The maximum length of a webpage to send to the kani at once
            (default max context len / 3).
        :param page_concurrency_sem: A semaphore that this tool will acquire when opening a browser page.
        """
        super().__init__(*args, **kwargs)
        self.http = httpx.AsyncClient(follow_redirects=True)
        self.page: Optional["Page"] = None
        self.long_engine = long_engine
        self.page_concurrency_sem = page_concurrency_sem

        # the max number of tokens before asking for a summary - default 1/3rd ctx len
        if max_webpage_len is None:
            max_webpage_len = self.kani.engine.max_context_size // 3
        self.max_webpage_len = max_webpage_len

        # content handlers
        self.content_handlers = {
            "application/pdf": self.pdf_content,
            "application/json": self.json_content,
            "text/": self.html_content,
        }

    # ==== functions ====
    @ai_function()
    async def search(self, query: str):
        """Search for a query on a web search engine."""
        # page = await self.get_page()
        # query_enc = urllib.parse.quote_plus(query)
        # await page.goto(f"https://www.google.com/search?q={query_enc}")
        # # content
        # try:
        #     # if the main content is borked, fallback
        #     search_html = await page.inner_html("#main", timeout=5000)
        #     search_text = web_markdownify(search_html, include_links=False)
        #     # links
        #     search_loc = page.locator("#search")
        #     links = await get_google_links(search_loc)
        #     return (
        #         f"{search_text.strip()}\n\nYou should visit some of these links for more information or delegate"
        #         f" helpers to visit multiple:\n\n===== Links =====\n{links.to_md_str()}"
        #     )
        # except PlaywrightTimeoutError:
        #     content_html = await page.content()
        #     content = web_markdownify(content_html)
        #     return content
        results = await AsyncDDGS().atext(query)
        return results

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
        resp = await self.http.get(href)
        resp.raise_for_status()
        await resp.aread()
        content = web_markdownify(resp.text)
        # summarization
        content = await self.maybe_summarize(content)
        # result
        return content

    # ==== helpers ====
    async def maybe_summarize(self, content, max_len=None):
        max_len = max_len or self.max_webpage_len
        if self.kani.message_token_len(ChatMessage.function("visit_page", content)) > max_len:
            msg_ctx = "\n\n".join(
                m.text for m in self.kani.chat_history if m.role != ChatRole.FUNCTION and m.text is not None
            )
            content = await web_summarize(
                content,
                parent=self.kani,
                long_engine=self.long_engine or self.kani.engine,
                task=(
                    "Keep the current context in mind:\n"
                    f"<context>\n{msg_ctx}\n</context>\n\n"
                    "Keeping the context and task in mind, please summarize the main content above."
                ),
            )
        return content
