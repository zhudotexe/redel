import hashlib
import json
import os
import re
from urllib.parse import urlencode
from xml.etree import ElementTree

import html_to_markdown
import httpx

from redel.config import REDEL_CACHE_DIR

WIKI_CACHE_DIR = REDEL_CACHE_DIR / "kiwix"
WIKI_CACHE_DIR.mkdir(exist_ok=True, parents=True)


class KiwixClient:
    def __init__(self, base_url=None, zimname="wikipedia_en_all", md_options=None):
        if base_url is None:
            base_url = os.getenv("KIWIX_HOST")
            if not base_url:
                raise ValueError("either base_url or the KIWIX_HOST env var must be set")

        self.base_url = base_url
        self.zimname = zimname
        self.http = httpx.AsyncClient(base_url=self.base_url, follow_redirects=True, timeout=300)
        self.md_options = md_options or html_to_markdown.ConversionOptions(autolinks=True, default_title=False)
        self.cache_dir = WIKI_CACHE_DIR / zimname
        self.cache_dir.mkdir(exist_ok=True, parents=True)

    async def wiki_search(self, query: str, results: int = 10, start: int = 0) -> list[dict]:
        """Return a list of {title, href} dicts for the search query."""
        # check for cache
        q_hash = hashlib.sha256(query.encode()).hexdigest()
        cache_fp = self.cache_dir / "search" / q_hash[:3] / f"{q_hash}-{start}-{start + results}.json"
        cache_fp.parent.mkdir(parents=True, exist_ok=True)
        if cache_fp.exists():
            with open(cache_fp) as f:
                return json.load(f)

        params = urlencode(
            {"books.name": self.zimname, "pattern": query, "start": start, "pageLength": results, "format": "xml"}
        )
        resp = await self.http.get(f"/search?{params}")
        resp.raise_for_status()
        await resp.aread()
        text = resp.text

        # Kiwix returns an OpenSearch Atom feed
        root = ElementTree.fromstring(text)

        entries = []
        for entry in root.findall("channel/item"):
            title_el = entry.find("title")
            link_el = entry.find("link")
            desc_el = entry.find("description")
            wordcount_el = entry.find("wordCount")
            if title_el is None:
                continue
            title = title_el.text or ""
            href = link_el.text or ""
            href = href.removeprefix(f"/content/{self.zimname}/A/")
            desc = "".join(desc_el.itertext()) if desc_el is not None else None
            wordcount = wordcount_el.text
            entries.append({"title": title, "href": href, "description": desc, "wordcount": wordcount})

        cache_fp.write_text(json.dumps(entries), encoding="utf-8")
        return entries

    async def wiki_content(self, title: str, start: int = 0, max_len: int = None) -> str:
        """
        Get the page content in markdown, including tables and infoboxes, appropriate for displaying to an LLM.
        """
        # check for cache
        title_slug = re.sub(r"\W", "-", title)
        cache_fp = self.cache_dir / "content" / title_slug[:3] / f"{title_slug}.md"
        cache_fp.parent.mkdir(parents=True, exist_ok=True)
        if cache_fp.exists():
            text = cache_fp.read_text(encoding="utf-8")
        else:
            # Use the title as the cache key (strip leading slash, replace slashes with dashes)
            title_underscore = title.replace(" ", "_")
            resp = await self.http.get(f"/content/{self.zimname}/A/{title_underscore}")
            if resp.status_code == 404:
                return "This page does not exist."
            resp.raise_for_status()
            await resp.aread()

            md = html_to_markdown.convert(resp.text, self.md_options)
            text = md["content"] or "No content."
            cache_fp.write_text(text, encoding="utf-8")

        # handle trimming
        prefix = ""
        suffix = ""
        content_len = len(text)
        if start > 0:
            text = text[start:]
            prefix = f"[{min(content_len, start)} more characters...]\n"
        if max_len is not None and content_len > start + max_len:
            text = text[:max_len]
            suffix = f"\n[{content_len - (start + max_len)} more characters...]"
        return prefix + text + suffix
