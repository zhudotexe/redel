import asyncio
import functools
import logging
import time
import uuid
from collections.abc import AsyncIterable
from pathlib import Path
from typing import Any, Awaitable, Callable
from weakref import WeakValueDictionary

from kani import ChatRole, chat_in_terminal_async
from kani.engines import BaseEngine
from kani.engines.openai import OpenAIEngine

from . import config, events
from .base_kani import BaseKani
from .delegation.delegate_and_wait import DelegateWaitMixin
from .eventlogger import EventLogger
from .kanis import DELEGATE_KANPAI, ROOT_KANPAI, create_root_kani
from .tool_config import ToolConfigType, validate_tool_configs
from .utils import generate_conversation_title

log = logging.getLogger(__name__)
AUTOGENERATE_TITLE = object()


@functools.cache
def default_engine():
    return OpenAIEngine(model="gpt-4", temperature=0.8, top_p=0.95, organization=config.OPENAI_ORG_ID_GPT4)


@functools.cache
def default_long_engine():
    # engine = RatelimitedEngine(
    #     AnthropicEngine(model="claude-3-opus-20240229", temperature=0.7, max_tokens=4096), max_concurrency=1
    # )
    return OpenAIEngine(model="gpt-4o", temperature=0.1)


class Kanpai:
    """This class is the monolithic core app. It represents a single session with recursive delegation.

    It's responsible for:
    - all delegation configuration options
    - all the spawned kani and their relations within the session
    - dispatching all events from the session
    - logging events
    """

    def __init__(
        self,
        *,
        # engines
        root_engine: BaseEngine = None,
        delegate_engine: BaseEngine = None,
        long_engine: BaseEngine = None,
        # prompt/kani
        root_system_prompt: str | None = ROOT_KANPAI,
        root_kani_kwargs: dict = None,
        delegate_system_prompt: str | None = DELEGATE_KANPAI,
        delegate_kani_kwargs: dict = None,
        # delegation/function calling
        delegation_scheme: type | None = DelegateWaitMixin,
        max_delegation_depth: int = 8,
        tool_configs: ToolConfigType = None,
        root_has_tools: bool = False,
        # logging
        title: str = None,
        log_dir: Path = None,
        clear_existing_log: bool = False,
    ):
        """
        :param root_engine: The engine to use for the root kani. Requires function calling. (default: gpt-4)
        :param delegate_engine: The engine to use for each delegate kani. Requires function calling. (default: gpt-4)
        :param long_engine: The engine to use for long-context tasks (e.g. summarization of long web pages). Does not
            require function calling. (default: gpt-4o)
        :param root_system_prompt: The system prompt for the root kani. See ``redel.kanis`` for default.
        :param root_kani_kwargs: Additional keyword args to pass to :class:``kani.Kani``.
        :param delegate_system_prompt: The system prompt for the each delegate kani. See ``redel.kanis`` for default.
        :param delegate_kani_kwargs: Additional keyword args to pass to :class:``kani.Kani``.
        :param delegation_scheme: A class that each kani capable of delegation will inherit from. See
            ``redel.delegation`` for examples. This class can assume the existence of a ``create_delegate_kani`` method.
            Can be ``None`` to disable delegation (this makes ReDel a nice kani visualization tool).
        :param max_delegation_depth: The maximum delegation depth. Kanis created at this depth will not inherit from the
            ``delegation_scheme`` class.
        :param tool_configs: A mapping of tool mixin classes to their configurations (see :class:`.ToolConfig`).
        :param root_has_tools: Whether the root kani should have access to the configured tools (default
            False).
        :param title: The title of this session. Set to ``AUTOGENERATE_TITLE`` to automatically generate one.
        :param log_dir: A path to a directory to save logs for this session. Defaults to ``.kanpai/{session_id}/``.
        :param clear_existing_log: If the log directory has existing events, clear them before writing new events.
            Otherwise, append to existing events.
        """
        if root_engine is None:
            root_engine = default_engine()
        if delegate_engine is None:
            delegate_engine = default_engine()
        if long_engine is None:
            long_engine = default_long_engine()
        if root_kani_kwargs is None:
            root_kani_kwargs = {}
        if delegate_kani_kwargs is None:
            delegate_kani_kwargs = {}
        if tool_configs is None:
            tool_configs = {}

        validate_tool_configs(tool_configs)

        # engines
        self.root_engine = root_engine
        self.delegate_engine = delegate_engine
        self.long_engine = long_engine
        # prompt/kani
        self.root_system_prompt = root_system_prompt
        self.root_kani_kwargs = root_kani_kwargs
        self.delegate_system_prompt = delegate_system_prompt
        self.delegate_kani_kwargs = delegate_kani_kwargs
        # delegation/function calling
        self.delegation_scheme = delegation_scheme
        self.max_delegation_depth = max_delegation_depth
        self.tool_configs = tool_configs
        self.root_has_tools = root_has_tools

        # events
        self.listeners = []
        self.event_queue = asyncio.Queue()
        self.dispatch_task = None
        # state
        self.session_id = f"{int(time.time())}-{uuid.uuid4()}"
        if title is AUTOGENERATE_TITLE:
            self.title = None
            self.add_listener(self.create_title_listener)
        else:
            self.title = title
        # logging
        self.logger = EventLogger(self, self.session_id, log_dir=log_dir, clear_existing_log=clear_existing_log)
        self.add_listener(self.logger.log_event)
        # kanis
        self.kanis = WeakValueDictionary()
        self.root_kani = create_root_kani(
            self.root_engine,
            # create_root_kani args
            delegation_scheme=delegation_scheme,
            tool_configs=tool_configs,
            root_has_tools=root_has_tools,
            # BaseKani args
            app=self,
            name="kanpai",
            # Kani args
            system_prompt=root_system_prompt,
            **root_kani_kwargs,
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
            if event.type == "round_complete":
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
        self.dispatch(events.KaniSpawn.from_kani(ai))

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
            self.logger.close(),
            self.root_kani.close(),
            *(child.close() for child in self.kanis.values()),
        )
