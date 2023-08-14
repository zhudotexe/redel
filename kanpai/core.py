import urllib.parse
from typing import Annotated, Optional, TYPE_CHECKING

from kani import AIParam, ChatMessage, Kani, ai_function

from .webutils import get_links, web_summarize

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page


class Kanpai(Kani):
    def __init__(self, *args, browser: "Browser", **kwargs):
        super().__init__(*args, **kwargs)
        self.browser = browser
        self.context = None
        self.page = None

    # browser management
    async def get_context(self) -> "BrowserContext":
        """Return the browser context if it's initialized, else create and save a context."""
        if self.context:
            return self.context
        self.context = await self.browser.new_context()
        return self.context

    async def get_page(self, create=True) -> Optional["Page"]:
        """Get the current page.

        Returns None if the browser is not on a page unless `create` is True, in which case it creates a new page.
        """
        context = await self.get_context()
        if self.page is None and create:
            self.page = await context.new_page()
        return self.page

    # browsing
    @ai_function()
    async def search(
        self,
        query: str,
        new_tab: Annotated[bool, AIParam("Whether to search in a new tab or the current tab.")] = False,
    ):
        """Search a query on Google."""
        context = await self.get_context()
        if new_tab:
            page = await context.new_page()
        else:
            page = await self.get_page()
        query_enc = urllib.parse.quote_plus(query)
        await page.goto(f"https://www.google.com/search?q={query_enc}")
        search_loc = page.locator("#search")
        search_text = await search_loc.inner_text()
        links = await get_links(search_loc)
        return f"{search_text}\n\n===== Links =====\n{links.model_dump_json(indent=2)}"

    @ai_function()
    async def visit_page(self, href: str):
        """Visit a web page and view its contents."""
        page = await self.get_page()
        await page.goto(href)
        # header
        title = await page.title()
        header = f"{title}\n{'=' * len(title)}\n"
        # content
        content = await page.inner_text("body")
        # links
        links = await get_links(page)
        if links:
            links_str = f"\n\nLinks\n=====\n{links.model_dump_json(indent=2)}"
        else:
            links_str = ""
        # summarization
        if self.message_token_len(ChatMessage.function("visit_page", content)) > 1024:
            content = await web_summarize(content)
        if links_str and self.message_token_len(ChatMessage.function("visit_page", links_str)) > 512:
            links_str = await web_summarize(
                links_str,
                task=f"Please extract the most important links from above given the following context:\n{content}",
            )
        result = header + content + links_str
        return result
