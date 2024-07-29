from contextlib import contextmanager
from typing import AsyncIterable, TYPE_CHECKING
from weakref import WeakValueDictionary

from kani import ChatMessage, ChatRole, Kani
from kani.engines.base import BaseCompletion
from kani.engines.openai import OpenAIEngine
from kani.streaming import StreamManager

from . import events
from .state import KaniState, RunState
from .utils import create_kani_id

if TYPE_CHECKING:
    from .app import ReDel


class BaseKani(Kani):
    """
    Base class for all kani in the application, regardless of recursive delegation.

    Extends :class:`kani.Kani`. See the Kani documentation for more details on the internal chat state and LLM
    interface.
    """

    def __init__(
        self,
        *args,
        app: "ReDel",
        parent: "BaseKani" = None,
        id: str = None,
        name: str = None,
        dispatch_creation: bool = True,
        **kwargs,
    ):
        """
        :param app: The :class:`.ReDel` instance this kani is a part of.
        :param parent: The parent of this kani, or ``None`` if this is the root of a system.
        :param id: The internal ID of this kani. If not passed, generates a UUID.
        :param name: The human-readable name of this kani. If not passed, uses the ID.
        :param dispatch_creation: Whether to dispatch a :class:`.events.KaniSpawn` event automatically. If false, the
            caller is responsible for calling ``app.on_kani_creation()`` to dispatch the event.
        """
        super().__init__(*args, **kwargs)
        self.state = RunState.STOPPED
        self._old_state_stack = []
        # tree management
        if parent is not None:
            self.depth = parent.depth + 1
        else:
            self.depth = 0
        self.parent = parent
        self.children = WeakValueDictionary()
        # app management
        self.id = create_kani_id() if id is None else id
        self.name = self.id if name is None else name
        self.app = app
        if dispatch_creation:
            app.on_kani_creation(self)

    # ==== overrides ====
    async def get_model_completion(self, include_functions: bool = True, **kwargs) -> BaseCompletion:
        # if include_functions is False but we have functions and are using an OpenAIEngine, we should set
        # tool_choice="none" instead -- this prevents the API from exploding if we set parallel_tool_calls
        if self.functions and (not include_functions) and isinstance(self.engine, OpenAIEngine):
            include_functions = True
            kwargs["tool_choice"] = "none"

        return await super().get_model_completion(include_functions=include_functions, **kwargs)

    async def get_model_stream(self, include_functions: bool = True, **kwargs) -> AsyncIterable[str | BaseCompletion]:
        # same as above for streaming
        if self.functions and (not include_functions) and isinstance(self.engine, OpenAIEngine):
            include_functions = True
            kwargs["tool_choice"] = "none"

        async for elem in super().get_model_stream(include_functions=include_functions, **kwargs):
            yield elem

    async def chat_round(self, *args, **kwargs):
        with self.run_state(RunState.RUNNING):
            return await super().chat_round(*args, **kwargs)

    def chat_round_stream(self, *args, **kwargs) -> StreamManager:
        stream = super().chat_round_stream(*args, **kwargs)

        # consume from the inner StreamManager and re-yield with bookkeeping
        async def _impl():
            with self.run_state(RunState.RUNNING):
                async for token in stream:
                    yield token
                    self.app.dispatch(events.StreamDelta(id=self.id, delta=token, role=stream.role))
                yield await stream.completion()

        return StreamManager(_impl(), role=stream.role)

    async def full_round(self, *args, **kwargs):
        with self.run_state(RunState.RUNNING):
            async for msg in super().full_round(*args, **kwargs):
                yield msg

    async def full_round_stream(self, *args, **kwargs) -> AsyncIterable[StreamManager]:
        with self.run_state(RunState.RUNNING):
            async for stream in super().full_round_stream(*args, **kwargs):
                # consume from the inner StreamManager and re-yield with bookkeeping
                async def _impl():
                    async for token in stream:
                        yield token
                        self.app.dispatch(events.StreamDelta(id=self.id, delta=token, role=stream.role))
                    yield await stream.completion()

                yield StreamManager(_impl(), role=stream.role)

    async def add_to_history(self, message: ChatMessage):
        await super().add_to_history(message)
        self.app.dispatch(events.KaniMessage(id=self.id, msg=message))
        if self.parent is None:
            self.app.dispatch(events.RootMessage(msg=message))

    async def add_completion_to_history(self, completion):
        message = await super().add_completion_to_history(completion)
        self.app.dispatch(
            events.TokensUsed(
                id=self.id, prompt_tokens=completion.prompt_tokens, completion_tokens=completion.completion_tokens
            )
        )
        # HACK: sometimes openai's function calls are borked; we fix them here
        if message.tool_calls:
            for tc in message.tool_calls:
                if (function_call := tc.function) and function_call.name.startswith("functions."):
                    function_call.name = function_call.name.removeprefix("functions.")
        return message

    # ==== utils ====
    @property
    def last_user_message(self) -> ChatMessage | None:
        """The most recent USER message in this kani's chat history, if one exists."""
        return next((m for m in reversed(self.chat_history) if m.role == ChatRole.USER), None)

    @property
    def last_assistant_message(self) -> ChatMessage | None:
        """The most recent ASSISTANT message in this kani's chat history, if one exists."""
        return next((m for m in reversed(self.chat_history) if m.role == ChatRole.ASSISTANT), None)

    def get_save_state(self) -> KaniState:
        """Get a Pydantic state suitable for saving/loading."""
        return KaniState.from_kani(self)

    # --- state utils ---
    def set_run_state(self, state: RunState):
        """Set the run state and dispatch the event."""
        # noop if we're already in that state
        if self.state == state:
            return
        self.state = state
        self.app.dispatch(events.KaniStateChange(id=self.id, state=self.state))

    @contextmanager
    def run_state(self, state: RunState):
        """Run the body of this statement with a different run state then set it back after."""
        self._old_state_stack.append(self.state)
        self.set_run_state(state)
        try:
            yield
        finally:
            self.set_run_state(self._old_state_stack.pop())

    async def cleanup(self):
        """This kani may run again but is done for now; clean up any ephemeral resources but save its state."""
        pass

    async def close(self):
        """The application is shutting down and all resources should be gracefully cleaned up."""
        pass
