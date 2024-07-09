import asyncio

from fastapi import WebSocket
from kani.engines.anthropic import AnthropicEngine
from kani.engines.openai import OpenAIEngine
from kani.ext.ratelimits import RatelimitedEngine

from redel import Kanpai
from redel.events import BaseEvent
from redel.tools.browsing import BrowsingMixin

engine = OpenAIEngine(model="gpt-4", temperature=0.8, top_p=0.95)
long_engine = RatelimitedEngine(
    AnthropicEngine(model="claude-3-opus-20240229", temperature=0.7, max_tokens=4096), max_concurrency=1
)

class KanpaiManager:
    def __init__(self):
        self.kanpai_app = Kanpai(
            root_engine=engine,
            delegate_engine=engine,
            tool_configs={
                BrowsingMixin: {
                    "always_include": True,
                    "kwargs": {"long_engine": long_engine},
                },
            }
        )
        self.kanpai_app.add_listener(self.on_event)
        self.msg_queue = asyncio.Queue()
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: str):
        for connection in self.active_connections:
            await connection.send_text(data)

    async def on_event(self, event: BaseEvent):
        await self.broadcast(event.model_dump_json())