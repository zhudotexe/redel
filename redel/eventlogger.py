import asyncio
import json
import logging
import pathlib
import time
from collections import Counter
from typing import TYPE_CHECKING

from . import events
from .utils import read_jsonl

if TYPE_CHECKING:
    from .app import Kanpai

DEFAULT_LOG_DIR = pathlib.Path(__file__).parents[1] / ".kanpai/instances"
DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True)

log = logging.getLogger(__name__)


class EventLogger:
    def __init__(self, app: "Kanpai", session_id: str, log_dir: pathlib.Path = None, clear_existing_log: bool = False):
        self.app = app
        self.session_id = session_id
        self.log_dir = log_dir or (DEFAULT_LOG_DIR / session_id)
        self.log_dir.mkdir(exist_ok=True)
        self._save_lock = asyncio.Lock()

        if clear_existing_log:
            self.event_file = open(self.log_dir / f"events.jsonl", "w")
            self.event_count = Counter()
        else:
            aof_path = self.log_dir / f"events.jsonl"
            if aof_path.exists():
                existing_events = read_jsonl(self.log_dir / f"events.jsonl")
                self.event_count = Counter(event["type"] for event in existing_events)
            else:
                self.event_count = Counter()
            self.event_file = open(aof_path, "a")

    async def log_event(self, event: events.BaseEvent):
        if not event.__log_event__:
            return
        self.event_file.write(event.model_dump_json())
        self.event_file.write("\n")
        self.event_count[event.type] += 1

    async def write_state(self):
        """Write the full state of the app to the state file, with a basic checksum against the AOF to check validity"""
        state = [ai.get_save_state().model_dump(mode="json") for ai in self.app.kanis.values()]
        data = {
            "id": self.session_id,
            "title": self.app.title,
            "last_modified": time.time(),
            "n_events": self.event_count.total(),
            "state": state,
        }
        async with self._save_lock:
            with open(self.log_dir / "state.json", "w") as f:
                json.dump(data, f, indent=2)

    async def close(self):
        await self.write_state()
        self.event_file.close()
