import asyncio
import logging
import time
import uuid
from typing import Any, Awaitable, Callable
from weakref import WeakValueDictionary

from kani import ChatRole, chat_in_terminal_async
from kani.engines.openai import OpenAIEngine
from playwright.async_api import BrowserContext, async_playwright

from . import events
from .base_kani import BaseKani
from .engines import RatelimitedOpenAIEngine
from .kanis import RootKani
from .logger import Logger
from .prompts import ROOT_KANPAI

log = logging.getLogger(__name__)


class Kanpai:
    """Kanpai is the core app.
    It's responsible for keeping track of all the spawned kani, and reporting their relations.
    It also manages any app-global resources, like playwright.
    """

    def __init__(self):
        # engines
        self.engine = OpenAIEngine(model="gpt-4", temperature=0.8, top_p=0.95)
        self.long_engine = RatelimitedOpenAIEngine(model="gpt-4-32k", temperature=0.1, max_rate=3)
        # browser
        self.playwright = None
        self.browser = None
        self.browser_context = None
        # events
        self.listeners = []
        self.event_queue = asyncio.Queue()
        self.dispatch_task = None
        # logging
        self.session_id = f"{int(time.time())}-{uuid.uuid4()}"
        self.logger = Logger(self, self.session_id)
        self.add_listener(self.logger.log_event)
        # children
        self.kanis = WeakValueDictionary()
        self.root_kani = RootKani(self.engine, app=self, system_prompt=ROOT_KANPAI, name="kanpai")

    async def init(self, browser_headless=True):
        await self.get_browser(headless=browser_headless)
        if self.dispatch_task is None:
            self.dispatch_task = asyncio.create_task(self._dispatch_task(), name="kanpai-dispatch")

    # === entrypoints ===
    async def chat_from_queue(self, q: asyncio.Queue):
        """Get chat messages from the queue."""
        await self.init()
        while True:
            try:
                user_msg = await q.get()
                log.info(f"Message from queue: {user_msg.content!r}")
                async for msg in self.root_kani.full_round(user_msg.content):
                    if msg.role == ChatRole.ASSISTANT:
                        log.info(f"AI: {msg}")
            except Exception:
                log.exception("Error in chat_from_queue:")

    async def chat_in_terminal(self):
        await self.init(browser_headless=False)
        try:
            await chat_in_terminal_async(self.root_kani)
        except KeyboardInterrupt:
            await self.close()

    # === events ===
    def add_listener(self, callback: Callable[[events.BaseEvent], Awaitable[Any]]):
        self.listeners.append(callback)

    async def _dispatch_task(self):
        while True:
            # noinspection PyBroadException
            try:
                event = await self.event_queue.get()
                # get listeners, call them
                await asyncio.gather(*(callback(event) for callback in self.listeners), return_exceptions=True)
            except Exception:
                log.exception("Exception when dispatching event:")

    def dispatch(self, event: events.BaseEvent):
        """Dispatch an event to all listeners.
        Technically this just adds it to a queue and then an async background task dispatches it."""
        self.event_queue.put_nowait(event)

    # --- kani lifecycle ---
    def on_kani_creation(self, ai: BaseKani):
        """Called by the kanpai kani constructor.
        Registers a new kani in the app, handles parent-child bookkeeping, and dispatches a KaniSpawn event."""
        self.kanis[ai.id] = ai
        if ai.parent:
            ai.parent.children[ai.id] = ai
        self.dispatch(
            events.KaniSpawn(
                id=ai.id,
                depth=ai.depth,
                parent=ai.parent.id if ai.parent else None,
                always_included_messages=ai.always_included_messages,
                chat_history=ai.chat_history,
                state=ai.state,
                name=ai.name,
            )
        )

    # === resources + app lifecycle ===
    async def get_browser(self, **kwargs) -> BrowserContext:
        """Get the current active browser context, or launch it on the first call."""
        if self.playwright is None:
            self.playwright = await async_playwright().start()
        if self.browser is None:
            self.browser = await self.playwright.chromium.launch(**kwargs)
        if self.browser_context is None:
            self.browser_context = await self.browser.new_context()
        return self.browser_context

    async def close(self):
        """Clean up all the app resources."""
        if self.dispatch_task is not None:
            self.dispatch_task.cancel()
        if self.browser is not None:
            await self.browser.close()
        if self.playwright is not None:
            await self.playwright.stop()
        await asyncio.gather(
            self.engine.close(),
            self.long_engine.close(),
            self.logger.close(),
        )
