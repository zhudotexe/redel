from typing import TYPE_CHECKING
from weakref import WeakValueDictionary

from kani import ChatMessage, ChatRole, Kani

from . import events
from .utils import create_kani_id

if TYPE_CHECKING:
    from .app import Kanpai


class BaseKani(Kani):
    def __init__(self, *args, app: "Kanpai", parent: "BaseKani" = None, id: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        # tree management
        if parent is not None:
            self.depth = parent.depth + 1
        else:
            self.depth = 0
        self.parent = parent
        self.children = WeakValueDictionary()
        # app management
        self.id = create_kani_id() if id is None else id
        self.app = app
        app.on_kani_creation(self)

    # ==== overrides ====
    async def add_to_history(self, message: ChatMessage):
        await super().add_to_history(message)
        self.app.dispatch(events.KaniMessage(id=self.id, msg=message))

    # ==== utils ====
    @property
    def last_user_message(self) -> ChatMessage | None:
        return next((m for m in self.chat_history if m.role == ChatRole.USER), None)
