import os

import html_to_markdown
import httpx
from kani import ai_function

from redel.tools import ToolBase
from .kiwix_client import KiwixClient

KIWIX_BASE = os.getenv("KIWIX_HOST_FOQA")  # set in foqa_*.sh
KIWIX_ZIMNAME = "wikipedia_en_all_nopic_2023-09"
md_options = html_to_markdown.ConversionOptions(autolinks=True, default_title=False)

kiwix_client = KiwixClient(base_url=KIWIX_BASE, zimname=KIWIX_ZIMNAME, md_options=md_options)

SEARCH_WIKIPEDIA_SCHEMA = {
    "properties": {"query": {"type": "string"}},
    "required": ["query"],
    "type": "object",
}

GET_WIKIPEDIA_ARTICLE_SCHEMA = {
    "properties": {
        "title": {"type": "string"},
        "start": {"default": 0, "type": "integer"},
        "max_len": {"default": 1000, "type": "integer"},
    },
    "required": ["title"],
    "type": "object",
}


# ai functions
class FanOutQAMixin(ToolBase):
    @ai_function(json_schema=SEARCH_WIKIPEDIA_SCHEMA)
    async def search_wikipedia(self, query: str):
        """
        Search Wikipedia for a given query.
        """
        try:
            return await kiwix_client.wiki_search(query)
        except httpx.TimeoutException as e:
            print(f"kiwix search timeout: {e}")
            return "The Wikipedia client timed out. Please try again."

    @ai_function(json_schema=GET_WIKIPEDIA_ARTICLE_SCHEMA)
    async def get_wikipedia_article(self, title: str, start: int = 0, max_len: int = 5000):
        """
        Get the contents of a given Wikipedia article by title.
        Returns up to `max_len` characters of content starting at the given `start` index.
        """
        try:
            content = await kiwix_client.wiki_content(title, start=start, max_len=max_len)
            return content
        except httpx.TimeoutException as e:
            print(f"kiwix fetch timeout: {e}")
            return "The Wikipedia client timed out. Please try again."
