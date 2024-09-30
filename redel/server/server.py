import asyncio
import logging
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Awaitable, Callable, Collection, TYPE_CHECKING

try:
    from fastapi import Body, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, WebSocketException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
except ImportError:
    raise ImportError(
        "You are missing required dependencies to use the bundled web viewer. Please install ReDel using `pip install"
        ' "redel[web]"`.'
    ) from None

from redel import ReDel
from redel.config import DEFAULT_LOG_DIR
from redel.events import Error, SendMessage
from redel.kanis import ReDelKani, create_root_kani
from redel.utils import read_jsonl
from .indexer import find_saves
from .models import LoadSavePayload, SaveMeta, SessionMeta, SessionState
from .session_manager import SessionManager

if TYPE_CHECKING:
    from redel.state import KaniState

VIZ_DIST = Path(__file__).parent / "viz_dist"
log = logging.getLogger("server")


class VizServer:
    def __init__(
        self,
        redel_proto: ReDel = None,
        /,
        *,
        save_dirs: Collection[Path] = (DEFAULT_LOG_DIR,),
        redel_factory: Callable[[...], Awaitable[ReDel]] = None,
    ):
        """
        :param redel_proto: If passed, interactive sessions will use the same configuration as the given prototype.
            Mutually exclusive with ``redel_factory``.
        :param save_dirs: A list of paths to scan for ReDel saves to make available to load. Defaults to
            ``~/.redel/instances/``.
        :param redel_factory: An asynchronous function that creates a new :class:`.ReDel` instance when called.
            If this is set, ``redel_proto`` must not be set.
        """
        if redel_proto and redel_factory:
            raise ValueError("At most one of ('redel_proto', 'redel_factory') may be supplied.")
        elif not (redel_proto or redel_factory):
            redel_proto = ReDel()
        self.redel_proto = redel_proto
        self.redel_factory = redel_factory

        # saves
        self.save_dirs = save_dirs
        self.saves: dict[str, SaveMeta] = {}

        # interactive session states
        self.interactive_sessions: dict[str, SessionManager] = {}

        # webserver
        self.fastapi = FastAPI(lifespan=self._lifespan)
        self.setup_app()

    # ==== utils ====
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

    async def create_new_redel(self, **override_kwargs) -> ReDel:
        """Return a new ReDel instance given the server config."""
        if self.redel_proto:
            return ReDel(**(self.redel_proto.get_config() | override_kwargs))
        return await self.redel_factory(**override_kwargs)

    def serve(self, host="127.0.0.1", port=8000, **kwargs):
        """Serve this server at the given IP and port. Blocks until interrupted."""
        import uvicorn

        uvicorn.run(self.fastapi, host=host, port=port, **kwargs)

    # ==== fastapi ====
    @asynccontextmanager
    async def _lifespan(self, _: FastAPI):
        _ = asyncio.create_task(self.reindex_saves())
        yield
        await asyncio.gather(*(session.close() for session in self.interactive_sessions.values()))

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

        @self.fastapi.get("/api/saves/{save_id}/events")
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
                if manager := self.interactive_sessions.pop(save_id, None):
                    await manager.close()
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

        @self.fastapi.post("/api/saves/{save_id}/load")
        async def load_save_to_interactive(save_id: str, payload: LoadSavePayload) -> SessionState:
            """
            Load the state into interactive memory, with a fresh new ReDel instance as the config.

            Payload:

                {
                    "fork": true  // if fork, make a copy into interactive memory
                }
            """
            # load save
            if save_id not in self.saves:
                raise HTTPException(404, "save not found")
            save = self.saves[save_id]
            state = SessionState.model_validate_json(save.state_fp.read_text())

            # create a new redel instance given the settings, with meta from saves
            if payload.fork:
                redel = await self.create_new_redel(title=state.title, clear_existing_log=False)
                # copy existing AOF over - state file will be written on first interaction
                try:
                    redel.logger.log_dir.mkdir(exist_ok=True)
                    shutil.copy(save.event_fp, redel.logger.aof_path)
                except FileNotFoundError:
                    pass
            else:
                redel = await self.create_new_redel(
                    session_id=state.id,
                    title=state.title,
                    log_dir=save.state_fp.parent,
                    clear_existing_log=False,
                )

            with redel.logger.suppress_logs():
                # load the root (if it exists)
                state_map = {s.id: s for s in state.state}
                root_kani_state = next((s for s in state.state if s.depth == 0), None)
                if root_kani_state:
                    root_kani = await create_root_kani(
                        redel.root_engine,
                        # create_root_kani args
                        app=redel,
                        delegation_scheme=redel.delegation_scheme,
                        tool_configs=redel.tool_configs,
                        root_has_tools=redel.root_has_tools,
                        # BaseKani args
                        name=root_kani_state.name,
                        # Kani args
                        system_prompt=redel.root_system_prompt,
                        always_included_messages=root_kani_state.always_included_messages,
                        chat_history=root_kani_state.chat_history,
                        **redel.root_kani_kwargs,
                    )
                    redel.root_kani = root_kani

                    await redel.ensure_init()

                    # DFS load the kani states into the redel instance
                    async def load_child_states(ai: "ReDelKani", ai_state: "KaniState"):
                        for child_id in ai_state.children:
                            child_state = state_map[child_id]  # should always exist
                            # create and register child instance
                            child_kani = ReDelKani(
                                redel.delegate_engine,
                                # app args
                                app=redel,
                                parent=ai,
                                id=child_state.id,
                                name=child_state.name,
                                dispatch_creation=False,
                                # kani args
                                system_prompt=redel.delegate_system_prompt,
                                always_included_messages=child_state.always_included_messages,
                                chat_history=child_state.chat_history,
                                **redel.delegate_kani_kwargs,
                            )
                            await ai.register_child_kani(child_kani, instructions=None)
                            await load_child_states(child_kani, child_state)

                    await load_child_states(root_kani, root_kani_state)
                    await redel.drain()

            # assign it to a sessionmanager and start
            manager = SessionManager(self, redel)
            self.interactive_sessions[redel.session_id] = manager
            self.saves[redel.session_id] = manager.get_save_meta()
            await manager.start()
            return manager.get_state()

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
            # create a new redel instance given the settings
            redel = await self.create_new_redel()
            # assign it to a sessionmanager and start
            manager = SessionManager(self, redel)
            self.interactive_sessions[redel.session_id] = manager
            self.saves[redel.session_id] = manager.get_save_meta()
            await manager.start()
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
        if not VIZ_DIST.exists():
            raise RuntimeError(
                f"The {VIZ_DIST} directory does not exist. If you have cloned ReDel from source, this is likely because"
                " you need to build the web frontend.\nSee"
                " https://redel.readthedocs.io/en/latest/install.html#building-web-interface for more information."
            )
        self.fastapi.mount("/", StaticFiles(directory=VIZ_DIST, html=True), name="viz")
