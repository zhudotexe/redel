import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Body, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, WebSocketException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from redel.eventlogger import DEFAULT_LOG_DIR
from redel.events import BaseEvent, Error, SendMessage
from redel.utils import read_jsonl
from .indexer import find_saves
from .models import SaveMeta, SessionMeta, SessionState
from .session_manager import SessionManager

REPO_ROOT = Path(__file__).parents[1]
log = logging.getLogger("server")


class VizServer:
    def __init__(self, save_dirs=(DEFAULT_LOG_DIR,)):
        # archives
        self.save_dirs = save_dirs
        self.saves: dict[str, SaveMeta] = {}

        # interactive session states
        self.interactive_sessions: dict[str, SessionManager] = {}
        self._chat_tasks = set()

        # webserver
        self.fastapi = FastAPI(lifespan=self._lifespan)
        self.setup_app()

    @asynccontextmanager
    async def _lifespan(self, _: FastAPI):
        _ = asyncio.create_task(self.reindex_saves())
        yield
        for task in self._chat_tasks:
            task.cancel()
        await asyncio.gather(*(session.kanpai_app.close() for session in self.interactive_sessions.values()))

    async def reindex_saves(self):
        """Asynchronously walk the save_dirs and update self.saves."""

        def _index():
            new_saves = {}
            for root in self.save_dirs:
                for save in find_saves(root):
                    new_saves[save.id] = save
            self.saves = new_saves
            log.info(f"Finished indexing saves - {len(self.saves)} files loaded.")

        # most of the time is spent in IO with the filesystem so we can thread this
        await asyncio.get_event_loop().run_in_executor(None, _index)

    def setup_app(self):
        """Set up the FastAPI routes, middleware, etc."""
        # cors middleware
        # noinspection PyTypeChecker
        self.fastapi.add_middleware(
            CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
        )

        # ===== routes =====
        # ---- saves ----
        @self.fastapi.get("/api/saves")
        async def list_saves() -> list[SaveMeta]:
            """List all the saves the server is configured to see."""
            return list(self.saves.values())

        @self.fastapi.get("/api/saves/{save_id}")
        async def get_save_state(save_id: str) -> SessionState:
            """Get the state saves in a given save (not interactive - this just loads from file)."""
            if save_id not in self.saves:
                raise HTTPException(404, "save not found")
            save = self.saves[save_id]
            return SessionState.model_validate_json(save.state_fp.read_text())

        @self.fastapi.get("/api/saves/{save_id}/events", response_model=list[BaseEvent])
        async def get_save_events(save_id: str):
            """Get all events in a given save (not interactive - this just loads from file)."""
            if save_id not in self.saves:
                raise HTTPException(404, "save not found")
            save = self.saves[save_id]
            return list(read_jsonl(save.event_fp))

        @self.fastapi.delete("/api/saves/{save_id}")
        async def delete_save(save_id: str) -> SaveMeta:
            """Delete the state and event files of the given save, and the directory they're contained in if empty."""
            if save_id not in self.saves:
                raise HTTPException(404, "save not found")
            save = self.saves[save_id]
            try:
                save.state_fp.unlink(missing_ok=True)
                save.event_fp.unlink(missing_ok=True)
                del self.saves[save_id]
                save.state_fp.parent.rmdir()
            except FileNotFoundError:
                raise HTTPException(404, "save not found")
            except OSError as e:
                # probably additional files - let's just log it
                log.warning(f"Could not fully delete save: {e}")
            return save

        # todo: load save

        # ---- interactive ----
        @self.fastapi.get("/api/states")
        async def list_states_interactive() -> list[SessionMeta]:
            """List the interactive sessions currently loaded by the server."""
            return [manager.get_session_meta() for manager in self.interactive_sessions.values()]

        @self.fastapi.post("/api/states")
        async def create_state_interactive(start_content: Annotated[str, Body(embed=True)] = None) -> SessionState:
            """Create a fresh new interactive session, optionally with a first user message.
            This will also create a new save.
            """
            manager = SessionManager(self)
            self.interactive_sessions[manager.kanpai_app.session_id] = manager
            self.saves[manager.kanpai_app.session_id] = manager.get_save_meta()
            chat_task = asyncio.create_task(manager.kanpai_app.chat_from_queue(manager.msg_queue))
            self._chat_tasks.add(chat_task)
            if start_content:
                await manager.msg_queue.put(SendMessage(content=start_content))
            return manager.get_state()

        @self.fastapi.get("/api/states/{session_id}")
        async def get_state_interactive(session_id: str) -> SessionState:
            """Get the state of a specific interactive session loaded in the server."""
            if session_id not in self.interactive_sessions:
                raise HTTPException(404, "session is not initialized - load from archive or create new first")
            manager = self.interactive_sessions[session_id]
            return manager.get_state()

        @self.fastapi.websocket("/api/ws/{session_id}")
        async def ws_interactive(websocket: WebSocket, session_id: str):
            """Stream events from a given session loaded in the server."""
            if session_id not in self.interactive_sessions:
                raise WebSocketException(
                    1008,  # policy violation
                    "session is not initialized - load from archive or create new first",
                )
            manager = self.interactive_sessions[session_id]
            await manager.connect(websocket)
            while True:
                try:
                    data = await websocket.receive_text()
                    log.debug(f"got data from ws for session {session_id}: {data}")
                    event = SendMessage.model_validate_json(data)  # todo additional message types
                    await manager.msg_queue.put(event)
                except WebSocketDisconnect:
                    manager.disconnect(websocket)
                    break
                except Exception as e:
                    log.exception(f"Exception on ws event in session {session_id}:")
                    await websocket.send_text(Error(msg=str(e)).model_dump_json())

        # viz static files
        self.fastapi.mount("/", StaticFiles(directory=REPO_ROOT / "viz/dist", html=True), name="viz")
