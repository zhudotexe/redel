import logging

from kani import ChatMessage

from . import events
from .base_kani import BaseKani
from .mixins.browsing import BrowsingMixin
from .mixins.delegate_and_wait import DelegateWaitMixin
from .namer import Namer
from .prompts import DELEGATE_KANPAI

log = logging.getLogger(__name__)


class RootKani(DelegateWaitMixin, BaseKani):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.namer = Namer()

    def create_delegate_kani(self):
        name = self.namer.get_name()
        return DelegateKani(self.engine, app=self.app, parent=self, system_prompt=DELEGATE_KANPAI, name=name)

    async def add_to_history(self, message: ChatMessage):
        await super().add_to_history(message)
        if self.parent is None:
            self.app.dispatch(events.RootMessage(msg=message))


class DelegateKani(BrowsingMixin, RootKani):
    pass
