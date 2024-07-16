import asyncio
from typing import TYPE_CHECKING

from fastapi import WebSocket

from redel import ReDel
from redel.events import BaseEvent, RoundComplete
from .models import SaveMeta, SessionMeta, SessionState

if TYPE_CHECKING:
    from .server import VizServer


class SessionManager:
    """Responsible for a single session and all connections to it."""

    def __init__(self, server: "VizServer", redel: ReDel):
        self.server = server
        self.redel = redel
        self.redel.add_listener(self.on_event)
        self.task = None
        self.msg_queue = asyncio.Queue()
        self.active_connections: list[WebSocket] = []

    # ==== lifecycle ====
    async def start(self):
        if self.task is not None:
            raise RuntimeError("This session has already been started.")
        self.task = asyncio.create_task(self.redel.chat_from_queue(self.msg_queue))

    async def close(self):
        if self.task is not None:
            self.task.cancel()
        await self.redel.close()

    # ==== state ====
    def get_state(self) -> SessionState:
        kanis = [ai.get_save_state() for ai in self.redel.kanis.values()]
        return SessionState(
            id=self.redel.session_id,
            title=self.redel.title,
            last_modified=self.redel.logger.last_modified,
            n_events=self.redel.logger.event_count.total(),
            state=kanis,
        )

    def get_session_meta(self) -> SessionMeta:
        return SessionMeta(
            id=self.redel.session_id,
            title=self.redel.title,
            last_modified=self.redel.logger.last_modified,
            n_events=self.redel.logger.event_count.total(),
        )

    def get_save_meta(self) -> SaveMeta:
        return SaveMeta(
            id=self.redel.session_id,
            title=self.redel.title,
            last_modified=self.redel.logger.last_modified,
            n_events=self.redel.logger.event_count.total(),
            grouping_prefix=self.redel.logger.log_dir.parent.parts,
            state_fp=self.redel.logger.state_path,
            event_fp=self.redel.logger.aof_path,
        )

    # ==== ws ====
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: str):
        await asyncio.gather(
            *(connection.send_text(data) for connection in self.active_connections), return_exceptions=True
        )

    async def on_event(self, event: BaseEvent):
        await self.broadcast(event.model_dump_json())
        # update the server save info on each RoundComplete
        if isinstance(event, RoundComplete):
            self.server.saves[self.redel.session_id] = self.get_save_meta()
