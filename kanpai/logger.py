import json
import logging
import pathlib
import time
from collections import Counter
from typing import TYPE_CHECKING

from kani import ChatRole
from kani.exceptions import KaniException

from . import events
from .utils import generate_conversation_title

if TYPE_CHECKING:
    from .app import Kanpai

LOG_BASE = pathlib.Path(__file__).parents[1] / ".kanpai"
LOG_BASE.mkdir(exist_ok=True)

log = logging.getLogger(__name__)


class Logger:
    def __init__(self, app: "Kanpai", session_id: str):
        self.app = app
        self.session_id = session_id
        self.log_dir = LOG_BASE / session_id
        self.log_dir.mkdir(exist_ok=True)
        self.events = open(self.log_dir / f"events.jsonl", "a")

        self.event_count = Counter()
        self.title = None

    async def log_event(self, event: events.BaseEvent):
        self.events.write(event.model_dump_json())
        self.events.write("\n")
        self.event_count[event.type] += 1

        # generate a title for the chat when we get 2 rounds in
        if (
            self.title is None
            and isinstance(event, events.RootMessage)
            and self.event_count["root_message"] >= 4
            and event.msg.role == ChatRole.ASSISTANT
            and event.msg.content
        ):
            self.title = "..."  # prevent another message from generating a title
            try:
                self.title = await generate_conversation_title(self.app.root_kani)
            except KaniException:
                log.exception("Could not generate conversation title:")
                self.title = None

    def write_state(self):
        """Write the full state of the app to the state file, with a basic checksum against the AOF to check validity"""
        state = [ai.get_save_state().model_dump(mode="json") for ai in self.app.kanis.values()]
        data = {
            "id": self.session_id,
            "title": self.title,
            "last_modified": time.time(),
            "n_events": self.event_count.total(),
            "state": state,
        }
        with open(self.log_dir / "state.json", "w") as f:
            json.dump(data, f, indent=2)

    async def close(self):
        self.write_state()
        self.events.close()
