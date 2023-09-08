"""
Visualized UI for interacting with kanpai.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from kani import ChatMessage
from pydantic import BaseModel

from kanpai import Kanpai
from kanpai.events import BaseEvent, Error, SendMessage

log = logging.getLogger("viz-app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    chat_task = asyncio.create_task(manager.kanpai_app.chat_from_queue(manager.msg_queue))
    yield
    chat_task.cancel()
    await manager.kanpai_app.close()


# ws utils
class KanpaiManager:
    def __init__(self):
        self.kanpai_app = Kanpai()
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
class KaniState(BaseModel):
    id: str
    parent: str | None
    children: list[str]
    always_included_messages: list[ChatMessage]
    chat_history: list[ChatMessage]


class AppState(BaseModel):
    kanis: list[KaniState]


# routes
@app.get("/api/state")
async def get_state() -> AppState:
    kanis = [
        KaniState(
            id=ai.id,
            parent=ai.parent.id if ai.parent else None,
            children=list(ai.children),
            always_included_messages=ai.always_included_messages,
            chat_history=ai.chat_history,
        )
        for ai in manager.kanpai_app.kanis.values()
    ]
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


app.mount("/", StaticFiles(directory="kanpai-viz/dist", html=True), name="viz")

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app)
