import logging

from .base_kani import BaseKani
from .mixins.browsing import BrowsingMixin
from .mixins.delegate_one import Delegate1Mixin
from .prompts import DELEGATE_KANPAI

log = logging.getLogger(__name__)


class RootKani(Delegate1Mixin, BaseKani):
    def create_delegate_kani(self):
        return DelegateKani(self.engine, app=self.app, system_prompt=DELEGATE_KANPAI)


class DelegateKani(BrowsingMixin, RootKani):
    pass
