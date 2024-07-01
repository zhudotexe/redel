"""
Visualized UI for interacting with kanpai.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from kani.engines.anthropic import AnthropicEngine
from kani.ext.ratelimits import RatelimitedEngine
from pydantic import BaseModel

from redel import Kanpai
from redel.events import BaseEvent, Error, SendMessage
from redel.state import KaniState
from redel.tools.browsing import BrowsingMixin

log = logging.getLogger("viz-app")

long_engine = RatelimitedEngine(
    AnthropicEngine(model="claude-3-opus-20240229", temperature=0.7, max_tokens=4096), max_concurrency=1
)
# long_engine = OpenAIEngine(model="gpt-4o", temperature=0.1)


@asynccontextmanager
async def lifespan(_: FastAPI):
    chat_task = asyncio.create_task(manager.kanpai_app.chat_from_queue(manager.msg_queue))
    yield
    chat_task.cancel()
    await manager.kanpai_app.close()


# ws utils
class KanpaiManager:
    def __init__(self):
        self.kanpai_app = Kanpai(
            tool_configs={
                BrowsingMixin: {
                    "always_include": True,
                    "kwargs": {"browsing_long_engine": long_engine},
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


manager = KanpaiManager()
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


# state utils
class AppState(BaseModel):
    kanis: list[KaniState]


# routes
@app.get("/api/state")
async def get_state() -> AppState:
    kanis = [ai.get_save_state() for ai in manager.kanpai_app.kanis.values()]
    return AppState(kanis=kanis)


@app.websocket("/api/ws")
async def ws(websocket: WebSocket):
    await manager.connect(websocket)
    while True:
        try:
            data = await websocket.receive_text()
            log.debug(f"got data: {data}")
            event = SendMessage.model_validate_json(data)
            await manager.msg_queue.put(event)
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            break
        except Exception as e:
            log.exception("Exception on ws event:")
            await websocket.send_text(Error(msg=str(e)).model_dump_json())


app.mount("/", StaticFiles(directory="viz/dist", html=True), name="viz")

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app)
