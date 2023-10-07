"""This file has utilities for poking playwright in a REPL environment."""
from kanpai.webutils import web_markdownify


def start_playwright():
    from playwright.sync_api import sync_playwright

    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(f"https://www.google.com/search?q=tokyo+yamanote+line")
    search_html = page.content()
    content = web_markdownify(search_html)
    return content

if __name__ == '__main__':
    start_playwright()