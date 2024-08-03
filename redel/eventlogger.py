import json
import logging
import pathlib
import time
from collections import Counter
from functools import cached_property
from typing import TYPE_CHECKING

from . import events
from .config import DEFAULT_LOG_DIR
from .utils import read_jsonl

if TYPE_CHECKING:
    from .app import ReDel


log = logging.getLogger(__name__)


class EventLogger:
    def __init__(self, app: "ReDel", session_id: str, log_dir: pathlib.Path = None, clear_existing_log: bool = False):
        self.app = app
        self.session_id = session_id
        self.last_modified = time.time()
        self.log_dir = log_dir or (DEFAULT_LOG_DIR / session_id)
        self.clear_existing_log = clear_existing_log

        self.aof_path = self.log_dir / "events.jsonl"
        self.state_path = self.log_dir / "state.json"

        self.event_count = Counter()

    @cached_property
    def event_file(self):
        # we use a cached property here to only lazily create the log dir if we need it
        self.log_dir.mkdir(exist_ok=True)

        if self.clear_existing_log:
            return open(self.aof_path, "w", buffering=1, encoding="utf-8")

        if self.aof_path.exists():
            existing_events = read_jsonl(self.aof_path)
            self.event_count = Counter(event["type"] for event in existing_events)
        return open(self.aof_path, "a", buffering=1, encoding="utf-8")

    async def log_event(self, event: events.BaseEvent):
        if not event.__log_event__:
            return
        self.last_modified = time.time()
        # since this is a synch operation we don't need a lock here (though it is thread-unsafe)
        self.event_file.write(event.model_dump_json())
        self.event_file.write("\n")
        self.event_count[event.type] += 1

    async def write_state(self):
        """Write the full state of the app to the state file, with a basic checksum against the AOF to check validity"""
        self.log_dir.mkdir(exist_ok=True)
        state = [ai.get_save_state().model_dump(mode="json") for ai in self.app.kanis.values()]
        data = {
            "id": self.session_id,
            "title": self.app.title,
            "last_modified": self.last_modified,
            "n_events": self.event_count.total(),
            "state": state,
        }
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    async def close(self):
        # if we haven't done anything, don't write anything
        if not self.event_count.total():
            return
        await self.write_state()
        self.event_file.close()
