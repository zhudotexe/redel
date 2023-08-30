import asyncio
import logging
from weakref import WeakValueDictionary

from kani import chat_in_terminal_async
from playwright.async_api import Browser, async_playwright

from . import events
from .base_kani import BaseKani
from .engines import engine
from .kanis import RootKani
from .prompts import ROOT_KANPAI

log = logging.getLogger(__name__)


class Kanpai:
    """Kanpai is the core app.
    It's responsible for keeping track of all the spawned kani, and reporting their relations.
    It also manages any app-global resources, like playwright.
    """

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.event_queue = asyncio.Queue()
        self.dispatch_task = asyncio.create_task(self._dispatch_task(), name="kanpai-dispatch")
        self.kanis = WeakValueDictionary()

    # entrypoints
    async def chat_in_terminal(self):
        await self.get_browser(headless=False)
        ai = RootKani(engine, app=self, system_prompt=ROOT_KANPAI)
        await chat_in_terminal_async(ai)

    # events
    async def _dispatch_task(self):
        while True:
            # noinspection PyBroadException
            try:
                event = await self.event_queue.get()
                # todo get listeners, call them
            except asyncio.CancelledError:
                return
            except Exception:
                log.exception("Exception when dispatching event:")

    def dispatch(self, event: events.BaseEvent):
        """Dispatch an event to all listeners.
        Technically this just adds it to a queue and then an async background task dispatches it."""
        self.event_queue.put_nowait(event)

    # kani lifecycle
    def on_kani_creation(self, ai: BaseKani):
        self.kanis[ai.id] = ai
        if ai.parent:
            ai.parent.children[ai.id] = ai
        self.dispatch(
            events.KaniSpawn(
                id=ai.id,
                parent=ai.parent.id if ai.parent else None,
                always_included_messages=ai.always_included_messages,
                chat_history=ai.chat_history,
            )
        )

    # resources + app lifecycle
    async def get_browser(self, **kwargs) -> Browser:
        """Get the current active browser, or launch it on the first call."""
        if self.playwright is None:
            self.playwright = await async_playwright().start()
        if self.browser is None:
            self.browser = await self.playwright.chromium.launch(**kwargs)
        return self.browser

    async def close(self):
        self.dispatch_task.cancel()
        if self.browser is not None:
            await self.browser.close()
        if self.playwright is not None:
            await self.playwright.stop()
