import logging
import urllib.parse
from typing import Annotated, Optional, TYPE_CHECKING

from kani import AIParam, ChatMessage, ChatRole, Kani, ai_function
from rapidfuzz import fuzz

from .prompts import DELEGATE_KANPAI
from .webutils import get_links, web_markdownify, web_summarize

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page

log = logging.getLogger(__name__)


class Kanpai(Kani):
    def __init__(self, *args, browser: "Browser", **kwargs):
        super().__init__(*args, **kwargs)
        self.browser = browser
        self.helper = None

    # utils
    @property
    def last_user_message(self) -> ChatMessage | None:
        return next((m for m in self.chat_history if m.role == ChatRole.USER), None)

    # delegation
    @ai_function()
    async def delegate(
        self,
        instructions: Annotated[str, AIParam("Detailed instructions on what your helper should do to help you.")],
        new: Annotated[
            bool, AIParam("Continue the conversation with the same helper (false) or ask a new helper (true).")
        ] = False,
    ):
        """
        Ask a capable helper for help looking up a piece of information or performing an action.
        You can call this multiple times to take multiple actions; for example, you might break up a complex user query
        into multiple steps.
        """
        log.info(f"Delegated with instructions: {instructions}")
        # if the instructions are >95% the same as the current goal, bonk
        if self.last_user_message and fuzz.ratio(instructions, self.last_user_message.content) > 95:
            return (
                "You shouldn't delegate the entire task to a helper. Try breaking it up into smaller steps and call"
                " this again."
            )
        # set up the helper
        if new and self.helper is not None and self.helper.context:
            # close an existing helper's browser context
            await self.helper.context.close()
        if self.helper is None or new:
            self.helper = DelegateKanpai(self.engine, browser=self.browser, system_prompt=DELEGATE_KANPAI)

        result = []
        async for msg in self.helper.full_round(instructions):
            log.info(msg)
            if msg.content:
                result.append(msg.content)
        return "\n".join(result)


class DelegateKanpai(Kanpai):
    def __init__(self, *args, max_webpage_len: int = 1024, **kwargs):
        super().__init__(*args, **kwargs)
        self.context: Optional["BrowserContext"] = None
        self.page: Optional["Page"] = None
        self.max_webpage_len = max_webpage_len  # the max number of tokens before asking for a summary

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
        if self.page is None and create:
            context = await self.get_context()
            self.page = await context.new_page()
        return self.page

    # functions
    @ai_function()
    async def search(
        self,
        query: str,
        new_tab: Annotated[bool, AIParam("Whether to search in a new tab or the current tab.")] = False,
    ):
        """Search a query on Google."""
        if new_tab:
            context = await self.get_context()
            page = await context.new_page()
        else:
            page = await self.get_page()
        query_enc = urllib.parse.quote_plus(query)
        await page.goto(f"https://www.google.com/search?q={query_enc}")
        # content
        search_text = await page.inner_text("#main")
        if "Content Navigation Bar" in search_text:
            _, search_text = search_text.split("Content Navigation Bar", 1)
        # links
        search_loc = page.locator("#search")
        links = await get_links(search_loc)
        return f"{search_text.strip()}\n\n===== Links =====\n{links.model_dump_json(indent=2)}"

    @ai_function()
    async def visit_page(self, href: str):
        """Visit a web page and view its contents."""
        page = await self.get_page()
        await page.goto(href)
        # header
        title = await page.title()
        header = f"{title}\n{'=' * len(title)}\n\n"
        # content
        content_html = await page.inner_html("body")
        content = web_markdownify(content_html, page.url)
        # summarization
        if self.message_token_len(ChatMessage.function("visit_page", content)) > self.max_webpage_len:
            if last_user_msg := self.last_user_message:
                content = await web_summarize(
                    content,
                    task=(
                        "Please summarize the main content of the webpage above.\n"
                        f"Keep the current goal in mind: {last_user_msg.content}"
                    ),
                )
            else:
                content = await web_summarize(content)
        result = header + content
        return result
