"""
Visualized UI for interacting with kanpai.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from redel import Kanpai
from redel.events import BaseEvent, Error, SendMessage
from redel.state import KaniState
from redel.tools.browsing import BrowsingMixin

log = logging.getLogger("viz-app")

from kani.engines.openai import OpenAIEngine
from redel.delegation.delegate_one import Delegate1Mixin
from redel.tools.fanoutqa.impl import FanOutQAMixin

SYSTEM_TEST = (
    "# Delegation Instructions\n\nUnless you are certain the user's question can be answered in one step, you should"
    " break it up into smaller pieces and delegate those pieces.\nYou should retry with different phrasing if your"
    " helper does not return a useful answer. Don't give up!"
)

root_engine = OpenAIEngine(model="gpt-4o", temperature=0)
delegate_engine = OpenAIEngine(model="gpt-3.5-turbo", temperature=0)
foqa_test = Kanpai(
    root_engine=root_engine,
    delegate_engine=delegate_engine,
    long_engine=root_engine,
    root_system_prompt=SYSTEM_TEST,
    delegate_system_prompt=SYSTEM_TEST,
    delegation_scheme=Delegate1Mixin,
    tool_configs={
        FanOutQAMixin: {
            "always_include": True,
            "kwargs": {"foqa_config": dict(do_long_engine_upgrade=False, retrieval_type="openai")},
        },
    },
    root_has_tools=False,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    chat_task = asyncio.create_task(manager.kanpai_app.chat_from_queue(manager.msg_queue))
    yield
    chat_task.cancel()
    await manager.kanpai_app.close()


# ws utils
class KanpaiManager:
    def __init__(self):
        # self.kanpai_app = Kanpai(
        #     tool_configs={
        #         BrowsingMixin: {"always_include": True},
        #     }
        # )
        self.kanpai_app = foqa_test
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
