from contextlib import contextmanager
from typing import AsyncIterable, TYPE_CHECKING
from weakref import WeakValueDictionary

from kani import ChatMessage, ChatRole, Kani
from kani.streaming import StreamManager

from . import events
from .state import KaniState, RunState
from .utils import create_kani_id

if TYPE_CHECKING:
    from .app import Kanpai


class BaseKani(Kani):
    """Base class for all kani in the application, regardless of recursive delegation."""

    def __init__(self, *args, app: "Kanpai", parent: "BaseKani" = None, id: str = None, name: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = RunState.STOPPED
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
        app.on_kani_creation(self)

    # ==== overrides ====
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
        if (function_call := message.function_call) and function_call.name.startswith("functions."):
            function_call.name = function_call.name.removeprefix("functions.")
        return message

    # ==== utils ====
    @property
    def last_user_message(self) -> ChatMessage | None:
        return next((m for m in self.chat_history if m.role == ChatRole.USER), None)

    def set_run_state(self, state: RunState):
        """Set the run state and dispatch the event."""
        self.state = state
        self.app.dispatch(events.KaniStateChange(id=self.id, state=self.state))

    @contextmanager
    def run_state(self, state: RunState):
        """Run the body of this statement with a different run state then set it back after."""
        old_state = self.state
        self.set_run_state(state)
        try:
            yield
        finally:
            self.set_run_state(old_state)

    def get_save_state(self) -> KaniState:
        """Get a Pydantic state suitable for saving/loading."""
        return KaniState.from_kani(self)

    async def cleanup(self):
        """This kani may run again but is done for now; clean up any ephemeral resources but save its state."""
        pass

    async def close(self):
        """The application is shutting down and all resources should be gracefully cleaned up."""
        pass
