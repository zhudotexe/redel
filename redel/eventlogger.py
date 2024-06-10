import json
import logging
import pathlib
import time
from collections import Counter
from typing import TYPE_CHECKING

from . import events

if TYPE_CHECKING:
    from .app import Kanpai

LOG_BASE = pathlib.Path(__file__).parents[1] / ".kanpai/instances"
LOG_BASE.mkdir(parents=True, exist_ok=True)

log = logging.getLogger(__name__)


class EventLogger:
    def __init__(self, app: "Kanpai", session_id: str, log_dir: pathlib.Path = None, clear_existing_log: bool = False):
        self.app = app
        self.session_id = session_id
        self.log_dir = log_dir or (LOG_BASE / session_id)
        self.log_dir.mkdir(exist_ok=True)

        log_mode = "w" if clear_existing_log else "a"
        self.event_file = open(self.log_dir / f"events.jsonl", log_mode)
        self.event_count = Counter()

    async def log_event(self, event: events.BaseEvent):
        if not event.__log_event__:
            return
        self.event_file.write(event.model_dump_json())
        self.event_file.write("\n")
        self.event_count[event.type] += 1

    def write_state(self):
        """Write the full state of the app to the state file, with a basic checksum against the AOF to check validity"""
        state = [ai.get_save_state().model_dump(mode="json") for ai in self.app.kanis.values()]
        data = {
            "id": self.session_id,
            "title": self.app.title,
            "last_modified": time.time(),
            "n_events": self.event_count.total(),
            "state": state,
        }
        with open(self.log_dir / "state.json", "w") as f:
            json.dump(data, f, indent=2)

    async def close(self):
        self.write_state()
        self.event_file.close()
