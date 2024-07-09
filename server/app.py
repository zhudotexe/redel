import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from redel.events import Error, SendMessage
from redel.state import KaniState
from .ws import KanpaiManager

REPO_ROOT = Path(__file__).parents[1]
log = logging.getLogger("server")


class AppState(BaseModel):
    kanis: list[KaniState]


class VizServer:
    def __init__(self):
        # webserver
        self.fastapi = FastAPI(lifespan=self._lifespan)
        self.setup_app()

        # active redel states
        self.sessions: dict[str, KanpaiManager] = {}
        self._chat_tasks = set()

    @asynccontextmanager
    async def _lifespan(self, _: FastAPI):
        # todo temp
        manager = KanpaiManager()
        self.sessions["temp"] = manager
        chat_task = asyncio.create_task(manager.kanpai_app.chat_from_queue(manager.msg_queue))
        self._chat_tasks.add(chat_task)
        yield
        for task in self._chat_tasks:
            task.cancel()
        await asyncio.gather(*(session.kanpai_app.close() for session in self.sessions.values()))

    def setup_app(self):
        # cors middleware
        # noinspection PyTypeChecker
        self.fastapi.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
        )

        # routes
        @self.fastapi.get("/api/state")
        async def get_state() -> AppState:
            manager = self.sessions["temp"]  # todo
            kanis = [ai.get_save_state() for ai in manager.kanpai_app.kanis.values()]
            return AppState(kanis=kanis)

        @self.fastapi.websocket("/api/ws")
        async def ws(websocket: WebSocket):
            manager = self.sessions["temp"]  # todo
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

        # viz static files
        self.fastapi.mount("/", StaticFiles(directory=REPO_ROOT / "viz/dist", html=True), name="viz")
