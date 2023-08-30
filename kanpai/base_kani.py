from typing import TYPE_CHECKING
from weakref import WeakValueDictionary

from kani import Kani

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
