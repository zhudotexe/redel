import logging
from urllib.parse import urljoin

from kani import ChatMessage
from markdownify import MarkdownConverter, chomp
from playwright.async_api import Locator, Page
from pydantic import BaseModel, RootModel

from .base_kani import BaseKani

log = logging.getLogger(__name__)


# links
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


# summarization
async def web_summarize(content: str, parent: BaseKani, task="Please summarize the main content of the webpage above."):
    """Summarize the contents of a webpage."""
    app = parent.app
    msg = ChatMessage.user(content)
    summarizer = BaseKani(app.long_engine, chat_history=[msg], app=app, parent=parent, id=f"{parent.id}-summarizer")
    token_len = summarizer.message_token_len(msg) + summarizer.message_token_len(ChatMessage.user(task))
    log.info(f"Summarizing web content with length {len(content)} ({token_len} tokens)\n{content[:32]}...")
    # recursively summarize chunks if the content is *still* too long
    if token_len + summarizer.always_len > app.long_engine.max_context_size:
        half_len = len(content) // 2
        first_half = await web_summarize(f"{content[:half_len + 10]}\n[...]", task=task, parent=summarizer)
        second_half = await web_summarize(f"[...]\n{content[half_len - 10:]}", task=task, parent=summarizer)
        result = f"{first_half}\n---\n{second_half}"
    else:
        result = await summarizer.chat_round_str(task)
    return result


# markdownification
def yeet(*_):
    return ""


def is_valid_url(x):
    if not x:
        return False
    return not x.startswith("data:")


class MDConverter(MarkdownConverter):
    def __init__(self, base_url: str, **kwargs):
        super().__init__(**kwargs)
        self.base_url = base_url

    def convert_img(self, el, text, convert_as_inline):
        alt = el.attrs.get("alt", None) or ""
        src = el.attrs.get("src", None) or ""

        if not is_valid_url(src):
            if not alt:
                return ""
            src = "image"

        return f"![{alt}]({src})"

    def convert_a(self, el, text, convert_as_inline):
        prefix, suffix, inner = chomp(text)
        if not inner:
            return ""
        href = el.get("href")
        if not is_valid_url(href):
            return text
        # if the href is relative, resolve relative to the current page
        href = urljoin(self.base_url, href)
        # from super
        if self.options["autolinks"] and inner.replace(r"\_", "_") == href:
            # Shortcut syntax
            return f"<{href}>"
        return f"{prefix}[{inner}]({href}){suffix}" if href else text

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def convert_div(self, el, text, convert_as_inline):
        if not text.endswith("\n"):
            return f"{text}\n"
        return text

    # sometimes these appear inline and are just annoying
    convert_script = yeet
    convert_style = yeet


def web_markdownify(html: str, base_url: str):
    return MDConverter(base_url=base_url, heading_style="atx").convert(html)
