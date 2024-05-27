import asyncio
import logging
import time
import uuid
from collections.abc import AsyncIterable
from typing import Any, Awaitable, Callable
from weakref import WeakValueDictionary

from kani import ChatRole, chat_in_terminal_async
from kani.engines.openai import OpenAIEngine

from . import config, events
from .base_kani import BaseKani
from .delegation.delegate_and_wait import DelegateWaitMixin
from .eventlogger import EventLogger
from .functions.browsing import BrowsingMixin
from .kanis import ROOT_KANPAI, create_root_kani
from .utils import generate_conversation_title

log = logging.getLogger(__name__)


class Kanpai:
    """Kanpai is the core app.
    It's responsible for keeping track of all the spawned kani, and reporting their relations.
    """

    # app-global engines
    engine = OpenAIEngine(model="gpt-4", temperature=0.8, top_p=0.95, organization=config.OPENAI_ORG_ID_GPT4)
    long_engine = OpenAIEngine(model="gpt-4o", temperature=0.1)

    # engine = RatelimitedEngine(
    #     AnthropicEngine(model="claude-3-opus-20240229", temperature=0.7, max_tokens=4096), max_concurrency=1
    # )

    def __init__(self):
        # events
        self.listeners = []
        self.event_queue = asyncio.Queue()
        self.dispatch_task = None
        # state
        self.session_id = f"{int(time.time())}-{uuid.uuid4()}"
        self.title = None
        self.add_listener(self.create_title_listener)
        # logging
        self.logger = EventLogger(self, self.session_id)
        self.add_listener(self.logger.log_event)
        # kanis
        self.kanis = WeakValueDictionary()
        self.root_kani = create_root_kani(
            self.engine,
            # ReDelBase args
            delegation_scheme=DelegateWaitMixin,
            always_included_mixins=(BrowsingMixin,),
            max_delegation_depth=8,
            # BaseKani args
            app=self,
            system_prompt=ROOT_KANPAI,
            name="kanpai",
        )

    async def ensure_init(self):
        if self.dispatch_task is None:
            self.dispatch_task = asyncio.create_task(self._dispatch_task(), name="kanpai-dispatch")

    # === entrypoints ===
    async def chat_from_queue(self, q: asyncio.Queue):
        """Get chat messages from the queue."""
        await self.ensure_init()
        while True:
            # main loop
            try:
                user_msg = await q.get()
                log.info(f"Message from queue: {user_msg.content!r}")
                async for stream in self.root_kani.full_round_stream(user_msg.content):
                    msg = await stream.message()
                    if msg.role == ChatRole.ASSISTANT:
                        log.info(f"AI: {msg}")
            except Exception:
                log.exception("Error in chat_from_queue:")
            finally:
                self.dispatch(events.RoundComplete(session_id=self.session_id))

    async def chat_in_terminal(self):
        await self.ensure_init()
        while True:
            try:
                await chat_in_terminal_async(self.root_kani, show_function_args=True, rounds=1)
            except KeyboardInterrupt:
                await self.close()
            finally:
                self.dispatch(events.RoundComplete(session_id=self.session_id))

    async def query(self, query: str) -> AsyncIterable[events.BaseEvent]:
        """Run one round with the given query.

        Yields all loggable events from the app (i.e. no stream deltas) during the query. To get only messages
        from the root, filter for `events.RootMessage`.
        """
        await self.ensure_init()

        # register a new listener which passes events into a local queue
        q = asyncio.Queue()
        self.add_listener(q.put)

        # submit query to the kani to run in bg
        async def _task():
            try:
                async for _ in self.root_kani.full_round(query):
                    pass
            finally:
                self.dispatch(events.RoundComplete(session_id=self.session_id))

        task = asyncio.create_task(_task())

        # yield from the q until we get a RoundComplete
        while True:
            event = await q.get()
            if event.__log_event__:
                yield event
            if event.type == events.RoundComplete.type:
                break

        # ensure task is completed and cleanup
        await task
        self.remove_listener(q.put)

    # === events ===
    def add_listener(self, callback: Callable[[events.BaseEvent], Awaitable[Any]]):
        self.listeners.append(callback)

    def remove_listener(self, callback):
        self.listeners.remove(callback)

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
                children=list(ai.children),
                always_included_messages=ai.always_included_messages,
                chat_history=ai.chat_history,
                state=ai.state,
                name=ai.name,
            )
        )

    # === resources + app lifecycle ===
    async def create_title_listener(self, event):
        """A listener that generates a conversation title after 4 root message events."""
        if (
            self.title is None
            and isinstance(event, events.RootMessage)
            and self.logger.event_count["root_message"] >= 4
            and event.msg.role == ChatRole.ASSISTANT
            and event.msg.content
        ):
            self.title = "..."  # prevent another message from generating a title
            try:
                self.title = await generate_conversation_title(self.root_kani)
            except Exception:
                log.exception("Could not generate conversation title:")
                self.title = None
            finally:
                self.remove_listener(self.create_title_listener)

    async def close(self):
        """Clean up all the app resources."""
        if self.dispatch_task is not None:
            self.dispatch_task.cancel()
        await asyncio.gather(
            self.engine.close(),
            self.long_engine.close(),
            self.logger.close(),
            self.root_kani.close(),
            *(child.close() for child in self.kanis.values()),
        )
