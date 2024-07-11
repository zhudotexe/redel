import asyncio

from fastapi import WebSocket
from kani.engines.anthropic import AnthropicEngine
from kani.engines.openai import OpenAIEngine
from kani.ext.ratelimits import RatelimitedEngine

from redel import Kanpai
from redel.events import BaseEvent, RoundComplete
from redel.tools.browsing import BrowsingMixin
from .models import SaveMeta, SessionMeta, SessionState

engine = OpenAIEngine(model="gpt-4", temperature=0.8, top_p=0.95)
long_engine = RatelimitedEngine(
    AnthropicEngine(model="claude-3-opus-20240229", temperature=0.7, max_tokens=4096), max_concurrency=1
)


class SessionManager:
    """Responsible for a single session and all connections to it."""

    def __init__(self, server):
        self.server = server
        self.kanpai_app = Kanpai(
            root_engine=engine,
            delegate_engine=engine,
            tool_configs={
                BrowsingMixin: {
                    "always_include": True,
                    "kwargs": {"long_engine": long_engine},
                },
            },
        )
        self.kanpai_app.add_listener(self.on_event)
        self.msg_queue = asyncio.Queue()
        self.active_connections: list[WebSocket] = []

    # ==== state ====
    def get_state(self) -> SessionState:
        kanis = [ai.get_save_state() for ai in self.kanpai_app.kanis.values()]
        return SessionState(
            id=self.kanpai_app.session_id,
            title=self.kanpai_app.title,
            last_modified=self.kanpai_app.logger.last_modified,
            n_events=self.kanpai_app.logger.event_count.total(),
            state=kanis,
        )

    def get_session_meta(self) -> SessionMeta:
        return SessionMeta(
            id=self.kanpai_app.session_id,
            title=self.kanpai_app.title,
            last_modified=self.kanpai_app.logger.last_modified,
            n_events=self.kanpai_app.logger.event_count.total(),
        )

    def get_save_meta(self) -> SaveMeta:
        return SaveMeta(
            id=self.kanpai_app.session_id,
            title=self.kanpai_app.title,
            last_modified=self.kanpai_app.logger.last_modified,
            n_events=self.kanpai_app.logger.event_count.total(),
            state_fp=self.kanpai_app.logger.state_path,
            event_fp=self.kanpai_app.logger.aof_path,
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
            self.server.saves[self.kanpai_app.session_id] = self.get_save_meta()
